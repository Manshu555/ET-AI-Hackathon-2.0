from pydantic import BaseModel
from typing import Optional
from datetime import date


class ProjectCreate(BaseModel):
    name: str
    location: Optional[str] = None
    client: Optional[str] = None
    start_date: Optional[date] = None
    target_completion: Optional[date] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    client: Optional[str] = None
    start_date: Optional[date] = None
    target_completion: Optional[date] = None
    status: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    location: Optional[str] = None
    client: Optional[str] = None
    start_date: Optional[date] = None
    target_completion: Optional[date] = None
    status: str
