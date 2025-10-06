from fastapi import APIRouter, status, Depends, BackgroundTasks, Path, File, UploadFile, \
    WebSocket, WebSocketDisconnect, Response as FastAPIResponse, Request 
from fastapi.websockets import WebSocketState
from typing import Dict, Union
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from app.core.response import Response
from app.messages.user import ErrorMessage, InfoMessage
from app.schemas.user import (
    RegisterSchema, LoginSchema, RequestEmailLinkForgotPasswordSchema,
    ResetForgotPasswordSchema, ChangePasswordSchema, UpdateProfileSchema,
    CurrentUser
)
from app.models.user import User as UserModel
from fastapi.security import OAuth2PasswordRequestForm
from app.repositories.user_repository import get_notifications_by_user, update_notification_status
from app.api.deps.auth_deps import get_current_user, get_current_user_from_token
from app.db.database import get_db
from app.core.config import get_settings
from app.core import constants
from pathlib import Path as PathlibPath
import asyncio
from app.core.socket_manager import UserNotificationManager
from app.core.logging import setup_logger
from app.utils import send_email
from app.services.user_service import UserService
from app.core.exceptions import UserAlreadyExistsException
from app.core.security import create_access_token

settings = get_settings()
logger = setup_logger()
user_notification_manager = UserNotificationManager()
user_service = UserService()

UPLOAD_PROFILE_DIR: PathlibPath = PathlibPath("uploads/profile_pictures")
UPLOAD_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS: set[str] = {"image/jpg", "image/jpeg", "image/png"}

auth_router = APIRouter()

@auth_router.post("/register")
async def register(payload: RegisterSchema, db: AsyncSession = Depends(get_db)) -> FastAPIResponse:
    try:
        result = await user_service.register_user(db, payload)        
        return Response.created(InfoMessage.user_created, result)
    except UserAlreadyExistsException:
        return Response.error(status.HTTP_400_BAD_REQUEST, ErrorMessage.user_already_exists, None)
    except Exception as e:
        logger.error(str(e))
        return Response.error(status.HTTP_500_INTERNAL_SERVER_ERROR, ErrorMessage.server_error, str(e))

@auth_router.post("/login")
async def login_user(response: FastAPIResponse, payload: LoginSchema, db: AsyncSession = Depends(get_db)) -> FastAPIResponse:
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

@auth_router.post("/logout")
async def logout(response: FastAPIResponse) -> FastAPIResponse:
    try:
        response = Response.success_method(InfoMessage.logout_success, None)
        response.delete_cookie("access_token", path="/")
        response.delete_cookie("refresh_token", path="/")
        return response
    except Exception as e:
        logger.error(str(e))
        return Response.error(status.HTTP_500_INTERNAL_SERVER_ERROR, ErrorMessage.server_error, str(e))

@auth_router.post("/refresh-token")
async def refresh_token(request: Request, db: AsyncSession = Depends(get_db)) -> FastAPIResponse:
    try:
        refresh_token = request.cookies.get("refresh_token")
        result, error = await user_service.refresh_token(db, refresh_token)
        if error:
            return Response.error(status.HTTP_401_UNAUTHORIZED, error, None)
        
        response = Response.created(InfoMessage.access_token_refreshed, result)
               
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

@auth_router.post('/swagger-login', include_in_schema=False, response_model=None)
async def swagger_login(response: FastAPIResponse, form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    try:
        login_payload = LoginSchema(email=form_data.username, password=form_data.password)
        result, error = await user_service.login_user(db, login_payload)
        if error:
            return Response.error(status.HTTP_400_BAD_REQUEST, error, None)
        
        response.set_cookie(
            key="access_token", 
            value=result['access_token'], 
            httponly=True, 
            secure=True if settings.environment == constants.Environment.production else False,
            samesite="Lax"
        )

        response.set_cookie(
            key="refresh_token",
            value=result['refresh_token'],
            httponly=True,
            secure=True if settings.environment == constants.Environment.production else False,
            samesite="Lax",
            path="/auth/refresh"
        )

        return {"access_token": result['access_token']}
    except Exception as e:
        logger.error(str(e))
        return Response.error(status.HTTP_500_INTERNAL_SERVER_ERROR, ErrorMessage.server_error, str(e))

@auth_router.post('/forget-password', status_code=status.HTTP_200_OK)
async def forget_password(payload: RequestEmailLinkForgotPasswordSchema, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)) -> FastAPIResponse:
    try:
        context, email, template, token = await user_service.send_forgot_password_email(db, payload.email)
        if not context:
            return Response.error(status.HTTP_400_BAD_REQUEST, ErrorMessage.user_email_not_exists, None)
        
        background_tasks.add_task(send_email.send, "Reset password", email, template, context)
        return Response.success_method(InfoMessage.forgot_password_mail_sent, context)
    except Exception as e:
        logger.error(str(e))
        return Response.error(status.HTTP_500_INTERNAL_SERVER_ERROR, ErrorMessage.server_error, str(e))

@auth_router.post('/reset-password', status_code=status.HTTP_200_OK)
async def reset_password(payload: ResetForgotPasswordSchema, db: AsyncSession = Depends(get_db)) -> FastAPIResponse:
    try:
        result, error = await user_service.reset_forgotten_password(
            db,
            payload.secret_token,
            payload.new_password,
            payload.confirm_password
        )
        if error:
            return Response.error(status.HTTP_400_BAD_REQUEST, error, None)
        return Response.success_method(InfoMessage.password_updated, None)
    except Exception as e:
        logger.error(str(e))
        return Response.error(status.HTTP_500_INTERNAL_SERVER_ERROR, ErrorMessage.server_error, str(e))

