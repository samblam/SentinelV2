"""
Tests for Pydantic schemas and data validation
"""
import pytest
from pydantic import ValidationError
from datetime import datetime, timezone

from src.schemas import (
    BBox,
    Detection,
    Location,
    DetectionMessage,
    HealthResponse,
    BlackoutActivateResponse,
    BlackoutDeactivateResponse,
    BlackoutStatusResponse
)


def test_bbox_valid():
    """Test BBox model with valid data"""
    bbox = BBox(xmin=10.5, ymin=20.3, xmax=100.7, ymax=200.9)

    assert bbox.xmin == 10.5
    assert bbox.ymin == 20.3
    assert bbox.xmax == 100.7
    assert bbox.ymax == 200.9


def test_bbox_type_coercion():
    """Test BBox coerces integers to floats"""
    bbox = BBox(xmin=10, ymin=20, xmax=100, ymax=200)

    assert isinstance(bbox.xmin, float)
    assert bbox.xmin == 10.0


def test_bbox_invalid_type():
    """Test BBox rejects invalid types"""
    with pytest.raises(ValidationError):
        BBox(xmin="not a number", ymin=20, xmax=100, ymax=200)


def test_bbox_missing_required_fields():
    """Test BBox raises ValidationError when required fields are missing"""
    with pytest.raises(ValidationError):
        BBox(ymin=20, xmax=100, ymax=200)

    with pytest.raises(ValidationError):
        BBox(xmin=10, xmax=100, ymax=200)

    with pytest.raises(ValidationError):
        BBox(xmin=10, ymin=20, ymax=200)

    with pytest.raises(ValidationError):
        BBox(xmin=10, ymin=20, xmax=100)


def test_detection_valid():
    """Test Detection model with valid data"""
    bbox = BBox(xmin=10.5, ymin=20.3, xmax=100.7, ymax=200.9)
    detection = Detection(
        bbox=bbox,
        class_name="person",
        confidence=0.95,
        class_id=0
    )

    assert detection.bbox == bbox
    assert detection.class_name == "person"
    assert detection.confidence == 0.95
    assert detection.class_id == 0


def test_detection_with_alias():
    """Test Detection model accepts 'class' as alias for class_name"""
    detection = Detection(
        bbox=BBox(xmin=0, ymin=0, xmax=10, ymax=10),
        **{"class": "vehicle"},  # Using 'class' keyword as dict key
        confidence=0.85,
        class_id=1
    )

    assert detection.class_name == "vehicle"


def test_detection_confidence_bounds():
    """Test Detection validates confidence is between 0 and 1"""
    # Valid confidence
    detection = Detection(
        bbox=BBox(xmin=0, ymin=0, xmax=10, ymax=10),
        class_name="car",
        confidence=0.5,
        class_id=2
    )
    assert 0 <= detection.confidence <= 1

    # Edge cases: 0 and 1 should be valid
    detection_min = Detection(
        bbox=BBox(xmin=0, ymin=0, xmax=10, ymax=10),
        class_name="car",
        confidence=0.0,
        class_id=2
    )
    assert detection_min.confidence == 0.0

    detection_max = Detection(
        bbox=BBox(xmin=0, ymin=0, xmax=10, ymax=10),
        class_name="car",
        confidence=1.0,
        class_id=2
    )
    assert detection_max.confidence == 1.0


def test_detection_confidence_out_of_bounds():
    """Test Detection rejects out-of-bounds confidence values"""
    # Confidence less than 0
    with pytest.raises(ValidationError):
        Detection(
            bbox=BBox(xmin=0, ymin=0, xmax=10, ymax=10),
            class_name="car",
            confidence=-0.1,
            class_id=2
        )

    # Confidence greater than 1
    with pytest.raises(ValidationError):
        Detection(
            bbox=BBox(xmin=0, ymin=0, xmax=10, ymax=10),
            class_name="car",
            confidence=1.1,
            class_id=2
        )


def test_detection_missing_required_fields():
    """Test Detection raises ValidationError when required fields are missing"""
    # Missing bbox
    with pytest.raises(ValidationError):
        Detection(class_name="person", confidence=0.9, class_id=0)

    # Missing class_name
    with pytest.raises(ValidationError):
        Detection(
            bbox=BBox(xmin=0, ymin=0, xmax=10, ymax=10),
            confidence=0.9,
            class_id=0
        )

    # Missing confidence
    with pytest.raises(ValidationError):
        Detection(
            bbox=BBox(xmin=0, ymin=0, xmax=10, ymax=10),
            class_name="person",
            class_id=0
        )


