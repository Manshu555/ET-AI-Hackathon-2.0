from pydantic import BaseModel
from typing import Optional, List


class SubmittalCreate(BaseModel):
    document_id: str
    vendor_id: str
    spec_ids: Optional[List[str]] = None


class SubmittalResponse(BaseModel):
    id: str
    project_id: str
    vendor_id: str
    document_id: str
    status: str
    reviewed_by: Optional[str] = None


class DeviationResponse(BaseModel):
    id: str
    submittal_id: str
    spec_id: str
    spec_reference: Optional[str] = None
    description: str
    severity: str
    detected_by: str
    status: str
    resolution_note: Optional[str] = None


class DeviationActionRequest(BaseModel):
    action: str  # accept, override, dismiss
    note: Optional[str] = None


class ComplianceCheckResponse(BaseModel):
    submittal_id: str
    status: str
    deviations: List[DeviationResponse] = []
    total_deviations: int = 0
    critical_count: int = 0
    major_count: int = 0
    minor_count: int = 0
