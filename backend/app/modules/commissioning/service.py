"""
Commissioning service — guided checklist logic, real-time validation, auto-deviation creation.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.modules.commissioning.models import CommissioningTemplate, CommissioningRun, CommissioningStep
from app.modules.compliance.models import Deviation
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


async def get_templates(db: AsyncSession) -> list:
    result = await db.execute(select(CommissioningTemplate))
    return result.scalars().all()


async def create_run(db: AsyncSession, project_id: str, template_id: str, engineer_id: str) -> dict:
    """Create a new commissioning run and pre-populate steps from the template."""
    # Load template
    result = await db.execute(select(CommissioningTemplate).where(CommissioningTemplate.id == template_id))
    template = result.scalars().first()
    if not template:
        return None

    # Create run
    run = CommissioningRun(
        project_id=project_id,
        template_id=template_id,
        engineer_id=engineer_id,
    )
    db.add(run)
    await db.flush()

    # Create steps from template
    steps_data = json.loads(template.steps)
    for step_def in steps_data:
        step = CommissioningStep(
            run_id=run.id,
            step_number=step_def["step_number"],
            description=step_def["description"],
            expected_min=step_def.get("expected_min"),
            expected_max=step_def.get("expected_max"),
            expected_unit=step_def.get("expected_unit"),
        )
        db.add(step)

    await db.commit()
    await db.refresh(run)
    return await get_run_detail(db, run.id)


async def update_step(db: AsyncSession, run_id: str, step_id: str, actual_value: float) -> dict:
    """Update a step with the actual measured value. Validates against expected range."""
    result = await db.execute(
        select(CommissioningStep)
        .where(CommissioningStep.id == step_id, CommissioningStep.run_id == run_id)
    )
    step = result.scalars().first()
    if not step:
        return None

    step.actual_value = actual_value
    step.updated_at = datetime.utcnow()

    # Validate against expected range
    in_range = True
    if step.expected_min is not None and actual_value < step.expected_min:
        in_range = False
    if step.expected_max is not None and actual_value > step.expected_max:
        in_range = False

    if in_range:
        step.status = "pass"
    else:
        step.status = "fail"
        # Auto-create a linked deviation
        deviation = Deviation(
            submittal_id=run_id,  # Reuse submittal_id field for run_id linkage
            spec_id=step.id,  # Reuse spec_id for step linkage
            description=f"Commissioning step {step.step_number} failed: '{step.description}'. "
                        f"Expected {step.expected_min}-{step.expected_max} {step.expected_unit or ''}, "
                        f"got {actual_value} {step.expected_unit or ''}",
            severity="Major" if abs((actual_value - (step.expected_min or 0)) / max(abs(step.expected_max - step.expected_min), 1)) > 0.2 else "Minor",
            detected_by="commissioning",
            status="open",
        )
        db.add(deviation)
        await db.flush()
        step.deviation_id = deviation.id

    await db.commit()

    # Check if all steps are completed — if so, mark run as completed
    run_result = await db.execute(
        select(CommissioningStep).where(CommissioningStep.run_id == run_id)
    )
    all_steps = run_result.scalars().all()
    if all(s.status in ("pass", "fail") for s in all_steps):
        run_update_result = await db.execute(
            select(CommissioningRun).where(CommissioningRun.id == run_id)
        )
        run = run_update_result.scalars().first()
        if run:
            has_failures = any(s.status == "fail" for s in all_steps)
            run.status = "completed" if not has_failures else "failed"
            run.completed_at = datetime.utcnow()
            await db.commit()

    return await get_run_detail(db, run_id)


async def get_run_detail(db: AsyncSession, run_id: str) -> dict:
    """Get full detail of a commissioning run including all steps."""
    result = await db.execute(select(CommissioningRun).where(CommissioningRun.id == run_id))
    run = result.scalars().first()
    if not run:
        return None

    # Get template name
    tmpl_result = await db.execute(select(CommissioningTemplate).where(CommissioningTemplate.id == run.template_id))
    template = tmpl_result.scalars().first()

    # Get steps
    steps_result = await db.execute(
        select(CommissioningStep)
        .where(CommissioningStep.run_id == run_id)
        .order_by(CommissioningStep.step_number)
    )
    steps = steps_result.scalars().all()

    pass_count = sum(1 for s in steps if s.status == "pass")
    fail_count = sum(1 for s in steps if s.status == "fail")
    pending_count = sum(1 for s in steps if s.status == "pending")

    return {
        "id": run.id,
        "project_id": run.project_id,
        "template_id": run.template_id,
        "template_name": template.name if template else "Unknown",
        "standard": template.standard if template else "Unknown",
        "engineer_id": run.engineer_id,
        "status": run.status,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "steps": [
            {
                "id": s.id,
                "run_id": s.run_id,
                "step_number": s.step_number,
                "description": s.description,
                "expected_min": s.expected_min,
                "expected_max": s.expected_max,
                "expected_unit": s.expected_unit,
                "actual_value": s.actual_value,
                "status": s.status,
                "deviation_id": s.deviation_id,
            }
            for s in steps
        ],
        "pass_count": pass_count,
        "fail_count": fail_count,
        "pending_count": pending_count,
    }
