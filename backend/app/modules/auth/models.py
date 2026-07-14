from sqlalchemy import Column, String, DateTime, Boolean
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
    password_hash = Column(String, nullable=True)  # Nullable for Google OAuth users
    role = Column(String, nullable=False, default="engineer")
    google_id = Column(String, unique=True, nullable=True)  # Google sub ID
    auth_provider = Column(String, nullable=False, default="local")  # "local" or "google"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
