from fastapi import APIRouter, Depends, Header, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.base import get_db
from app.modules.commissioning.schemas import TemplateResponse, CommissioningRunCreate, CommissioningRunDetail, StepUpdateRequest
from app.modules.commissioning.service import get_templates, create_run, update_step, get_run_detail
from app.modules.auth.dependencies import get_current_user

router = APIRouter()

@router.get("/templates", response_model=list[TemplateResponse])
async def api_get_templates(db: AsyncIOMotorDatabase = Depends(get_db)):
    """List available equipment commissioning templates (e.g., HVAC, Generators)."""
    templates = await get_templates(db)
    return templates

@router.post("/runs", response_model=CommissioningRunDetail, status_code=201)
async def api_create_run(
    run_in: CommissioningRunCreate,
    project_id: str = Header(...),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Start a new commissioning run for an equipment instance."""
    run = await create_run(db, project_id, run_in.template_id, current_user["_id"])
    if not run:
        raise HTTPException(status_code=404, detail="Template not found")
    return run

@router.get("/runs/{run_id}", response_model=CommissioningRunDetail)
async def api_get_run(
    run_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Get the full checklist and status for a specific run."""
    run = await get_run_detail(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Commissioning run not found")
    return run

@router.patch("/runs/{run_id}/steps/{step_id}", response_model=CommissioningRunDetail)
async def api_update_step(
    run_id: str,
    step_id: str,
    step_in: StepUpdateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Record an actual measurement for a checklist step and auto-validate."""
    run = await update_step(db, run_id, step_id, step_in.actual_value)
    if not run:
        raise HTTPException(status_code=404, detail="Step or Run not found")
    return run
