"""Database configuration and connection management."""

from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine

from app.core.config import settings


class Database:
    """Database connection manager."""

    client: AsyncIOMotorClient = None
    engine: AIOEngine = None


db = Database()


async def connect_to_mongo():
    """Create database connection."""
    db.client = AsyncIOMotorClient(settings.MONGODB_URL)
    db.engine = AIOEngine(client=db.client, database=settings.DATABASE_NAME)

async def close_mongo_connection():
    """Close database connection."""
    if db.client:
        db.client.close()


def get_database() -> AIOEngine:
    """Get database engine instance."""
    return db.engine