from typing import Any
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=True,
    connect_args={"timeout": 2.0} # Fast timeout for hackathon fallback
)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

from sqlalchemy import text
from fastapi import Header, Depends
from typing import Optional

async def get_db():
    async with async_session_maker() as session:
        yield session

async def get_project_db(project_id: str = Header(None)):
    # In a full PostgreSQL implementation, this uses RLS via SET LOCAL app.current_project_id = :project_id
    # For this SQLite demo, we yield the normal session. The API layer handles project filtering.
    async with async_session_maker() as session:
        yield session
