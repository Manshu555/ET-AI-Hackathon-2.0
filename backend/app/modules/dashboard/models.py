from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
import uuid
from app.db.base import Base


def generate_uuid():
    return str(uuid.uuid4())


class Notification(Base):
    """In-app notification for critical events across modules."""
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # target user, null = broadcast
    type = Column(String, nullable=False)  # deviation, schedule_risk, shipment_risk, rfi
    message = Column(String, nullable=False)
    related_entity_id = Column(String, nullable=True)  # ID of the related deviation/task/shipment
    read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
