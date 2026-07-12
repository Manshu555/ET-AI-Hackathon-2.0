from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TemplateStepSchema(BaseModel):
    step_number: int
    description: str
    expected_min: Optional[float] = None
    expected_max: Optional[float] = None
    expected_unit: Optional[str] = None


class TemplateResponse(BaseModel):
    id: str
    name: str
    standard: str
    system_type: str
    steps: str  # JSON array


class CommissioningRunCreate(BaseModel):
    template_id: str


class CommissioningRunResponse(BaseModel):
    id: str
    project_id: str
    template_id: str
    engineer_id: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class StepUpdateRequest(BaseModel):
    actual_value: float


class StepResponse(BaseModel):
    id: str
    run_id: str
    step_number: int
    description: str
    expected_min: Optional[float] = None
    expected_max: Optional[float] = None
    expected_unit: Optional[str] = None
    actual_value: Optional[float] = None
    status: str
    deviation_id: Optional[str] = None


class CommissioningRunDetail(BaseModel):
    id: str
    project_id: str
    template_id: str
    template_name: str
    standard: str
    engineer_id: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    steps: List[StepResponse] = []
    pass_count: int = 0
    fail_count: int = 0
    pending_count: int = 0
