"""
Pydantic request/response schemas for the Documents module.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DocumentResponse(BaseModel):
    """Response schema for a single document."""
    id: str
    project_id: str
    filename: str
    doc_type: str
    storage_url: str
    version: int = 1
    page_count: Optional[int] = None
    ingestion_status: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DocumentStatusResponse(BaseModel):
    """Lightweight status-only response."""
    status: str


class DocumentChunkResponse(BaseModel):
    """Response schema for a document chunk (for debugging/demo)."""
    id: str
    document_id: str
    chunk_text: str
    page_number: Optional[int] = None
    section_heading: Optional[str] = None
    has_embedding: bool = False

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    """Paginated list of documents."""
    documents: list[DocumentResponse]
    total: int
