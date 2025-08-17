from datetime import datetime, timezone
from app.db.collections import User, Notification
from app.core.logging import setup_logger

logger = setup_logger()

async def get_user_by_email(email: str):
    try:
        user = await User().find_one({"email": email})
        return user

    except Exception as e:
        logger.error(str(e))
        return None

async def get_notifications_by_user(user_id: str):
    try:
        user_notifications = await Notification().find({"user_id": user_id}).sort({"created_at": -1}).to_list(length=None)
        return user_notifications

    except Exception as e:
        logger.error(str(e))
        return None
    
async def update_notification_status(user_id: str):
    try:
        user_notifications = await Notification().update_many({"user_id": user_id}, {"$set": {"is_seen": True, "updated_at": datetime.now(timezone.utc)}})
        return user_notifications

    except Exception as e:
        logger.error(str(e))
        return None
