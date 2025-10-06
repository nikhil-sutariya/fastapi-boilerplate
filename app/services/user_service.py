from datetime import datetime, timezone
import time
import uuid
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from fastapi import UploadFile
from app.models.user import User, UserProfileResponse
from app.schemas.user import RegisterSchema, LoginSchema, CreateNotificationSchema
from app.repositories import base_repository
from app.core.constants import Role, Modules, AppLogType, NotificationType
from app.db.collections import User as UserCollection
from app.core.security import get_password_hash, verify_password
from app.repositories.user_repository import get_user_by_email
from app.core.security import create_access_token, create_refresh_token
from app.api.deps.auth_deps import verify_refresh_token
from app.core.exceptions import UserAlreadyExistsException
from app.utils import send_email
from app.repositories.logging import create_log
from app.core.config import get_settings
from app.core.logging import setup_logger
from app.messages.user import ErrorMessage, NotificationMessage
from app.core.socket_manager import  UserNotificationManager
import jwt

user_notification_manager = UserNotificationManager()

settings = get_settings()
logger = setup_logger()

UPLOAD_PROFILE_DIR: Path = Path("uploads/profile_pictures")
UPLOAD_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS: set[str] = {"image/jpg", "image/jpeg", "image/png"}

class UserService:
    async def register_user(self, payload: RegisterSchema) -> Dict[str, Any]:
        try:
            payload = payload.model_dump()
            payload['email'] = payload['email'].lower()

            existing_user = await get_user_by_email(payload['email'])
            if existing_user:
                raise UserAlreadyExistsException

            payload['password'] = get_password_hash(payload['password'])
            payload.setdefault("role", Role.user)

            user = User(**payload)
            user_id = await base_repository.store_document(UserCollection(), user.to_mongo())

            if not user_id:
                raise Exception(ErrorMessage.user_not_added)

            # Get the complete user data from database and return it
            user_data = await base_repository.get_document_data(UserCollection(), user_id)
            if user_data:
                user = User.from_mongo(user_data)
                return user.to_api_response()
            return None
        except UserAlreadyExistsException:
            raise
        except Exception as e:
            logger.error(f"Error registering user: {str(e)}")
            raise Exception(ErrorMessage.user_not_added)

    async def login_user(self, payload: LoginSchema) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        try:
            user_data = await get_user_by_email(payload.email)

            if not user_data:
                return None, ErrorMessage.user_email_not_exists
            
            user = User.from_mongo(user_data)

            if payload.email != user.email:
                return None, ErrorMessage.wrong_email

            if not verify_password(payload.password, user.password):
                return None, ErrorMessage.wrong_password

            await base_repository.edit_document(UserCollection(), user.id, {
                "last_loggedin_at": datetime.now(timezone.utc)
            })

            user_data = {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            }

            access_token = create_access_token(user_data["id"])
            refresh_token = create_refresh_token(user_data["id"])

            await create_log({
                "user_id": str(user.id),
                "message": f"{user.email} successfully logged in",
                "module": Modules.auth.value,
                "log_type": AppLogType.login.value
            })

            return {
                "user_data": user_data,
                "access_token": access_token,
                "refresh_token": refresh_token
            }, None
        except Exception as e:
            logger.error(f"Error in login: {str(e)}")
            return None, ErrorMessage.server_error

    async def refresh_token(self, token: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        try:
            payload = await verify_refresh_token(token)

            if not payload:
                return None, ErrorMessage.empty_refresh_token

            user_id = payload.get("id")
            user_data = await base_repository.get_document_data(UserCollection(), user_id)

            if not user_data:
                return None, ErrorMessage.user_email_not_exists
            
            user = User.from_mongo(user_data)

            user_data = {
                "id": str(user.id),
                "email": user.email,
                "role": user.role,
                "first_name": user.first_name,
                "last_name": user.last_name
            }

            access_token = create_access_token(user_data["id"])
            refresh_token = create_refresh_token(user_data["id"])

            return {
                "user_data": user_data,
                "access_token": access_token,
                "refresh_token": refresh_token
            }, None
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return None, ErrorMessage.server_error

    async def send_forgot_password_email(self, email: str) -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[str], Optional[str]]:
        try:
            user_data = await get_user_by_email(email)
            if not user_data:
                return None, ErrorMessage.user_email_not_exists
            
            user = User.from_mongo(user_data)

            token_payload = {
                "user_id": user.id,
                "expires": time.time() + 900
            }

            secret_token = create_access_token(token_payload)
            forget_url_link = f"{settings.frontend_host_url}/{settings.frontend_forget_password_url}?token={secret_token}"

            context = {
                "name": f"{user.first_name} {user.last_name}",
                "link_expiry_min": 15,
                "reset_link": forget_url_link
            }

            await create_log({
                "user_id": user.id,
                "message": f"{user.email} requested forgot password link",
                "module": Modules.auth.value,
                "log_type": AppLogType.login.value
            })

            return context, user.email, "forgot_password.html", secret_token
        except Exception as e:
            logger.error(f"Error sending forgot password email: {str(e)}")
            return None, ErrorMessage.server_error

    async def reset_forgotten_password(self, token: str, new_password: str, confirm_password: str) -> Tuple[Optional[bool], Optional[str]]:
        try:
            decoded_payload = jwt.decode(token, settings.secret_key, algorithms=[settings.oauth_algorithm])
        except:
            return None, ErrorMessage.forgot_password_link_expire

        if time.time() > decoded_payload['expires']:
            return None, ErrorMessage.forgot_password_link_expire

        user_id = decoded_payload['user_id']
        if new_password != confirm_password:
            return None, ErrorMessage.same_not_password

        try:
            user_data = await base_repository.get_document_data(UserCollection(), user_id)
            user = User.from_mongo(user_data)

            if verify_password(new_password, user.password):
                return None, ErrorMessage.same_password

            password_hash = get_password_hash(new_password)
            updated = await base_repository.edit_document(UserCollection(), user_id, {"password": password_hash})

            if updated:
                await create_log({
                    "user_id": user.id,
                    "message": f"{user.email} reset the forgotten password",
                    "module": Modules.auth.value,
                    "log_type": AppLogType.update.value
                })

                notification_data = CreateNotificationSchema(
                    user_id=user_id,
                    type=NotificationType.success,
                    message=NotificationMessage.reset_password
                ).model_dump()
                await user_notification_manager.send_notification(user_id, notification_data)

                return True, None
            return None, ErrorMessage.password_not_updated
        except Exception as e:
            logger.error(f"Error resetting password: {str(e)}")
            return None, ErrorMessage.password_not_updated

    async def change_password(self, user: User, current_password: str, new_password: str, confirm_password: str) -> Tuple[Optional[bool], Optional[str]]:
        try:
            if not verify_password(current_password, user.password):
                return None, ErrorMessage.wrong_current_password
            if new_password != confirm_password:
                return None, ErrorMessage.same_not_password
            if verify_password(new_password, user.password):
                return None, ErrorMessage.same_password

            updated = await base_repository.edit_document(UserCollection(), user.id, {
                "password": get_password_hash(new_password)
            })

            if updated:
                await create_log({
                    "user_id": user.id,
                    "message": f"{user.email} updated their password",
                    "module": Modules.auth.value,
                    "log_type": AppLogType.update.value
                })

                notification_data = CreateNotificationSchema(
                    user_id=user.id,
                    type=NotificationType.success,
                    message=NotificationMessage.change_password
                ).model_dump()
                await user_notification_manager.send_notification(user.id, notification_data)

                return True, None
            return None, ErrorMessage.password_not_updated
        except Exception as e:
            logger.error(f"Error changing password: {str(e)}")
            return None, ErrorMessage.password_not_updated

    async def get_profile(self, user_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        try:
            user_data = await base_repository.get_document_data(UserCollection(), user_id)
            if not user_data:
                return None, ErrorMessage.profile_data_not_found
            user = UserProfileResponse.from_mongo(user_data)
            return user.to_api_response(), None
        except Exception as e:
            logger.error(f"Error getting profile: {str(e)}")
            return None, ErrorMessage.server_error

    async def update_profile(self, user_id: str, payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        try:
            user_data = await base_repository.get_document_data(UserCollection(), user_id)
            user = User.from_mongo(user_data)
            
            # Update user with new payload
            updated_user = user.model_copy(update=payload)
            
            updated = await base_repository.edit_document(UserCollection(), user_id, updated_user.to_mongo())
            if updated:
                updated_user_data = await base_repository.get_document_data(UserCollection(), user_id)

                await create_log({
                    "user_id": user_id,
                    "message": f"{updated_user_data['email']} updated their profile",
                    "module": Modules.auth.value,
                    "log_type": AppLogType.update.value
                })

                notification_data = CreateNotificationSchema(
                    user_id=user_id,
                    type=NotificationType.success,
                    message=NotificationMessage.profile_updated
                ).model_dump()
                await user_notification_manager.send_notification(user_id, notification_data)

                updated_user = User.from_mongo(updated_user_data)
                return updated_user.to_api_response(), None
            return None, ErrorMessage.profile_not_updated
        except Exception as e:
            logger.error(f"Error updating profile: {str(e)}")
            return None, ErrorMessage.profile_not_updated

    async def update_profile_picture(self, user_id: str, file: UploadFile) -> Tuple[Optional[str], Optional[str]]:
        if file.content_type not in ALLOWED_EXTENSIONS:
            return None, ErrorMessage.invalid_image_type

        extension = file.filename.split('.')[-1]
        filename = f"{uuid.uuid4().hex}.{extension}"
        file_path = UPLOAD_PROFILE_DIR / filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        profile_picture_url = f"/uploads/profile_pictures/{filename}"

        user_data = await base_repository.get_document_data(UserCollection(), user_id)
        user = User.from_mongo(user_data)
        
        # Update profile picture
        updated_user = user.model_copy(update={"profile_picture": profile_picture_url})
        updated = await base_repository.edit_document(UserCollection(), user_id, updated_user.to_mongo())

        if updated:
            await create_log({
                "user_id": user_id,
                "message": f"{user_data['email']} updated their profile picture",
                "module": Modules.auth.value,
                "log_type": AppLogType.update.value
            })

            notification_data = CreateNotificationSchema(
                user_id=user_id,
                type=NotificationType.success,
                message=NotificationMessage.profile_pic_updated
            ).model_dump()
            await user_notification_manager.send_notification(user_id, notification_data)

            return profile_picture_url, None
        return None, ErrorMessage.profile_not_updated
