from fastapi import APIRouter, Depends, UploadFile, File, Form, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.base import get_project_db
from app.modules.documents import schemas, models
from app.shared.storage.s3_client import s3_client
from app.modules.documents.tasks import process_document
import uuid

router = APIRouter()

@router.post("", response_model=schemas.DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    project_id: str = Header(...),
    db: AsyncSession = Depends(get_project_db)
):
    # Upload to MinIO/S3
    object_name = f"{uuid.uuid4()}_{file.filename}"
    s3_client.upload_file(file.file, object_name)
    
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
    
    # Trigger Celery Task
    process_document.delay(doc.id)
    
    return doc

@router.get("/{document_id}", response_model=schemas.DocumentResponse)
async def get_document(document_id: str, db: AsyncSession = Depends(get_project_db)):
    result = await db.execute(select(models.Document).where(models.Document.id == document_id))
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.get("/{document_id}/status", response_model=schemas.DocumentStatusResponse)
async def get_document_status(document_id: str, db: AsyncSession = Depends(get_project_db)):
    result = await db.execute(select(models.Document).where(models.Document.id == document_id))
    doc = result.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": doc.ingestion_status}