def test_location_valid():
    """Test Location model with valid Arctic coordinates"""
    location = Location(
        latitude=70.5,
        longitude=-100.3,
        altitude_m=50.2,
        accuracy_m=10.5
    )

    assert location.latitude == 70.5
    assert location.longitude == -100.3
    assert location.altitude_m == 50.2
    assert location.accuracy_m == 10.5


def test_location_extreme_values():
    """Test Location with extreme but valid GPS coordinates"""
    # North pole
    north_pole = Location(
        latitude=90.0,
        longitude=0.0,
        altitude_m=0.0,
        accuracy_m=5.0
    )
    assert north_pole.latitude == 90.0

    # South pole
    south_pole = Location(
        latitude=-90.0,
        longitude=180.0,
        altitude_m=2800.0,  # Antarctic plateau
        accuracy_m=20.0
    )
    assert south_pole.latitude == -90.0


def test_location_invalid_coordinates():
    """Test Location rejects invalid latitude and longitude values"""
    # Latitude > 90
    with pytest.raises(ValidationError):
        Location(latitude=91.0, longitude=0.0, altitude_m=0.0, accuracy_m=5.0)

    # Latitude < -90
    with pytest.raises(ValidationError):
        Location(latitude=-91.0, longitude=0.0, altitude_m=0.0, accuracy_m=5.0)

    # Longitude > 180
    with pytest.raises(ValidationError):
        Location(latitude=0.0, longitude=181.0, altitude_m=0.0, accuracy_m=5.0)

    # Longitude < -180
    with pytest.raises(ValidationError):
        Location(latitude=0.0, longitude=-181.0, altitude_m=0.0, accuracy_m=5.0)


def test_location_missing_required_fields():
    """Test Location raises ValidationError when required fields are missing"""
    with pytest.raises(ValidationError):
        Location(longitude=0.0, altitude_m=0.0, accuracy_m=5.0)

    with pytest.raises(ValidationError):
        Location(latitude=70.0, altitude_m=0.0, accuracy_m=5.0)


def test_detection_message_complete():
    """Test complete DetectionMessage with all fields"""
    now = datetime.now(timezone.utc).isoformat()
    bbox = BBox(xmin=10, ymin=20, xmax=100, ymax=200)
    detection = Detection(
        bbox=bbox,
        class_name="person",
        confidence=0.95,
        class_id=0
    )
    location = Location(
        latitude=70.5,
        longitude=-100.3,
        altitude_m=50.2,
        accuracy_m=10.5
    )

    message = DetectionMessage(
        timestamp=now,
        node_id="test-node-01",
        location=location,
        detections=[detection],
        detection_count=1,
        inference_time_ms=87.5,
        model="yolov5n"
    )

    assert message.node_id == "test-node-01"
    assert message.detection_count == 1
    assert message.inference_time_ms == 87.5
    assert message.model == "yolov5n"
    assert len(message.detections) == 1
    assert message.timestamp == now


def test_detection_message_empty_detections():
    """Test DetectionMessage with no detections"""
    now = datetime.now(timezone.utc).isoformat()
    location = Location(
        latitude=70.5,
        longitude=-100.3,
        altitude_m=50.2,
        accuracy_m=10.5
    )

    message = DetectionMessage(
        timestamp=now,
        node_id="test-node-02",
        location=location,
        detections=[],
        detection_count=0,
        inference_time_ms=45.2,
        model="yolov5n"
    )

    assert message.detection_count == 0
    assert len(message.detections) == 0


def test_detection_message_multiple_detections():
    """Test DetectionMessage with multiple detections"""
    now = datetime.now(timezone.utc).isoformat()
    location = Location(latitude=70.0, longitude=-100.0, altitude_m=0.0, accuracy_m=5.0)

    detections = [
        Detection(
            bbox=BBox(xmin=i*10, ymin=i*10, xmax=i*10+50, ymax=i*10+50),
            class_name=f"object_{i}",
            confidence=0.9 - i*0.1,
            class_id=i
        )
        for i in range(5)
    ]

    message = DetectionMessage(
        timestamp=now,
        node_id="multi-test",
        location=location,
        detections=detections,
        detection_count=5,
        inference_time_ms=120.0,
        model="yolov5n"
    )

    assert message.detection_count == 5
    assert len(message.detections) == 5


