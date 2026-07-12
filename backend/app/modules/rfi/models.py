from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
import uuid
from app.db.base import Base

def generate_uuid():
    return str(uuid.uuid4())

class Rfi(Base):
    __tablename__ = "rfis"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    subject = Column(String, nullable=False)
    question = Column(Text, nullable=False)
    status = Column(String, default="open") # open, answered, closed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    rfi_id = Column(String, ForeignKey("rfis.id"), nullable=True) # Linked if it results in a formal RFI
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String, nullable=False) # 'user' or 'ai'
    content = Column(Text, nullable=False)
    citations = Column(Text, nullable=True) # JSON array of document chunk IDs
    created_at = Column(DateTime(timezone=True), server_default=func.now())
