from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
import uuid
from app.db.base import Base

def generate_uuid():
    return str(uuid.uuid4())

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    doc_type = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    storage_url = Column(String, nullable=False)
    version = Column(Integer, default=1)
    ingestion_status = Column(String, default='queued') # queued, processing, ready, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_text = Column(String, nullable=False)
    embedding = Column(Text) # JSON serialized list of floats

    page_number = Column(Integer, nullable=True)
    section_heading = Column(String, nullable=True)
