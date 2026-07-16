from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from app.core.config import settings

# Async Client for FastAPI routes
async_client = AsyncIOMotorClient(
    settings.MONGODB_URI,
    serverSelectionTimeoutMS=5000  # Fail fast if MongoDB is down
)
async_db = async_client[settings.MONGODB_DB_NAME]

# Sync Client for Celery / background threads
sync_client = MongoClient(
    settings.MONGODB_URI,
    serverSelectionTimeoutMS=5000
)
sync_db = sync_client[settings.MONGODB_DB_NAME]

async def get_db():
    """Dependency to get the async MongoDB database instance."""
    yield async_db

def get_sync_db():
    """Get the synchronous MongoDB database instance for Celery workers."""
    return sync_db
