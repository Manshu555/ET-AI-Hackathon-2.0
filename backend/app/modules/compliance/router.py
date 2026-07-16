from fastapi import APIRouter, Depends, Header, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.base import get_db
from app.modules.compliance.schemas import SpecificationCreate, SpecificationResponse, SubmittalCreate, SubmittalResponse, DeviationResponse
from app.modules.compliance.service import check_compliance
from app.modules.auth.dependencies import get_current_user
import uuid
from datetime import datetime

router = APIRouter()

@router.post("/specifications", response_model=SpecificationResponse)
async def create_specification(
    spec_in: SpecificationCreate,
    project_id: str = Header(...),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    spec = {
        "_id": str(uuid.uuid4()),
        "project_id": project_id,
        "title": spec_in.title,
        "content": spec_in.content,
        "section_code": spec_in.section_code,
        "created_at": datetime.utcnow()
    }
    await db.specifications.insert_one(spec)
    spec["id"] = spec.pop("_id")
    return spec

@router.get("/specifications", response_model=list[SpecificationResponse])
async def list_specifications(
    project_id: str = Header(None),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    query = {}
    if project_id:
        query["project_id"] = project_id
    specs = []
    async for spec in db.specifications.find(query):
        spec["id"] = spec.pop("_id")
        specs.append(spec)
    return specs

@router.post("/submittals", response_model=SubmittalResponse)
async def create_submittal(
    submittal_in: SubmittalCreate,
    project_id: str = Header(...),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    submittal = {
        "_id": str(uuid.uuid4()),
        "project_id": project_id,
        "vendor_id": submittal_in.vendor_id,
        "title": submittal_in.title,
        "description": submittal_in.description,
        "document_id": submittal_in.document_id,
        "status": "pending",
        "created_at": datetime.utcnow()
    }
    await db.submittals.insert_one(submittal)
    submittal["id"] = submittal.pop("_id")
    return submittal

@router.post("/submittals/{submittal_id}/check")
async def run_compliance_check(
    submittal_id: str,
    spec_id: str,
    project_id: str = Header(...),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Trigger AI compliance check."""
    result = await check_compliance(db, submittal_id, spec_id, project_id)
    return result

@router.get("/deviations", response_model=list[DeviationResponse])
async def list_deviations(
    project_id: str = Header(None),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    query = {}
    if project_id:
        # Get all submittals for this project to find related deviations
        submittals = await db.submittals.find({"project_id": project_id}, {"_id": 1}).to_list(None)
        sub_ids = [s["_id"] for s in submittals]
        query["submittal_id"] = {"$in": sub_ids}
        
    deviations = []
    async for dev in db.deviations.find(query).sort("created_at", -1):
        dev["id"] = dev.pop("_id")
        deviations.append(dev)
    return deviations