def test_health_response_valid():
    """Test HealthResponse model"""
    health = HealthResponse(
        status="healthy",
        model="yolov5n",
        blackout_active=False,
        device="cpu"
    )

    assert health.status == "healthy"
    assert health.model == "yolov5n"
    assert health.blackout_active is False
    assert health.device == "cpu"


def test_health_response_with_gpu():
    """Test HealthResponse with GPU device"""
    health = HealthResponse(
        status="healthy",
        model="yolov5n",
        blackout_active=True,
        device="cuda:0"
    )

    assert health.device == "cuda:0"
    assert health.blackout_active is True


def test_blackout_activate_response():
    """Test BlackoutActivateResponse"""
    now = datetime.now(timezone.utc).isoformat()
    response = BlackoutActivateResponse(
        status="activated",
        activated_at=now
    )

    assert response.status == "activated"
    assert response.activated_at == now


def test_blackout_activate_response_already_active():
    """Test BlackoutActivateResponse when already active"""
    response = BlackoutActivateResponse(
        status="already_active",
        activated_at=None
    )

    assert response.status == "already_active"
    assert response.activated_at is None


def test_blackout_deactivate_response():
    """Test BlackoutDeactivateResponse"""
    response = BlackoutDeactivateResponse(
        status="deactivated",
        queued_detections=[{"test": "data"}],
        count=1
    )

    assert response.status == "deactivated"
    assert response.count == 1
    assert len(response.queued_detections) == 1


def test_blackout_deactivate_response_not_active():
    """Test BlackoutDeactivateResponse when not active"""
    response = BlackoutDeactivateResponse(
        status="not_active",
        queued_detections=[],
        count=0
    )

    assert response.status == "not_active"
    assert response.count == 0


def test_blackout_status_response_active():
    """Test BlackoutStatusResponse when active"""
    now = datetime.now(timezone.utc).isoformat()
    status = BlackoutStatusResponse(
        active=True,
        activated_at=now,
        queued_count=5
    )

    assert status.active is True
    assert status.activated_at == now
    assert status.queued_count == 5


def test_blackout_status_response_inactive():
    """Test BlackoutStatusResponse when inactive"""
    status = BlackoutStatusResponse(
        active=False,
        activated_at=None,
        queued_count=0
    )

    assert status.active is False
    assert status.activated_at is None
    assert status.queued_count == 0


def test_detection_message_json_serialization():
    """Test DetectionMessage can be serialized to JSON"""
    now = datetime.now(timezone.utc).isoformat()
    location = Location(latitude=70.0, longitude=-100.0, altitude_m=0.0, accuracy_m=5.0)
    detection = Detection(
        bbox=BBox(xmin=10, ymin=20, xmax=100, ymax=200),
        class_name="person",
        confidence=0.95,
        class_id=0
    )

    message = DetectionMessage(
        timestamp=now,
        node_id="json-test",
        location=location,
        detections=[detection],
        detection_count=1,
        inference_time_ms=87.5,
        model="yolov5n"
    )

    # Test model_dump (Pydantic v2)
    json_dict = message.model_dump()
    assert json_dict["node_id"] == "json-test"
    assert json_dict["detection_count"] == 1

    # Test model_dump_json
    json_str = message.model_dump_json()
    assert "json-test" in json_str
    assert "person" in json_str


def test_detection_message_from_dict():
    """Test creating DetectionMessage from dictionary"""
    data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "node_id": "dict-test",
        "location": {
            "latitude": 70.0,
            "longitude": -100.0,
            "altitude_m": 0.0,
            "accuracy_m": 5.0
        },
        "detections": [
            {
                "bbox": {"xmin": 10, "ymin": 20, "xmax": 100, "ymax": 200},
                "class": "person",
                "confidence": 0.95,
                "class_id": 0
            }
        ],
        "detection_count": 1,
        "inference_time_ms": 87.5,
        "model": "yolov5n"
    }

    message = DetectionMessage(**data)
    assert message.node_id == "dict-test"
    assert len(message.detections) == 1
    assert message.detections[0].class_name == "person"
