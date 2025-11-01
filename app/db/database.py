from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.core.config import get_settings
from app.core.logging import setup_logger
from typing import AsyncGenerator
import asyncio

settings = get_settings()
logger = setup_logger()

# Create async engine
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

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,                # safer, explicit commits only
    autocommit=False,
)

class Base(DeclarativeBase):
    """Base class for all database models"""
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {type(e).__name__}: {str(e)}")
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
    yield
    
    # Close database connections
    await engine.dispose()
    logger.info("Database connections closed")
