"""Configuration settings for Sentinel v2 Backend API."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for backend."""

    # Database settings
    DATABASE_URL: str = "postgresql+asyncpg://sentinel:sentinel@localhost:5432/sentinel"
    DATABASE_ECHO: bool = False

    # API settings
    HOST: str = "0.0.0.0"
    PORT: int = 8001

    # Queue settings
    MAX_RETRIES: int = 5
    BASE_RETRY_DELAY: int = 1  # seconds

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
