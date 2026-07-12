from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.modules.supply_chain import service, schemas
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User

router = APIRouter()


@router.post("", response_model=schemas.ShipmentResponse, status_code=status.HTTP_201_CREATED)
async def create_shipment(
    shipment_in: schemas.ShipmentCreate,
    project_id: str = Header(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await service.create_shipment(db, project_id, shipment_in.model_dump())


@router.post("/{shipment_id}/events", response_model=schemas.ShipmentEventResponse)
async def add_event(
    shipment_id: str,
    event_in: schemas.ShipmentEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = await service.add_shipment_event(db, shipment_id, event_in.model_dump())
    if not event:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return event


@router.get("/map", response_model=list[schemas.MapShipmentResponse])
async def get_shipment_map(
    project_id: str = Header(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await service.get_map_data(db, project_id)


@router.get("/at-risk", response_model=list[schemas.AtRiskShipmentResponse])
async def get_at_risk(
    project_id: str = Header(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await service.get_at_risk_shipments(db, project_id)
