from fastapi import APIRouter, status, Depends
from fastapi.responses import Response as FastAPIResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.response import Response
from app.messages.logging import ErrorMessage, InfoMessage
from app.schemas.user import CurrentUser
from app.api.deps.auth_deps import get_current_user
from app.db.database import get_db
from app.repositories.logging import get_logs_by_user
from app.core.logging import setup_logger

logger = setup_logger()

log_router = APIRouter()

@log_router.get("/get-logs")
async def get_logs(current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> FastAPIResponse:
    try:
        logs = await get_logs_by_user(db, current_user.id)
        
        # Convert SQLAlchemy objects to dictionaries for JSON serialization
        logs_data = []
        if logs:
            for log in logs:
                logs_data.append({
                    "id": log.id,
                    "user_id": log.user_id,
                    "message": log.message,
                    "module": log.module,
                    "log_type": log.log_type,
                    "created_at": log.created_at,
                    "updated_at": log.updated_at
                })
        
        return Response.success_method(InfoMessage.getting_logs, logs_data)
    
    except Exception as e:
        logger.error(str(e))
        return Response.error(status.HTTP_500_INTERNAL_SERVER_ERROR, ErrorMessage.server_error, str(e))
