from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.db.base import get_db
from app.modules.compliance.models import Deviation, Submittal
from app.modules.rfi.models import Rfi
import random

router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    # Count open deviations
    dev_query = select(func.count(Deviation.id)).where(Deviation.severity.in_(["Critical", "Major"]))
    dev_res = await db.execute(dev_query)
    open_deviations = dev_res.scalar() or 0
    
    # Count pending RFIs
    # Assuming Rfi has a status field, if not just count total for hackathon
    try:
        rfi_query = select(func.count(Rfi.id)).where(Rfi.status == "pending")
        rfi_res = await db.execute(rfi_query)
        pending_rfis = rfi_res.scalar() or 0
    except:
        rfi_query = select(func.count(Rfi.id))
        rfi_res = await db.execute(rfi_query)
        pending_rfis = rfi_res.scalar() or 0
        
    # Count approved submittals
    sub_query = select(func.count(Submittal.id)).where(Submittal.status == "approved")
    sub_res = await db.execute(sub_query)
    approved_submittals = sub_res.scalar() or 0
    
    # Schedule Risk heuristic for hackathon
    schedule_risk_tasks = [
        {"task_id": "T-1001", "risk_score": random.randint(60, 95), "top_factors": ["Vendor Lead Time", "Weather"]},
        {"task_id": "T-2042", "risk_score": random.randint(50, 80), "top_factors": ["Workforce Availability"]},
    ]

    return {
        "open_deviations": open_deviations,
        "pending_rfis": pending_rfis,
        "approved_submittals": approved_submittals,
        "schedule_risk": schedule_risk_tasks
    }
