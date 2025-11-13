"""Tests for Pydantic data models."""
import pytest
from datetime import datetime, timezone
from pydantic import ValidationError


def test_bounding_box_creation(sample_bounding_box):
    """Test BoundingBox model creation."""
    from src.cot_schemas import BoundingBox

    bbox = BoundingBox(**sample_bounding_box)
    assert bbox.xmin == 100
    assert bbox.ymin == 150
    assert bbox.xmax == 300
    assert bbox.ymax == 400


def test_bounding_box_validation():
    """Test BoundingBox validation."""
    from src.cot_schemas import BoundingBox

    # Should fail with missing fields
    with pytest.raises(ValidationError):
        BoundingBox(xmin=100, ymin=150)

    # Should fail with wrong types (non-numeric string)
    with pytest.raises(ValidationError):
        BoundingBox(xmin="invalid", ymin=150, xmax=300, ymax=400)


def test_detection_creation(sample_detection):
    """Test Detection model creation."""
    from src.cot_schemas import Detection

    detection = Detection(**sample_detection)
    assert detection.class_name == "person"
    assert detection.confidence == 0.89
    assert detection.class_id == 0
    assert detection.bbox.xmin == 100


def test_detection_alias_handling():
    """Test Detection handles 'class' alias correctly."""
    from src.cot_schemas import Detection

    # Should work with 'class' key
    detection = Detection(
        bbox={"xmin": 100, "ymin": 150, "xmax": 300, "ymax": 400},
        **{"class": "person"},
        confidence=0.89,
        class_id=0
    )
    assert detection.class_name == "person"


def test_detection_confidence_validation():
    """Test Detection confidence range validation."""
    from src.cot_schemas import Detection

    # Valid confidence values
    Detection(
        bbox={"xmin": 100, "ymin": 150, "xmax": 300, "ymax": 400},
        **{"class": "person"},
        confidence=0.0,
        class_id=0
    )

    Detection(
        bbox={"xmin": 100, "ymin": 150, "xmax": 300, "ymax": 400},
        **{"class": "person"},
        confidence=1.0,
        class_id=0
    )

    # Invalid confidence (should fail if we add validation)
    # This test documents expected behavior


def test_sentinel_detection_creation(sample_sentinel_detection):
    """Test SentinelDetection model creation."""
    from src.cot_schemas import SentinelDetection

    sentinel_det = SentinelDetection(**sample_sentinel_detection)
    assert sentinel_det.node_id == "sentry-01"
    assert sentinel_det.latitude == 70.5
    assert sentinel_det.longitude == -100.2
    assert sentinel_det.altitude_m == 50.0
    assert sentinel_det.detection_count == 1
    assert len(sentinel_det.detections) == 1


def test_sentinel_detection_defaults():
    """Test SentinelDetection default values."""
    from src.cot_schemas import SentinelDetection

    minimal_detection = {
        "node_id": "test-node",
        "timestamp": datetime.now(timezone.utc),
        "latitude": 70.0,
        "longitude": -100.0,
        "detections": [],
        "detection_count": 0,
        "inference_time_ms": 50.0
    }

    sentinel_det = SentinelDetection(**minimal_detection)
    assert sentinel_det.altitude_m == 0.0  # Default
    assert sentinel_det.accuracy_m == 10.0  # Default
    assert sentinel_det.model == "yolov5n"  # Default


def test_sentinel_detection_coordinate_validation():
    """Test SentinelDetection coordinate validation."""
    from src.cot_schemas import SentinelDetection

    # Valid coordinates
    valid = {
        "node_id": "test",
        "timestamp": datetime.now(timezone.utc),
        "latitude": 70.0,
        "longitude": -100.0,
        "detections": [],
        "detection_count": 0,
        "inference_time_ms": 50.0
    }
    SentinelDetection(**valid)

    # Edge cases: valid lat/lon ranges
    SentinelDetection(**{**valid, "latitude": -90.0, "longitude": -180.0})
    SentinelDetection(**{**valid, "latitude": 90.0, "longitude": 180.0})


def test_sentinel_detection_with_multiple_detections(sample_multi_detection):
    """Test SentinelDetection with multiple detected objects."""
    from src.cot_schemas import SentinelDetection

    sentinel_det = SentinelDetection(**sample_multi_detection)
    assert sentinel_det.detection_count == 2
    assert len(sentinel_det.detections) == 2
    assert sentinel_det.node_id == "sentry-02"


def test_sentinel_detection_timestamp_handling():
    """Test SentinelDetection handles timezone-aware timestamps."""
    from src.cot_schemas import SentinelDetection

    now = datetime.now(timezone.utc)
    detection = {
        "node_id": "test",
        "timestamp": now,
        "latitude": 70.0,
        "longitude": -100.0,
        "detections": [],
        "detection_count": 0,
        "inference_time_ms": 50.0
    }

    sentinel_det = SentinelDetection(**detection)
    assert sentinel_det.timestamp == now
    assert sentinel_det.timestamp.tzinfo is not None


def test_sentinel_detection_missing_required_fields():
    """Test SentinelDetection fails with missing required fields."""
    from src.cot_schemas import SentinelDetection

    with pytest.raises(ValidationError):
        SentinelDetection(
            node_id="test",
            latitude=70.0,
            longitude=-100.0
            # Missing timestamp, detections, detection_count, inference_time_ms
        )


def test_detection_json_serialization(sample_detection):
    """Test Detection can be serialized to JSON."""
    from src.cot_schemas import Detection

    detection = Detection(**sample_detection)
    json_data = detection.model_dump(mode='json')

    assert json_data['class_name'] == "person"
    assert json_data['confidence'] == 0.89


def test_sentinel_detection_json_serialization(sample_sentinel_detection):
    """Test SentinelDetection can be serialized to JSON."""
    from src.cot_schemas import SentinelDetection

    sentinel_det = SentinelDetection(**sample_sentinel_detection)
    json_data = sentinel_det.model_dump(mode='json')

    assert json_data['node_id'] == "sentry-01"
    assert json_data['detection_count'] == 1
    assert isinstance(json_data['timestamp'], str)  # ISO format string
