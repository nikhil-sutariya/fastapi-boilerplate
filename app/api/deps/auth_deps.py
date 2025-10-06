from fastapi import HTTPException, status, Request
from jwt.exceptions import InvalidTokenError
from typing import Dict, Any, Optional
from app.models.user import User, CurrentUser
from app.db.collections import User as UserCollection
from app.repositories import base_repository
from app.core.security import decode_token
from app.core.config import get_settings

settings = get_settings()

async def get_current_user(request: Request) -> CurrentUser:
    try:
        access_token = request.cookies.get("access_token")

        payload = decode_token(access_token)
        user_id = payload.get("id")
        
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token. Please log in again.")
        
        user_data = await base_repository.get_document_data(
            UserCollection(), 
            user_id
        )
        user = User(**user_data)
        return CurrentUser(id=str(user.id), role=user.role, email=user.email)

    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token. Please log in again.")

async def get_current_user_from_token(token: str) -> CurrentUser:
    """Get current user from token string (for websocket connections)"""
    try:
        payload = decode_token(token)
        user_id = payload.get("id")
        
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token. Please log in again.")
        
        user_data = await base_repository.get_document_data(
            UserCollection(), 
            user_id
        )
        user = User(**user_data)
        return CurrentUser(id=str(user.id), role=user.role, email=user.email)

    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token. Please log in again.")

async def verify_refresh_token(token: str) -> Dict[str, Any]:
    try:
        return decode_token(token)
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
