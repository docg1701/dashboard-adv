from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_active_user, get_db
from app.models.user import User
from .. import services # services.py is one level up
from .schemas import TaskStatusResponse, DocumentQueryRequest, GatewayDocumentUploadResponse, GatewayDocumentQueryResponse, DocumentListResponse, DocumentRead, TranscriberQueryData

router = APIRouter()

# Removed the /ping endpoint as it was just an example,
# focusing on the actual functional endpoints.
# If /ping is needed, it can be added back.

@router.get("/", summary="Root of Documents v1 Module", tags=["Documents v1"])
async def read_documents_v1_root():
    return {"message": "Welcome to the Documents Module v1"}

@router.post("/upload", summary="Upload a document for processing", tags=["Documents v1"], response_model=GatewayDocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    return await services.handle_file_upload(file, current_user.id, db)

@router.post("/query/{document_id}", summary="Query a processed document", tags=["Documents v1"], response_model=TranscriberQueryData)
async def query_document_v1(
    document_id: str,
    request_data: DocumentQueryRequest,
    current_user: User = Depends(get_current_active_user)
):
    if not request_data.user_query:
        raise HTTPException(status_code=400, detail="User query cannot be empty.")
    # Note: services.handle_document_query might need adjustment if document_id type changes (e.g. int vs str)
    return await services.handle_document_query(document_id, request_data.user_query, current_user.id)

@router.get(
    "/upload/status/{task_id}",
    response_model=TaskStatusResponse,
    summary="Get document processing status",
    tags=["Documents v1"]
)
async def get_document_upload_status_v1(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    return await services.get_document_processing_status(task_id)

# Example of a GET endpoint to list documents (from DocumentListResponse schema)
# This would require a new service function in documents/services.py
@router.get("/list", response_model=DocumentListResponse, summary="List processed documents", tags=["Documents v1"])
async def list_documents_v1(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # This service function doesn't exist yet, placeholder for structure
    # documents, total = await services.get_documents(db=db, skip=skip, limit=limit, user_id=current_user.id)
    # return {"items": documents, "total": total, "page": (skip // limit) + 1, "size": limit, "pages": (total + limit - 1) // limit if total > 0 else 0}
    raise HTTPException(status_code=501, detail="List documents endpoint not implemented yet.")

# Example of a GET endpoint to retrieve a specific document by its DB ID
# This would require a new service function
@router.get("/{document_db_id}", response_model=DocumentRead, summary="Get a specific document by DB ID", tags=["Documents v1"])
async def get_document_v1(
    document_db_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # db_document = await services.get_document_by_id(db=db, document_id=document_db_id, user_id=current_user.id)
    # if not db_document:
    #     raise HTTPException(status_code=404, detail="Document not found")
    # return db_document
    raise HTTPException(status_code=501, detail="Get document by ID endpoint not implemented yet.")
