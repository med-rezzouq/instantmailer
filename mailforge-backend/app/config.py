from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "MailForge"
    APP_ENV: str = "development"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str
    SYNC_DATABASE_URL: str = ""

    MICROSOFT_CLIENT_ID: str = ""
    MICROSOFT_CLIENT_SECRET: str = ""
    MICROSOFT_TENANT_ID: str = ""
    MICROSOFT_REDIRECT_URI: str = "http://localhost:8000/oauth/microsoft/callback"

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/oauth/google/callback"

    REDIS_URL: str = "redis://redis:6379/0"
    MAX_EMAILS_PER_BATCH: int = 500
    SEND_CONCURRENCY_LIMIT: int = 50
    FRONTEND_URL: str = "http://localhost:3000"
    REPLY_CATCH_ALL_DOMAIN: str = "replies.yourdomain.com"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    TRACKING_BASE_URL: str = "http://localhost:8000"

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_to: str | None = None
    smtp_ssl: bool = False
    smtp_starttls: bool = False
    smtp_timeout: int = 15

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
