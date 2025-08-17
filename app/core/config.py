from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from dotenv import load_dotenv
import os

load_dotenv()

CLIENT_ORIGINS = list(filter(None, os.getenv("CLIENT_ORIGINS", "").split(",")))

class Settings(BaseSettings):
    app_title: str
    app_version: str
    environment: str
    db_hostname: str
    db_port: str
    db_username: str
    db_password: str
    db_name: str
    mongo_uri: str
    secret_key: str
    oauth_algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    client_origin: list = CLIENT_ORIGINS
    frontend_host_url: str
    frontend_forget_password_url: str
    frontend_signup_url: str

    smtp_email_from: str
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str

    model_config = SettingsConfigDict(env_file=".env")

@lru_cache
def get_settings() -> Settings:
    return Settings()
