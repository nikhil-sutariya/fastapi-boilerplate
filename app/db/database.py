from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from contextvars import ContextVar
from fastapi import Request, FastAPI
from app.core.config import get_settings
from app.core.logging import setup_logger
from typing import Dict, Optional, Any, Union

settings = get_settings()
logger = setup_logger()

class DatabaseManager:
    _instance = None
    _db: Optional[AsyncIOMotorDatabase] = None
    _collections: Dict[str, AsyncIOMotorCollection] = {}

    def __new__(cls) -> "DatabaseManager":
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    @classmethod
    async def initialize(cls) -> None:
        """Initialize database connection and collections"""
        if cls._db is None:
            client = AsyncIOMotorClient(settings.mongo_uri)
            cls._db = client[settings.db_name]
            
            # Initialize collections
            cls._collections = {
                "user": cls._db["users"],
                "notification": cls._db["notifications"],
                "logs": cls._db["logs"]
            }

    @classmethod
    async def close(cls) -> None:
        """Close database connection"""
        if cls._db is not None:
            cls._db.client.close()
            cls._db = None
            cls._collections = {}

    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        """Get database instance"""
        if cls._db is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return cls._db

    @classmethod
    def get_collection(cls, name: str) -> AsyncIOMotorCollection:
        """Get collection by name"""
        if cls._db is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        if name not in cls._collections:
            raise ValueError(f"Collection '{name}' not found")
        return cls._collections[name]

async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for database connection"""
    await DatabaseManager.initialize()
    yield
    await DatabaseManager.close()
