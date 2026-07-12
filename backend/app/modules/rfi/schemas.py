from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str


class RfiCreate(BaseModel):
    subject: str
    question: str


class RfiResponse(BaseModel):
    id: str
    project_id: str
    created_by: str
    subject: str
    question: str
    status: str
    created_at: Optional[datetime] = None


class RfiResolveRequest(BaseModel):
    answer: Optional[str] = None
