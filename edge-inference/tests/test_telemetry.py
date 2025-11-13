"""
Test suite for telemetry generation
Following TDD - these tests should fail initially
"""
import pytest
from datetime import datetime, timezone

from src.telemetry import TelemetryGenerator


def test_generates_arctic_coordinates():
    """Test GPS coordinates are in Arctic range"""
    generator = TelemetryGenerator()
    coords = generator.generate_gps()

    assert 60.0 <= coords["latitude"] <= 85.0  # Arctic range
    assert -180.0 <= coords["longitude"] <= 180.0
    assert "accuracy_m" in coords
    assert "altitude_m" in coords
    assert coords["accuracy_m"] > 0
    assert coords["altitude_m"] >= 0


def test_generates_unique_node_id():
    """Test node ID generation"""
    generator = TelemetryGenerator()
    node_id = generator.generate_node_id()

    assert isinstance(node_id, str)
    assert len(node_id) > 5  # e.g., "sentry-01"
    assert "-" in node_id  # Format: type-number


def test_node_id_is_consistent():
    """Test node ID remains consistent for same generator instance"""
    generator = TelemetryGenerator()
    node_id_1 = generator.node_id
    node_id_2 = generator.node_id

    assert node_id_1 == node_id_2


def test_creates_detection_message(sample_detection_result):
    """Test complete detection message with telemetry"""
    generator = TelemetryGenerator()

    message = generator.create_detection_message(sample_detection_result)

    assert "timestamp" in message
    assert "node_id" in message
    assert "location" in message
    assert "detections" in message
    assert "detection_count" in message
    assert "inference_time_ms" in message
    assert "model" in message

    # Verify timestamp format
    timestamp = datetime.fromisoformat(message["timestamp"])
    assert timestamp.tzinfo is not None  # Should be timezone-aware

    # Verify location structure
    location = message["location"]
    assert "latitude" in location
    assert "longitude" in location
    assert "altitude_m" in location
    assert "accuracy_m" in location


def test_creates_message_with_empty_detections(empty_detection_result):
    """Test message creation with no detections"""
    generator = TelemetryGenerator()

    message = generator.create_detection_message(empty_detection_result)

    assert message["detection_count"] == 0
    assert len(message["detections"]) == 0
    assert "timestamp" in message
    assert "node_id" in message


def test_custom_node_id_override(sample_detection_result):
    """Test node ID can be overridden"""
    generator = TelemetryGenerator()
    custom_node_id = "custom-node-99"

    message = generator.create_detection_message(
        sample_detection_result,
        node_id=custom_node_id
    )

    assert message["node_id"] == custom_node_id


def test_custom_gps_override(sample_detection_result):
    """Test GPS coordinates can be overridden"""
    generator = TelemetryGenerator()
    custom_gps = {
        "latitude": 75.5,
        "longitude": -120.0,
        "altitude_m": 50.0,
        "accuracy_m": 10.0
    }

    message = generator.create_detection_message(
        sample_detection_result,
        gps=custom_gps
    )

    assert message["location"]["latitude"] == 75.5
    assert message["location"]["longitude"] == -120.0


def test_multiple_gps_generations_vary():
    """Test GPS coordinates vary slightly between calls"""
    generator = TelemetryGenerator()

    coords_1 = generator.generate_gps()
    coords_2 = generator.generate_gps()

    # Coordinates should vary slightly (random offset)
    # They might occasionally be the same, but very unlikely
    assert (coords_1["latitude"] != coords_2["latitude"] or
            coords_1["longitude"] != coords_2["longitude"])


def test_base_coordinates_configurable():
    """Test base coordinates can be configured"""
    custom_lat = 75.0
    custom_lon = -110.0

    generator = TelemetryGenerator(base_lat=custom_lat, base_lon=custom_lon)
    coords = generator.generate_gps()

    # Coordinates should be close to base (within offset range)
    assert abs(coords["latitude"] - custom_lat) < 0.02
    assert abs(coords["longitude"] - custom_lon) < 0.02
