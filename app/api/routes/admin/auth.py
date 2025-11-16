from fastapi import APIRouter, status, Depends, Response as FastAPIResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.response import Response
from app.messages.user import ErrorMessage, InfoMessage
from app.schemas.user import LoginSchema
from app.api.deps.db_deps import get_admin_db
from app.core.config import get_settings
from app.core import constants
from pathlib import Path as PathlibPath
from app.core.socket_manager import UserNotificationManager
from app.core.logging import setup_logger
from app.services.admin.user_service import UserService

settings = get_settings()
logger = setup_logger()
user_service = UserService()

UPLOAD_PROFILE_DIR: PathlibPath = PathlibPath("uploads/profile_pictures")
UPLOAD_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS: set[str] = {"image/jpg", "image/jpeg", "image/png"}

router = APIRouter()

@router.post("/login")
async def login_user(response: FastAPIResponse, payload: LoginSchema, db: AsyncSession = Depends(get_admin_db)) -> FastAPIResponse:
    try:
        result, error = await user_service.login_user(db, payload)
        if error:
            return Response.error(status.HTTP_400_BAD_REQUEST, error, None)
        
        response = Response.success_method(InfoMessage.login_success, result['user_data'])
               
        response.set_cookie(
            key="access_token", 
            value=result['access_token'], 
            httponly=True, 
            secure=True if settings.environment == constants.Environment.production else False,
            samesite="Lax",
            path="/"
        )

        response.set_cookie(
            key="refresh_token",
            value=result['refresh_token'],
            httponly=True,
            secure=True if settings.environment == constants.Environment.production else False,
            samesite="Lax",
            path="/"
        )
        return response
    
    except Exception as e:
        logger.error(str(e))
        return Response.error(status.HTTP_500_INTERNAL_SERVER_ERROR, ErrorMessage.server_error, str(e))