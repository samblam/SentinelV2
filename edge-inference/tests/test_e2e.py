"""
End-to-end tests for complete workflow scenarios
Tests the full integration of all components working together
"""
import pytest
from httpx import AsyncClient
from pathlib import Path
import asyncio
import json

from src.main import app
from src.blackout import BlackoutController
from src.telemetry import TelemetryGenerator
from src.inference import InferenceEngine


@pytest.mark.asyncio
async def test_complete_detection_workflow(client, test_image_path):
    """Test complete detection workflow from image upload to response"""
    # Step 1: Verify service is healthy
    health_response = await client.get("/health")
    assert health_response.status_code == 200
    assert health_response.json()["status"] == "healthy"

    # Step 2: Upload image and get detection
    with open(test_image_path, 'rb') as f:
        files = {"file": ("test.jpg", f, "image/jpeg")}
        detect_response = await client.post("/detect", files=files)

    assert detect_response.status_code == 200
    data = detect_response.json()

    # Step 3: Verify complete message structure
    assert "timestamp" in data
    assert "node_id" in data
    assert "location" in data
    assert "detections" in data
    assert "detection_count" in data
    assert "inference_time_ms" in data
    assert "model" in data

    # Step 4: Verify location is Arctic
    location = data["location"]
    assert 60.0 <= location["latitude"] <= 85.0
    assert -180.0 <= location["longitude"] <= 180.0
    assert "altitude_m" in location
    assert "accuracy_m" in location


