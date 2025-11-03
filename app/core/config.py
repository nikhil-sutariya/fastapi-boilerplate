from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from dotenv import load_dotenv
import os
from typing import List

load_dotenv()

CLIENT_ORIGINS: List[str] = list(filter(None, os.getenv("CLIENT_ORIGINS", "").split(",")))

class Settings(BaseSettings):
    app_title: str
    app_version: str
    environment: str
    # Regular DB connection (with RLS)
    db_hostname: str
    db_port: str
    db_username: str
    db_password: str
    db_name: str
    # Admin DB connection (bypasses RLS)
    db_admin_username: str
    db_admin_password: str
    
    secret_key: str
    oauth_algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    client_origin: List[str] = CLIENT_ORIGINS
    frontend_host_url: str
    frontend_forget_password_url: str
    frontend_signup_url: str

    smtp_email_from: str
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str

    model_config = SettingsConfigDict(env_file=".env")
    
    @property
    def database_url(self) -> str:
        """Regular database URL with RLS-restricted user"""
        return f"postgresql+asyncpg://{self.db_username}:{self.db_password}@{self.db_hostname}:{self.db_port}/{self.db_name}"
    
    @property
    def database_admin_url(self) -> str:
        """Admin database URL with superuser privileges (bypasses RLS)"""
        return f"postgresql+asyncpg://{self.db_admin_username}:{self.db_admin_password}@{self.db_hostname}:{self.db_port}/{self.db_name}"

@lru_cache
def get_settings() -> Settings:
    return Settings()
