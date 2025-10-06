from typing import Optional, List, Dict, Any, Union, Type, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.exc import SQLAlchemyError
from app.core.logging import setup_logger
from datetime import datetime, timezone

logger = setup_logger()

T = TypeVar('T', bound=DeclarativeBase)

async def create_record(session: AsyncSession, model: Type[T], data: Dict[str, Any]) -> Optional[T]:
    """Create a new record in the database"""
    try:
        record = model(**data)
        session.add(record)
        await session.commit()
        await session.refresh(record)
        return record
    except SQLAlchemyError as e:
        logger.error(f"Error creating record: {e}")
        await session.rollback()
        return None

async def create_bulk_records(session: AsyncSession, model: Type[T], records_data: List[Dict[str, Any]]) -> Optional[List[T]]:
    """Create multiple records in the database"""
    try:
        records = [model(**data) for data in records_data]
        session.add_all(records)
        await session.commit()
        for record in records:
            await session.refresh(record)
        return records
    except SQLAlchemyError as e:
        logger.error(f"Error creating bulk records: {e}")
        await session.rollback()
        return None

async def get_record_by_id(session: AsyncSession, model: Type[T], record_id: int) -> Optional[T]:
    """Get a single record by ID"""
    try:
        result = await session.execute(select(model).where(model.id == record_id))
        return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.error(f"Error getting record by ID: {e}")
        return None

async def get_all_records(session: AsyncSession, model: Type[T]) -> Optional[List[T]]:
    """Get all records of a model"""
    try:
        result = await session.execute(select(model))
        return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"Error getting all records: {e}")
        return None

async def get_records_by_filter(session: AsyncSession, model: Type[T], **filters) -> Optional[List[T]]:
    """Get records by filter criteria"""
    try:
        query = select(model)
        for key, value in filters.items():
            if hasattr(model, key):
                query = query.where(getattr(model, key) == value)
        
        result = await session.execute(query)
        return result.scalars().all()
    except SQLAlchemyError as e:
        logger.error(f"Error getting records by filter: {e}")
        return None

async def update_record(session: AsyncSession, model: Type[T], record_id: int, data: Dict[str, Any]) -> Optional[T]:
    """Update a record by ID"""
    try:
        # Add updated_at timestamp
        data['updated_at'] = datetime.now(timezone.utc)
        
        stmt = update(model).where(model.id == record_id).values(**data)
        await session.execute(stmt)
        await session.commit()
        
        # Return the updated record
        return await get_record_by_id(session, model, record_id)
    except SQLAlchemyError as e:
        logger.error(f"Error updating record: {e}")
        await session.rollback()
        return None

async def delete_record(session: AsyncSession, model: Type[T], record_id: int) -> bool:
    """Delete a record by ID"""
    try:
        stmt = delete(model).where(model.id == record_id)
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0
    except SQLAlchemyError as e:
        logger.error(f"Error deleting record: {e}")
        await session.rollback()
        return False

async def get_record_by_field(session: AsyncSession, model: Type[T], field_name: str, field_value: Any) -> Optional[T]:
    """Get a single record by a specific field value"""
    try:
        if not hasattr(model, field_name):
            logger.error(f"Field {field_name} does not exist on model {model.__name__}")
            return None
            
        field = getattr(model, field_name)
        result = await session.execute(select(model).where(field == field_value))
        return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.error(f"Error getting record by field: {e}")
        return None
    