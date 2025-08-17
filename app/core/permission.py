from fastapi import Depends, status
from app.models.user import User
from app.core.response import Response
from app.core.constants import Role
from functools import wraps

def has_role(*required_roles: Role):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User, **kwargs):
            if current_user.role not in required_roles:
                return Response.error(status.HTTP_403_FORBIDDEN, "Insufficient permissions", None)
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator
