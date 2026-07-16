from fastapi import APIRouter, Depends, Header
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.base import get_db
from app.modules.auth.dependencies import get_current_user

router = APIRouter()


@router.get("/summary")
async def get_dashboard_summary(
    project_id: str = Header(None),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Aggregated dashboard payload — cross-module state in one call."""
    match_stage = {}
    if project_id:
        match_stage["project_id"] = project_id

    open_deviations = await db.deviations.count_documents({"status": "open"})
    critical_deviations = await db.deviations.count_documents({"status": "open", "severity": "Critical"})
    
    pending_rfis = await db.rfis.count_documents({"status": "open"})
    
    approved_submittals = await db.submittals.count_documents({"status": "approved"})
    total_submittals = await db.submittals.count_documents({})
    
    # Schedule risk — top 5 riskiest tasks
    risk_scores = []
    async for rs in db.schedule_risk_scores.find().sort("risk_score", -1).limit(5):
        task = await db.schedule_tasks.find_one({"_id": rs["task_id"]})
        if not task:
            continue
        risk_scores.append({
            "task_id": rs["task_id"],
            "task_name": task.get("task_name", "Unknown"),
            "wbs_code": task.get("wbs_code"),
            "risk_score": rs["risk_score"],
            "predicted_delay_days": rs.get("predicted_delay_days"),
            "contributing_factors": rs.get("contributing_factors", []),
            "status": task.get("status", "not_started"),
            "is_critical_path": task.get("is_critical_path", False),
        })

    at_risk_shipments = await db.shipments.count_documents({"risk_score": {"$gte": 40}})
    total_shipments = await db.shipments.count_documents({})
    
    active_commissioning = await db.commissioning_runs.count_documents({"status": "in_progress"})

    return {
        "open_deviations": open_deviations,
        "critical_deviations": critical_deviations,
        "pending_rfis": pending_rfis,
        "approved_submittals": approved_submittals,
        "total_submittals": total_submittals,
        "schedule_risk": risk_scores,
        "at_risk_shipments": at_risk_shipments,
        "total_shipments": total_shipments,
        "active_commissioning": active_commissioning,
    }


@router.get("/stats")
async def get_dashboard_stats(db: AsyncIOMotorDatabase = Depends(get_db)):
    """Legacy stats endpoint for backward compatibility."""
    summary = await get_dashboard_summary(project_id=None, db=db)
    return {
        "open_deviations": summary["open_deviations"],
        "pending_rfis": summary["pending_rfis"],
        "approved_submittals": summary["approved_submittals"],
        "schedule_risk": summary["schedule_risk"],
    }


@router.get("/notifications")
async def get_notifications(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get in-app notifications for the current user."""
    query = {"$or": [{"user_id": current_user["_id"]}, {"user_id": None}]}
    
    notifications = []
    async for n in db.notifications.find(query).sort("created_at", -1).limit(20):
        n["id"] = n.pop("_id")
        notifications.append(n)
        
    return notifications
