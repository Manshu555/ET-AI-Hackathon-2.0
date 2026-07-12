from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
import uuid
from app.db.base import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False) # Admin, PM, QA_ENGINEER, PROCUREMENT, COMMISSIONING
    created_at = Column(DateTime(timezone=True), server_default=func.now())
