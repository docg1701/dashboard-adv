# -*- coding: utf-8 -*-
"""
Main entry point for the Transcritor PDF API.
"""
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Form
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_500_INTERNAL_SERVER_ERROR
from typing import List, Dict, Any, Optional # Keep List, Dict, Any, Optional if used by models or responses
from pydantic import BaseModel

from src.celery_app import celery_app
from celery.result import AsyncResult
from src.query_processor import get_llm_answer_with_context

# Import new core components
from src.core.config import settings, setup_logging
from src.core.database import (
    initialize_database,
    close_database_connection,
    get_db_contextmanager, # For startup DDL
)
from src.core.security import verify_api_key # Import the API key verification dependency
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from fastapi import Depends # Import Depends

# --- Logging Configuration ---
# Call setup_logging() early, before FastAPI app initialization, to ensure all loggers use this config.
# This uses LOGGING_LEVEL from Pydantic settings.
setup_logging()
logger = logging.getLogger(__name__) # Get logger instance after setup

# --- FastAPI App Initialization ---
app = FastAPI(
    title=settings.PROJECT_NAME + " (Transcritor PDF)",
    description="API para processar arquivos PDF, extrair texto e informações estruturadas, e preparar dados para RAG.",
    version="0.1.0"
)

# Prometheus Instrumentator
# Must be initialized after FastAPI app creation and before adding routes (if specific route configs are needed for it)
# or after routes if it instruments based on existing routes. Standard practice is after app creation.
from prometheus_fastapi_instrumentator import Instrumentator
instrumentator = Instrumentator(
    should_group_status_codes=True, # Group 2xx, 3xx, 4xx, 5xx status codes
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics"], # Don't instrument the /metrics endpoint itself
    inprogress_name="fastapi_http_requests_inprogress",
    inprogress_labels=True,
).instrument(app)


# --- Pydantic Models ---
class UserQueryRequest(BaseModel):
    user_query: str

# --- Exception Handlers ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc.errors()} for request: {request.url.path}", exc_info=False)
    serializable_errors = []
    for error in exc.errors():
        new_error = error.copy()
        if 'ctx' in new_error and 'error' in new_error['ctx']:
            if isinstance(new_error['ctx']['error'], (ValueError, TypeError)): # Broader catch
                new_error['ctx']['error'] = str(new_error['ctx']['error'])
        serializable_errors.append(new_error)
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation Error", "errors": serializable_errors},
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTPException: {exc.status_code} {exc.detail} for request: {request.url.path}", exc_info=False)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)} for request: {request.url.path}", exc_info=True)
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected internal server error occurred. Please contact support."},
    )

# --- Database Setup & Teardown Events ---
@app.on_event("startup")
async def startup_db_event():
    """
    Initializes the database connection and ensures necessary extensions (like pgvector) are available.
    Schema (tables, indexes) should primarily be managed by Alembic migrations from the backend.
    """
    logger.info("FastAPI startup event: Initializing database connection...")
    initialize_database() # This is a synchronous call from core.database

    logger.info(f"FastAPI startup event: Ensuring 'vector' extension exists using SQLAlchemy. EMBEDDING_DIMENSIONS from settings: {settings.EMBEDDING_DIMENSIONS}")
    try:
        async with get_db_contextmanager() as db_session: # Use new context manager
            async with db_session.begin(): # Start a transaction for DDL
                await db_session.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                logger.info("SQLAlchemy: Ensured 'vector' extension exists.")
            await db_session.commit() # Commit the transaction
        logger.info("Database initialization and vector extension check complete.")
    except SQLAlchemyError as sa_error:
        logger.error(f"SQLAlchemy error during startup DDL (CREATE EXTENSION vector): {sa_error}", exc_info=True)
        # Depending on requirements, might raise an error here to stop app startup if DB/vector is critical.
    except Exception as e:
        logger.error(f"An unexpected error occurred during startup DDL (CREATE EXTENSION vector): {e}", exc_info=True)
        # Potentially critical, consider app behavior

    # Note: Table and other index creations previously here are assumed to be handled by Alembic migrations
    # from the main backend to ensure a single source of truth for the schema.
    logger.info("Schema setup for tables/indexes in transcritor-pdf/main.py startup is disabled/minimal. Schema is primarily managed by backend Alembic migrations.")

    # Expose the /metrics endpoint for Prometheus
    instrumentator.expose(app, include_in_schema=False, should_gzip=True) # Added should_gzip


