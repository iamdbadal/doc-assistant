from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# 1. Document Metadata Model
class DocumentMetadata(BaseModel):
    id: str = Field(..., description="Unique identifier for the document")
    tenant_id: str = Field(..., description="ID of the tenant that owns this document")
    filename: str
    uploaded_at: datetime
    language: Optional[str] = None
    status: str = Field(
        ..., description="E.g., 'uploaded', 'processing', 'completed', 'failed'"
    )


# 2. Chunk Metadata Model
class ChunkMetadata(BaseModel):
    chunk_id: str
    doc_id: str = Field(..., description="Links back to DocumentMetadata.id")
    start_offset: int
    end_offset: int
    tokens: int = Field(..., description="Number of tokens in this specific chunk")


# 3. Query Request Model
class QueryRequest(BaseModel):
    tenant_id: str
    user_id: str
    query: str
    options: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional parameters like top_k or temperature",
    )


# 4. Query Response Model
class QueryResponse(BaseModel):
    answer: str
    sources: List[str] = Field(
        default_factory=list, description="List of source document snippets or IDs"
    )
    confidence: float


# 5. User Creation Model
class UserCreate(BaseModel):
    email: str
    password: str
    tenant_name: str


# --- Upload & DB Response Models ---


class UploadInitRequest(BaseModel):
    """Payload sent by the client to initiate an upload."""

    filename: str = Field(..., json_schema_extra={"example": "annual_report.pdf"})
    content_type: str = Field(..., json_schema_extra={"example": "application/pdf"})
    file_size: int = Field(..., gt=0, description="Size in bytes")


class UploadInitResponse(BaseModel):
    """Response containing the presigned URL for direct upload."""

    doc_id: str
    upload_url: str
    object_name: str


class DocumentStatusUpdate(BaseModel):
    """Payload to update the status of a document."""

    status: str


class DocumentResponse(BaseModel):
    """Response model for returning database document records."""

    id: str
    tenant_id: str
    filename: str
    object_name: str
    file_size: Optional[int] = None
    content_type: Optional[str] = None
    status: str
    uploaded_at: datetime

    # This allows Pydantic to read directly from the SQLAlchemy Document object
    model_config = ConfigDict(from_attributes=True)
