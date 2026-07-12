"""Supply chain service — CRUD + risk computation for shipments."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from app.modules.supply_chain.models import Shipment, ShipmentEvent
from app.modules.supply_chain.risk import compute_shipment_risk, get_risk_status, suggest_mitigations
from datetime import date
import logging

logger = logging.getLogger(__name__)


async def create_shipment(db: AsyncSession, project_id: str, data: dict) -> Shipment:
    shipment = Shipment(project_id=project_id, **data)
    # Compute initial risk
    shipment.risk_score = compute_shipment_risk(
        required_on_site=shipment.required_on_site,
        status=shipment.status,
    )
    shipment.status = get_risk_status(shipment.risk_score)
    db.add(shipment)
    await db.commit()
    await db.refresh(shipment)
    return shipment


async def add_shipment_event(db: AsyncSession, shipment_id: str, data: dict) -> ShipmentEvent:
    # Verify shipment exists
    result = await db.execute(select(Shipment).where(Shipment.id == shipment_id))
    shipment = result.scalars().first()
    if not shipment:
        return None

    event = ShipmentEvent(shipment_id=shipment_id, **data)
    db.add(event)

    # Recompute risk based on events
    events_result = await db.execute(
        select(ShipmentEvent)
        .where(ShipmentEvent.shipment_id == shipment_id)
        .order_by(desc(ShipmentEvent.occurred_at))
    )
    events = events_result.scalars().all()

    # Count missed milestones (delayed events)
    missed = sum(1 for e in events if e.event_type == "delayed")
    total = len(events)

    if data.get("event_type") == "arrived":
        shipment.status = "delivered"
        shipment.risk_score = 0.0
    else:
        shipment.risk_score = compute_shipment_risk(
            required_on_site=shipment.required_on_site,
            missed_milestones=missed,
            total_milestones=max(total, 1),
            status=shipment.status,
        )
        shipment.status = get_risk_status(shipment.risk_score)

    await db.commit()
    await db.refresh(event)
    return event


async def get_map_data(db: AsyncSession, project_id: str) -> list:
    """Return all shipments with current position for map rendering."""
    result = await db.execute(
        select(Shipment).where(Shipment.project_id == project_id)
    )
    shipments = result.scalars().all()

    map_data = []
    for s in shipments:
        # Get latest event with coordinates
        events_result = await db.execute(
            select(ShipmentEvent)
            .where(ShipmentEvent.shipment_id == s.id)
            .order_by(desc(ShipmentEvent.occurred_at))
            .limit(1)
        )
        latest_event = events_result.scalars().first()

        current_lat = latest_event.lat if latest_event and latest_event.lat else s.origin_lat
        current_lng = latest_event.lng if latest_event and latest_event.lng else s.origin_lng

        map_data.append({
            "id": s.id,
            "equipment_type": s.equipment_type,
            "description": s.description,
            "status": s.status,
            "risk_score": s.risk_score,
            "current_lat": current_lat,
            "current_lng": current_lng,
            "destination_lat": s.destination_lat,
            "destination_lng": s.destination_lng,
            "required_on_site": s.required_on_site,
        })

    return map_data


async def get_at_risk_shipments(db: AsyncSession, project_id: str) -> list:
    """Return shipments flagged as at-risk with mitigation suggestions."""
    result = await db.execute(
        select(Shipment)
        .where(Shipment.project_id == project_id, Shipment.risk_score >= 40)
        .order_by(desc(Shipment.risk_score))
    )
    shipments = result.scalars().all()

    at_risk = []
    for s in shipments:
        days_remaining = None
        if s.required_on_site:
            days_remaining = (s.required_on_site - date.today()).days

        at_risk.append({
            "id": s.id,
            "equipment_type": s.equipment_type,
            "description": s.description,
            "risk_score": s.risk_score,
            "days_until_required": days_remaining,
            "mitigation_suggestions": suggest_mitigations(s.equipment_type, s.risk_score, days_remaining),
        })

    return at_risk
