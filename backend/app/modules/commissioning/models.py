from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
import uuid
from app.db.base import Base


def generate_uuid():
    return str(uuid.uuid4())


class CommissioningTemplate(Base):
    """A standard test template (TIA-942 / BICSI / Uptime Tier)."""
    __tablename__ = "commissioning_templates"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    standard = Column(String, nullable=False)  # TIA-942, BICSI, Uptime
    system_type = Column(String, nullable=False)  # power, cooling, IT
    steps = Column(Text, nullable=False)  # JSON array of step definitions
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CommissioningRun(Base):
    """An active or completed commissioning test run."""
    __tablename__ = "commissioning_runs"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    template_id = Column(String, ForeignKey("commissioning_templates.id"), nullable=False)
    engineer_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="in_progress")  # in_progress, completed, failed
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)


class CommissioningStep(Base):
    """A single step result within a commissioning run."""
    __tablename__ = "commissioning_steps"

    id = Column(String, primary_key=True, default=generate_uuid)
    run_id = Column(String, ForeignKey("commissioning_runs.id"), nullable=False)
    step_number = Column(Integer, nullable=False)
    description = Column(String, nullable=False)
    expected_min = Column(Float, nullable=True)
    expected_max = Column(Float, nullable=True)
    expected_unit = Column(String, nullable=True)
    actual_value = Column(Float, nullable=True)
    status = Column(String, default="pending")  # pending, pass, fail
    deviation_id = Column(String, ForeignKey("deviations.id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
