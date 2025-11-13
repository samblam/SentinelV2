"""Configuration management for ATAK/CoT integration."""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    # TAK Server Configuration
    TAK_SERVER_ENABLED: bool = os.getenv("TAK_SERVER_ENABLED", "false").lower() == "true"
    TAK_SERVER_HOST: str = os.getenv("TAK_SERVER_HOST", "localhost")
    TAK_SERVER_PORT: int = int(os.getenv("TAK_SERVER_PORT", "8089"))

    # Mock TAK Server Configuration
    MOCK_TAK_SERVER_HOST: str = os.getenv("MOCK_TAK_SERVER_HOST", "127.0.0.1")
    MOCK_TAK_SERVER_PORT: int = int(os.getenv("MOCK_TAK_SERVER_PORT", "8089"))

    # CoT Configuration
    COT_STALE_MINUTES: int = int(os.getenv("COT_STALE_MINUTES", "5"))
    COT_TYPE: str = os.getenv("COT_TYPE", "a-f-G-E-S")


settings = Settings()
