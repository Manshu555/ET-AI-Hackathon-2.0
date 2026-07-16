from fastapi import APIRouter, Depends, Header, UploadFile, File, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.base import get_db
from app.modules.schedule.schemas import ScheduleTaskResponse, RiskExplanationResponse, RiskScoreResponse
from app.modules.schedule.service import import_schedule_csv, compute_all_risk_scores, get_task_risk_explanation
from app.modules.auth.dependencies import get_current_user
import uuid

router = APIRouter()

@router.post("/import")
async def import_schedule(
    file: UploadFile = File(...),
    project_id: str = Header(...),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Import an MS Project / Primavera schedule exported as CSV."""
    content = await file.read()
    result = await import_schedule_csv(db, project_id, content.decode("utf-8", errors="ignore"))
    return result

@router.get("/tasks", response_model=list[ScheduleTaskResponse])
async def get_tasks(
    project_id: str = Header(...),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Get raw tasks."""
    tasks = []
    async for t in db.schedule_tasks.find({"project_id": project_id}):
        t["id"] = t.pop("_id")
        # Ensure datetimes are formatted if they exist
        if t.get("planned_start"): t["planned_start"] = t["planned_start"].date() if hasattr(t["planned_start"], "date") else t["planned_start"]
        if t.get("planned_end"): t["planned_end"] = t["planned_end"].date() if hasattr(t["planned_end"], "date") else t["planned_end"]
        if t.get("actual_start"): t["actual_start"] = t["actual_start"].date() if hasattr(t["actual_start"], "date") else t["actual_start"]
        if t.get("actual_end"): t["actual_end"] = t["actual_end"].date() if hasattr(t["actual_end"], "date") else t["actual_end"]
        tasks.append(t)
    return tasks

@router.post("/compute-risk", response_model=list[RiskScoreResponse])
async def compute_risk(
    project_id: str = Header(...),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Recompute AI Risk Scores for all tasks in the project."""
    results = await compute_all_risk_scores(db, project_id)
    return results

@router.get("/tasks/{task_id}/risk", response_model=RiskExplanationResponse)
async def get_risk_explanation(
    task_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Get detailed risk feature explanation for a specific task."""
    explanation = await get_task_risk_explanation(db, task_id)
    if not explanation:
        raise HTTPException(status_code=404, detail="Task not found")
    return explanation
