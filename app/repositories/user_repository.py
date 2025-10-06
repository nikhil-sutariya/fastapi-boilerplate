from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.user import User, Notification
from app.core.logging import setup_logger
from app.repositories.base_repository import get_record_by_field, get_records_by_filter, update_record
import uuid

logger = setup_logger()

async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    """Get user by email address"""
    try:
        return await get_record_by_field(session, User, "email", email.lower())
    except Exception as e:
        logger.error(f"Error getting user by email: {e}")
        return None

async def get_user_by_id(session: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    """Get user by ID"""
    try:
        from app.repositories.base_repository import get_record_by_id
        return await get_record_by_id(session, User, user_id)
    except Exception as e:
        logger.error(f"Error getting user by ID: {e}")
        return None

async def get_notifications_by_user(session: AsyncSession, user_id: uuid.UUID) -> Optional[List[Notification]]:
    """Get all notifications for a user"""
    try:
        notifications = await get_records_by_filter(session, Notification, user_id=user_id)
        # Sort by created_at descending (most recent first)
        if notifications:
            return sorted(notifications, key=lambda x: x.created_at, reverse=True)
        return notifications
    except Exception as e:
        logger.error(f"Error getting notifications by user: {e}")
        return None

async def update_notification_status(session: AsyncSession, user_id: uuid.UUID) -> bool:
    """Update all notifications for a user to seen status"""
    try:
        stmt = update(Notification).where(Notification.user_id == user_id).values(
            is_seen=True, 
            updated_at=datetime.now(timezone.utc)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0
    except Exception as e:
        logger.error(f"Error updating notification status: {e}")
        await session.rollback()
        return False

async def create_user(session: AsyncSession, user_data: Dict[str, Any]) -> Optional[User]:
    """Create a new user"""
    try:
        from app.repositories.base_repository import create_record
        return await create_record(session, User, user_data)
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return None

async def update_user(session: AsyncSession, user_id: uuid.UUID, user_data: Dict[str, Any]) -> Optional[User]:
    """Update user data"""
    try:
        return await update_record(session, User, user_id, user_data)
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        return None
