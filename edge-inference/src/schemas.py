"""
Pydantic schemas for data validation
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class BBox(BaseModel):
    """Bounding box coordinates"""
    xmin: float
    ymin: float
    xmax: float
    ymax: float


class Detection(BaseModel):
    """Single object detection"""
    bbox: BBox
    class_name: str = Field(..., alias="class")
    confidence: float
    class_id: int

    class Config:
        populate_by_name = True


class Location(BaseModel):
    """GPS location"""
    latitude: float
    longitude: float
    altitude_m: float
    accuracy_m: float


class DetectionMessage(BaseModel):
    """Complete detection message with telemetry"""
    timestamp: str
    node_id: str
    location: Location
    detections: List[Detection]
    detection_count: int
    inference_time_ms: float
    model: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    model: str
    blackout_active: bool
    device: str


class BlackoutActivateResponse(BaseModel):
    """Blackout activation response"""
    status: str
    activated_at: Optional[str] = None


class BlackoutDeactivateResponse(BaseModel):
    """Blackout deactivation response"""
    status: str
    queued_detections: List[dict]
    count: int


class BlackoutStatusResponse(BaseModel):
    """Blackout status response"""
    active: bool
    activated_at: Optional[str]
    queued_count: int
