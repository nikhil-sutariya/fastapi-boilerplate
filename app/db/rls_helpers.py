"""
Row Level Security (RLS) Helper Functions

This module provides utilities for working with PostgreSQL Row Level Security policies.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import uuid

async def enable_rls_for_table(session: AsyncSession, table_name: str) -> None:
    """
    Enable RLS for a specific table.
    Should be run with admin privileges.
    
    Args:
        session: Admin database session
        table_name: Name of the table to enable RLS on
    """
    await session.execute(text(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY"))
    await session.commit()

async def create_rls_policy(
    session: AsyncSession,
    table_name: str,
    policy_name: str,
    operation: str = "ALL",
    using_expression: str = "true",
    with_check_expression: Optional[str] = None
) -> None:
    """
    Create an RLS policy for a table.
    Should be run with admin privileges.
    
    Args:
        session: Admin database session
        table_name: Name of the table
        policy_name: Name of the policy
        operation: SQL operation (SELECT, INSERT, UPDATE, DELETE, ALL)
        using_expression: SQL expression for row visibility
        with_check_expression: SQL expression for row modification checks
    
    Example:
        # Users can only see their own data
        await create_rls_policy(
            session,
            "users",
            "users_isolation_policy",
            "SELECT",
            "id::text = current_setting('app.current_user_id', true)"
        )
    """
    policy_sql = f"""
        CREATE POLICY {policy_name}
        ON {table_name}
        FOR {operation}
        USING ({using_expression})
    """
    
    if with_check_expression:
        policy_sql += f" WITH CHECK ({with_check_expression})"
    
    await session.execute(text(policy_sql))
    await session.commit()

async def drop_rls_policy(
    session: AsyncSession,
    table_name: str,
    policy_name: str
) -> None:
    """
    Drop an RLS policy from a table.
    Should be run with admin privileges.
    
    Args:
        session: Admin database session
        table_name: Name of the table
        policy_name: Name of the policy to drop
    """
    await session.execute(text(f"DROP POLICY IF EXISTS {policy_name} ON {table_name}"))
    await session.commit()

async def disable_rls_for_table(session: AsyncSession, table_name: str) -> None:
    """
    Disable RLS for a specific table.
    Should be run with admin privileges.
    
    Args:
        session: Admin database session
        table_name: Name of the table to disable RLS on
    """
    await session.execute(text(f"ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY"))
    await session.commit()

def get_rls_user_filter(column_name: str = "user_id") -> str:
    """
    Get the SQL expression for filtering by current user.
    
    Args:
        column_name: Name of the column containing user ID
    
    Returns:
        SQL expression string
    """
    return f"{column_name}::text = current_setting('app.current_user_id', true)"

# Common RLS policy expressions
class RLSExpressions:
    """Common SQL expressions for RLS policies"""
    
    @staticmethod
    def user_owns_row(column_name: str = "user_id") -> str:
        """User can only access their own rows"""
        return f"{column_name}::text = current_setting('app.current_user_id', true)"
    
    @staticmethod
    def is_admin() -> str:
        """Only admin users can access"""
        return "current_setting('app.user_role', true) = 'admin'"
    
    @staticmethod
    def user_or_admin(column_name: str = "user_id") -> str:
        """User owns row OR user is admin"""
        return f"""
            {column_name}::text = current_setting('app.current_user_id', true)
            OR current_setting('app.user_role', true) = 'admin'
        """
    
    @staticmethod
    def public_or_owner(visibility_column: str = "is_public", owner_column: str = "user_id") -> str:
        """Row is public OR user owns it"""
        return f"""
            {visibility_column} = true
            OR {owner_column}::text = current_setting('app.current_user_id', true)
        """

