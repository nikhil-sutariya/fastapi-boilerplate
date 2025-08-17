from pydantic import BaseModel, Field
from datetime import datetime
from app.core.custom_model_fields import PyObjectId

class CurrentUser(BaseModel):
    id: str
    email: str
    role: str
    first_name: str | None = None
    last_name: str | None = None

class User(BaseModel):
    id: PyObjectId | None = Field(default=None, alias="_id")
    email: str
    first_name: str | None = None
    last_name: str | None = None
    password: str
    role: str
    profile_picture: str | None = None
    last_loggedin_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}

class UserProfileResponse(BaseModel):
    id: PyObjectId | None = Field(default=None, alias="_id")
    email: str
    first_name: str | None = None
    last_name: str | None = None
    profile_picture: str | None = None
    last_loggedin_at: datetime | None = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}

class Notification(BaseModel):
    id: PyObjectId = Field(alias="_id")
    user_id: str
    organization_id: str
    type: str
    message: str
    is_seen: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {PyObjectId: str}
