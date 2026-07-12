from sqlalchemy import Column, String, Float, DateTime, Date, ForeignKey, Text
from sqlalchemy.sql import func
import uuid
from app.db.base import Base


def generate_uuid():
    return str(uuid.uuid4())


class Shipment(Base):
    """A shipment of critical long-lead equipment tracked geospatially."""
    __tablename__ = "shipments"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    vendor_id = Column(String, ForeignKey("vendors.id"), nullable=True)
    equipment_type = Column(String, nullable=False)  # UPS, generator, cooling_tower, switchgear
    description = Column(String, nullable=True)
    origin_lat = Column(Float, nullable=True)
    origin_lng = Column(Float, nullable=True)
    destination_lat = Column(Float, nullable=True)
    destination_lng = Column(Float, nullable=True)
    required_on_site = Column(Date, nullable=True)
    status = Column(String, default="in_transit")  # in_transit, delivered, at_risk, delayed
    risk_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ShipmentEvent(Base):
    """A tracking event on a shipment — appended in chronological order."""
    __tablename__ = "shipment_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    shipment_id = Column(String, ForeignKey("shipments.id"), nullable=False)
    event_type = Column(String, nullable=False)  # departed, in_transit, customs, arrived, delayed
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())
