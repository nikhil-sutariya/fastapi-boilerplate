"""
RLS (Row Level Security) Middleware

This middleware automatically sets the current user context for database sessions,
enabling Row Level Security policies to work correctly.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.db.database import current_user_id
from app.core.security import decode_token
from app.core.logging import setup_logger
from typing import Callable
import uuid

logger = setup_logger()

class RLSMiddleware(BaseHTTPMiddleware):
    """
    Middleware to set the current user ID in context for RLS policies.
    
    This middleware:
    1. Extracts the user ID from the JWT token in cookies
    2. Sets it in a context variable for use by database sessions
    3. Automatically applies RLS policies based on the authenticated user
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Try to get user ID from access token
        user_id = None
        token = None
        
        try:
            # Get access token from cookies
            access_token = (
                request.cookies.get("access_token")
                or request.headers.get("Authorization", "").replace("Bearer ", "")
            )
            
            if access_token:
                # Decode token to get user ID
                payload = decode_token(access_token)
                if payload and "id" in payload:
                    user_id = uuid.UUID(payload["id"])
                    # Set the user ID in context
                    if user_id:
                        token = current_user_id.set(user_id)
                        logger.debug(f"RLS middleware: User {user_id} authenticated")
            else:
                # No token, clear the context
                if token is not None:
                    current_user_id.reset(token)
                logger.debug("RLS middleware: No authentication token")
                
            response = await call_next(request)

        except Exception as e:
            # If token is invalid, just log and continue without setting user
            logger.warning(f"RLS middleware: Failed to extract user ID: {e}")
            response = await call_next(request)
        
        # Clear the context after the request
        finally:
            if token is not None:
                current_user_id.reset(token)

        # Process the request
        return response
