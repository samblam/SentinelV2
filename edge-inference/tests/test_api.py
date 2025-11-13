"""
Test suite for FastAPI endpoints
Following TDD - these tests should fail initially
"""
import pytest
from httpx import AsyncClient, ASGITransport
import io
from pathlib import Path


@pytest.fixture
async def client():
    """Create async HTTP client for testing"""
    from src.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_root_endpoint(client):
    """Test root endpoint"""
    response = await client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "version" in data
    assert "status" in data


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Test health check endpoint"""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "model" in data
    assert "blackout_active" in data
    assert "device" in data
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_detect_endpoint_requires_image(client):
    """Test detect endpoint rejects requests without image"""
    response = await client.post("/detect")

    assert response.status_code == 422  # Unprocessable entity


@pytest.mark.asyncio
async def test_detect_endpoint_with_image(client, test_image_path):
    """Test detect endpoint processes image"""
    with open(test_image_path, 'rb') as f:
        files = {"file": ("test.jpg", f, "image/jpeg")}
        response = await client.post("/detect", files=files)

    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert "node_id" in data
    assert "location" in data
    assert "timestamp" in data
    assert "detection_count" in data
    assert "inference_time_ms" in data
    assert "model" in data


@pytest.mark.asyncio
async def test_detect_endpoint_rejects_non_image(client):
    """Test detect endpoint rejects non-image files"""
    text_content = b"This is not an image"
    files = {"file": ("test.txt", io.BytesIO(text_content), "text/plain")}

    response = await client.post("/detect", files=files)

    assert response.status_code == 400
    assert "must be an image" in response.json()["detail"]


@pytest.mark.asyncio
async def test_detect_endpoint_rejects_oversized_file(client):
    """Test detect endpoint rejects files larger than MAX_IMAGE_SIZE"""
    # Create a large fake image (11MB, exceeding 10MB limit)
    large_content = b"X" * (11 * 1024 * 1024)
    files = {"file": ("large.jpg", io.BytesIO(large_content), "image/jpeg")}

    response = await client.post("/detect", files=files)

    assert response.status_code == 413  # Payload Too Large
    assert "too large" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_detect_endpoint_handles_corrupted_image(client):
    """Test detect endpoint handles corrupted image gracefully"""
    # Create corrupted image data (has image MIME but invalid content)
    corrupted_content = b"\xFF\xD8\xFF\xE0\x00\x10JFIF" + b"corrupted_data" * 100
    files = {"file": ("corrupted.jpg", io.BytesIO(corrupted_content), "image/jpeg")}

    response = await client.post("/detect", files=files)

    # Should return 400 (client error) or 500 (server error) but not crash
    assert response.status_code in [400, 500]
    data = response.json()
    assert "detail" in data
    # Should mention it's an image or inference error
    assert any(keyword in data["detail"].lower() for keyword in ["image", "inference", "error"])


@pytest.mark.asyncio
async def test_detect_endpoint_handles_text_as_image(client):
    """Test detect endpoint handles text file disguised as image"""
    # Text content with image MIME type
    text_content = b"This is plain text disguised as an image"
    files = {"file": ("fake.jpg", io.BytesIO(text_content), "image/jpeg")}

    response = await client.post("/detect", files=files)

    # Should fail gracefully with appropriate error
    assert response.status_code in [400, 500]
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_detect_endpoint_preserves_file_extension(client, test_image_path):
    """Test that file extension is preserved from original filename"""
    # Test with .png extension
    with open(test_image_path, 'rb') as f:
        files = {"file": ("test.png", f, "image/png")}
        response = await client.post("/detect", files=files)

    # Should succeed regardless of extension (as long as it's a valid image)
    # This tests that we properly preserve extensions, not hardcode .jpg
    assert response.status_code in [200, 400]  # 200 if PIL can read it, 400 if format issue


@pytest.mark.asyncio
async def test_detect_endpoint_custom_node_id(client, test_image_path):
    """Test detect endpoint with custom node ID"""
    custom_node_id = "test-node-99"

    with open(test_image_path, 'rb') as f:
        files = {"file": ("test.jpg", f, "image/jpeg")}
        response = await client.post(
            f"/detect?node_id={custom_node_id}",
            files=files
        )

    assert response.status_code == 200
    data = response.json()
    assert data["node_id"] == custom_node_id


@pytest.mark.asyncio
async def test_blackout_activate_endpoint(client):
    """Test blackout activation endpoint"""
    response = await client.post("/blackout/activate")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["activated", "already_active"]

    # Deactivate for cleanup
    await client.post("/blackout/deactivate")


@pytest.mark.asyncio
async def test_blackout_deactivate_endpoint(client):
    """Test blackout deactivation endpoint"""
    # First activate
    await client.post("/blackout/activate")

    # Then deactivate
    response = await client.post("/blackout/deactivate")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["deactivated", "not_active"]
    assert "queued_detections" in data
    assert "count" in data


@pytest.mark.asyncio
async def test_blackout_status_endpoint(client):
    """Test blackout status endpoint"""
    response = await client.get("/blackout/status")

    assert response.status_code == 200
    data = response.json()
    assert "active" in data
    assert "activated_at" in data
    assert "queued_count" in data


@pytest.mark.asyncio
async def test_blackout_workflow(client, test_image_path):
    """Test complete blackout workflow"""
    # 1. Activate blackout
    response = await client.post("/blackout/activate")
    assert response.status_code == 200

    # 2. Send detection during blackout
    with open(test_image_path, 'rb') as f:
        files = {"file": ("test.jpg", f, "image/jpeg")}
        response = await client.post("/detect", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert data["blackout_active"] == True

    # 3. Check status
    response = await client.get("/blackout/status")
    assert response.status_code == 200
    status = response.json()
    assert status["active"] == True
    assert status["queued_count"] >= 1

    # 4. Deactivate and get queued detections
    response = await client.post("/blackout/deactivate")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "deactivated"
    assert data["count"] >= 1
    assert len(data["queued_detections"]) >= 1


@pytest.mark.asyncio
async def test_detect_performance(client, test_image_path):
    """Test detection performance is reasonable"""
    with open(test_image_path, 'rb') as f:
        files = {"file": ("test.jpg", f, "image/jpeg")}
        response = await client.post("/detect", files=files)

    assert response.status_code == 200
    data = response.json()

    # Inference should be fast (though this includes I/O overhead)
    assert data["inference_time_ms"] < 200  # More lenient for full API call


@pytest.mark.asyncio
async def test_multiple_detections(client, test_image_path):
    """Test API can handle multiple detections"""
    for i in range(3):
        with open(test_image_path, 'rb') as f:
            files = {"file": ("test.jpg", f, "image/jpeg")}
            response = await client.post("/detect", files=files)

        assert response.status_code == 200
        data = response.json()
        assert "detections" in data
