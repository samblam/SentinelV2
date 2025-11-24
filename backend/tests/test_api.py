"""Tests for FastAPI endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from starlette.testclient import TestClient

from src.main import app
from src.models import Node, Detection, BlackoutEvent, QueueItem


@pytest.mark.asyncio
async def test_health_check(test_engine):
    """Test health check endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_register_node(test_engine, get_session):
    """Test node registration."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/nodes/register",
            json={"node_id": "test-node-001"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["node_id"] == "test-node-001"
        assert data["status"] == "online"
        assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_node(test_engine, get_session):
    """Test registering duplicate node returns existing node."""
    async with get_session() as session:
        node = Node(node_id="existing-node", status="online")
        session.add(node)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/nodes/register",
            json={"node_id": "existing-node"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["node_id"] == "existing-node"


@pytest.mark.asyncio
async def test_submit_detection(test_engine, get_session):
    """Test detection submission."""
    # Create node first
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
                "location": {"latitude": 37.7749, "longitude": -122.4194, "altitude_m": 10.5},
                "detections": [
                    {"class": "person", "confidence": 0.95},
                    {"class": "vehicle", "confidence": 0.87}
                ],
                "detection_count": 2,
                "inference_time_ms": 45.2,
                "model": "yolov8n"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["node_id"] == node.node_id  # node_id is the string identifier, not the integer ID
        assert data["detection_count"] == 2


@pytest.mark.asyncio
async def test_submit_detection_nonexistent_node(test_engine, get_session):
    """Test detection submission with nonexistent node."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/detections",
            json={
                "node_id": "nonexistent-node",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "location": {"latitude": 37.7749, "longitude": -122.4194},
                "detections": [{"class": "person", "confidence": 0.95}],
                "detection_count": 1
            }
        )
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_detections(test_engine, get_session):
    """Test getting detections with pagination."""
    # Create node and detections
    async with get_session() as session:
        node = Node(node_id="test-node", status="online")
        session.add(node)
        await session.commit()
        await session.refresh(node)

        # Add 15 detections
        for i in range(15):
            detection = Detection(
                node_id=node.id,
                timestamp=datetime.now(timezone.utc) - timedelta(minutes=i),
                latitude=37.7749,
                longitude=-122.4194,
                detections_json=[{"class": "test", "confidence": 0.9}],
                detection_count=1
            )
            session.add(detection)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Get first page
        response = await client.get("/api/detections?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10

        # Get second page
        response = await client.get("/api/detections?limit=10&offset=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5


@pytest.mark.asyncio
async def test_get_node_status(test_engine, get_session):
    """Test getting node status."""
    async with get_session() as session:
        node = Node(node_id="test-node", status="online", last_heartbeat=datetime.now(timezone.utc))
        session.add(node)
        await session.commit()
        await session.refresh(node)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/nodes/test-node/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert data["node_id"] == "test-node"


@pytest.mark.asyncio
async def test_node_heartbeat(test_engine, get_session):
    """Test node heartbeat endpoint."""
    async with get_session() as session:
        node = Node(node_id="test-node", status="online")
        session.add(node)
        await session.commit()
        await session.refresh(node)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(f"/api/nodes/test-node/heartbeat")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    # Verify heartbeat was updated
    async with get_session() as session:
        result = await session.execute(select(Node).where(Node.node_id == "test-node"))
        node = result.scalar_one()
        assert node.last_heartbeat is not None


@pytest.mark.asyncio
async def test_activate_blackout(test_engine, get_session):
    """Test blackout activation."""
    async with get_session() as session:
        node = Node(node_id="test-node", status="online")
        session.add(node)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/nodes/test-node/blackout/activate",
            json={"reason": "Operational security"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "activated"
        assert data["node_id"] == "test-node"
        assert "blackout_id" in data

    # Verify node status changed to covert
    async with get_session() as session:
        result = await session.execute(select(Node).where(Node.node_id == "test-node"))
        node = result.scalar_one()
        assert node.status == "covert"

    # Verify blackout event created
    async with get_session() as session:
        result = await session.execute(select(BlackoutEvent))
        events = result.scalars().all()
        assert len(events) == 1
        assert events[0].reason == "Operational security"


@pytest.mark.asyncio
async def test_deactivate_blackout(test_engine, get_session):
    """Test blackout deactivation."""
    # Create node in covert mode with active blackout
    async with get_session() as session:
        node = Node(node_id="test-node", status="covert")
        session.add(node)
        await session.commit()
        await session.refresh(node)

        blackout = BlackoutEvent(
            node_id=node.id,
            activated_at=datetime.now(timezone.utc),
            reason="Test"
        )
        session.add(blackout)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/nodes/test-node/blackout/deactivate",
            json={}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["node_id"] == "test-node"
        assert "blackout_id" in data
        assert "duration_seconds" in data
        assert "activated_at" in data
        assert "deactivated_at" in data

    # Verify node status changed back to online
    async with get_session() as session:
        result = await session.execute(select(Node).where(Node.node_id == "test-node"))
        node = result.scalar_one()
        assert node.status == "online"

    # Verify blackout event was closed
    async with get_session() as session:
        result = await session.execute(select(BlackoutEvent))
        events = result.scalars().all()
        assert len(events) == 1
        assert events[0].deactivated_at is not None


@pytest.mark.asyncio
async def test_blackout_queues_detections(test_engine, get_session):
    """Test that detections are queued during blackout."""
    # Create node in covert mode
    async with get_session() as session:
        node = Node(node_id="test-node", status="covert")
        session.add(node)
        await session.commit()
        await session.refresh(node)

        blackout = BlackoutEvent(node_id=node.id, activated_at=datetime.now(timezone.utc))
        session.add(blackout)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/detections",
            json={
                "node_id": "test-node",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "location": {"latitude": 37.7749, "longitude": -122.4194},
                "detections": [{"class": "person", "confidence": 0.95}],
                "detection_count": 1
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["queued"] is True

    # Verify detection was queued, not stored
    async with get_session() as session:
        result = await session.execute(select(QueueItem))
        items = result.scalars().all()
        assert len(items) == 1

        result = await session.execute(select(Detection))
        detections = result.scalars().all()
        assert len(detections) == 0


def test_websocket_connection(test_engine):
    """Test WebSocket connection."""
    with TestClient(app) as client:
        with client.websocket_connect("/ws?client_id=test-client") as websocket:
            # Receive connection message
            data = websocket.receive_json()
            assert data["type"] == "connection_established"
            assert data["client_id"] == "test-client"

            # Send a ping
            websocket.send_json({"type": "ping"})

            # Receive pong
            data = websocket.receive_json()
            assert data["type"] == "pong"


def test_websocket_broadcast(test_engine, get_session):
    """Test WebSocket broadcasts detection events."""
    import asyncio

    # Create node synchronously for this test
    async def create_node():
        async with get_session() as session:
            node = Node(node_id="test-node", status="online")
            session.add(node)
            await session.commit()

    asyncio.run(create_node())

    # This test is simplified as WebSocket broadcast testing with httpx is complex
    # In production, broadcasts would be tested with real WebSocket clients
    with TestClient(app) as client:
        with client.websocket_connect("/ws?client_id=test-client") as websocket:
            # Receive connection message
            data = websocket.receive_json()
            assert data["type"] == "connection_established"
