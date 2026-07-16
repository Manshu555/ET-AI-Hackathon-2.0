from motor.motor_asyncio import AsyncIOMotorDatabase
from app.modules.supply_chain.risk import compute_shipment_risk, get_risk_status, suggest_mitigations
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


async def create_shipment(db: AsyncIOMotorDatabase, project_id: str, data: dict) -> dict:
    shipment_id = str(uuid.uuid4())
    req_date = data.get("required_on_site")
    if req_date and hasattr(req_date, "isoformat"):
        req_date = req_date.isoformat()
    
    shipment = {
        "_id": shipment_id,
        "project_id": project_id,
        "vendor_id": data.get("vendor_id"),
        "equipment_type": data.get("equipment_type"),
        "description": data.get("description"),
        "origin_lat": data.get("origin_lat"),
        "origin_lng": data.get("origin_lng"),
        "destination_lat": data.get("destination_lat"),
        "destination_lng": data.get("destination_lng"),
        "required_on_site": req_date,
        "status": data.get("status", "pending"),
    }
    
    # Compute initial risk
    # For MongoDB, we need real python dates for delta calculation
    req_dt = None
    if shipment["required_on_site"]:
        req_dt = datetime.fromisoformat(shipment["required_on_site"]) if isinstance(shipment["required_on_site"], str) else shipment["required_on_site"]

    shipment["risk_score"] = compute_shipment_risk(
        required_on_site=req_dt.date() if req_dt else None,
        status=shipment["status"],
    )
    shipment["status"] = get_risk_status(shipment["risk_score"])
    
    await db.shipments.insert_one(shipment)
    shipment["id"] = shipment.pop("_id")
    return shipment


async def add_shipment_event(db: AsyncIOMotorDatabase, shipment_id: str, data: dict) -> dict:
    shipment = await db.shipments.find_one({"_id": shipment_id})
    if not shipment:
        return None

    event = {
        "_id": str(uuid.uuid4()),
        "shipment_id": shipment_id,
        "event_type": data.get("event_type"),
        "description": data.get("description"),
        "lat": data.get("lat"),
        "lng": data.get("lng"),
        "occurred_at": data.get("occurred_at", datetime.utcnow())
    }
    
    await db.shipment_events.insert_one(event)

    events = await db.shipment_events.find({"shipment_id": shipment_id}).sort("occurred_at", -1).to_list(None)

    missed = sum(1 for e in events if e.get("event_type") == "delayed")
    total = len(events)

    if data.get("event_type") == "arrived":
        shipment["status"] = "delivered"
        shipment["risk_score"] = 0.0
    else:
        req_dt = None
        if shipment.get("required_on_site"):
            req_dt = datetime.fromisoformat(shipment["required_on_site"]) if isinstance(shipment["required_on_site"], str) else shipment["required_on_site"]
            
        shipment["risk_score"] = compute_shipment_risk(
            required_on_site=req_dt.date() if req_dt else None,
            missed_milestones=missed,
            total_milestones=max(total, 1),
            status=shipment["status"],
        )
        shipment["status"] = get_risk_status(shipment["risk_score"])

    await db.shipments.update_one({"_id": shipment_id}, {"$set": {"status": shipment["status"], "risk_score": shipment["risk_score"]}})
    
    event["id"] = event.pop("_id")
    return event


async def get_map_data(db: AsyncIOMotorDatabase, project_id: str) -> list:
    shipments = await db.shipments.find({"project_id": project_id}).to_list(None)

    map_data = []
    for s in shipments:
        events = await db.shipment_events.find({"shipment_id": s["_id"]}).sort("occurred_at", -1).limit(1).to_list(1)
        latest_event = events[0] if events else None

        current_lat = latest_event.get("lat") if latest_event and latest_event.get("lat") else s.get("origin_lat")
        current_lng = latest_event.get("lng") if latest_event and latest_event.get("lng") else s.get("origin_lng")

        map_data.append({
            "id": s["_id"],
            "equipment_type": s.get("equipment_type"),
            "description": s.get("description"),
            "status": s.get("status"),
            "risk_score": s.get("risk_score"),
            "current_lat": current_lat,
            "current_lng": current_lng,
            "destination_lat": s.get("destination_lat"),
            "destination_lng": s.get("destination_lng"),
            "required_on_site": s.get("required_on_site"),
        })

    return map_data


async def get_at_risk_shipments(db: AsyncIOMotorDatabase, project_id: str) -> list:
    shipments = await db.shipments.find(
        {"project_id": project_id, "risk_score": {"$gte": 40}}
    ).sort("risk_score", -1).to_list(None)

    at_risk = []
    from datetime import date
    
    for s in shipments:
        days_remaining = None
        req_dt = None
        if s.get("required_on_site"):
            req_dt = datetime.fromisoformat(s["required_on_site"]) if isinstance(s["required_on_site"], str) else s["required_on_site"]
            if hasattr(req_dt, "date"):
                days_remaining = (req_dt.date() - date.today()).days
            else:
                days_remaining = (req_dt - date.today()).days

        at_risk.append({
            "id": s["_id"],
            "equipment_type": s.get("equipment_type"),
            "description": s.get("description"),
            "risk_score": s.get("risk_score"),
            "days_until_required": days_remaining,
            "mitigation_suggestions": suggest_mitigations(s.get("equipment_type"), s.get("risk_score"), days_remaining),
        })

    return at_risk
