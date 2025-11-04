from fastapi import HTTPException, status, Request, Depends
from jwt.exceptions import InvalidTokenError
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User as UserModel
from app.schemas.user import CurrentUser
from app.db.database import get_admin_db
from app.repositories.user_repository import get_user_by_id
from app.core.security import decode_token, oauth2_scheme
from app.core.config import get_settings
import uuid

settings = get_settings()

async def get_current_user(
    request: Request, 
    db: AsyncSession = Depends(get_admin_db),  # Use admin DB to bypass RLS for auth
    token: Optional[str] = Depends(oauth2_scheme)  # For Swagger UI
) -> CurrentUser:
    """
    Get current user from either:
    1. Bearer token (for Swagger UI testing)
    2. HTTP-only cookie (for production use)
    
    This dual approach allows secure cookie-based auth in production
    while still enabling Swagger UI testing with the Authorize button.
    """
    try:
        # Try Bearer token first (from Swagger UI Authorization header)
        access_token = token
        
        # Fall back to cookie-based auth if no Bearer token
        if not access_token:
            access_token = request.cookies.get("access_token")
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Not authenticated. Please log in.",
                headers={"WWW-Authenticate": "Bearer"}
            )

        payload = decode_token(access_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid or expired token. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"}
            )
            
        user_id = uuid.UUID(payload.get("id"))
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid token. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="User not found.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return CurrentUser(
            id=user.id, 
            role=user.role, 
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name
        )

    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid token format. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )

async def get_current_user_from_token(token: str, db: AsyncSession) -> CurrentUser:
    """
    Get current user from token string (for websocket connections).
    Note: This function doesn't use Depends() since it's called manually.
    The caller should provide an admin DB session to bypass RLS.
    """
    try:
        payload = decode_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid or expired token. Please log in again."
            )
            
        user_id = uuid.UUID(payload.get("id"))
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid token. Please log in again."
            )
        
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="User not found."
            )
            
        return CurrentUser(
            id=user.id, 
            role=user.role, 
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name
        )

    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid token. Please log in again."
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid token format. Please log in again."
        )

async def verify_refresh_token(token: str) -> Dict[str, Any]:
    try:
        return decode_token(token)
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
