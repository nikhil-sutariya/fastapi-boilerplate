from fastapi import APIRouter, status, Depends, Depends
from app.core.response import Response
from app.messages.logging import ErrorMessage, InfoMessage
from app.models.user import CurrentUser
from app.api.deps.auth_deps import get_current_user
from app.core.config import get_settings
from app.repositories.logging import get_logs_by_user
from app.core.logging import setup_logger

settings = get_settings()
logger = setup_logger()

log_router = APIRouter()

@log_router.get("/get-logs")
async def get_logs(current_user: CurrentUser = Depends(get_current_user)):
    try:
        user_id = current_user.id
        
        logs = await get_logs_by_user(user_id)
        return Response.success_method(InfoMessage.getting_logs, logs)
    
    except Exception as e:
        logger.error(str(e))
        return Response.error(status.HTTP_500_INTERNAL_SERVER_ERROR, ErrorMessage.server_error, str(e))
