from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.db.base import get_db
from app.modules.compliance.models import Deviation, Submittal, Specification

router = APIRouter()

@router.get("/deviations")
async def get_all_deviations(db: AsyncSession = Depends(get_db)):
    # In a full implementation, we would filter by project_id.
    # For the hackathon demo, just return all deviations.
    query = select(Deviation).options(
        selectinload(Deviation.specification)
    ).order_by(Deviation.created_at.desc())
    
    result = await db.execute(query)
    deviations = result.scalars().all()
    
    out = []
    for d in deviations:
        spec_ref = d.specification.requirement_text[:50] + "..." if d.specification and d.specification.requirement_text else "Unknown Spec"
        out.append({
            "id": d.id,
            "spec": spec_ref,
            "severity": d.severity,
            "description": d.description,
            "submittal_id": d.submittal_id
        })
        
    return out
