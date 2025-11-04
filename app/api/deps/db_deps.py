"""
Database Dependencies

This module provides FastAPI dependencies for database sessions with RLS support.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator, Optional
from app.db.database import get_db, get_admin_db, current_user_id, set_rls_user
from app.schemas.user import CurrentUser
from app.api.deps.auth_deps import get_current_user
from app.core.logging import setup_logger
import uuid

logger = setup_logger()

async def get_db_with_rls(
    current_user: Optional[CurrentUser] = Depends(get_current_user)
) -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session with RLS policies applied for the current user.
    
    This dependency:
    1. Gets the authenticated user from the request
    2. Creates a database session
    3. Sets the user context for RLS policies
    4. Yields the session for use in the route
    
    Args:
        current_user: The authenticated user (from JWT token)
    
    Yields:
        Database session with RLS applied
    """
    user_id = current_user.id if current_user else None
    
    async for session in get_db(user_id):
        yield session

async def get_db_without_auth() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session without authentication requirement.
    
    Use this for public endpoints like login, register, etc.
    No RLS policies will be applied.
    
    Yields:
        Database session without RLS
    """
    async for session in get_db(None):
        yield session

async def get_admin_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get admin database session that bypasses RLS policies.
    
    ⚠️ WARNING: This session has unrestricted access to all data.
    Only use for:
    - Admin-only operations
    - System-level tasks
    - Data migrations
    - Bulk operations
    
    Yields:
        Admin database session (bypasses RLS)
    """
    async for session in get_admin_db():
        yield session

async def get_db_with_custom_user(user_id: uuid.UUID) -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session with RLS policies for a specific user.
    
    Use this when you need to perform operations on behalf of a different user.
    
    Args:
        user_id: The user ID to use for RLS policies
    
    Yields:
        Database session with RLS applied for the specified user
    """
    async for session in get_db(user_id):
        yield session