@app.on_event("shutdown")
async def shutdown_db_event():
    """
    Closes the database connections managed by SQLAlchemy.
    """
    logger.info("FastAPI shutdown event: Closing database connections...")
    await close_database_connection() # Calls the new core.database function


# --- Root Endpoint ---
@app.get("/")
async def root():
    """
    Root endpoint providing a welcome message.
    """
    logger.info("Root endpoint '/' was called.")
    return {"message": "Welcome to the Transcritor PDF API"}

# --- Health Check Endpoint ---
@app.get("/health/")
async def health_check():
    """
    Health check endpoint to verify if the API is running.
    """
    logger.info("Health check endpoint '/health/' was called.")
    return {"status": "ok"}

# --- PDF Processing Endpoint ---
@app.post("/process-pdf/", dependencies=[Depends(verify_api_key)])
async def process_pdf_endpoint(
    file: UploadFile = File(...),
    document_id: int = Form(...), # Added document_id from form data
    db: AsyncSession = Depends(get_db_session) # Inject DB session
):
    """
    Endpoint to upload and process a PDF file. Requires API Key.
    Calculates file hash, checks for duplicates. If new, queues for processing.
    It reads the file, then calls the main processing pipeline, passing the document_id.
    """
    import hashlib
    from src.tasks import process_pdf_task
    
    logger.info(f"Received file: {file.filename} (type: {file.content_type}) for document_id: {document_id}")

    # Basic file validation
    if not file.filename:
        logger.warning("File upload attempt with no filename.")
        raise HTTPException(status_code=400, detail="No filename provided.")

    if file.content_type != "application/pdf":
        logger.warning(f"Invalid file type: {file.content_type} for file {file.filename}. Only PDF is allowed.")
        raise HTTPException(status_code=415, detail="Invalid file type. Only PDF files are allowed.")

    try:
        file_bytes = await file.read()
        logger.info(f"File '{file.filename}' read into memory, size: {len(file_bytes)} bytes for document_id: {document_id}.")

        if not file_bytes:
            logger.warning(f"Uploaded file '{file.filename}' is empty for document_id: {document_id}.")
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        # 1. Calculate SHA-256 hash of the file content
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        logger.info(f"Calculated SHA-256 hash for {file.filename} (doc_id: {document_id}): {file_hash}")

        # 2. Check if this hash exists in the 'documents' table
        # Assumes 'documents' table has 'file_hash' and 'status' columns.
        # This query checks if the exact content (hash) already exists.
        query_str = "SELECT id, status FROM documents WHERE file_hash = :file_hash LIMIT 1"
        result = await db.execute(text(query_str), {"file_hash": file_hash})
        existing_doc = result.mappings().first()

        if existing_doc:
            # Content already exists in the database
            logger.warning(
                f"Duplicate content detected for file {file.filename} (doc_id: {document_id}). "
                f"Hash {file_hash} matches existing document_id: {existing_doc['id']} with status: {existing_doc['status']}."
            )
            # If the existing document_id is the one we were given, it implies the backend might be re-triggering.
            # If it's a different document_id, it's a true content collision.
            # The response should inform the backend about this.
            return JSONResponse(
                status_code=200, # Or 409 Conflict, depending on API contract with backend
                content={
                    "status": "duplicate",
                    "message": "Document content already processed or processing.",
                    "file_hash": file_hash,
                    "existing_document_id": existing_doc['id'],
                    "existing_document_status": existing_doc['status'],
                    "current_document_id": document_id, # The ID passed in this request
                    "task_id": None
                }
            )

        # If hash does not exist, proceed to queue the task.
        # The backend is responsible for ensuring the 'file_hash' is updated for the 'document_id' record.
        logger.info(f"File content for {file.filename} (doc_id: {document_id}, hash: {file_hash}) is unique. Proceeding with processing.")

        task = process_pdf_task.delay(
            file_content_bytes=file_bytes,
            filename=file.filename,
            document_id=document_id # document_id is for the record backend already created
        )
        logger.info(f"File '{file.filename}' (Document ID: {document_id}, hash: {file_hash}) queued for processing with Task ID: {task.id}")

        return {"task_id": task.id, "document_id": document_id, "file_hash": file_hash, "message": "PDF processing has been queued."}

    except HTTPException as http_exc:
        # Re-raise HTTPException so it's caught by its specific handler or FastAPI default
        logger.debug(f"Re-raising HTTPException for '{file.filename}': {http_exc.detail}")
        raise http_exc
    except Exception as e:
        # This catches unexpected errors during file read or within the pipeline if not handled by HTTPExceptions
        logger.error(f"Unexpected error processing file '{file.filename}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal server error occurred while processing the PDF: {file.filename}.")
    finally:
        await file.close()
        logger.info(f"File '{file.filename}' closed.")

