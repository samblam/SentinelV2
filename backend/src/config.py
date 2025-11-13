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

    # CoT/TAK settings
    COT_ENABLED: bool = True  # Enable CoT generation
    COT_STALE_MINUTES: int = 5  # CoT stale time
    TAK_SERVER_ENABLED: bool = False  # Enable TAK server transmission
    TAK_SERVER_HOST: str = "localhost"
    TAK_SERVER_PORT: int = 8089

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
