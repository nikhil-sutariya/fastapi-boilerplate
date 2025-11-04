import asyncio
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
    echo=False,                     # Set to True for SQL query logging
    future=True,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,                   # reasonable default for t3.micro / dev
    max_overflow=20,                # allow burst load
    connect_args={"timeout": 10},   # fail fast if DB is unavailable
    # For production (2 vCPUs+), scale pool_size to ~20–30 and max_overflow to ~50.
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
    autoflush=False,                # safer, explicit commits only
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
            user_id = user_id or current_user_id.get(None)
            if user_id:
                await set_rls_user(session, user_id)

            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()
        finally:
            try:
                await session.execute(text("RESET app.current_user_id"))
            except Exception:
                pass
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
    """FastAPI lifespan context manager for database connection"""
    retries = 3
    for attempt in range(1, retries + 1):
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1").execution_options(timeout=10))
            logger.info("Database connection established successfully")
            break
        except Exception as e:
            logger.warning(f"DB connection attempt {attempt}/{retries} failed: {e}")
            if attempt == retries:
                raise
            await asyncio.sleep(3 * attempt)
    
    
    # Test admin database connection
    retries = 3
    for attempt in range(1, retries + 1):
        try:
            async with AsyncAdminSessionLocal() as session:
                await session.execute(text("SELECT 1").execution_options(timeout=10))
            logger.info("Admin database connection established successfully")
            break
        except Exception as e:
            logger.warning(f"DB connection attempt {attempt}/{retries} failed: {e}")
            if attempt == retries:
                raise
            await asyncio.sleep(3 * attempt)
    
    yield
    
    # Close all database connections
    await engine.dispose()
    await admin_engine.dispose()
    logger.info("Database connections closed")
