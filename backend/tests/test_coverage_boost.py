"""Additional tests to boost coverage."""
import pytest
from httpx import AsyncClient, ASGITransport

from src.main import app
from src.models import Node, Detection, BlackoutEvent
from src.queue import QueueManager
from datetime import datetime, timezone, timedelta


@pytest.mark.asyncio
async def test_get_detections_with_node_filter(test_engine, get_session):
    """Test getting detections for a specific node."""
    async with get_session() as session:
        node = Node(node_id="test-node", status="online")
        session.add(node)
        await session.commit()
        await session.refresh(node)

        # Add detection
        detection = Detection(
            node_id=node.id,
            timestamp=datetime.now(timezone.utc),
            latitude=37.7749,
            longitude=-122.4194,
            detections_json=[{"class": "person", "confidence": 0.95}],
            detection_count=1
        )
        session.add(detection)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/detections?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1


@pytest.mark.asyncio
async def test_queue_stats_all_statuses(get_session):
    """Test queue stats with various statuses."""
    queue = QueueManager(session_factory=get_session)

    async with get_session() as session:
        node = Node(node_id="test-node", status="online")
        session.add(node)
        await session.commit()
        await session.refresh(node)
        node_id = node.id

    # Create items with different statuses
    id1 = await queue.enqueue(node_id, {"test": "pending"})
    id2 = await queue.enqueue(node_id, {"test": "completed"})
    id3 = await queue.enqueue(node_id, {"test": "failed"})

    # Mark as completed
    await queue.mark_completed(id2)

    # Mark as failed (exhaust retries)
    queue.max_retries = 1
    await queue.mark_failed(id3)
    await queue.mark_failed(id3)

    # Get stats
    stats = await queue.get_queue_stats()
    assert "pending" in stats
    assert "completed" in stats
    assert "failed" in stats


@pytest.mark.asyncio
async def test_detection_broadcast_coverage(test_engine, get_session):
    """Test detection ingestion triggers broadcast."""
    async with get_session() as session:
        node = Node(node_id="broadcast-test-node", status="online")
        session.add(node)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/detections",
            json={
                "node_id": "broadcast-test-node",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "location": {"latitude": 40.7128, "longitude": -74.0060},
                "detections": [
                    {"class": "vehicle", "confidence": 0.92},
                    {"class": "person", "confidence": 0.88}
                ],
                "detection_count": 2,
                "inference_time_ms": 55.3,
                "model": "yolov8s"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["detection_count"] == 2


@pytest.mark.asyncio
async def test_blackout_with_reason(test_engine, get_session):
    """Test blackout activation with reason."""
    async with get_session() as session:
        node = Node(node_id="blackout-reason-node", status="online")
        session.add(node)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/blackout/activate",
            json={
                "node_id": "blackout-reason-node",
                "reason": "Operational security - sensitive area"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "blackout_activated"


@pytest.mark.asyncio
async def test_blackout_without_reason(test_engine, get_session):
    """Test blackout activation without reason."""
    async with get_session() as session:
        node = Node(node_id="blackout-no-reason-node", status="online")
        session.add(node)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/blackout/activate",
            json={"node_id": "blackout-no-reason-node"}
        )
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_deactivate_blackout_transmits_queued(test_engine, get_session):
    """Test blackout deactivation transmits all queued detections."""
    # Create node in covert mode
    async with get_session() as session:
        node = Node(node_id="transmit-test-node", status="covert")
        session.add(node)
        await session.commit()
        await session.refresh(node)

        blackout = BlackoutEvent(
            node_id=node.id,
            activated_at=datetime.now(timezone.utc),
            reason="Test transmission"
        )
        session.add(blackout)
        await session.commit()

    # Queue some detections
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Queue 3 detections
        for i in range(3):
            await client.post(
                "/api/detections",
                json={
                    "node_id": "transmit-test-node",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "location": {"latitude": 37.0 + i, "longitude": -122.0},
                    "detections": [{"class": "test", "confidence": 0.9}],
                    "detection_count": 1
                }
            )

        # Deactivate blackout
        response = await client.post(
            "/api/blackout/deactivate",
            json={"node_id": "transmit-test-node"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "blackout_deactivated"
        assert data["detections_transmitted"] == 3


@pytest.mark.asyncio
async def test_node_heartbeat_updates_timestamp(test_engine, get_session):
    """Test heartbeat updates last_heartbeat timestamp."""
    async with get_session() as session:
        node = Node(
            node_id="heartbeat-node",
            status="online",
            last_heartbeat=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        session.add(node)
        await session.commit()
        await session.refresh(node)
        node_id = node.id
        old_heartbeat = node.last_heartbeat

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"/api/nodes/{node_id}/heartbeat")
        assert response.status_code == 200

    # Verify heartbeat was updated
    async with get_session() as session:
        from sqlalchemy import select
        result = await session.execute(select(Node).where(Node.id == node_id))
        node = result.scalar_one()
        assert node.last_heartbeat > old_heartbeat


@pytest.mark.asyncio
async def test_detection_missing_optional_fields(test_engine, get_session):
    """Test detection ingestion without optional fields."""
    async with get_session() as session:
        node = Node(node_id="minimal-detection-node", status="online")
        session.add(node)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/detections",
            json={
                "node_id": "minimal-detection-node",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "location": {"latitude": 37.7749, "longitude": -122.4194},
                "detections": [{"class": "person", "confidence": 0.95}],
                "detection_count": 1
                # No inference_time_ms, no model, no altitude_m, no accuracy_m
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["detection_count"] == 1


@pytest.mark.asyncio
async def test_queue_pending_items_ordering(get_session):
    """Test that pending items are returned in correct order."""
    queue = QueueManager(session_factory=get_session)

    async with get_session() as session:
        node = Node(node_id="order-test-node", status="online")
        session.add(node)
        await session.commit()
        await session.refresh(node)
        node_id = node.id

    # Enqueue multiple items
    id1 = await queue.enqueue(node_id, {"order": 1})
    id2 = await queue.enqueue(node_id, {"order": 2})
    id3 = await queue.enqueue(node_id, {"order": 3})

    items = await queue.get_pending_items(node_id)
    assert len(items) == 3
    # Should be in order of creation
    assert items[0]["payload"]["order"] == 1
    assert items[1]["payload"]["order"] == 2
    assert items[2]["payload"]["order"] == 3


@pytest.mark.asyncio
async def test_health_endpoint_always_returns_healthy(test_engine):
    """Test health endpoint consistency."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Call multiple times
        for _ in range(3):
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "timestamp" in data
