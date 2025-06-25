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
# Import db utilities
from .db_config import connect_to_db, close_db_connection, db_pool, EMBEDDING_DIMENSIONS
import asyncpg # Required for conn.execute within startup event

@app.on_event("startup")
async def startup_db_event():
    """
    Connects to the database and creates the necessary table(s) if they don't exist.
    """
    logger.info("FastAPI startup event: Attempting to connect to database and setup schema...")
    await connect_to_db() # Establishes the db_pool
    if db_pool: # Ensure pool was created successfully
        async with db_pool.acquire() as conn:
            # It's good practice to use transactions for DDL sequences,
            # though for simple IF NOT EXISTS it might be less critical.
            async with conn.transaction():
                try:
                    # Create vector extension
                    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                    logger.info("Ensured 'vector' extension exists.")

                    # Define and create documents table
                    # EMBEDDING_DIMENSIONS will be used from db_config
                    # --- BEGINNING OF SECTION TO COMMENT OUT ---
                    # The creation of the 'documents' table (for chunks, in the old design)
                    # is now handled by Alembic migrations in the backend, which create
                    # 'documents' (for metadata) and 'document_chunks' (for chunks and embeddings).
                    # This old logic here can conflict or cause confusion.
                    # create_table_query = f"""
                    # CREATE TABLE IF NOT EXISTS documents (
                    #     chunk_id TEXT PRIMARY KEY,
                    #     filename TEXT,
                    #     page_number INTEGER,
                    #     text_content TEXT,
                    #     metadata JSONB,
                    #     embedding VECTOR({EMBEDDING_DIMENSIONS}),
                    #     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    # );
                    # """
                    # await conn.execute(create_table_query)
                    # logger.info(f"Ensured 'documents' table exists with schema (chunk_id PK, embedding dimension {EMBEDDING_DIMENSIONS}).")
                    # --- END OF SECTION TO COMMENT OUT ---
                    logger.info("Schema setup for 'documents' table in transcritor-pdf/main.py startup is now disabled. Schema is managed by backend Alembic migrations.")

                    # Example: Create an index (optional, can also be managed via migrations)
                    # This is a basic index, refer to pgvector docs for IVFFlat or HNSW for larger datasets
                    create_index_query = f"""
                    CREATE INDEX IF NOT EXISTS idx_documents_embedding ON documents USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);
                    """
                    # Using vector_l2_ops as an example, choose based on your distance metric
                    # await conn.execute(create_index_query)
                    # logger.info("Ensured basic index on embedding column exists (example using IVFFlat).")
                    # Commenting out index creation for now, as it might be slow for startup
                    # and depends on the specific vector ops preferred (l2, cosine, ip).

                except asyncpg.exceptions.PostgresError as pe:
                    logger.error(f"PostgreSQL error during startup schema setup: {pe}")
                except Exception as e:
                    logger.error(f"An unexpected error occurred during startup schema setup: {e}", exc_info=True)
    else:
        logger.error("Database pool not available after connect_to_db() call, skipping schema setup. Application might not function correctly.")
        # Depending on requirements, might raise an error here to stop app startup if DB is critical.

@app.on_event("shutdown")
async def shutdown_db_event():
    """
    Closes the database connection pool.
    """
    logger.info("FastAPI shutdown event: Closing database connection pool...")
    await close_db_connection()

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
    document_id: int = Form(...) # Added document_id from form data
):
    """
    Endpoint to upload and process a PDF file.
    It reads the file, then calls the main processing pipeline, passing the document_id.
    """
    from src.tasks import process_pdf_task
    
    logger.info(f"Received file: {file.filename} (type: {file.content_type})")

    # Basic file validation
    if not file.filename:
        logger.warning("File upload attempt with no filename.")
        raise HTTPException(status_code=400, detail="No filename provided.")

    if file.content_type != "application/pdf":
        logger.warning(f"Invalid file type: {file.content_type} for file {file.filename}. Only PDF is allowed.")
        raise HTTPException(status_code=415, detail="Invalid file type. Only PDF files are allowed.")

    try:
        file_bytes = await file.read()
        logger.info(f"File '{file.filename}' read into memory, size: {len(file_bytes)} bytes.")

        if not file_bytes:
            logger.warning(f"Uploaded file '{file.filename}' is empty.")
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        # Dispatch the processing to a Celery task, now including document_id
        task = process_pdf_task.delay(
            file_content_bytes=file_bytes,
            filename=file.filename,
            document_id=document_id
        )
        logger.info(f"File '{file.filename}' (Document ID: {document_id}) queued for processing with Task ID: {task.id}")

        return {"task_id": task.id, "document_id": document_id, "message": "PDF processing has been queued."}

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
