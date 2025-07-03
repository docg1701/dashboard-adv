import httpx
import hashlib
from fastapi import UploadFile, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


from app.core.database import get_db
from app.models.document import Document
from app.models.user import User # Assuming User model is needed for current_user.id


# URL for the transcriber PDF service, expected to be running and accessible.
# The hostname "transcritor_pdf_service" should be resolvable by this service,
# typically in a containerized environment (e.g., Docker Compose).
# Path updated with trailing slash for /process-pdf/ as per TASK-009. Hostname reverted to service name.
TRANSCRIBER_SERVICE_URL = "http://transcritor_pdf_service:8002/process-pdf/"
# Reverted other URLs to use service name. Trailing slash status for these is unknown but not the primary bug.
TRANSCRIBER_QUERY_SERVICE_URL_TEMPLATE = "http://transcritor_pdf_service:8002/query-document/{document_id}"
TRANSCRIBER_TASK_STATUS_URL_TEMPLATE = "http://transcritor_pdf_service:8002/process-pdf/status/{task_id}"

async def handle_file_upload(file: UploadFile, user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Handles the file upload:
    1. Calculates the file hash to check for duplicates.
    2. If the document is a duplicate, returns a message indicating so.
    3. If it's a new file, creates a Document record in the database.
    4. Sends the file and the new document_id to the transcriber PDF service.
    """
    file_content = await file.read()
    await file.seek(0)

    file_hash = hashlib.sha256(file_content).hexdigest()

    # Check if a document with this hash already exists
    stmt = select(Document).where(Document.file_hash == file_hash)
    result = await db.execute(stmt)
    db_document = result.scalars().first()

    if db_document:
        return {
            "message": "File already exists.",
            "transcriber_data": {
                "task_id": None,
                "document_id": db_document.id
            },
            "original_filename": db_document.file_name,
            "uploader_user_id": user_id
        }

    # Create a new document record for the new file
    db_document = Document(
        file_hash=file_hash,
        file_name=file.filename,
        # created_at is handled by a server_default
    )
    db.add(db_document)
    await db.commit()
    await db.refresh(db_document)
    document_id = db_document.id

    if document_id is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve document ID after creation.")

    async with httpx.AsyncClient() as client:
        try:
            files_data = {'file': (file.filename, file_content, file.content_type)}
            form_data = {'document_id': str(document_id)}

            response = await client.post(
                TRANSCRIBER_SERVICE_URL,
                files=files_data,
                data=form_data,
                timeout=60.0
            )
            response.raise_for_status()
            transcriber_response = response.json()

            return {
                "message": "File successfully sent for processing.",
                "transcriber_data": transcriber_response,
                "original_filename": file.filename,
                "uploader_user_id": user_id
            }
        except httpx.HTTPStatusError as e:
            error_detail = f"Error from transcriber service: Status {e.response.status_code}."
            raise HTTPException(status_code=e.response.status_code, detail=error_detail)
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Could not connect to transcriber service.")
        except Exception as e:
            raise HTTPException(status_code=500, detail="An unexpected error occurred while processing the file.")
        finally:
            await file.close()


async def handle_document_query(document_id: str, user_query: str, user_id: int):
    # Ensure httpx is imported: import httpx # Already imported
    # Ensure HTTPException is imported: from fastapi import HTTPException # Already imported
    query_url = TRANSCRIBER_QUERY_SERVICE_URL_TEMPLATE.format(document_id=document_id)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                query_url,
                json={"user_query": user_query}, # Ensure this matches transcritor's expected input
                timeout=60.0
            )
            response.raise_for_status()
            query_response_data = response.json()
            return query_response_data
        except httpx.HTTPStatusError as e:
            # Log e.response.text for server-side debugging
            # print(f"Transcriber query service error: {e.response.text}") # Example logging
            raise HTTPException(
                status_code=e.response.status_code, # Or a generic 502/503
                detail=f"Error from transcriber query service: Status {e.response.status_code}."
            )
        except httpx.RequestError as e:
            # Log str(e) for server-side debugging
            # print(f"RequestError connecting to transcriber query service: {str(e)}") # Example logging
            raise HTTPException(
                status_code=503, # Service Unavailable
                detail="Could not connect to transcriber query service."
            )
        except Exception as e:
            # Log str(e) for server-side debugging
            # print(f"Unexpected error in handle_document_query: {str(e)}") # Example logging
            raise HTTPException(
                status_code=500, # Internal Server Error
                detail="An unexpected error occurred while querying the document."
            )

# To keep the module clean, the example_service_function has been removed.
# If you need other service functions, define them here.

async def get_document_processing_status(task_id: str):
    status_url = TRANSCRIBER_TASK_STATUS_URL_TEMPLATE.format(task_id=task_id)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(status_url, timeout=30.0)
            response.raise_for_status() # Raises an exception for 4XX/5XX responses
            return response.json()
        except httpx.HTTPStatusError as e:
            # Forward the status code and detail from the downstream service if possible
            detail_msg = f"Error from transcriber status service: Status {e.response.status_code}."
            try:
                # Try to get more specific detail from the transcriber's response body
                error_content = e.response.json()
                if isinstance(error_content, dict) and "detail" in error_content:
                    detail_msg = f"Transcriber status service error: {error_content['detail']}"
                elif isinstance(error_content, dict) and "error_info" in error_content and error_content["error_info"] and "error" in error_content["error_info"]: # Check nested error
                    detail_msg = f"Transcriber status service error: {error_content['error_info']['error']}"
            except Exception:
                pass # Keep generic detail_msg if parsing fails
            raise HTTPException(
                status_code=e.response.status_code,
                detail=detail_msg
            )
        except httpx.RequestError as e:
            # Network-related errors (e.g., connection refused)
            raise HTTPException(
                status_code=503, # Service Unavailable
                detail=f"Could not connect to transcriber status service: {str(e)}"
            )
        except Exception as e:
            # Other unexpected errors
            raise HTTPException(
                status_code=500, # Internal Server Error
                detail=f"An unexpected error occurred while fetching task status: {str(e)}"
            )
