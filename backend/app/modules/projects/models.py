from sqlalchemy import Column, String, Date
import uuid
from app.db.base import Base

def generate_uuid():
    return str(uuid.uuid4())

class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    location = Column(String, nullable=True)
    client = Column(String, nullable=True)
    start_date = Column(Date, nullable=True)
    target_completion = Column(Date, nullable=True)
    status = Column(String, nullable=False, default="Active")
