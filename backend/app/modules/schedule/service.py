"""
Schedule Risk Engine service layer.
Orchestrates feature engineering, risk scoring, and critical-path analysis.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.modules.schedule.models import ScheduleTask, ScheduleRiskScore
from app.modules.schedule.features import compute_features, compute_risk_score, get_contributing_factors
from app.modules.schedule.critical_path import compute_critical_path, get_downstream_tasks
from datetime import date
import json
import logging
import csv
import io

logger = logging.getLogger(__name__)


async def import_schedule_csv(db: AsyncSession, project_id: str, csv_content: str) -> dict:
    """Parse CSV and create ScheduleTask rows."""
    reader = csv.DictReader(io.StringIO(csv_content))
    imported = 0
    skipped = 0

    pending_dependencies: list[tuple[ScheduleTask, str | None]] = []
    wbs_to_id: dict[str, str] = {}
    for row in reader:
        try:
            task = ScheduleTask(
                project_id=project_id,
                wbs_code=row.get("wbs_code", row.get("WBS", "")),
                task_name=row.get("task_name", row.get("Task Name", row.get("name", "Unnamed"))),
                planned_start=_parse_date(row.get("planned_start", row.get("Planned Start"))),
                planned_end=_parse_date(row.get("planned_end", row.get("Planned End"))),
                actual_start=_parse_date(row.get("actual_start", row.get("Actual Start"))),
                actual_end=_parse_date(row.get("actual_end", row.get("Actual End"))),
                duration_days=_parse_int(row.get("duration_days", row.get("Duration"))),
                dependencies=row.get("dependencies", row.get("Dependencies")),
                workforce_availability=_parse_float(row.get("workforce_availability", row.get("Workforce %")), 100.0),
                status=row.get("status", "not_started"),
            )
            db.add(task)
            await db.flush()
            if task.wbs_code:
                wbs_to_id[task.wbs_code] = task.id
            pending_dependencies.append((task, row.get("dependencies", row.get("Dependencies"))))
            imported += 1
        except Exception as e:
            logger.warning(f"Skipping row: {e}")
            skipped += 1

    for task, raw_dependencies in pending_dependencies:
        if not raw_dependencies:
            continue
        dependency_refs = json.loads(raw_dependencies)
        if not isinstance(dependency_refs, list):
            raise ValueError("Dependencies must be a JSON list")
        resolved = [wbs_to_id.get(str(ref), str(ref)) for ref in dependency_refs]
        unknown = [ref for ref in resolved if ref not in wbs_to_id.values()]
        if unknown:
            raise ValueError(f"Unknown dependencies for '{task.task_name}': {', '.join(unknown)}")
        task.dependencies = json.dumps(resolved)

    await db.commit()
    return {"imported_count": imported, "skipped_count": skipped, "message": f"Imported {imported} tasks, skipped {skipped}"}


async def compute_all_risk_scores(db: AsyncSession, project_id: str) -> list:
    """Compute risk scores for all tasks in a project."""
    result = await db.execute(
        select(ScheduleTask).where(ScheduleTask.project_id == project_id)
    )
    tasks = result.scalars().all()

    if not tasks:
        return []

    # Build lookup for cross-task features
    task_dicts = []
    all_tasks_map = {}
    for t in tasks:
        td = {
            "id": t.id,
            "task_name": t.task_name,
            "wbs_code": t.wbs_code,
            "planned_start": t.planned_start,
            "planned_end": t.planned_end,
            "actual_start": t.actual_start,
            "actual_end": t.actual_end,
            "duration_days": t.duration_days,
            "dependencies": t.dependencies,
            "workforce_availability": t.workforce_availability,
            "status": t.status,
        }
        task_dicts.append(td)
        all_tasks_map[t.id] = td

    # Critical path
    critical_set = compute_critical_path(task_dicts)

    # Compute risk for each task
    risk_results = []
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

        # Persist risk score
        risk_record = ScheduleRiskScore(
            task_id=td["id"],
            risk_score=score,
            predicted_delay_days=max(delay_prediction, 0),
            contributing_factors=json.dumps([f["factor"] for f in factors]),
        )
        db.add(risk_record)

        risk_results.append({
            "task_id": td["id"],
            "task_name": td["task_name"],
            "wbs_code": td["wbs_code"],
            "risk_score": score,
            "predicted_delay_days": max(delay_prediction, 0),
            "contributing_factors": [f["factor"] for f in factors],
            "status": td["status"],
            "is_critical_path": td["id"] in critical_set,
        })

    await db.commit()

    # Sort by risk_score desc (highest risk first), critical-path tasks prioritized
    risk_results.sort(key=lambda x: (not x["is_critical_path"], -x["risk_score"]))
    return risk_results


async def get_task_risk_explanation(db: AsyncSession, task_id: str) -> dict:
    """Get detailed risk explanation for a single task."""
    result = await db.execute(select(ScheduleTask).where(ScheduleTask.id == task_id))
    task = result.scalars().first()
    if not task:
        return None

    # Load all tasks for cross-referencing
    all_result = await db.execute(
        select(ScheduleTask).where(ScheduleTask.project_id == task.project_id)
    )
    all_tasks = all_result.scalars().all()
    all_tasks_map = {}
    task_dicts = []
    for t in all_tasks:
        td = {
            "id": t.id, "task_name": t.task_name, "wbs_code": t.wbs_code,
            "planned_start": t.planned_start, "planned_end": t.planned_end,
            "actual_start": t.actual_start, "actual_end": t.actual_end,
            "duration_days": t.duration_days, "dependencies": t.dependencies,
            "workforce_availability": t.workforce_availability, "status": t.status,
        }
        task_dicts.append(td)
        all_tasks_map[t.id] = td

    target_td = all_tasks_map.get(task_id, {})
    features = compute_features(target_td, all_tasks_map)
    score = compute_risk_score(features)
    factors = get_contributing_factors(features)
    critical_set = compute_critical_path(task_dicts)
    downstream = get_downstream_tasks(task_id, task_dicts)

    return {
        "task_id": task_id,
        "task_name": task.task_name,
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
        return date.fromisoformat(val.strip())
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
