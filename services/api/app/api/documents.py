import uuid
from typing import List

from app.api.auth import get_current_tenant
from app.db.models import Document, DocumentStatus, get_db
from app.models.schemas import (
    DocumentResponse,
    DocumentStatusUpdate,
    UploadInitRequest,
    UploadInitResponse,
)
from app.services.processing import process_document_ingestion
from app.services.storage import storage_service
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1/documents", tags=["documents"])

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # docx
}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB limit


@router.post(
    "/upload", response_model=UploadInitResponse, status_code=status.HTTP_201_CREATED
)
async def initialize_upload(
    payload: UploadInitRequest,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Initializes a document upload by creating a PENDING DB record
    and returning a presigned MinIO URL for direct file upload.
    """
    # 1. Validate file type and size
    if payload.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {ALLOWED_CONTENT_TYPES}",
        )
    if payload.file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds maximum limit of 50MB.",
        )

    doc_id = str(uuid.uuid4())
    # Tenant isolation path: <tenant_id>/<doc_id>_<filename>
    object_name = f"{tenant_id}/{doc_id}_{payload.filename}"

    # 2. Save metadata in DB with PENDING status
    doc = Document(
        id=doc_id,
        tenant_id=tenant_id,
        filename=payload.filename,
        object_name=object_name,
        file_size=payload.file_size,
        content_type=payload.content_type,
        status=DocumentStatus.PENDING,
    )
    db.add(doc)
    await db.commit()

    # 3. Generate presigned URL
    upload_url = storage_service.generate_presigned_upload_url(object_name=object_name)

    return UploadInitResponse(
        doc_id=doc_id,
        upload_url=upload_url,
        object_name=object_name,
    )


@router.patch("/{doc_id}/status", response_model=DocumentResponse)
async def update_document_status(
    doc_id: str,
    payload: DocumentStatusUpdate,
    background_tasks: BackgroundTasks,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Callback endpoint to update status (e.g. mark UPLOADED after frontend upload finishes)."""
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.tenant_id == tenant_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    new_status = DocumentStatus(payload.status)
    doc.status = new_status
    await db.commit()
    await db.refresh(doc)

    # Automatically trigger background ingestion when upload is confirmed
    if new_status == DocumentStatus.UPLOADED:
        background_tasks.add_task(process_document_ingestion, doc.id)

    return doc


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """List all documents for the authenticated tenant."""
    result = await db.execute(select(Document).where(Document.tenant_id == tenant_id))
    return result.scalars().all()


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: str,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Fetch metadata for a single document."""
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.tenant_id == tenant_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc
