"""
Application configuration using pydantic-settings.
Loads values from .env file and environment variables.
"""

from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- App ---
    APP_NAME: str = "Restoran Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- Database (Neon PostgreSQL) ---
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@host/db"

    # --- Cloudinary ---
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # --- SMS (Eskiz.uz) ---
    SMS_API_URL: str = "https://notify.eskiz.uz/api"
    SMS_API_EMAIL: str = ""
    SMS_API_PASSWORD: str = ""

    # --- Payment (Click) ---
    CLICK_MERCHANT_ID: str = ""
    CLICK_SERVICE_ID: str = ""
    CLICK_SECRET_KEY: str = ""

    # --- Payment (Payme) ---
    PAYME_MERCHANT_ID: str = ""
    PAYME_SECRET_KEY: str = ""

    # --- CORS ---
    CORS_ORIGINS: List[str] = ["*"]
    
    # --- Telegram Bot ---
    BOT_TOKEN: str = ""

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug_mode(cls, value):
        if isinstance(value, str) and value.lower() in {"release", "prod", "production"}:
            return False
        return value

    @property
    def database_url_sync(self) -> str:
        """Return sync database URL for Alembic migrations."""
        return self.DATABASE_URL.replace(
            "postgresql+asyncpg://", "postgresql+psycopg2://"
        )


settings = Settings()
