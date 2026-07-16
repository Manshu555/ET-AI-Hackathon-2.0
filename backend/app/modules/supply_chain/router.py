from fastapi import APIRouter, Depends, Header, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.base import get_db
from app.modules.supply_chain.schemas import ShipmentCreate, ShipmentResponse, ShipmentEventCreate, ShipmentEventResponse, MapShipmentResponse, AtRiskShipmentResponse
from app.modules.supply_chain.service import create_shipment, add_shipment_event, get_map_data, get_at_risk_shipments
from app.modules.auth.dependencies import get_current_user

router = APIRouter()

@router.post("", response_model=ShipmentResponse, status_code=201)
async def api_create_shipment(
    shipment_in: ShipmentCreate,
    project_id: str = Header(...),
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Register a new shipment for tracking."""
    result = await create_shipment(db, project_id, shipment_in.model_dump())
    return result

@router.post("/{shipment_id}/events", response_model=ShipmentEventResponse)
async def api_add_event(
    shipment_id: str,
    event_in: ShipmentEventCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Add a tracking event (location update, delay, arrival)."""
    event = await add_shipment_event(db, shipment_id, event_in.model_dump())
    if not event:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return event

@router.get("/map", response_model=list[MapShipmentResponse])
async def api_get_map_data(
    project_id: str = Header(...),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Get all shipments with their latest coordinates for map rendering."""
    data = await get_map_data(db, project_id)
    return data

@router.get("/at-risk", response_model=list[AtRiskShipmentResponse])
async def api_get_at_risk(
    project_id: str = Header(...),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Get shipments with high delay risk and mitigation suggestions."""
    data = await get_at_risk_shipments(db, project_id)
    return data
