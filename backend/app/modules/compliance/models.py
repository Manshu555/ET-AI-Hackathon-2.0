from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
import uuid
from app.db.base import Base

def generate_uuid():
    return str(uuid.uuid4())

class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)

class Specification(Base):
    __tablename__ = "specifications"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    spec_code = Column(String, nullable=False)
    section = Column(String, nullable=True)
    requirement_text = Column(String, nullable=False)
    numeric_requirement = Column(Float, nullable=True) # Optional numeric extraction

class Submittal(Base):
    __tablename__ = "submittals"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    vendor_id = Column(String, ForeignKey("vendors.id"), nullable=False)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    status = Column(String, default="pending") # pending, under_review, approved, rejected
    reviewed_by = Column(String, ForeignKey("users.id"), nullable=True)

class Deviation(Base):
    __tablename__ = "deviations"

    id = Column(String, primary_key=True, default=generate_uuid)
    submittal_id = Column(String, ForeignKey("submittals.id"), nullable=False)
    spec_id = Column(String, ForeignKey("specifications.id"), nullable=False)
    description = Column(String, nullable=False)
    severity = Column(String, nullable=False) # Minor, Major, Critical
    detected_by = Column(String, nullable=False) # 'ai' or 'rule'
    status = Column(String, default="open") # open, overridden, dismissed
    resolution_note = Column(String, nullable=True)
