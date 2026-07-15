from sqlalchemy import Column, String, Date, ForeignKey, UniqueConstraint
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


class ProjectMember(Base):
    """Explicit user-to-project membership used to enforce tenant boundaries."""
    __tablename__ = "project_members"
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_member"),)

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
