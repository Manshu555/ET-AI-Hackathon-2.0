from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class ScheduleTaskCreate(BaseModel):
    wbs_code: Optional[str] = None
    task_name: str
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    duration_days: Optional[int] = None
    dependencies: Optional[str] = None  # JSON array
    workforce_availability: Optional[float] = 100.0
    status: Optional[str] = "not_started"


class ScheduleTaskResponse(BaseModel):
    id: str
    project_id: str
    wbs_code: Optional[str] = None
    task_name: str
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    duration_days: Optional[int] = None
    dependencies: Optional[str] = None
    workforce_availability: Optional[float] = None
    status: str


class RiskScoreResponse(BaseModel):
    task_id: str
    task_name: str
    wbs_code: Optional[str] = None
    risk_score: float
    predicted_delay_days: Optional[float] = None
    contributing_factors: List[str] = []
    status: str
    is_critical_path: bool = False


class RiskExplanationResponse(BaseModel):
    task_id: str
    task_name: str
    risk_score: float
    predicted_delay_days: Optional[float] = None
    contributing_factors: List[dict] = []
    is_critical_path: bool = False
    downstream_impact: List[str] = []


class CSVImportResponse(BaseModel):
    imported_count: int
    skipped_count: int
    message: str
