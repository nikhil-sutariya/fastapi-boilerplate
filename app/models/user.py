from pydantic import Field
from datetime import datetime
from app.core.custom_model_fields import PyObjectId, MongoModel

class CurrentUser(MongoModel):
    """User model for authentication context - doesn't include sensitive fields"""
    id: str
    email: str
    role: str
    first_name: str | None = None
    last_name: str | None = None

class User(MongoModel):
    """Complete user model for database operations"""
    email: str
    first_name: str | None = None
    last_name: str | None = None
    password: str
    role: str
    profile_picture: str | None = None
    last_loggedin_at: datetime | None = None

class UserProfileResponse(MongoModel):
    """User profile model for API responses - excludes sensitive fields"""
    email: str
    first_name: str | None = None
    last_name: str | None = None
    profile_picture: str | None = None
    last_loggedin_at: datetime | None = None

class Notification(MongoModel):
    """Notification model"""
    user_id: str
    organization_id: str
    type: str
    message: str
    is_seen: bool
