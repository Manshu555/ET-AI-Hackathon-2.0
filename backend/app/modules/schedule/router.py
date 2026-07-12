from fastapi import APIRouter, Depends, UploadFile, File, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.modules.schedule import service, schemas
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User

router = APIRouter()


@router.post("/import", response_model=schemas.CSVImportResponse)
async def import_schedule(
    file: UploadFile = File(...),
    project_id: str = Header(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import schedule tasks from a CSV file."""
    content = await file.read()
    csv_text = content.decode("utf-8")
    result = await service.import_schedule_csv(db, project_id, csv_text)
    return result


@router.get("/risk", response_model=list[schemas.RiskScoreResponse])
async def get_schedule_risk(
    project_id: str = Header(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compute and return risk scores for all tasks in the project."""
    return await service.compute_all_risk_scores(db, project_id)


@router.get("/tasks/{task_id}/risk-explanation", response_model=schemas.RiskExplanationResponse)
async def get_risk_explanation(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed risk explanation with SHAP-style contributing factors."""
    result = await service.get_task_risk_explanation(db, task_id)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return result
