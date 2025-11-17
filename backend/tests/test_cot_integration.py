"""Integration tests for CoT/TAK endpoints (Module 3 integration)."""
import pytest
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport

from src.main import app
from src.models import Node, Detection


@pytest.mark.asyncio
async def test_generate_cot_endpoint(test_engine, get_session):
    """Test /api/cot/generate endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register a node
        node_response = await client.post(
            "/api/nodes/register",
            json={"node_id": "cot-test-node-01"}
        )
        assert node_response.status_code == 200

        # Create a detection
        detection_data = {
            "node_id": "cot-test-node-01",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "location": {
                "latitude": 70.5,
                "longitude": -100.2,
                "altitude_m": 50.0,
                "accuracy_m": 10.0
            },
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

        detection_response = await client.post(
            "/api/detections",
            json=detection_data
        )
        assert detection_response.status_code == 200
        detection_id = detection_response.json()["id"]

        # Generate CoT for this detection
        cot_response = await client.post(
            f"/api/cot/generate?detection_id={detection_id}"
        )
        assert cot_response.status_code == 200

        cot_data = cot_response.json()
        assert cot_data["status"] == "success"
        assert cot_data["detection_id"] == detection_id
        assert cot_data["node_id"] == "cot-test-node-01"
        assert "cot_xml" in cot_data

        # Verify CoT XML structure
        cot_xml = cot_data["cot_xml"]
        assert '<?xml version' in cot_xml
        assert '<event' in cot_xml
        assert 'type="a-f-G-E-S"' in cot_xml
        assert 'lat="70.5"' in cot_xml
        assert 'lon="-100.2"' in cot_xml
        assert '<contact callsign="cot-test-node-01"' in cot_xml
        assert '<detection>' in cot_xml
        assert 'person' in cot_xml


@pytest.mark.asyncio
async def test_generate_cot_multi_detection(test_engine, get_session):
    """Test CoT generation with multiple detections."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register node
        await client.post(
            "/api/nodes/register",
            json={"node_id": "cot-multi-node"}
        )

        # Create detection with multiple objects
        detection_data = {
            "node_id": "cot-multi-node",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "location": {
                "latitude": 71.3,
                "longitude": -99.8,
                "altitude_m": 35.0,
                "accuracy_m": 15.0
            },
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

        detection_response = await client.post(
            "/api/detections",
            json=detection_data
        )
        assert detection_response.status_code == 200
        detection_id = detection_response.json()["id"]

        # Generate CoT
        cot_response = await client.post(
            f"/api/cot/generate?detection_id={detection_id}"
        )
        assert cot_response.status_code == 200

        cot_xml = cot_response.json()["cot_xml"]

        # Should have 2 detection elements
        assert cot_xml.count('<detection>') == 2
        assert 'person' in cot_xml
        assert 'vehicle' in cot_xml
        assert '0.92' in cot_xml
        assert '0.85' in cot_xml


@pytest.mark.asyncio
async def test_generate_cot_detection_not_found(test_engine):
    """Test CoT generation with non-existent detection."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        cot_response = await client.post(
            "/api/cot/generate?detection_id=99999"
        )
        assert cot_response.status_code == 404
        assert "not found" in cot_response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_generate_cot_missing_detection_id(test_engine):
    """Test CoT generation without detection_id parameter."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        cot_response = await client.post("/api/cot/generate")
        assert cot_response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_send_cot_endpoint_disabled(test_engine, get_session):
    """Test /api/cot/send endpoint when TAK server is disabled."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register node and create detection
        await client.post(
            "/api/nodes/register",
            json={"node_id": "cot-send-node"}
        )

        detection_data = {
            "node_id": "cot-send-node",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "location": {
                "latitude": 70.0,
                "longitude": -100.0,
                "altitude_m": 0.0,
                "accuracy_m": 10.0
            },
            "detections": [
                {
                    "bbox": {"xmin": 0, "ymin": 0, "xmax": 100, "ymax": 100},
                    "class": "person",
                    "confidence": 0.8,
                    "class_id": 0
                }
            ],
            "detection_count": 1,
            "inference_time_ms": 50.0,
            "model": "yolov5n"
        }

        detection_response = await client.post(
            "/api/detections",
            json=detection_data
        )
        detection_id = detection_response.json()["id"]

        # Try to send CoT (should fail because TAK_SERVER_ENABLED=False by default)
        send_response = await client.post(
            f"/api/cot/send?detection_id={detection_id}"
        )
        assert send_response.status_code == 503
        assert "disabled" in send_response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_cot_validation_in_pipeline(test_engine, get_session):
    """Test that generated CoT passes validation."""
    from atak_integration.src.cot_validator import CoTValidator

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register node
        await client.post(
            "/api/nodes/register",
            json={"node_id": "validation-node"}
        )

        # Create detection
        detection_data = {
            "node_id": "validation-node",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "location": {
                "latitude": 75.0,
                "longitude": -110.0,
                "altitude_m": 100.0,
                "accuracy_m": 5.0
            },
            "detections": [
                {
                    "bbox": {"xmin": 50, "ymin": 60, "xmax": 150, "ymax": 200},
                    "class": "vehicle",
                    "confidence": 0.95,
                    "class_id": 2
                }
            ],
            "detection_count": 1,
            "inference_time_ms": 75.0,
            "model": "yolov5s"
        }

        detection_response = await client.post(
            "/api/detections",
            json=detection_data
        )
        detection_id = detection_response.json()["id"]

        # Generate CoT
        cot_response = await client.post(
            f"/api/cot/generate?detection_id={detection_id}"
        )
        cot_xml = cot_response.json()["cot_xml"]

        # Validate the generated CoT
        validator = CoTValidator()
        is_valid, errors = validator.validate(cot_xml)
        assert is_valid, f"Generated CoT failed validation: {errors}"


@pytest.mark.asyncio
async def test_cot_arctic_coordinates(test_engine, get_session):
    """Test CoT generation with extreme Arctic coordinates."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register node
        await client.post(
            "/api/nodes/register",
            json={"node_id": "arctic-extreme"}
        )

        # Create detection near North Pole
        detection_data = {
            "node_id": "arctic-extreme",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "location": {
                "latitude": 89.9,  # Very far north
                "longitude": -45.0,
                "altitude_m": 0.0,
                "accuracy_m": 20.0
            },
            "detections": [
                {
                    "bbox": {"xmin": 0, "ymin": 0, "xmax": 50, "ymax": 50},
                    "class": "person",
                    "confidence": 0.75,
                    "class_id": 0
                }
            ],
            "detection_count": 1,
            "inference_time_ms": 100.0,
            "model": "yolov5n"
        }

        detection_response = await client.post(
            "/api/detections",
            json=detection_data
        )
        detection_id = detection_response.json()["id"]

        # Generate CoT
        cot_response = await client.post(
            f"/api/cot/generate?detection_id={detection_id}"
        )
        assert cot_response.status_code == 200

        cot_xml = cot_response.json()["cot_xml"]
        assert 'lat="89.9"' in cot_xml
        assert 'lon="-45.0"' in cot_xml


@pytest.mark.asyncio
async def test_batch_cot_generation(test_engine, get_session):
    """Test generating CoT for multiple detections sequentially."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register node
        await client.post(
            "/api/nodes/register",
            json={"node_id": "batch-node"}
        )

        # Create multiple detections
        detection_ids = []
        for i in range(3):
            detection_data = {
                "node_id": "batch-node",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "location": {
                    "latitude": 70.0 + i * 0.1,
                    "longitude": -100.0 - i * 0.1,
                    "altitude_m": 10.0 * i,
                    "accuracy_m": 10.0
                },
                "detections": [
                    {
                        "bbox": {"xmin": i*10, "ymin": i*10, "xmax": 100+i*10, "ymax": 100+i*10},
                        "class": "person",
                        "confidence": 0.8 + i * 0.05,
                        "class_id": 0
                    }
                ],
                "detection_count": 1,
                "inference_time_ms": 50.0 + i * 10,
                "model": "yolov5n"
            }

            response = await client.post("/api/detections", json=detection_data)
            detection_ids.append(response.json()["id"])

        # Generate CoT for each detection
        for detection_id in detection_ids:
            cot_response = await client.post(
                f"/api/cot/generate?detection_id={detection_id}"
            )
            assert cot_response.status_code == 200
            assert "cot_xml" in cot_response.json()


@pytest.mark.asyncio
async def test_cot_with_queued_detection(test_engine, get_session):
    """Test CoT generation after dequeuing detection from blackout mode."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register node
        await client.post(
            "/api/nodes/register",
            json={"node_id": "blackout-cot-node"}
        )

        # Activate blackout
        await client.post(
            "/api/blackout/activate",
            json={"node_id": "blackout-cot-node", "reason": "Testing"}
        )

        # Send detection (will be queued)
        detection_data = {
            "node_id": "blackout-cot-node",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "location": {
                "latitude": 72.0,
                "longitude": -105.0,
                "altitude_m": 25.0,
                "accuracy_m": 12.0
            },
            "detections": [
                {
                    "bbox": {"xmin": 20, "ymin": 30, "xmax": 120, "ymax": 130},
                    "class": "vehicle",
                    "confidence": 0.88,
                    "class_id": 2
                }
            ],
            "detection_count": 1,
            "inference_time_ms": 65.0,
            "model": "yolov5n"
        }

        queued_response = await client.post(
            "/api/detections",
            json=detection_data
        )
        assert queued_response.json().get("queued") == True

        # Deactivate blackout (will process queued detection)
        deactivate_response = await client.post(
            "/api/blackout/deactivate",
            json={"node_id": "blackout-cot-node"}
        )
        assert deactivate_response.status_code == 200
        assert deactivate_response.json()["node_id"] == "blackout-cot-node"

        # Get the detection ID
        detections_response = await client.get("/api/detections?limit=1")

        if detections := detections_response.json():
            detection_id = detections[0]["id"]

            # Generate CoT for the dequeued detection
            cot_response = await client.post(
                f"/api/cot/generate?detection_id={detection_id}"
            )
            assert cot_response.status_code == 200
            assert "cot_xml" in cot_response.json()
