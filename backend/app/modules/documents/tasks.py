import asyncio
import tempfile
import fitz # PyMuPDF
import os
from celery import shared_task
from app.shared.storage.s3_client import s3_client
from app.shared.ai.embedding_client import get_embeddings
from app.db.base import async_session_maker
from app.modules.documents.models import Document, DocumentChunk
from sqlalchemy.future import select

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    # A very naive word-based chunker for the hackathon
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks

async def process_document_async(document_id: str):
    async with async_session_maker() as session:
        result = await session.execute(select(Document).where(Document.id == document_id))
        doc = result.scalars().first()
        if not doc:
            return
        
        doc.ingestion_status = 'processing'
        await session.commit()
        
        try:
            # Download file from S3
            content = s3_client.get_file_content(doc.storage_url)
            
            # Extract text
            text_content = ""
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
                
            try:
                pdf_doc = fitz.open(temp_file_path)
                for page in pdf_doc:
                    text_content += page.get_text()
            finally:
                os.unlink(temp_file_path)
                
            # Chunking
            chunks = chunk_text(text_content)
            
            # Embeddings
            embeddings = get_embeddings(chunks)
            
            # Store chunks
            for idx, chunk in enumerate(chunks):
                doc_chunk = DocumentChunk(
                    document_id=doc.id,
                    chunk_text=chunk,
                    embedding=embeddings[idx],
                    page_number=1 # Simplified for hackathon, actual page tracking requires complex chunk mapping
                )
                session.add(doc_chunk)
                
            doc.ingestion_status = 'ready'
            await session.commit()
            
        except Exception as e:
            doc.ingestion_status = 'failed'
            await session.commit()
            raise e

@shared_task
def process_document(document_id: str):
    asyncio.run(process_document_async(document_id))
