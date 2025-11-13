"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
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

    class Config:
        from_attributes = True


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
    """Detection response."""
    id: int
    node_id: int
    timestamp: datetime
    latitude: float
    longitude: float
    detection_count: int
    queued: Optional[bool] = None

    class Config:
        from_attributes = True


class BlackoutActivate(BaseModel):
    """Blackout activation request."""
    node_id: str
    reason: Optional[str] = None


class BlackoutDeactivate(BaseModel):
    """Blackout deactivation request."""
    node_id: str
