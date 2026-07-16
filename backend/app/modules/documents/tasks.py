import logging
from celery import shared_task
from app.shared.ai.embedding_client import get_embeddings
from app.db.base import get_sync_db
from app.modules.documents.parser import parse_pdf_bytes
from app.modules.documents.chunker import chunk_pages
import uuid

logger = logging.getLogger(__name__)

def _run_ingestion(document_id: str) -> None:
    db = get_sync_db()
    try:
        doc = db.documents.find_one({"_id": document_id})
        if not doc:
            logger.error(f"Document {document_id} not found in database")
            return

        db.documents.update_one({"_id": document_id}, {"$set": {"ingestion_status": "processing"}})

        try:
            logger.info(f"Reading {doc['filename']} from local storage...")
            with open(doc['storage_url'], "rb") as f:
                content = f.read()

            logger.info(f"Parsing PDF ({doc['filename']})...")
            parsed = parse_pdf_bytes(content)

            logger.info(f"Extracted text from {parsed.page_count} pages ({len(parsed.failed_pages)} failed)")

            chunks = chunk_pages(parsed.pages)
            if not chunks:
                logger.warning(f"No chunks produced from {doc['filename']}")
                status = "partial" if parsed.failed_pages else "ready"
                db.documents.update_one({"_id": document_id}, {"$set": {"ingestion_status": status, "page_count": parsed.page_count}})
                return

            logger.info(f"Generating embeddings for {len(chunks)} chunks...")
            chunk_texts = [c.text for c in chunks]

            BATCH_SIZE = 64
            all_embeddings = []
            for i in range(0, len(chunk_texts), BATCH_SIZE):
                batch = chunk_texts[i:i + BATCH_SIZE]
                batch_embeddings = get_embeddings(batch)
                all_embeddings.extend(batch_embeddings)

            logger.info(f"Storing {len(chunks)} chunks in database...")
            chunk_docs = []
            for idx, chunk in enumerate(chunks):
                chunk_docs.append({
                    "_id": str(uuid.uuid4()),
                    "document_id": document_id,
                    "chunk_text": chunk.text,
                    "embedding": all_embeddings[idx], # Store as native MongoDB array of floats
                    "page_number": chunk.page_number,
                    "section_heading": chunk.section_heading,
                })
            
            if chunk_docs:
                db.document_chunks.insert_many(chunk_docs)

            if parsed.failed_pages:
                status = "partial"
            else:
                status = "ready"

            db.documents.update_one({"_id": document_id}, {"$set": {"ingestion_status": status, "page_count": parsed.page_count}})
            logger.info(f"✅ Document {doc['filename']} ingested successfully")

        except Exception as e:
            logger.error(f"❌ Ingestion failed for {doc['filename']}: {e}", exc_info=True)
            db.documents.update_one({"_id": document_id}, {"$set": {"ingestion_status": "failed"}})
            raise
    except Exception as e:
        logger.error(f"MongoDB connection failed during ingestion: {e}")


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def process_document(self, document_id: str) -> None:
    logger.info(f"Celery worker starting ingestion for document {document_id}")
    _run_ingestion(document_id)

def process_document_inline(document_id: str) -> None:
    logger.info(f"Inline ingestion for document {document_id} (no Celery)")
    _run_ingestion(document_id)
