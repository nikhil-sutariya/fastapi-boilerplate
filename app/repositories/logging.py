from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.user import Log
from app.core.logging import setup_logger
from app.repositories.base_repository import create_record, get_records_by_filter
import uuid

logger = setup_logger()

async def get_logs_by_user(session: AsyncSession, user_id: uuid.UUID) -> Optional[List[Log]]:
    """Get all logs for a specific user, sorted by created_at descending"""
    try:
        logs = await get_records_by_filter(session, Log, user_id=user_id)
        if logs:
            return sorted(logs, key=lambda x: x.created_at, reverse=True)
        return logs
    except Exception as e:
        logger.error(f"Error getting logs by user: {e}")
        return None

async def create_log(session: AsyncSession, log_data: Dict[str, Any]) -> bool:
    """Create a new log entry"""
    try:
        log_record = await create_record(session, Log, log_data)
        if log_record:
            return True
        return False
    except Exception as e:
        logger.error(f"Error creating log: {e}")
        return False
