from typing import Any, Optional
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi import Header, Depends
from app.core.config import settings

# ── Async engine (for FastAPI request handlers) ──────────────────
engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=True,
    connect_args={"timeout": 2.0} # Fast timeout for hackathon fallback
)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ── Sync engine (for Celery workers) ─────────────────────────────
# Convert async URL to sync: sqlite+aiosqlite → sqlite, postgresql+asyncpg → postgresql+psycopg2
_sync_url = settings.DATABASE_URL
if "+aiosqlite" in _sync_url:
    _sync_url = _sync_url.replace("+aiosqlite", "")
elif "+asyncpg" in _sync_url:
    _sync_url = _sync_url.replace("+asyncpg", "+psycopg2")

sync_engine = create_engine(_sync_url, echo=False)
SyncSessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False)

Base = declarative_base()


def get_sync_db() -> Session:
    """Get a synchronous DB session — used by Celery workers."""
    session = SyncSessionLocal()
    try:
        return session
    except Exception:
        session.close()
        raise


async def get_db():
    async with async_session_maker() as session:
        yield session


async def get_project_db(project_id: str = Header(None)):
    # In a full PostgreSQL implementation, this uses RLS via SET LOCAL app.current_project_id = :project_id
    # For this SQLite demo, we yield the normal session. The API layer handles project filtering.
    async with async_session_maker() as session:
        yield session
