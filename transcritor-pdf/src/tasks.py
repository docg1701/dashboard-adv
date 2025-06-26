from src.celery_app import celery_app
from src.processing import process_pdf_pipeline # Import from the new processing module

# If direct import of process_pdf_pipeline causes issues due to FastAPI app context
# or other main.py specific initializations, the core logic of
# process_pdf_pipeline might need to be extracted into a separate utility module
# that both main.py and tasks.py can import.
import logging
from sqlalchemy import text
from src.core.database import get_db_contextmanager, initialize_database
from typing import Optional # Added for type hinting

# Prometheus client for custom metrics
from prometheus_client import Counter

logger = logging.getLogger(__name__)

# --- Prometheus Custom Metrics for Celery Tasks ---
CELERY_PDF_TASKS_TOTAL = Counter(
    'transcritor_celery_pdf_tasks_total', # Metric name
    'Total number of PDF processing Celery tasks.', # Description
    ['task_name', 'status'] # Labels: task name and final status (success, failure)
)
# Note: It's good practice to initialize metrics at the module level (i.e., when the worker starts).
# This ensures they are registered with the Prometheus client registry.
# If this file is imported by multiple workers, this Counter will refer to the same metric object.

# Define retry parameters
RETRY_EXCEPTIONS = (Exception,) # Retry on generic Exception for now, can be refined
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = True # Enable exponential backoff
RETRY_BACKOFF_MAX_SECONDS = 600 # Max delay 10 minutes
RETRY_JITTER = True # Add jitter to backoff

@celery_app.task(
    name='src.tasks.process_pdf_task',
    bind=True,  # Bind task instance to self
    autoretry_for=RETRY_EXCEPTIONS,
    max_retries=MAX_RETRIES,
    retry_backoff=RETRY_BACKOFF_SECONDS,
    retry_backoff_max=RETRY_BACKOFF_MAX_SECONDS,
    retry_jitter=RETRY_JITTER
)
def process_pdf_task(self, file_content_bytes: bytes, filename: str, document_id: int) -> dict: # Added self, document_id
    '''
    Celery task to process a PDF file with retry logic and final failure handling.
    Relies on process_pdf_pipeline for the core logic.
    Now requires document_id to link chunks to the parent document.
    '''
    logger.info(f"Celery task started for file: {filename}, document_id: {document_id}. Attempt: {self.request.retries + 1}/{MAX_RETRIES + 1}")
    task_name = self.name # or 'process_pdf_task' directly

    initialize_database() # Idempotent, ensures DB is ready for potential status updates

    try:
        import asyncio
        result_summary = asyncio.run(process_pdf_pipeline(
            file_content=file_content_bytes,
            filename=filename,
            document_id=document_id
        ))

        pipeline_status = result_summary.get("status", "unknown_pipeline_status")
        logger.info(f"Celery task processing completed for: {filename} (Doc ID: {document_id}). Pipeline status: {pipeline_status}")

        if pipeline_status.startswith("error_"):
            logger.error(f"Pipeline reported error for {filename} (Doc ID: {document_id}): {result_summary.get('message')}")
            _update_document_status_on_failure(document_id, "FALHOU_PROCESSAMENTO_INTERNO", result_summary.get('message', 'Pipeline error'))
            CELERY_PDF_TASKS_TOTAL.labels(task_name=task_name, status='failure_pipeline').inc()
        elif pipeline_status == "success":
            CELERY_PDF_TASKS_TOTAL.labels(task_name=task_name, status='success').inc()
        else: # e.g. "completed_with_no_chunks"
            CELERY_PDF_TASKS_TOTAL.labels(task_name=task_name, status=pipeline_status).inc()

        return result_summary

    except Exception as e:
        logger.error(f"Celery task attempt {self.request.retries + 1} failed for {filename} (Doc ID: {document_id}): {e}", exc_info=True)

        if self.request.retries >= MAX_RETRIES:
            final_failure_status = "FALHOU_MAX_RETENTATIVAS"
            logger.critical(
                f"Final attempt failed for task {self.request.id} (file: {filename}, doc_id: {document_id}). "
                f"Updating document status to {final_failure_status}."
            )
            _update_document_status_on_failure(document_id, final_failure_status, str(e))
            CELERY_PDF_TASKS_TOTAL.labels(task_name=task_name, status='failure_max_retries').inc()
            # Sentry or other external error reporting would go here.

        # Exception is re-raised for Celery to handle retries or mark as FAILED.
        # If it's not the final retry, Celery won't mark it as 'failure' for the metric yet.
        # The metric increment for 'failure_exception' could be done here if we don't want to wait for final failure.
        # However, a task that retries and then succeeds should be counted as success.
        # So, incrementing failure metric only on final retry exhaustion is more accurate for "permanent failures".
        raise


def _update_document_status_on_failure(document_id: int, status_value: str, error_message: Optional[str]):
    """
    Helper function to update the document status in the database upon final failure.
    """
    logger.info(f"Attempting to update document_id {document_id} status to '{status_value}' due to failure.")
    try:
        # Run the async DB update in a new event loop for sync Celery task context
        async def update_status():
            async with get_db_contextmanager() as db:
                # Assuming 'documents' table has 'status' and 'error_details' (or similar) columns
                # Adjust column names and table name as per actual schema
                update_query = text("""
                    UPDATE documents
                    SET status = :status, error_details = :error_details, updated_at = CURRENT_TIMESTAMP
                    WHERE id = :document_id
                """)
                await db.execute(update_query, {"status": status_value, "document_id": document_id, "error_details": error_message[:1000]}) # Limit error message length
                await db.commit()
                logger.info(f"Successfully updated document_id {document_id} status to '{status_value}'.")

        import asyncio
        asyncio.run(update_status())

    except Exception as db_exc:
        logger.error(f"CRITICAL: Failed to update document_id {document_id} status to '{status_value}' in database after task failure: {db_exc}", exc_info=True)
        # This is a critical failure in error handling itself.

# The celery_app is already imported at the top of the file as:
# from src.celery_app import celery_app
# So, we use that instance for all tasks.

@celery_app.task(name="transcritor_pdf.tasks.health_check_task")
def health_check_task():
    return "Celery is healthy!"
