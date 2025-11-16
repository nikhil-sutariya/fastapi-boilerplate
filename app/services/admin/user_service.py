from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import LoginSchema
from app.repositories.user_repository import (
    get_user_by_email, update_user
)
from app.repositories.logging import create_log
from app.core.constants import Role, Modules, AppLogType
from app.core.security import verify_password
from app.core.security import create_access_token, create_refresh_token
from app.core.logging import setup_logger
from app.messages.user import ErrorMessage

logger = setup_logger()

class UserService:
    async def login_user(self, session: AsyncSession, payload: LoginSchema) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        try:
            user = await get_user_by_email(session, payload.email)

            if not user:
                return None, ErrorMessage.user_email_not_exists
            
            if payload.email.lower() != user.email:
                return None, ErrorMessage.wrong_email

            if not verify_password(payload.password, user.password):
                return None, ErrorMessage.wrong_password

            if user.role != Role.admin.value:
                return None, ErrorMessage.user_not_authorized_to_login

            # Update last login time
            await update_user(session, user.id, {
                "last_loggedin_at": datetime.now(timezone.utc)
            })

            user_data = {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role
            }

            access_token = create_access_token(str(user.id))
            refresh_token = create_refresh_token(str(user.id))

            await create_log(session, {
                "user_id": user.id,
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

