from app.db.collections import Logs
from pymongo import DESCENDING
from app.schemas.logging import LogSchema
from app.core.logging import setup_logger
from typing import Optional, List, Dict, Any

logger = setup_logger()

async def get_logs_by_user(user_id: str) -> Optional[List[Dict[str, Any]]]:
    try:
        logs = await Logs().find({"user_id": user_id}).sort('created_at', DESCENDING).to_list(length=None)
        return logs
        
    except Exception as e:
        logger.error(str(e))
        return None

async def create_log(data: Dict[str, Any]) -> Optional[str]:
    try:
        log_data = LogSchema(**data).model_dump()
        log_inserted = await Logs().insert_one(log_data)
        return str(log_inserted)
        
    except Exception as e:
        logger.error(str(e))
        return None
