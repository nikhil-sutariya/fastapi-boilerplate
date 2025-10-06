from app.db.database import DatabaseManager
from motor.motor_asyncio import AsyncIOMotorCollection
from app.core.logging import setup_logger
from typing import Callable

logger = setup_logger()

def get_user_collection() -> AsyncIOMotorCollection:
    try:
        return DatabaseManager.get_collection("user")
    except RuntimeError as e:
        logger.error(f"Database not initialized: {e}")
        raise

def get_notification_collection() -> AsyncIOMotorCollection:
    try:
        return DatabaseManager.get_collection("notification")
    except RuntimeError as e:
        logger.error(f"Database not initialized: {e}")
        raise

def get_logs_collection() -> AsyncIOMotorCollection:
    try:
        return DatabaseManager.get_collection("logs")
    except RuntimeError as e:
        logger.error(f"Database not initialized: {e}")
        raise

# For backward compatibility
User: Callable[[], AsyncIOMotorCollection] = get_user_collection
Notification: Callable[[], AsyncIOMotorCollection] = get_notification_collection
Logs: Callable[[], AsyncIOMotorCollection] = get_logs_collection
