"""
Document module API endpoints.

Provides upload, status check, list, and chunk-inspection endpoints.
Supports both Celery-based async processing and inline fallback
for development without Docker/Redis.
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func as sa_func
from app.db.base import get_project_db, get_db
from app.modules.documents import schemas, models
from app.shared.storage.s3_client import s3_client
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def _try_celery_dispatch(document_id: str) -> bool:
    """
    Try to dispatch ingestion to Celery. Returns True if successful,
    False if Redis/Celery is unavailable.
    """
    try:
        from app.modules.documents.tasks import process_document
        process_document.delay(document_id)
        logger.info(f"Dispatched ingestion to Celery for document {document_id}")
        return True
    except Exception as e:
        logger.warning(f"Celery dispatch failed (Redis likely unavailable): {e}")
        return False


@router.post("", response_model=schemas.DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    project_id: str | None = Header(default=None),
    db: AsyncSession = Depends(get_project_db)
):
    """
    Upload a document to the project.
    
    The file is stored in S3/MinIO and a background ingestion task is queued
    to extract text, chunk, and generate embeddings. If Celery is unavailable,
    processing happens inline (slower but works without Docker).
    """
    # Default to the first project if no project-id header is sent
    if not project_id:
        from app.modules.projects.models import Project
        proj_res = await db.execute(select(Project).limit(1))
        proj = proj_res.scalars().first()
        project_id = proj.id if proj else "default"

    # Read file content before any storage attempt (prevents closed-file issues)
    object_name = f"{project_id}/{uuid.uuid4()}_{file.filename}"
    file_bytes = await file.read()

    try:
        import io
        s3_client.upload_file(io.BytesIO(file_bytes), object_name)
        logger.info(f"File {file.filename} stored as {object_name}")
    except Exception as e:
        # Final fallback: save directly to local filesystem
        logger.warning(f"S3 client upload failed ({e}), saving directly to local fs")
        import os
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")
        local_path = os.path.join(uploads_dir, object_name)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(file_bytes)
        logger.info(f"File saved locally: {local_path}")

    # Save to database
    doc = models.Document(
        project_id=project_id,
        doc_type=doc_type,
        filename=file.filename,
        storage_url=object_name,
        ingestion_status='queued'
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Try Celery, fall back to inline processing
    if not _try_celery_dispatch(doc.id):
        # Inline fallback — process in a background thread to avoid blocking
        import threading
        from app.modules.documents.tasks import process_document_inline
        thread = threading.Thread(target=process_document_inline, args=(doc.id,))
        thread.start()
        logger.info(f"Started inline ingestion thread for document {doc.id}")

    return doc


@router.get("", response_model=schemas.DocumentListResponse)
async def list_documents(
    project_id: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    List all documents, optionally filtered by project_id.
    """
    query = select(models.Document).order_by(models.Document.created_at.desc())
    if project_id:
        query = query.where(models.Document.project_id == project_id)

    result = await db.execute(query)
    docs = result.scalars().all()

    # Get total count
    count_query = select(sa_func.count(models.Document.id))
    if project_id:
        count_query = count_query.where(models.Document.project_id == project_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return schemas.DocumentListResponse(
        documents=[schemas.DocumentResponse.model_validate(d) for d in docs],
        total=total,
    )


@router.get("/{document_id}", response_model=schemas.DocumentResponse)
async def get_document(document_id: str, db: AsyncSession = Depends(get_project_db)):
    """Get a single document by ID."""
    result = await db.execute(select(models.Document).where(models.Document.id == document_id))
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.get("/{document_id}/status", response_model=schemas.DocumentStatusResponse)
async def get_document_status(document_id: str, db: AsyncSession = Depends(get_project_db)):
    """Check the ingestion status of a document."""
    result = await db.execute(select(models.Document).where(models.Document.id == document_id))
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": doc.ingestion_status}


@router.get("/{document_id}/chunks", response_model=list[schemas.DocumentChunkResponse])
async def get_document_chunks(document_id: str, db: AsyncSession = Depends(get_db)):
    """
    List all chunks for a document. Useful for debugging ingestion and
    verifying that page numbers and section headings are correctly assigned.
    """
    # Verify document exists
    doc_result = await db.execute(select(models.Document).where(models.Document.id == document_id))
    doc = doc_result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get chunks
    result = await db.execute(
        select(models.DocumentChunk)
        .where(models.DocumentChunk.document_id == document_id)
        .order_by(models.DocumentChunk.page_number)
    )
    chunks = result.scalars().all()

    return [
        schemas.DocumentChunkResponse(
            id=c.id,
            document_id=c.document_id,
            chunk_text=c.chunk_text,
            page_number=c.page_number,
            section_heading=c.section_heading,
            has_embedding=bool(c.embedding),
        )
        for c in chunks
    ]
