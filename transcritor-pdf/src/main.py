# -*- coding: utf-8 -*-
"""
Main entry point for the Transcritor PDF API.
"""
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Form # Added Form
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_500_INTERNAL_SERVER_ERROR
from typing import List, Dict, Any, Optional
from pydantic import BaseModel # Added for Pydantic model

# from src.tasks import process_pdf_task # Added for Celery task dispatch
from src.celery_app import celery_app # Added for task status check
from celery.result import AsyncResult # Added for task status check
from src.query_processor import get_llm_answer_with_context # Added for query endpoint

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Transcritor PDF API",
    description="API para processar arquivos PDF, extrair texto e informações estruturadas, e preparar dados para RAG.",
    version="0.1.0"
)

# --- Pydantic Models ---
class UserQueryRequest(BaseModel):
    user_query: str

# --- Exception Handlers ---

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handles validation errors (e.g., invalid request body).
    Returns a 422 Unprocessable Entity response with error details.
    """
    logger.error(f"Validation error: {exc.errors()} for request: {request.url.path}", exc_info=False) # exc_info=False as exc.errors() is detailed enough
    # It's good practice to log exc.body() if the body content might be relevant and not too large/sensitive
    # logger.debug(f"Request body: {exc.body()}")

    # Convert non-serializable errors (like ValueError in ctx) to strings
    serializable_errors = []
    for error in exc.errors():
        new_error = error.copy()
        if 'ctx' in new_error and 'error' in new_error['ctx']:
            if isinstance(new_error['ctx']['error'], ValueError): # Or more general Exception
                new_error['ctx']['error'] = str(new_error['ctx']['error'])
        serializable_errors.append(new_error)

    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        # Providing a more structured error, including the type of error and where it occurred.
        content={"detail": "Validation Error", "errors": serializable_errors},
        # Alternative simpler content: content={"detail": exc.errors(), "body": exc.body}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handles FastAPI's HTTPException.
    Ensures these are also logged and returned in a consistent JSON format.
    FastAPI does this by default, but explicit handling allows for custom logging or format if needed.
    """
    logger.error(f"HTTPException: {exc.status_code} {exc.detail} for request: {request.url.path}", exc_info=False)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}, # This is FastAPI's default structure for HTTPException
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Handles any other unhandled exceptions.
    Returns a 500 Internal Server Error response.
    """
    logger.error(f"Unhandled exception: {str(exc)} for request: {request.url.path}", exc_info=True)
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected internal server error occurred. Please contact support."},
        # It's generally not a good idea to expose raw exception details to the client in production.
        # For debugging, you might include: "error_type": type(exc).__name__, "message": str(exc)
    )

# --- Database Setup & Teardown Events ---
# A gestão da conexão com o banco de dados agora é tratada pelo SQLAlchemy
# através do gerenciador de contexto 'get_db_session', não sendo mais necessários
# eventos de startup/shutdown para criar um pool de conexão global.
# O esquema do banco de dados, incluindo a extensão 'vector', é gerenciado
# exclusivamente pelas migrações do Alembic no serviço de backend.


# --- Logging Configuration ---
# Basic logging setup, can be expanded later (e.g., from config file)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

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
@app.post("/process-pdf/")
async def process_pdf_endpoint(
    file: UploadFile = File(...),
    document_id: int = Form(...)
):
    """
    Endpoint to upload and process a PDF file.
    It receives a file and a document_id from the backend, and dispatches
    the processing to a Celery task. It trusts that the calling service
    (backend) has already performed necessary validations (like duplicate checks).
    """
    from src.tasks import process_pdf_task
    
    logger.info(f"Received file: {file.filename} (type: {file.content_type}) for document_id: {document_id}")

    # Basic file validation
    if not file.filename:
        logger.warning("File upload attempt with no filename.")
        raise HTTPException(status_code=400, detail="No filename provided.")
    if file.content_type != "application/pdf":
        logger.warning(f"Invalid file type: {file.content_type} for file {file.filename}.")
        raise HTTPException(status_code=415, detail="Invalid file type. Only PDF files are allowed.")

    try:
        file_bytes = await file.read()
        if not file_bytes:
            logger.warning(f"Uploaded file '{file.filename}' is empty.")
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        # Dispatch the processing to a Celery task
        task = process_pdf_task.delay(
            file_content_bytes=file_bytes,
            filename=file.filename,
            document_id=document_id
        )
        logger.info(f"File '{file.filename}' (Document ID: {document_id}) queued for processing with Task ID: {task.id}")

        return {"task_id": task.id, "document_id": document_id, "message": "PDF processing has been queued."}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error processing file '{file.filename}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal server error occurred while processing the PDF.")
    finally:
        await file.close()
        logger.info(f"File '{file.filename}' closed.")


# --- Task Status Endpoint ---
@app.get("/process-pdf/status/{task_id}", summary="Get the status of a PDF processing task")
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
          tags=["Document Query"])
async def query_document_endpoint(document_id: str, request_data: UserQueryRequest):
    """
    Allows querying a specific document by its ID (filename) using a user-provided query.
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
