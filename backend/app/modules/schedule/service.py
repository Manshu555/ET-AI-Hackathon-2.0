from motor.motor_asyncio import AsyncIOMotorDatabase
from app.modules.schedule.features import compute_features, compute_risk_score, get_contributing_factors
from app.modules.schedule.critical_path import compute_critical_path, get_downstream_tasks
from datetime import date
import json
import logging
import csv
import io
import uuid

logger = logging.getLogger(__name__)


async def import_schedule_csv(db: AsyncIOMotorDatabase, project_id: str, csv_content: str) -> dict:
    reader = csv.DictReader(io.StringIO(csv_content))
    imported = 0
    skipped = 0

    tasks = []
    for row in reader:
        try:
            task = {
                "_id": str(uuid.uuid4()),
                "project_id": project_id,
                "wbs_code": row.get("wbs_code", row.get("WBS", "")),
                "task_name": row.get("task_name", row.get("Task Name", row.get("name", "Unnamed"))),
                "planned_start": _parse_date(row.get("planned_start", row.get("Planned Start"))),
                "planned_end": _parse_date(row.get("planned_end", row.get("Planned End"))),
                "actual_start": _parse_date(row.get("actual_start", row.get("Actual Start"))),
                "actual_end": _parse_date(row.get("actual_end", row.get("Actual End"))),
                "duration_days": _parse_int(row.get("duration_days", row.get("Duration"))),
                "dependencies": row.get("dependencies", row.get("Dependencies")),
                "workforce_availability": _parse_float(row.get("workforce_availability", row.get("Workforce %")), 100.0),
                "status": row.get("status", "not_started"),
            }
            tasks.append(task)
            imported += 1
        except Exception as e:
            logger.warning(f"Skipping row: {e}")
            skipped += 1

    if tasks:
        await db.schedule_tasks.insert_many(tasks)

    return {"imported_count": imported, "skipped_count": skipped, "message": f"Imported {imported} tasks, skipped {skipped}"}


async def compute_all_risk_scores(db: AsyncIOMotorDatabase, project_id: str) -> list:
    tasks = await db.schedule_tasks.find({"project_id": project_id}).to_list(None)
    if not tasks:
        return []

    task_dicts = []
    all_tasks_map = {}
    for t in tasks:
        td = {
            "id": t["_id"],
            "task_name": t["task_name"],
            "wbs_code": t.get("wbs_code", ""),
            "planned_start": t.get("planned_start"),
            "planned_end": t.get("planned_end"),
            "actual_start": t.get("actual_start"),
            "actual_end": t.get("actual_end"),
            "duration_days": t.get("duration_days"),
            "dependencies": t.get("dependencies"),
            "workforce_availability": t.get("workforce_availability", 100.0),
            "status": t.get("status", "not_started"),
        }
        task_dicts.append(td)
        all_tasks_map[t["_id"]] = td

    critical_set = compute_critical_path(task_dicts)

    risk_results = []
    risk_docs = []
    
    # Clean old risk scores
    await db.schedule_risk_scores.delete_many({"task_id": {"$in": [t["id"] for t in task_dicts]}})

    for td in task_dicts:
        if td["status"] == "completed":
            risk_results.append({
                "task_id": td["id"],
                "task_name": td["task_name"],
                "wbs_code": td["wbs_code"],
                "risk_score": 0.0,
                "predicted_delay_days": 0.0,
                "contributing_factors": [],
                "status": td["status"],
                "is_critical_path": td["id"] in critical_set,
            })
            continue

        features = compute_features(td, all_tasks_map)
        score = compute_risk_score(features)
        factors = get_contributing_factors(features)
        delay_prediction = round(features["lead_time_variance"] * 1.5 + features["upstream_slippage"] * 0.8, 1)

        factors_list = [f["factor"] for f in factors]
        
        risk_record = {
            "_id": str(uuid.uuid4()),
            "task_id": td["id"],
            "risk_score": score,
            "predicted_delay_days": max(delay_prediction, 0),
            "contributing_factors": factors_list,
        }
        risk_docs.append(risk_record)

        risk_results.append({
            "task_id": td["id"],
            "task_name": td["task_name"],
            "wbs_code": td["wbs_code"],
            "risk_score": score,
            "predicted_delay_days": max(delay_prediction, 0),
            "contributing_factors": factors_list,
            "status": td["status"],
            "is_critical_path": td["id"] in critical_set,
        })

    if risk_docs:
        await db.schedule_risk_scores.insert_many(risk_docs)

    risk_results.sort(key=lambda x: (not x["is_critical_path"], -x["risk_score"]))
    return risk_results


async def get_task_risk_explanation(db: AsyncIOMotorDatabase, task_id: str) -> dict:
    task = await db.schedule_tasks.find_one({"_id": task_id})
    if not task:
        return None

    all_tasks = await db.schedule_tasks.find({"project_id": task["project_id"]}).to_list(None)
    all_tasks_map = {}
    task_dicts = []
    
    for t in all_tasks:
        td = {
            "id": t["_id"],
            "task_name": t["task_name"],
            "wbs_code": t.get("wbs_code", ""),
            "planned_start": t.get("planned_start"),
            "planned_end": t.get("planned_end"),
            "actual_start": t.get("actual_start"),
            "actual_end": t.get("actual_end"),
            "duration_days": t.get("duration_days"),
            "dependencies": t.get("dependencies"),
            "workforce_availability": t.get("workforce_availability", 100.0),
            "status": t.get("status", "not_started"),
        }
        task_dicts.append(td)
        all_tasks_map[t["_id"]] = td

    target_td = all_tasks_map.get(task_id, {})
    features = compute_features(target_td, all_tasks_map)
    score = compute_risk_score(features)
    factors = get_contributing_factors(features)
    critical_set = compute_critical_path(task_dicts)
    downstream = get_downstream_tasks(task_id, task_dicts)

    return {
        "task_id": task_id,
        "task_name": task["task_name"],
        "risk_score": score,
        "predicted_delay_days": max(round(features["lead_time_variance"] * 1.5 + features["upstream_slippage"] * 0.8, 1), 0),
        "contributing_factors": factors,
        "is_critical_path": task_id in critical_set,
        "downstream_impact": downstream,
    }


def _parse_date(val):
    if not val or val.strip() == "":
        return None
    try:
        from datetime import datetime
        # MongoDB handles datetime natively
        return datetime.fromisoformat(val.strip())
    except (ValueError, AttributeError):
        return None

def _parse_int(val):
    if not val:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None

def _parse_float(val, default=None):
    if not val:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default
