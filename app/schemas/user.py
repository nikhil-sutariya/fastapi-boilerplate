from pydantic import BaseModel, Field, field_validator
from pydantic.networks import EmailStr
from app.core import constants
import re

class RegisterSchema(BaseModel):
    first_name: str | None = Field(default=None)
    last_name: str | None = Field(default=None)
    email: EmailStr = Field(pattern=constants.email_regex)
    password: str = Field(min_length=8, max_length=16)

    @field_validator('email')
    def validate_email(cls, value):
        if not re.match(constants.email_regex, value):
            raise ValueError("Invalid email address")
        return value
    
    @field_validator("password")
    def validate_password(cls, value):
        if not any(c.isupper() for c in value):
            raise ValueError("Password must contain at least one uppercase character.")

        symbols = "!@#$%^&*()_-+=<>?"
        if not any(c in symbols for c in value):
            raise ValueError("Password must contain at least one symbol.")
        
        numbers = "0123456789"
        if not any(c in numbers for c in numbers):
            raise ValueError("Password must contain at least one number.")

        return value

class LoginSchema(BaseModel):
    email: EmailStr = Field(pattern=constants.email_regex)
    password: str = Field(min_length=8, max_length=16)

    @field_validator('email')
    def validate_email(cls, value):
        if not re.match(constants.email_regex, value):
            raise ValueError("Invalid email address")
        return value
    
    @field_validator("password")
    def validate_password(cls, value):
        if not any(c.isupper() for c in value):
            raise ValueError("Password must contain at least one uppercase character.")

        symbols = "!@#$%^&*()_-+=<>?"
        if not any(c in symbols for c in value):
            raise ValueError("Password must contain at least one symbol.")
        
        numbers = "0123456789"
        if not any(c in numbers for c in numbers):
            raise ValueError("Password must contain at least one number.")

        return value
    
class RequestEmailLinkForgotPasswordSchema(BaseModel):
    email: EmailStr = Field(pattern=constants.email_regex)

    @field_validator('email')
    def validate_email(cls, value):
        if not re.match(constants.email_regex, value):
            raise ValueError("Invalid email address")
        return value

class ResetForgotPasswordSchema(BaseModel):
    secret_token: str = Field()
    new_password: str = Field()
    confirm_password: str = Field()

class ChangePasswordSchema(BaseModel):
    current_password: str = Field()
    new_password: str = Field()
    confirm_password: str = Field()

class VerifyPasswordSchema(BaseModel):
    password: str = Field()

class UpdateProfileSchema(BaseModel):
    first_name: str | None = Field(default=None)
    last_name: str | None = Field(default=None)
    phone: str | None = Field(default=None)
    address: str | None = Field(default=None)

class CreateNotificationSchema(BaseModel):
    user_id: str
    type: str
    message: str
    is_seen: bool = False
