from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.base import get_db
from app.modules.projects import schemas
from app.modules.auth.dependencies import get_current_user
import uuid

router = APIRouter()


@router.post("", response_model=schemas.ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: schemas.ProjectCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    project_dict = {
        "_id": str(uuid.uuid4()),
        "name": project_in.name,
        "location": project_in.location,
        "client": project_in.client,
        "start_date": project_in.start_date.isoformat() if project_in.start_date else None,
        "target_completion": project_in.target_completion.isoformat() if project_in.target_completion else None,
        "status": "Active"
    }
    await db.projects.insert_one(project_dict)
    
    project_dict["id"] = project_dict.pop("_id")
    return project_dict


@router.get("", response_model=list[schemas.ProjectResponse])
async def list_projects(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    projects = []
    async for p in db.projects.find().sort("name", 1):
        p["id"] = p.pop("_id")
        projects.append(p)

    if not projects:
        default_project = {
            "_id": str(uuid.uuid4()),
            "name": "Hyperscale Data Center - Phase 1",
            "location": "Mumbai, India",
            "client": "TechCorp Global",
            "start_date": None,
            "target_completion": None,
            "status": "Active"
        }
        await db.projects.insert_one(default_project)
        default_project["id"] = default_project.pop("_id")
        projects.append(default_project)

    return projects


@router.get("/{project_id}", response_model=schemas.ProjectResponse)
async def get_project(
    project_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    project = await db.projects.find_one({"_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project["id"] = project.pop("_id")
    return project


@router.patch("/{project_id}", response_model=schemas.ProjectResponse)
async def update_project(
    project_id: str,
    project_in: schemas.ProjectUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    project = await db.projects.find_one({"_id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = project_in.model_dump(exclude_unset=True)
    if "start_date" in update_data and update_data["start_date"]:
        update_data["start_date"] = update_data["start_date"].isoformat()
    if "target_completion" in update_data and update_data["target_completion"]:
        update_data["target_completion"] = update_data["target_completion"].isoformat()

    if update_data:
        await db.projects.update_one({"_id": project_id}, {"$set": update_data})
        
    project = await db.projects.find_one({"_id": project_id})
    project["id"] = project.pop("_id")
    return project
