from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc
from app.db.base import get_db
from app.modules.compliance.models import Deviation, Submittal
from app.modules.rfi.models import Rfi
from app.modules.schedule.models import ScheduleTask, ScheduleRiskScore
from app.modules.supply_chain.models import Shipment
from app.modules.commissioning.models import CommissioningRun
from app.modules.dashboard.models import Notification
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User

router = APIRouter()


@router.get("/summary")
async def get_dashboard_summary(
    project_id: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Aggregated dashboard payload — cross-module state in one call."""

    # Open deviations
    dev_query = select(func.count(Deviation.id)).where(Deviation.status == "open")
    dev_res = await db.execute(dev_query)
    open_deviations = dev_res.scalar() or 0

    critical_query = select(func.count(Deviation.id)).where(
        Deviation.status == "open", Deviation.severity == "Critical"
    )
    critical_res = await db.execute(critical_query)
    critical_deviations = critical_res.scalar() or 0

    # Pending RFIs
    try:
        rfi_query = select(func.count(Rfi.id)).where(Rfi.status == "open")
        rfi_res = await db.execute(rfi_query)
        pending_rfis = rfi_res.scalar() or 0
    except Exception:
        pending_rfis = 0

    # Submittals
    sub_approved_q = select(func.count(Submittal.id)).where(Submittal.status == "approved")
    sub_approved_res = await db.execute(sub_approved_q)
    approved_submittals = sub_approved_res.scalar() or 0

    sub_total_q = select(func.count(Submittal.id))
    sub_total_res = await db.execute(sub_total_q)
    total_submittals = sub_total_res.scalar() or 0

    # Schedule risk — top 5 riskiest tasks
    try:
        risk_query = select(ScheduleRiskScore).order_by(desc(ScheduleRiskScore.risk_score)).limit(5)
        risk_res = await db.execute(risk_query)
        risk_scores = risk_res.scalars().all()

        schedule_risk = []
        for rs in risk_scores:
            task_res = await db.execute(select(ScheduleTask).where(ScheduleTask.id == rs.task_id))
            task = task_res.scalars().first()
            import json
            schedule_risk.append({
                "task_id": rs.task_id,
                "task_name": task.task_name if task else "Unknown",
                "wbs_code": task.wbs_code if task else None,
                "risk_score": rs.risk_score,
                "predicted_delay_days": rs.predicted_delay_days,
                "contributing_factors": json.loads(rs.contributing_factors) if rs.contributing_factors else [],
                "status": task.status if task else "not_started",
            })
    except Exception as e:
        print(f"Error fetching schedule risk: {e}")
        schedule_risk = []

    # At-risk shipments
    try:
        ship_query = select(func.count(Shipment.id)).where(Shipment.risk_score >= 40)
        ship_res = await db.execute(ship_query)
        at_risk_shipments = ship_res.scalar() or 0
    except Exception:
        at_risk_shipments = 0

    # Total shipments
    try:
        ship_total_q = select(func.count(Shipment.id))
        ship_total_res = await db.execute(ship_total_q)
        total_shipments = ship_total_res.scalar() or 0
    except Exception:
        total_shipments = 0

    # Active commissioning runs
    try:
        comm_query = select(func.count(CommissioningRun.id)).where(CommissioningRun.status == "in_progress")
        comm_res = await db.execute(comm_query)
        active_commissioning = comm_res.scalar() or 0
    except Exception:
        active_commissioning = 0

    return {
        "open_deviations": open_deviations,
        "critical_deviations": critical_deviations,
        "pending_rfis": pending_rfis,
        "approved_submittals": approved_submittals,
        "total_submittals": total_submittals,
        "schedule_risk": schedule_risk,
        "at_risk_shipments": at_risk_shipments,
        "total_shipments": total_shipments,
        "active_commissioning": active_commissioning,
    }


@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get in-app notifications for the current user."""
    result = await db.execute(
        select(Notification)
        .where(
            (Notification.user_id == current_user.id) | (Notification.user_id == None)
        )
        .order_by(desc(Notification.created_at))
        .limit(20)
    )
    notifications = result.scalars().all()
    return [
        {
            "id": n.id,
            "type": n.type,
            "message": n.message,
            "related_entity_id": n.related_entity_id,
            "read": n.read,
            "created_at": n.created_at,
        }
        for n in notifications
    ]
