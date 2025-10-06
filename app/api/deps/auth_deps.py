from fastapi import HTTPException, status, Request, Depends
from jwt.exceptions import InvalidTokenError
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User as UserModel
from app.schemas.user import CurrentUser
from app.db.database import get_db
from app.repositories.user_repository import get_user_by_id
from app.core.security import decode_token
from app.core.config import get_settings
import uuid

settings = get_settings()

async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> CurrentUser:
    try:
        access_token = request.cookies.get("access_token")

        payload = decode_token(access_token)
        user_id = uuid.UUID(payload.get("id"))
        
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token. Please log in again.")
        
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
            
        return CurrentUser(
            id=user.id, 
            role=user.role, 
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name
        )

    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token. Please log in again.")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format. Please log in again.")

async def get_current_user_from_token(token: str, db: AsyncSession = Depends(get_db)) -> CurrentUser:
    """Get current user from token string (for websocket connections)"""
    try:
        payload = decode_token(token)
        user_id = uuid.UUID(payload.get("id"))
        
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token. Please log in again.")
        
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
            
        return CurrentUser(
            id=user.id, 
            role=user.role, 
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name
        )

    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token. Please log in again.")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format. Please log in again.")

async def verify_refresh_token(token: str) -> Dict[str, Any]:
    try:
        return decode_token(token)
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
