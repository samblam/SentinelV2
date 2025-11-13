"""Tests for edge cases and error handling."""
import pytest
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone

from src.main import app
from src.models import Node
from src.queue import QueueManager
from src.websocket import ConnectionManager


@pytest.mark.asyncio
async def test_heartbeat_nonexistent_node(test_engine, get_session):
    """Test heartbeat for nonexistent node."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/nodes/nonexistent-node/heartbeat")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_node_status_nonexistent(test_engine, get_session):
    """Test getting status of nonexistent node."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/nodes/nonexistent-node/status")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_activate_blackout_nonexistent_node(test_engine, get_session):
    """Test activating blackout for nonexistent node."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/blackout/activate",
            json={"node_id": "nonexistent"}
        )
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_activate_blackout_already_active(test_engine, get_session):
    """Test activating blackout when already active."""
    async with get_session() as session:
        node = Node(node_id="test-node", status="covert")
        session.add(node)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/blackout/activate",
            json={"node_id": "test-node"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "already_active"


@pytest.mark.asyncio
async def test_deactivate_blackout_nonexistent_node(test_engine, get_session):
    """Test deactivating blackout for nonexistent node."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/blackout/deactivate",
            json={"node_id": "nonexistent"}
        )
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_deactivate_blackout_not_active(test_engine, get_session):
    """Test deactivating blackout when not active."""
    async with get_session() as session:
        node = Node(node_id="test-node", status="online")
        session.add(node)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/blackout/deactivate",
            json={"node_id": "test-node"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_active"


@pytest.mark.asyncio
async def test_get_detections_pagination_edge_cases(test_engine, get_session):
    """Test detection pagination with various limits and offsets."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test with large limit
        response = await client.get("/api/detections?limit=1000&offset=0")
        assert response.status_code == 200

        # Test with offset beyond available records
        response = await client.get("/api/detections?limit=10&offset=10000")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


@pytest.mark.asyncio
async def test_queue_exponential_backoff(get_session):
    """Test exponential backoff calculation in queue."""
    queue = QueueManager(session_factory=get_session)

    # Create a node and queue item
    async with get_session() as session:
        node = Node(node_id="test-node", status="online")
        session.add(node)
        await session.commit()
        await session.refresh(node)
        node_id = node.id

    item_id = await queue.enqueue(node_id, {"test": "data"})

    # Test retry delays
    for i in range(3):
        await queue.mark_failed(item_id)
        item = await queue.get_item(item_id)
        assert item.retry_count == i + 1
        # Verify item is still pending (not failed yet)
        assert item.status == "pending"


@pytest.mark.asyncio
async def test_queue_get_item(get_session):
    """Test getting individual queue item."""
    queue = QueueManager(session_factory=get_session)

    async with get_session() as session:
        node = Node(node_id="test-node", status="online")
        session.add(node)
        await session.commit()
        await session.refresh(node)
        node_id = node.id

    item_id = await queue.enqueue(node_id, {"test": "data"})
    item = await queue.get_item(item_id)

    assert item is not None
    assert item.id == item_id
    assert item.payload["test"] == "data"


def test_websocket_manager_initialization():
    """Test WebSocket manager initialization."""
    manager = ConnectionManager()
    assert manager.active_connections == {}
    assert len(manager.active_connections) == 0


@pytest.mark.asyncio
async def test_detection_with_all_optional_fields(test_engine, get_session):
    """Test detection ingestion with all optional fields."""
    async with get_session() as session:
        node = Node(node_id="test-node", status="online")
        session.add(node)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/detections",
            json={
                "node_id": "test-node",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "location": {
                    "latitude": 37.7749,
                    "longitude": -122.4194,
                    "altitude_m": 100.5,
                    "accuracy_m": 5.0
                },
                "detections": [{"class": "person", "confidence": 0.95}],
                "detection_count": 1,
                "inference_time_ms": 42.5,
                "model": "yolov8n"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["detection_count"] == 1


@pytest.mark.asyncio
async def test_websocket_without_client_id(test_engine):
    """Test WebSocket connection without client_id."""
    from starlette.testclient import TestClient

    with TestClient(app) as client:
        # Attempt to connect without client_id should fail
        with pytest.raises(Exception):
            with client.websocket_connect("/ws"):
                pass


@pytest.mark.asyncio
async def test_pagination_with_zero_limit(test_engine, get_session):
    """Test detection pagination with zero limit."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test with limit=0 (should fail validation)
        response = await client.get("/api/detections?limit=0&offset=0")
        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_pagination_with_negative_limit(test_engine, get_session):
    """Test detection pagination with negative limit."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test with negative limit (should fail validation)
        response = await client.get("/api/detections?limit=-10&offset=0")
        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_failed_queue_items_not_reprocessed(get_session):
    """Test that permanently failed queue items are not reprocessed."""
    queue = QueueManager(session_factory=get_session)
    queue.max_retries = 2  # Set low max for testing

    async with get_session() as session:
        node = Node(node_id="test-node", status="online")
        session.add(node)
        await session.commit()
        await session.refresh(node)
        node_id = node.id

    # Enqueue an item
    item_id = await queue.enqueue(node_id, {"test": "permanent_failure"})

    # Fail it until it's permanently failed
    await queue.mark_failed(item_id)  # retry_count = 1, status = pending
    await queue.mark_failed(item_id)  # retry_count = 2, status = failed

    # Verify status is failed
    item = await queue.get_item(item_id)
    assert item.status == "failed"
    assert item.retry_count >= queue.max_retries

    # Get pending items should not include this failed item
    pending_items = await queue.get_pending_items(node_id)
    assert len(pending_items) == 0


@pytest.mark.asyncio
async def test_queue_processing_with_exception(get_session):
    """Test queue processing handles exceptions properly."""
    from unittest.mock import patch

    queue = QueueManager(session_factory=get_session)
    queue.base_retry_delay = 0  # No delay for testing

    async with get_session() as session:
        node = Node(node_id="error-test-node", status="online")
        session.add(node)
        await session.commit()
        await session.refresh(node)
        node_id = node.id

    # Enqueue an item
    item_id = await queue.enqueue(node_id, {"test": "error_handling"})

    # Mock mark_completed to raise an exception
    with patch.object(queue, 'mark_completed', side_effect=Exception("Simulated error")):
        # Process queue should handle the exception by calling mark_failed
        await queue.process_queue(node_id)

    # Item should have been marked as failed
    item = await queue.get_item(item_id)
    assert item.retry_count == 1
    assert item.status == "pending"  # Still pending because retry_count < max_retries
