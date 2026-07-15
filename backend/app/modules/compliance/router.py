from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.base import get_db
from app.modules.compliance.models import Deviation, Submittal, Specification
from app.modules.compliance.service import run_compliance_check
from app.modules.compliance import schemas
from app.modules.auth.dependencies import get_authorized_project_id, get_current_user
from app.modules.auth.models import User

router = APIRouter()


@router.post("/submittals", response_model=schemas.SubmittalResponse, status_code=status.HTTP_201_CREATED)
async def create_submittal(
    submittal_in: schemas.SubmittalCreate,
    project_id: str = Header(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new submittal and link it to spec sections."""
    submittal = Submittal(
        project_id=project_id,
        document_id=submittal_in.document_id,
        vendor_id=submittal_in.vendor_id,
    )
    db.add(submittal)
    await db.commit()
    await db.refresh(submittal)
    return submittal


@router.post("/submittals/{submittal_id}/check", response_model=schemas.ComplianceCheckResponse)
async def check_submittal(
    submittal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run AI + rule-based compliance check on a submittal."""
    try:
        await run_compliance_check(db, submittal_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Fetch resulting deviations
    result = await db.execute(
        select(Deviation).where(Deviation.submittal_id == submittal_id)
    )
    deviations = result.scalars().all()

    dev_list = []
    for d in deviations:
        # Get spec reference
        spec_result = await db.execute(select(Specification).where(Specification.id == d.spec_id))
        spec = spec_result.scalars().first()
        spec_ref = f"{spec.spec_code} §{spec.section}" if spec else "Unknown"

        dev_list.append({
            "id": d.id,
            "submittal_id": d.submittal_id,
            "spec_id": d.spec_id,
            "spec_reference": spec_ref,
            "description": d.description,
            "severity": d.severity,
            "detected_by": d.detected_by,
            "status": d.status,
            "resolution_note": d.resolution_note,
        })

    critical = sum(1 for d in deviations if d.severity == "Critical")
    major = sum(1 for d in deviations if d.severity == "Major")
    minor = sum(1 for d in deviations if d.severity == "Minor")

    # Update submittal status
    sub_result = await db.execute(select(Submittal).where(Submittal.id == submittal_id))
    submittal = sub_result.scalars().first()
    if submittal:
        if critical > 0:
            submittal.status = "rejected"
        elif len(deviations) == 0:
            submittal.status = "approved"
        else:
            submittal.status = "under_review"
        await db.commit()

    return {
        "submittal_id": submittal_id,
        "status": submittal.status if submittal else "unknown",
        "deviations": dev_list,
        "total_deviations": len(deviations),
        "critical_count": critical,
        "major_count": major,
        "minor_count": minor,
    }


@router.get("/submittals/{submittal_id}/deviations", response_model=list[schemas.DeviationResponse])
async def get_submittal_deviations(
    submittal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all deviations for a specific submittal."""
    result = await db.execute(
        select(Deviation).where(Deviation.submittal_id == submittal_id)
    )
    deviations = result.scalars().all()
    dev_list = []
    for d in deviations:
        spec_result = await db.execute(select(Specification).where(Specification.id == d.spec_id))
        spec = spec_result.scalars().first()
        spec_ref = f"{spec.spec_code} §{spec.section}" if spec else "Unknown"
        dev_list.append({
            "id": d.id, "submittal_id": d.submittal_id, "spec_id": d.spec_id,
            "spec_reference": spec_ref, "description": d.description,
            "severity": d.severity, "detected_by": d.detected_by,
            "status": d.status, "resolution_note": d.resolution_note,
        })
    return dev_list


@router.get("/deviations", response_model=list[schemas.DeviationResponse])
async def get_all_deviations(
    db: AsyncSession = Depends(get_db),
    project_id: str = Depends(get_authorized_project_id),
    current_user: User = Depends(get_current_user),
):
    """Get all deviations across the project."""
    result = await db.execute(
        select(Deviation)
        .join(Submittal, Deviation.submittal_id == Submittal.id)
        .where(Submittal.project_id == project_id)
    )
    deviations = result.scalars().all()
    dev_list = []
    for d in deviations:
        spec_result = await db.execute(select(Specification).where(Specification.id == d.spec_id))
        spec = spec_result.scalars().first()
        spec_ref = f"{spec.spec_code} §{spec.section}" if spec else "Unknown"
        dev_list.append({
            "id": d.id, "submittal_id": d.submittal_id, "spec_id": d.spec_id,
            "spec_reference": spec_ref, "description": d.description,
            "severity": d.severity, "detected_by": d.detected_by,
            "status": d.status, "resolution_note": d.resolution_note,
        })
    return dev_list


@router.patch("/deviations/{deviation_id}", response_model=schemas.DeviationResponse)
async def update_deviation(
    deviation_id: str,
    action_in: schemas.DeviationActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accept, override, or dismiss an AI-flagged deviation."""
    result = await db.execute(select(Deviation).where(Deviation.id == deviation_id))
    deviation = result.scalars().first()
    if not deviation:
        raise HTTPException(status_code=404, detail="Deviation not found")

    action = action_in.action.lower()
    if action == "accept":
        deviation.status = "accepted"
    elif action == "override":
        deviation.status = "overridden"
    elif action == "dismiss":
        deviation.status = "dismissed"
    else:
        raise HTTPException(status_code=422, detail=f"Invalid action: {action}. Use accept, override, or dismiss.")

    if action_in.note:
        deviation.resolution_note = action_in.note

    await db.commit()
    await db.refresh(deviation)

    spec_result = await db.execute(select(Specification).where(Specification.id == deviation.spec_id))
    spec = spec_result.scalars().first()
    spec_ref = f"{spec.spec_code} §{spec.section}" if spec else "Unknown"

    return {
        "id": deviation.id, "submittal_id": deviation.submittal_id,
        "spec_id": deviation.spec_id, "spec_reference": spec_ref,
        "description": deviation.description, "severity": deviation.severity,
        "detected_by": deviation.detected_by, "status": deviation.status,
        "resolution_note": deviation.resolution_note,
    }