@pytest.mark.asyncio
async def test_blackout_mode_complete_workflow(client, test_image_path):
    """Test complete blackout mode workflow"""
    # Step 1: Check initial blackout status
    status_response = await client.get("/blackout/status")
    assert status_response.status_code == 200
    assert status_response.json()["active"] is False

    # Step 2: Activate blackout mode
    activate_response = await client.post("/blackout/activate")
    assert activate_response.status_code == 200
    assert activate_response.json()["status"] == "activated"

    # Step 3: Upload detections during blackout (should be queued)
    detections_sent = []
    for i in range(3):
        with open(test_image_path, 'rb') as f:
            files = {"file": (f"test_{i}.jpg", f, "image/jpeg")}
            response = await client.post(
                f"/detect?node_id=test-node-{i:02d}",
                files=files
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert data["blackout_active"] is True
        detections_sent.append(f"test-node-{i:02d}")

    # Step 4: Check blackout status shows queued items
    status_response = await client.get("/blackout/status")
    status = status_response.json()
    assert status["active"] is True
    assert status["queued_count"] == 3

    # Step 5: Deactivate blackout and retrieve queue
    deactivate_response = await client.post("/blackout/deactivate")
    assert deactivate_response.status_code == 200

    deactivate_data = deactivate_response.json()
    assert deactivate_data["status"] == "deactivated"
    assert deactivate_data["count"] == 3
    assert len(deactivate_data["queued_detections"]) == 3

    # Step 6: Verify queued detections have correct node IDs
    queued_node_ids = [d["node_id"] for d in deactivate_data["queued_detections"]]
    assert queued_node_ids == detections_sent

    # Step 7: Verify blackout is now inactive
    final_status = await client.get("/blackout/status")
    assert final_status.json()["active"] is False
    assert final_status.json()["queued_count"] == 0


@pytest.mark.asyncio
async def test_concurrent_detections(client, test_image_path):
    """Test system handles concurrent detection requests"""
    async def send_detection(node_num: int):
        with open(test_image_path, 'rb') as f:
            files = {"file": (f"test_{node_num}.jpg", f, "image/jpeg")}
            response = await client.post(
                f"/detect?node_id=concurrent-{node_num:02d}",
                files=files
            )
        return response

    # Send 5 concurrent detection requests
    tasks = [send_detection(i) for i in range(5)]
    responses = await asyncio.gather(*tasks)

    # Verify all succeeded
    for i, response in enumerate(responses):
        assert response.status_code == 200
        data = response.json()
        assert data["node_id"] == f"concurrent-{i:02d}"
        assert "detections" in data
        assert "inference_time_ms" in data


@pytest.mark.asyncio
async def test_blackout_reactivation_workflow(client, test_image_path):
    """Test activating blackout multiple times in sequence"""
    # First blackout cycle
    await client.post("/blackout/activate")

    with open(test_image_path, 'rb') as f:
        files = {"file": ("test1.jpg", f, "image/jpeg")}
        await client.post("/detect", files=files)

    result1 = await client.post("/blackout/deactivate")
    assert result1.json()["count"] == 1

    # Second blackout cycle
    await client.post("/blackout/activate")

    for i in range(2):
        with open(test_image_path, 'rb') as f:
            files = {"file": (f"test{i}.jpg", f, "image/jpeg")}
            await client.post("/detect", files=files)

    result2 = await client.post("/blackout/deactivate")
    assert result2.json()["count"] == 2

    # Verify queue was cleared between cycles
    final_status = await client.get("/blackout/status")
    assert final_status.json()["queued_count"] == 0


@pytest.mark.asyncio
async def test_custom_node_id_propagation(client, test_image_path):
    """Test custom node ID is properly propagated through the system"""
    custom_id = "arctic-sentinel-99"

    with open(test_image_path, 'rb') as f:
        files = {"file": ("test.jpg", f, "image/jpeg")}
        response = await client.post(f"/detect?node_id={custom_id}", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["node_id"] == custom_id

    # Verify it also works during blackout
    await client.post("/blackout/activate")

    custom_id_2 = "arctic-sentinel-100"
    with open(test_image_path, 'rb') as f:
        files = {"file": ("test.jpg", f, "image/jpeg")}
        await client.post(f"/detect?node_id={custom_id_2}", files=files)

    deactivate_result = await client.post("/blackout/deactivate")
    queued = deactivate_result.json()["queued_detections"]
    assert queued[0]["node_id"] == custom_id_2


@pytest.mark.asyncio
async def test_error_recovery_workflow(client, test_image_path):
    """Test system recovers gracefully from errors"""
    # Test 1: Invalid file type
    invalid_response = await client.post(
        "/detect",
        files={"file": ("test.txt", b"not an image", "text/plain")}
    )
    assert invalid_response.status_code == 400

    # Test 2: System still works after error
    with open(test_image_path, 'rb') as f:
        files = {"file": ("test.jpg", f, "image/jpeg")}
        valid_response = await client.post("/detect", files=files)

    assert valid_response.status_code == 200

    # Test 3: Health check still reports healthy
    health = await client.get("/health")
    assert health.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_blackout_already_active_idempotency(client):
    """Test activating blackout when already active is idempotent"""
    # Activate blackout
    response1 = await client.post("/blackout/activate")
    assert response1.json()["status"] == "activated"

    # Try to activate again
    response2 = await client.post("/blackout/activate")
    assert response2.json()["status"] == "already_active"

    # Cleanup
    await client.post("/blackout/deactivate")


@pytest.mark.asyncio
async def test_blackout_deactivate_when_inactive(client):
    """Test deactivating blackout when not active"""
    response = await client.post("/blackout/deactivate")
    assert response.json()["status"] == "not_active"


@pytest.mark.asyncio
async def test_full_arctic_deployment_simulation(client, test_image_path):
    """
    Simulate a complete Arctic deployment scenario:
    1. Node comes online
    2. Performs normal detections
    3. Enters blackout mode (covert operation)
    4. Performs detections during blackout
    5. Exits blackout and transmits queued data
    """
    # Phase 1: Node initialization
    health = await client.get("/health")
    assert health.json()["status"] == "healthy"

    root = await client.get("/")
    assert "Sentinel" in root.json()["service"]

    # Phase 2: Normal operations (3 detections)
    normal_detections = []
    for i in range(3):
        with open(test_image_path, 'rb') as f:
            files = {"file": (f"normal_{i}.jpg", f, "image/jpeg")}
            response = await client.post(
                "/detect?node_id=arctic-base-01",
                files=files
            )
        assert response.status_code == 200
        normal_detections.append(response.json())

    # Verify normal detections have Arctic GPS
    for detection in normal_detections:
        assert 60.0 <= detection["location"]["latitude"] <= 85.0
        assert detection["node_id"] == "arctic-base-01"

    # Phase 3: Enter blackout mode
    await client.post("/blackout/activate")

    # Phase 4: Covert operations (5 detections queued)
    for i in range(5):
        with open(test_image_path, 'rb') as f:
            files = {"file": (f"covert_{i}.jpg", f, "image/jpeg")}
            response = await client.post(
                "/detect?node_id=arctic-base-01",
                files=files
            )
        assert response.json()["status"] == "queued"

    # Phase 5: Exit blackout and verify queued transmissions
    deactivate = await client.post("/blackout/deactivate")
    assert deactivate.json()["count"] == 5

    queued = deactivate.json()["queued_detections"]
    for detection in queued:
        assert detection["node_id"] == "arctic-base-01"
        assert "detections" in detection
        assert "location" in detection

    # Phase 6: Resume normal operations
    with open(test_image_path, 'rb') as f:
        files = {"file": ("post_blackout.jpg", f, "image/jpeg")}
        final_response = await client.post(
            "/detect?node_id=arctic-base-01",
            files=files
        )

    assert final_response.status_code == 200
    # Should NOT be queued anymore
    assert "status" not in final_response.json() or final_response.json().get("status") != "queued"


@pytest.mark.asyncio
async def test_component_integration():
    """Test direct integration between components without HTTP layer"""
    # Test 1: Inference → Telemetry integration
    engine = InferenceEngine()
    telemetry = TelemetryGenerator(base_lat=75.0, base_lon=-110.0)

    test_image = Path(__file__).parent / "fixtures" / "test_image.jpg"

    # Run inference
    inference_result = engine.detect(str(test_image))
    assert "detections" in inference_result

    # Generate telemetry message
    message = telemetry.create_detection_message(
        inference_result,
        node_id="integration-test-01"
    )

    assert message["node_id"] == "integration-test-01"
    assert 60.0 <= message["location"]["latitude"] <= 85.0
    assert message["detection_count"] == inference_result["count"]
    assert message["model"] == inference_result["model"]

    # Test 2: Blackout controller integration
    controller = BlackoutController(db_path=":memory:")  # Use in-memory DB

    await controller.activate()
    await controller.queue_detection(message)

    queued = await controller.get_queued_detections()
    assert len(queued) == 1
    assert queued[0]["node_id"] == "integration-test-01"

    await controller.deactivate()
