from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pymongo.results import UpdateResult
from app.db.collections import User, Notification
from app.core.logging import setup_logger
from app.core.custom_model_fields import mongo_to_dict

logger = setup_logger()

async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    try:
        user = await User().find_one({"email": email})
        if user:
            # Convert _id to id for API usage
            return mongo_to_dict(user)
        return None

    except Exception as e:
        logger.error(str(e))
        return None

async def get_notifications_by_user(user_id: str) -> Optional[List[Dict[str, Any]]]:
    try:
        user_notifications = await Notification().find({"user_id": user_id}).sort({"created_at": -1}).to_list(length=None)
        # Convert all notifications _id to id for API usage
        return [mongo_to_dict(notification) for notification in user_notifications] if user_notifications else None

    except Exception as e:
        logger.error(str(e))
        return None
    
async def update_notification_status(user_id: str) -> Optional[UpdateResult]:
    try:
        user_notifications = await Notification().update_many({"user_id": user_id}, {"$set": {"is_seen": True, "updated_at": datetime.now(timezone.utc)}})
        return user_notifications

    except Exception as e:
        logger.error(str(e))
        return None