# --- Task Status Endpoint ---
@app.get("/process-pdf/status/{task_id}", summary="Get the status of a PDF processing task", dependencies=[Depends(verify_api_key)])
async def get_task_status(task_id: str):
    logger.info(f"Accessing status for task_id: {task_id}")
    task_result = AsyncResult(task_id, app=celery_app)

    response_data = {
        "task_id": task_id,
        "status": task_result.status,
        "result": None,
        "error_info": None
    }

    if task_result.successful():
        response_data["result"] = task_result.result
        logger.info(f"Task {task_id} succeeded with result: {task_result.result}")
    elif task_result.failed():
        response_data["error_info"] = {
            "error": str(task_result.info), # task_result.info often holds the exception instance
            "traceback": task_result.traceback
        }
        logger.error(f"Task {task_id} failed. Info: {task_result.info}")
    elif task_result.status == 'PENDING':
        logger.info(f"Task {task_id} is pending.")
    elif task_result.status == 'STARTED':
        logger.info(f"Task {task_id} has started.")
    elif task_result.status == 'RETRY':
        response_data["error_info"] = { # For RETRY, info might also contain the exception
            "error": str(task_result.info),
            "traceback": task_result.traceback
        }
        logger.info(f"Task {task_id} is being retried.")
    else:
        logger.warning(f"Task {task_id} in unhandled state: {task_result.status}")

    return response_data

# --- Document Query Endpoint ---
@app.post("/query-document/{document_id}",
          summary="Query a specific document",
          tags=["Document Query"],
          dependencies=[Depends(verify_api_key)])
async def query_document_endpoint(document_id: str, request_data: UserQueryRequest):
    """
    Allows querying a specific document by its ID (filename) using a user-provided query. Requires API Key.
    The query is processed by an LLM which uses context retrieved from the specified document.

    - **document_id**: The filename of the document to query. This is used to filter context chunks from the database.
    - **request_data**: The user's query string.
    """
    logger.info(f"Querying document_id: {document_id} with query: '{request_data.user_query}'")
    try:
        # The function get_llm_answer_with_context expects 'user_query' as its first parameter name
        llm_response_data = await get_llm_answer_with_context(
            user_query=request_data.user_query, # Changed 'query_text' to 'user_query'
            document_filename=document_id
        )
        # get_llm_answer_with_context returns a dict: {"answer": str, "retrieved_context": list, "error": str|None}
        if llm_response_data.get("error"):
            logger.error(f"Error from get_llm_answer_with_context: {llm_response_data['error']}")
            # Consider if this should be a 500 or a more specific error based on llm_response_data['error']
            raise HTTPException(status_code=500, detail=llm_response_data.get("answer") or "Error processing query with LLM.")

        answer = llm_response_data.get("answer")

        if answer is None: # Should ideally not happen if error field is checked first
            logger.warning(f"No answer found or error in get_llm_answer_with_context for document_id: {document_id}, query: '{request_data.user_query}'")
            raise HTTPException(status_code=404, detail="Could not retrieve an answer for the given query and document.")

        logger.info(f"Answer for document_id: {document_id}, query: '{request_data.user_query}' -> '{answer}'")
        return {"document_id": document_id, "query": request_data.user_query, "answer": answer}
    except HTTPException as http_exc:
        # Re-raise HTTPException so it's caught by its specific handler
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error in query_document_endpoint for document_id: {document_id}, query: '{request_data.user_query}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal server error occurred while querying the document.")


# --- Placeholder for future imports and pipeline logic ---
# These would eventually be real imports if logic is moved to other files/modules
# from .input_handler.pdf_splitter import split_pdf_to_pages, TEMP_PAGE_DIR
# from .input_handler.loader import load_page_image
# (etc.)
# --- Placeholder for future imports and pipeline logic ---
# The actual pipeline logic is now in src.processing
# from .processing import process_pdf_pipeline # This line will be added by the user

# To run this FastAPI app (ensure uvicorn is installed: pip install "uvicorn[standard]"):
# uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
# Or from the project root, if src is in PYTHONPATH:
# python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
