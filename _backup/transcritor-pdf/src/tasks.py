from src.celery_app import celery_app
from src.processing import process_pdf_pipeline # Import from the new processing module

# If direct import of process_pdf_pipeline causes issues due to FastAPI app context
# or other main.py specific initializations, the core logic of
# process_pdf_pipeline might need to be extracted into a separate utility module
# that both main.py and tasks.py can import.

@celery_app.task(name='src.tasks.process_pdf_task')
def process_pdf_task(file_content_bytes: bytes, filename: str, document_id: int) -> dict: # Added document_id
    '''
    Celery task to process a PDF file.
    Relies on process_pdf_pipeline for the core logic.
    Now requires document_id to link chunks to the parent document.
    '''
    try:
        # Now calling process_pdf_pipeline imported from src.processing
        print(f"Celery task received processing for: {filename}. Calling process_pdf_pipeline.")

        # The actual call to the (simulated) pipeline
        # Note: process_pdf_pipeline is an async function.
        # Celery tasks can be async, but it depends on the Celery version and configuration.
        # Assuming Celery is set up to handle async tasks (e.g., Celery 5+ with an asyncio worker or by running the async code within `asyncio.run()`).
        # For simplicity, if process_pdf_pipeline was synchronous, it would be a direct call.
        # If it MUST remain async and the Celery worker isn't async-native, one might do:
        # import asyncio
        # result_summary = asyncio.run(process_pdf_pipeline(file_content=file_content_bytes, filename=filename))
        # However, the `process_pdf_pipeline` in `src.processing` is already `async`.
        # For now, let's assume the Celery setup can handle invoking async functions.
        # If not, this part might need adjustment (e.g. making pipeline sync or using asyncio.run).
        # Given the current structure, Celery would need to be able to `await` this.
        # A standard Celery task is synchronous. To call async code from a sync task,
        # we need `asyncio.run()`.

        import asyncio # Ensure asyncio is imported

        # Call the async pipeline using asyncio.run()
        result_summary = asyncio.run(process_pdf_pipeline(
            file_content=file_content_bytes,
            filename=filename,
            document_id=document_id # Pass document_id
        ))

        print(f"Celery task finished processing for: {filename} (Doc ID: {document_id}). Result: {result_summary.get('status')}")
        return result_summary
    except Exception as e:
        # Log the exception
        # It's good to use Celery's logger if available, or standard logging.
        # For now, print is used as per existing style.
        print(f"Celery task failed for {filename}: {str(e)}")
        # Re-raise the exception so Celery can mark the task as FAILED
        # and store the exception information.
        raise

# The celery_app is already imported at the top of the file as:
# from src.celery_app import celery_app
# So, we use that instance for all tasks.

@celery_app.task(name="transcritor_pdf.tasks.health_check_task")
def health_check_task():
    return "Celery is healthy!"
