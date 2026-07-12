from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class ShipmentCreate(BaseModel):
    equipment_type: str
    description: Optional[str] = None
    vendor_id: Optional[str] = None
    origin_lat: Optional[float] = None
    origin_lng: Optional[float] = None
    destination_lat: Optional[float] = None
    destination_lng: Optional[float] = None
    required_on_site: Optional[date] = None


class ShipmentResponse(BaseModel):
    id: str
    project_id: str
    vendor_id: Optional[str] = None
    equipment_type: str
    description: Optional[str] = None
    origin_lat: Optional[float] = None
    origin_lng: Optional[float] = None
    destination_lat: Optional[float] = None
    destination_lng: Optional[float] = None
    required_on_site: Optional[date] = None
    status: str
    risk_score: float


class ShipmentEventCreate(BaseModel):
    event_type: str  # departed, in_transit, customs, arrived, delayed
    lat: Optional[float] = None
    lng: Optional[float] = None
    notes: Optional[str] = None


class ShipmentEventResponse(BaseModel):
    id: str
    shipment_id: str
    event_type: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    notes: Optional[str] = None
    occurred_at: Optional[datetime] = None


class MapShipmentResponse(BaseModel):
    id: str
    equipment_type: str
    description: Optional[str] = None
    status: str
    risk_score: float
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None
    destination_lat: Optional[float] = None
    destination_lng: Optional[float] = None
    required_on_site: Optional[date] = None


class AtRiskShipmentResponse(BaseModel):
    id: str
    equipment_type: str
    description: Optional[str] = None
    risk_score: float
    days_until_required: Optional[int] = None
    mitigation_suggestions: List[str] = []
