"""Pytest fixtures for ATAK/CoT integration tests."""
import pytest
from datetime import datetime, timezone
from typing import Dict, Any


@pytest.fixture
def sample_bounding_box() -> Dict[str, int]:
    """Sample bounding box data."""
    return {
        "xmin": 100,
        "ymin": 150,
        "xmax": 300,
        "ymax": 400
    }


@pytest.fixture
def sample_detection(sample_bounding_box) -> Dict[str, Any]:
    """Sample detection data."""
    return {
        "bbox": sample_bounding_box,
        "class": "person",
        "confidence": 0.89,
        "class_id": 0
    }


@pytest.fixture
def sample_sentinel_detection(sample_detection) -> Dict[str, Any]:
    """Sample complete Sentinel detection."""
    return {
        "node_id": "sentry-01",
        "timestamp": datetime.now(timezone.utc),
        "latitude": 70.5,
        "longitude": -100.2,
        "altitude_m": 50.0,
        "accuracy_m": 10.0,
        "detections": [sample_detection],
        "detection_count": 1,
        "inference_time_ms": 87.5,
        "model": "yolov5n"
    }


@pytest.fixture
def sample_multi_detection(sample_bounding_box) -> Dict[str, Any]:
    """Sample detection with multiple objects."""
    return {
        "node_id": "sentry-02",
        "timestamp": datetime.now(timezone.utc),
        "latitude": 71.3,
        "longitude": -99.8,
        "altitude_m": 35.0,
        "accuracy_m": 15.0,
        "detections": [
            {
                "bbox": {"xmin": 100, "ymin": 150, "xmax": 300, "ymax": 400},
                "class": "person",
                "confidence": 0.92,
                "class_id": 0
            },
            {
                "bbox": {"xmin": 350, "ymin": 200, "xmax": 500, "ymax": 450},
                "class": "vehicle",
                "confidence": 0.85,
                "class_id": 2
            }
        ],
        "detection_count": 2,
        "inference_time_ms": 112.3,
        "model": "yolov5n"
    }


def create_sample_detection(**overrides):
    """Helper to create detection with custom values."""
    base = {
        "node_id": "sentry-01",
        "timestamp": datetime.now(timezone.utc),
        "latitude": 70.5,
        "longitude": -100.2,
        "altitude_m": 50.0,
        "accuracy_m": 10.0,
        "detections": [
            {
                "bbox": {"xmin": 100, "ymin": 150, "xmax": 300, "ymax": 400},
                "class": "person",
                "confidence": 0.89,
                "class_id": 0
            }
        ],
        "detection_count": 1,
        "inference_time_ms": 87.5,
        "model": "yolov5n"
    }
    base.update(overrides)
    return base
