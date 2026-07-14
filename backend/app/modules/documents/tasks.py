"""
Celery task for document ingestion.

Downloads a PDF from S3/MinIO, extracts text per page, chunks with metadata,
generates embeddings, and stores everything in the database.

Uses SYNCHRONOUS database sessions (Celery workers are sync by default).
Falls back to inline processing if Celery/Redis is unavailable.
"""
import json
import logging
from celery import shared_task
from app.shared.storage.s3_client import s3_client
from app.shared.ai.embedding_client import get_embeddings
from app.db.base import get_sync_db
from app.modules.documents.models import Document, DocumentChunk
from app.modules.documents.parser import parse_pdf_bytes
from app.modules.documents.chunker import chunk_pages

logger = logging.getLogger(__name__)


def _run_ingestion(document_id: str) -> None:
    """
    Core ingestion logic — fully synchronous.
    Called by both the Celery task and the inline fallback.
    """
    session = get_sync_db()
    try:
        # 1. Load the document record
        doc = session.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"Document {document_id} not found in database")
            return

        doc.ingestion_status = "processing"
        session.commit()

        try:
            # 2. Download file from S3/MinIO
            logger.info(f"Downloading {doc.filename} from storage...")
            content = s3_client.get_file_content(doc.storage_url)

            # 3. Parse PDF → per-page text
            logger.info(f"Parsing PDF ({doc.filename})...")
            parsed = parse_pdf_bytes(content)

            doc.page_count = parsed.page_count
            logger.info(f"Extracted text from {parsed.page_count} pages "
                        f"({len(parsed.failed_pages)} failed)")

            # 4. Chunk with page/section metadata
            chunks = chunk_pages(parsed.pages)
            if not chunks:
                logger.warning(f"No chunks produced from {doc.filename} — document may be empty or image-only")
                doc.ingestion_status = "partial" if parsed.failed_pages else "ready"
                session.commit()
                return

            # 5. Generate embeddings in batch
            logger.info(f"Generating embeddings for {len(chunks)} chunks...")
            chunk_texts = [c.text for c in chunks]

            # Process in batches of 64 to avoid memory issues
            BATCH_SIZE = 64
            all_embeddings: list[list[float]] = []
            for i in range(0, len(chunk_texts), BATCH_SIZE):
                batch = chunk_texts[i:i + BATCH_SIZE]
                batch_embeddings = get_embeddings(batch)
                all_embeddings.extend(batch_embeddings)

            # 6. Store chunks in the database
            logger.info(f"Storing {len(chunks)} chunks in database...")
            for idx, chunk in enumerate(chunks):
                doc_chunk = DocumentChunk(
                    document_id=doc.id,
                    chunk_text=chunk.text,
                    embedding=json.dumps(all_embeddings[idx]),
                    page_number=chunk.page_number,
                    section_heading=chunk.section_heading,
                )
                session.add(doc_chunk)

            # 7. Update status
            if parsed.failed_pages:
                doc.ingestion_status = "partial"
                logger.warning(f"Document {doc.filename}: partial ingestion — "
                               f"pages {parsed.failed_pages} had extraction issues")
            else:
                doc.ingestion_status = "ready"

            session.commit()
            logger.info(f"✅ Document {doc.filename} ingested successfully: "
                        f"{len(chunks)} chunks, {parsed.page_count} pages")

        except Exception as e:
            logger.error(f"❌ Ingestion failed for {doc.filename}: {e}", exc_info=True)
            doc.ingestion_status = "failed"
            session.commit()
            raise

    finally:
        session.close()


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    autoretry_for=(ConnectionError, TimeoutError),
)
def process_document(self, document_id: str) -> None:
    """Celery task: ingest a document asynchronously."""
    logger.info(f"Celery worker starting ingestion for document {document_id}")
    _run_ingestion(document_id)


def process_document_inline(document_id: str) -> None:
    """
    Inline fallback: process the document synchronously in the request thread.
    Used when Celery/Redis is unavailable (e.g. local dev without Docker).
    """
    logger.info(f"Inline ingestion for document {document_id} (no Celery)")
    _run_ingestion(document_id)
