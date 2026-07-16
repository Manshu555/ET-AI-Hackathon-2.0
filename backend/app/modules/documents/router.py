from fastapi import APIRouter, Depends, UploadFile, File, Form, Header, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.base import get_db
from app.modules.documents import schemas
import uuid
import os
import shutil
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

def _try_celery_dispatch(document_id: str) -> bool:
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
    project_id: str = Header(...),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    upload_dir = os.path.join("uploads", project_id)
    os.makedirs(upload_dir, exist_ok=True)
    object_name = os.path.join(upload_dir, f"{uuid.uuid4()}_{file.filename}")

    try:
        with open(object_name, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Local file save failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded file locally."
        )

    doc_id = str(uuid.uuid4())
    doc = {
        "_id": doc_id,
        "project_id": project_id,
        "doc_type": doc_type,
        "filename": file.filename,
        "storage_url": object_name,
        "version": 1,
        "page_count": None,
        "ingestion_status": "queued",
        "created_at": datetime.utcnow()
    }
    await db.documents.insert_one(doc)

    if not _try_celery_dispatch(doc_id):
        import threading
        from app.modules.documents.tasks import process_document_inline
        thread = threading.Thread(target=process_document_inline, args=(doc_id,))
        thread.start()
        logger.info(f"Started inline ingestion thread for document {doc_id}")

    doc["id"] = doc.pop("_id")
    return doc


@router.get("", response_model=schemas.DocumentListResponse)
async def list_documents(
    project_id: str = Header(None),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    query = {}
    if project_id:
        query["project_id"] = project_id

    total = await db.documents.count_documents(query)
    
    docs = []
    async for d in db.documents.find(query).sort("created_at", -1):
        d["id"] = d.pop("_id")
        docs.append(d)

    return {"documents": docs, "total": total}


@router.get("/{document_id}", response_model=schemas.DocumentResponse)
async def get_document(document_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    doc = await db.documents.find_one({"_id": document_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc["id"] = doc.pop("_id")
    return doc


@router.get("/{document_id}/status", response_model=schemas.DocumentStatusResponse)
async def get_document_status(document_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    doc = await db.documents.find_one({"_id": document_id}, projection={"ingestion_status": 1})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": doc.get("ingestion_status", "unknown")}


@router.get("/{document_id}/chunks", response_model=list[schemas.DocumentChunkResponse])
async def get_document_chunks(document_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    doc = await db.documents.find_one({"_id": document_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks = []
    async for c in db.document_chunks.find({"document_id": document_id}).sort("page_number", 1):
        c["id"] = c.pop("_id")
        c["has_embedding"] = bool(c.get("embedding"))
        chunks.append(c)

    return chunks
