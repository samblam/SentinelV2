"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field, computed_field, ConfigDict
from typing import List, Dict, Optional, Any
from datetime import datetime


class NodeRegister(BaseModel):
    """Node registration request."""
    node_id: str


class NodeResponse(BaseModel):
    """Node response."""
    id: int
    node_id: str
    status: str
    last_heartbeat: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class DetectionCreate(BaseModel):
    """Detection ingestion request."""
    node_id: str
    timestamp: datetime
    location: Dict[str, float]
    detections: List[Dict]
    detection_count: int
    inference_time_ms: Optional[float] = None
    model: Optional[str] = None


class DetectionResponse(BaseModel):
    """Detection response with full detection data.

    Note: node_id is the string node identifier (e.g., 'sentry-01').
    """
    id: int
    node_id: str  # String node identifier (e.g., "sentry-01")
    timestamp: datetime
    latitude: float
    longitude: float
    altitude_m: Optional[float] = None
    accuracy_m: Optional[float] = None
    detections: List[Dict[str, Any]]  # Actual detection objects (from detections_json)
    detection_count: int
    inference_time_ms: Optional[float] = None
    model: Optional[str] = None
    queued: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class BlackoutActivate(BaseModel):
    """Blackout activation request."""
    node_id: str
    reason: Optional[str] = None


class BlackoutDeactivate(BaseModel):
    """Blackout deactivation request."""
    node_id: str
