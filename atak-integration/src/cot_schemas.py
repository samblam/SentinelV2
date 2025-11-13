"""Pydantic data models for CoT generation from Sentinel detections."""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import List, Optional, Dict, Any


class BoundingBox(BaseModel):
    """Bounding box coordinates for object detection.

    Attributes:
        xmin: Minimum x coordinate (left edge)
        ymin: Minimum y coordinate (top edge)
        xmax: Maximum x coordinate (right edge)
        ymax: Maximum y coordinate (bottom edge)
    """
    xmin: int
    ymin: int
    xmax: int
    ymax: int


class Detection(BaseModel):
    """Single object detection from YOLO model.

    Attributes:
        bbox: Bounding box coordinates
        class_name: Object class name (e.g., "person", "vehicle")
        confidence: Detection confidence score (0.0 to 1.0)
        class_id: Numeric class ID from YOLO model
    """
    bbox: BoundingBox
    class_name: str = Field(alias="class")
    confidence: float
    class_id: int

    model_config = {
        "populate_by_name": True
    }


class SentinelDetection(BaseModel):
    """Complete Sentinel detection for CoT generation.

    This represents a detection event from a Sentinel edge node,
    including location, timestamp, and detected objects.

    Attributes:
        node_id: Unique identifier for the edge node
        timestamp: Detection timestamp (timezone-aware)
        latitude: Latitude in decimal degrees (-90 to 90)
        longitude: Longitude in decimal degrees (-180 to 180)
        altitude_m: Altitude in meters (default: 0.0)
        accuracy_m: Positional accuracy in meters (default: 10.0)
        detections: List of detected objects
        detection_count: Number of objects detected
        inference_time_ms: ML inference time in milliseconds
        model: ML model name (default: "yolov5n")
    """
    node_id: str
    timestamp: datetime
    latitude: float
    longitude: float
    altitude_m: float = 0.0
    accuracy_m: Optional[float] = 10.0
    detections: List[Dict[str, Any]]
    detection_count: int
    inference_time_ms: float
    model: Optional[str] = "yolov5n"

    @field_validator('latitude')
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        """Validate latitude is in valid range."""
        if not -90.0 <= v <= 90.0:
            raise ValueError(f"Latitude must be between -90 and 90, got {v}")
        return v

    @field_validator('longitude')
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        """Validate longitude is in valid range."""
        if not -180.0 <= v <= 180.0:
            raise ValueError(f"Longitude must be between -180 and 180, got {v}")
        return v
