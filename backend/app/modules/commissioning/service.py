from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
import json
import logging
import uuid

logger = logging.getLogger(__name__)


async def get_templates(db: AsyncIOMotorDatabase) -> list:
    templates = []
    async for t in db.commissioning_templates.find():
        t["id"] = t.pop("_id")
        templates.append(t)
    return templates


async def create_run(db: AsyncIOMotorDatabase, project_id: str, template_id: str, engineer_id: str) -> dict:
    template = await db.commissioning_templates.find_one({"_id": template_id})
    if not template:
        return None

    run_id = str(uuid.uuid4())
    run = {
        "_id": run_id,
        "project_id": project_id,
        "template_id": template_id,
        "engineer_id": engineer_id,
        "status": "in_progress",
        "started_at": datetime.utcnow()
    }
    
    await db.commissioning_runs.insert_one(run)

    steps_data = template.get("steps", [])
    if isinstance(steps_data, str):
        steps_data = json.loads(steps_data)
        
    steps_to_insert = []
    for step_def in steps_data:
        steps_to_insert.append({
            "_id": str(uuid.uuid4()),
            "run_id": run_id,
            "step_number": step_def.get("step_number"),
            "description": step_def.get("description"),
            "expected_min": step_def.get("expected_min"),
            "expected_max": step_def.get("expected_max"),
            "expected_unit": step_def.get("expected_unit"),
            "status": "pending"
        })
        
    if steps_to_insert:
        await db.commissioning_steps.insert_many(steps_to_insert)

    return await get_run_detail(db, run_id)


async def update_step(db: AsyncIOMotorDatabase, run_id: str, step_id: str, actual_value: float) -> dict:
    step = await db.commissioning_steps.find_one({"_id": step_id, "run_id": run_id})
    if not step:
        return None

    in_range = True
    expected_min = step.get("expected_min")
    expected_max = step.get("expected_max")
    expected_unit = step.get("expected_unit")
    
    if expected_min is not None and actual_value < expected_min:
        in_range = False
    if expected_max is not None and actual_value > expected_max:
        in_range = False

    status = "pass" if in_range else "fail"
    deviation_id = None
    
    if not in_range:
        severity = "Minor"
        if expected_min is not None and expected_max is not None:
            if abs((actual_value - expected_min) / max(abs(expected_max - expected_min), 1)) > 0.2:
                severity = "Major"
                
        deviation_id = str(uuid.uuid4())
        deviation = {
            "_id": deviation_id,
            "submittal_id": run_id,
            "spec_id": step_id,
            "description": f"Commissioning step {step.get('step_number')} failed: '{step.get('description')}'. "
                           f"Expected {expected_min}-{expected_max} {expected_unit or ''}, "
                           f"got {actual_value} {expected_unit or ''}",
            "severity": severity,
            "detected_by": "commissioning",
            "status": "open",
            "created_at": datetime.utcnow()
        }
        await db.deviations.insert_one(deviation)

    await db.commissioning_steps.update_one(
        {"_id": step_id}, 
        {"$set": {
            "actual_value": actual_value, 
            "updated_at": datetime.utcnow(),
            "status": status,
            "deviation_id": deviation_id
        }}
    )

    all_steps = await db.commissioning_steps.find({"run_id": run_id}).to_list(None)
    if all(s.get("status") in ("pass", "fail") for s in all_steps):
        has_failures = any(s.get("status") == "fail" for s in all_steps)
        run_status = "failed" if has_failures else "completed"
        await db.commissioning_runs.update_one(
            {"_id": run_id}, 
            {"$set": {"status": run_status, "completed_at": datetime.utcnow()}}
        )

    return await get_run_detail(db, run_id)


async def get_run_detail(db: AsyncIOMotorDatabase, run_id: str) -> dict:
    run = await db.commissioning_runs.find_one({"_id": run_id})
    if not run:
        return None

    template = await db.commissioning_templates.find_one({"_id": run.get("template_id")})
    
    steps = await db.commissioning_steps.find({"run_id": run_id}).sort("step_number", 1).to_list(None)

    pass_count = sum(1 for s in steps if s.get("status") == "pass")
    fail_count = sum(1 for s in steps if s.get("status") == "fail")
    pending_count = sum(1 for s in steps if s.get("status") == "pending")
    
    formatted_steps = []
    for s in steps:
        s["id"] = s.pop("_id")
        formatted_steps.append(s)

    return {
        "id": run["_id"],
        "project_id": run.get("project_id"),
        "template_id": run.get("template_id"),
        "template_name": template.get("name") if template else "Unknown",
        "standard": template.get("standard") if template else "Unknown",
        "engineer_id": run.get("engineer_id"),
        "status": run.get("status"),
        "started_at": run.get("started_at"),
        "completed_at": run.get("completed_at"),
        "steps": formatted_steps,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "pending_count": pending_count,
    }
