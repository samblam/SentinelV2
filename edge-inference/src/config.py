"""
Configuration settings for edge inference engine
Uses pydantic-settings for environment variable management
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for edge inference"""

    # Model settings
    MODEL_NAME: str = "yolov5n"
    CONFIDENCE_THRESHOLD: float = 0.25
    IOU_THRESHOLD: float = 0.45
    MAX_DETECTIONS: int = 100

    # Performance settings
    DEVICE: str = "cpu"  # "cuda" if GPU available

    # API settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    MAX_IMAGE_SIZE: int = 10 * 1024 * 1024  # 10MB

    # Arctic simulation settings
    MOCK_GPS: bool = True
    DEFAULT_LAT: float = 70.0  # Arctic latitude
    DEFAULT_LON: float = -100.0  # Arctic longitude

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
