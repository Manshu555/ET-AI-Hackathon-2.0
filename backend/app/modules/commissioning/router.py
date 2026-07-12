from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.modules.commissioning import service, schemas
from app.modules.commissioning.report import generate_commissioning_report
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User

router = APIRouter()


@router.get("/templates", response_model=list[schemas.TemplateResponse])
async def list_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all available commissioning test templates."""
    return await service.get_templates(db)


@router.post("/runs", response_model=schemas.CommissioningRunDetail, status_code=status.HTTP_201_CREATED)
async def create_run(
    run_in: schemas.CommissioningRunCreate,
    project_id: str = Header(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start a new commissioning test run from a template."""
    result = await service.create_run(db, project_id, run_in.template_id, current_user.id)
    if not result:
        raise HTTPException(status_code=404, detail="Template not found")
    return result


@router.get("/runs/{run_id}", response_model=schemas.CommissioningRunDetail)
async def get_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full detail of a commissioning run."""
    result = await service.get_run_detail(db, run_id)
    if not result:
        raise HTTPException(status_code=404, detail="Run not found")
    return result


@router.patch("/runs/{run_id}/steps/{step_id}", response_model=schemas.CommissioningRunDetail)
async def update_step(
    run_id: str,
    step_id: str,
    step_in: schemas.StepUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit an actual measurement value for a commissioning step."""
    result = await service.update_step(db, run_id, step_id, step_in.actual_value)
    if not result:
        raise HTTPException(status_code=404, detail="Step or run not found")
    return result


@router.get("/runs/{run_id}/report")
async def get_report(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate and download the commissioning report."""
    run_detail = await service.get_run_detail(db, run_id)
    if not run_detail:
        raise HTTPException(status_code=404, detail="Run not found")

    report_bytes = generate_commissioning_report(run_detail)
    return Response(
        content=report_bytes,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=commissioning_report_{run_id}.txt"}
    )
