from sqlalchemy import Column, String, Integer, Float, DateTime, Date, ForeignKey, Text
from sqlalchemy.sql import func
import uuid
from app.db.base import Base


def generate_uuid():
    return str(uuid.uuid4())


class ScheduleTask(Base):
    """A single task in the project schedule (imported from CSV / MS Project export)."""
    __tablename__ = "schedule_tasks"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    wbs_code = Column(String, nullable=True)
    task_name = Column(String, nullable=False)
    planned_start = Column(Date, nullable=True)
    planned_end = Column(Date, nullable=True)
    actual_start = Column(Date, nullable=True)
    actual_end = Column(Date, nullable=True)
    duration_days = Column(Integer, nullable=True)
    dependencies = Column(Text, nullable=True)  # JSON array of task IDs
    workforce_availability = Column(Float, default=100.0)  # percentage
    status = Column(String, default="not_started")  # not_started, in_progress, completed, delayed
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ScheduleRiskScore(Base):
    """Risk assessment for a schedule task — historical rows retained for trend charts."""
    __tablename__ = "schedule_risk_scores"

    id = Column(String, primary_key=True, default=generate_uuid)
    task_id = Column(String, ForeignKey("schedule_tasks.id"), nullable=False)
    risk_score = Column(Float, nullable=False)  # 0-100
    predicted_delay_days = Column(Float, nullable=True)
    contributing_factors = Column(Text, nullable=True)  # JSON array
    model_version = Column(String, default="v1.0")
    scored_at = Column(DateTime(timezone=True), server_default=func.now())
