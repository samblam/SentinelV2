"""Test helper functions for ATAK/CoT integration tests.

This module contains non-test helper functions that can be imported
by test modules without violating the "don't import test modules" rule.
"""
from datetime import datetime, timezone


def create_sample_detection(**overrides):
    """Helper to create detection with custom values.

    Args:
        **overrides: Fields to override in the base detection

    Returns:
        Dictionary with detection data
    """
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
    return base | overrides
