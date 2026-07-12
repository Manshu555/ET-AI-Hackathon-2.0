from pydantic import BaseModel
from typing import Optional

class DocumentResponse(BaseModel):
    id: str
    filename: str
    doc_type: str
    ingestion_status: str
    
class DocumentStatusResponse(BaseModel):
    status: str
