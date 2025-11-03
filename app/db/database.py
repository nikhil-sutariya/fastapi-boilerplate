from uuid import UUID
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.core.config import get_settings
from app.core.logging import setup_logger
from typing import AsyncGenerator, Optional
from contextvars import ContextVar

settings = get_settings()
logger = setup_logger()

# Context variable to store current user ID for RLS
current_user_id: ContextVar[Optional[UUID]] = ContextVar[UUID | None]("current_user_id", default=None)

# Create regular async engine (with RLS policies)
engine = create_async_engine(
    settings.database_url,
    echo=False,  # Set to True for SQL query logging
    future=True,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create admin async engine (bypasses RLS policies)
admin_engine = create_async_engine(
    settings.database_admin_url,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create async session factory for regular operations (with RLS)
AsyncSessionLocal = async_sessionmaker[AsyncSession](
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False,
)

# Create async session factory for admin operations (bypasses RLS)
AsyncAdminSessionLocal = async_sessionmaker[AsyncSession](
    admin_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False,
)

class Base(DeclarativeBase):
    """Base class for all database models"""
    pass

async def set_rls_user(session: AsyncSession, user_id: Optional[UUID] = None) -> None:
    """
    Set the current user ID for RLS policies.
    This should be called at the beginning of each request with the authenticated user's ID.
    """
    if user_id:
        # Set the user_id in PostgreSQL session variable for RLS policies
        await session.execute(
            text(f"SET LOCAL app.current_user_id = '{str(user_id)}'")
        )
        logger.debug(f"RLS policy applied for user: {user_id}")
    else:
        # Clear the user_id (for unauthenticated requests)
        await session.execute(
            text("SET LOCAL app.current_user_id = ''")
        )

async def get_db(user_id: Optional[UUID] = None) -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session with RLS policies applied.
    
    Args:
        user_id: Optional user ID to set for RLS policies
    """
    async with AsyncSessionLocal() as session:
        try:
            # Set RLS context if user_id is provided
            if user_id:
                await set_rls_user(session, user_id)
            
            yield session
            await session.commit()
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

async def get_admin_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get admin database session (bypasses RLS policies).
    Use this for admin operations, migrations, and system-level tasks.
    """
    async with AsyncAdminSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            logger.error(f"Admin database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

async def lifespan(app):
    """FastAPI lifespan context manager for database connections"""
    # Test regular database connection
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        logger.info("✓ Regular database connection established successfully")
    except Exception as e:
        logger.error(f"✗ Failed to connect to regular database: {e}")
        raise
    
    # Test admin database connection
    try:
        async with AsyncAdminSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        logger.info("✓ Admin database connection established successfully")
    except Exception as e:
        logger.error(f"✗ Failed to connect to admin database: {e}")
        raise
    
    yield
    
    # Close all database connections
    await engine.dispose()
    await admin_engine.dispose()
    logger.info("Database connections closed")