@auth_router.patch('/change-password')
async def change_password(payload: ChangePasswordSchema, current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> FastAPIResponse:
    try:
        # Get the full user object from database
        from app.repositories.user_repository import get_user_by_id
        user = await get_user_by_id(db, current_user.id)
        if not user:
            return Response.error(status.HTTP_404_NOT_FOUND, ErrorMessage.user_email_not_exists, None)
            
        result, error = await user_service.change_password(
            db,
            user,
            payload.current_password,
            payload.new_password,
            payload.confirm_password
        )
        if error:
            return Response.error(status.HTTP_400_BAD_REQUEST, error, None)
        return Response.success_method(InfoMessage.password_updated, None)
    except Exception as e:
        logger.error(str(e))
        return Response.error(status.HTTP_500_INTERNAL_SERVER_ERROR, ErrorMessage.server_error, str(e))

@auth_router.get("/get-profile")
async def get_profile(current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> FastAPIResponse:
    try:
        user_data, error = await user_service.get_profile(db, current_user.id)
        if error:
            return Response.error(status.HTTP_400_BAD_REQUEST, error, None)
        return Response.success_method(InfoMessage.user_account_fetched, user_data)
    except Exception as e:
        logger.error(str(e))
        return Response.error(status.HTTP_500_INTERNAL_SERVER_ERROR, ErrorMessage.server_error, str(e))

@auth_router.patch("/update-profile/{user_id}")
async def update_profile(payload: UpdateProfileSchema, user_id: uuid.UUID = Path(description="Id of the user"), current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> FastAPIResponse:
    try:
        user_data, error = await user_service.update_profile(db, user_id, payload.model_dump(exclude_unset=True))
        if error:
            return Response.error(status.HTTP_400_BAD_REQUEST, error, None)
        return Response.success_method(InfoMessage.profile_updated, user_data)
    except Exception as e:
        logger.error(str(e))
        return Response.error(status.HTTP_500_INTERNAL_SERVER_ERROR, ErrorMessage.server_error, str(e))

@auth_router.patch("/upload-profile-picture/{user_id}")
async def update_profile_picture(profile_picture: UploadFile = File(), user_id: uuid.UUID = Path(description="Id of the user"), current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> FastAPIResponse:
    try:
        result, error = await user_service.update_profile_picture(db, user_id, profile_picture)
        if error:
            return Response.error(status.HTTP_400_BAD_REQUEST, error, None)
        return Response.success_method(InfoMessage.profile_updated, {"profile_picture": result})
    except Exception as e:
        logger.error(str(e))
        return Response.error(status.HTTP_500_INTERNAL_SERVER_ERROR, ErrorMessage.server_error, str(e))

@auth_router.get("/get-notifications")
async def get_notifications(current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> FastAPIResponse:
    try:
        notifications = await get_notifications_by_user(db, current_user.id)
        # Convert SQLAlchemy objects to dictionaries for JSON serialization
        notifications_data = []
        if notifications:
            for notification in notifications:
                notifications_data.append({
                    "id": notification.id,
                    "user_id": notification.user_id,
                    "organization_id": notification.organization_id,
                    "type": notification.type,
                    "message": notification.message,
                    "is_seen": notification.is_seen,
                    "created_at": notification.created_at,
                    "updated_at": notification.updated_at
                })
        return Response.success_method(InfoMessage.available_notifications, notifications_data)
    except Exception as e:
        logger.error(str(e))
        return Response.error(status.HTTP_500_INTERNAL_SERVER_ERROR, ErrorMessage.server_error, str(e))

@auth_router.put("/notification-seen")
async def notification_seen(current_user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> FastAPIResponse:
    try:
        await update_notification_status(db, current_user.id)
        return Response.success_method(InfoMessage.notification_seen, None)
    except Exception as e:
        logger.error(str(e))
        return Response.error(status.HTTP_500_INTERNAL_SERVER_ERROR, ErrorMessage.server_error, str(e))

@auth_router.get("/ws-token")
async def get_ws_token(user: CurrentUser = Depends(get_current_user)) -> Dict[str, str]:
    token = create_access_token(str(user.id), duration=5)
    return {"ws_token": token}

@auth_router.websocket("/ws/notifications")
async def notification_websocket(websocket: WebSocket, db: AsyncSession = Depends(get_db)) -> None:
    token = websocket.query_params.get("token")
    if not token:
        logger.warning("WebSocket connection attempt without token")
        await websocket.close(code=4000)
        return

    try:
        logger.info("Attempting to authenticate websocket connection")
        current_user = await get_current_user_from_token(token, db)
        user_id = current_user.id
        logger.info(f"WebSocket authenticated for user {user_id}")
        await user_notification_manager.manage_connection(str(user_id), websocket)

        try:
            while websocket.client_state == WebSocketState.CONNECTED:
                try:
                    await asyncio.wait_for(websocket.receive_text(), timeout=10)
                except asyncio.TimeoutError:
                    pass
        except WebSocketDisconnect:
            logger.info(f"User disconnected {user_id}")
        except Exception as e:
            logger.error(f"Unexpected error for user {user_id}: {e}")
        finally:
            await user_notification_manager.manage_disconnection(str(user_id), websocket)
    except Exception as e:
        logger.error(f"Authentication error in websocket: {e}")
        await websocket.close(code=4000)
