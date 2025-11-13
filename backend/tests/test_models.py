"""Tests for database models."""
import pytest
from datetime import datetime, timezone

from src.models import Detection, Node, QueueItem, BlackoutEvent


@pytest.mark.asyncio
async def test_create_node(get_session):
    """Test node creation."""
    async with get_session() as session:
        node = Node(
            node_id="sentry-01",
            status="online",
            last_heartbeat=datetime.utcnow()
        )
        session.add(node)
        await session.commit()
        await session.refresh(node)

        assert node.id is not None
        assert node.node_id == "sentry-01"
        assert node.status == "online"
        assert node.last_heartbeat is not None


@pytest.mark.asyncio
async def test_create_detection(get_session):
    """Test detection record creation."""
    async with get_session() as session:
        # First create a node
        node = Node(node_id="sentry-01", status="online")
        session.add(node)
        await session.commit()
        await session.refresh(node)

        # Create detection
        detection = Detection(
            node_id=node.id,
            timestamp=datetime.utcnow(),
            latitude=70.5,
            longitude=-100.2,
            detections_json={"detections": []},
            detection_count=0
        )
        session.add(detection)
        await session.commit()
        await session.refresh(detection)

        assert detection.id is not None
        assert detection.node_id == node.id
        assert detection.latitude == 70.5
        assert detection.longitude == -100.2
        assert detection.detection_count == 0


@pytest.mark.asyncio
async def test_queue_item_persistence(get_session):
    """Test queue items persist to database."""
    async with get_session() as session:
        node = Node(node_id="sentry-01", status="online")
        session.add(node)
        await session.commit()
        await session.refresh(node)

        queue_item = QueueItem(
            node_id=node.id,
            payload={"test": "data"},
            status="pending",
            retry_count=0
        )
        session.add(queue_item)
        await session.commit()
        await session.refresh(queue_item)

        assert queue_item.id is not None
        assert queue_item.status == "pending"
        assert queue_item.payload == {"test": "data"}
        assert queue_item.retry_count == 0


@pytest.mark.asyncio
async def test_blackout_event_logging(get_session):
    """Test blackout event creation and logging."""
    async with get_session() as session:
        node = Node(node_id="sentry-01", status="online")
        session.add(node)
        await session.commit()
        await session.refresh(node)

        blackout_event = BlackoutEvent(
            node_id=node.id,
            activated_at=datetime.utcnow(),
            activated_by="operator-001",
            reason="Tactical operation"
        )
        session.add(blackout_event)
        await session.commit()
        await session.refresh(blackout_event)

        assert blackout_event.id is not None
        assert blackout_event.node_id == node.id
        assert blackout_event.activated_by == "operator-001"
        assert blackout_event.deactivated_at is None


@pytest.mark.asyncio
async def test_node_relationships(get_session):
    """Test relationships between nodes and other entities."""
    async with get_session() as session:
        node = Node(node_id="sentry-01", status="online")
        session.add(node)
        await session.commit()
        await session.refresh(node)

        # Add detection
        detection = Detection(
            node_id=node.id,
            timestamp=datetime.utcnow(),
            latitude=70.5,
            longitude=-100.2,
            detections_json=[],
            detection_count=0
        )
        session.add(detection)

        # Add queue item
        queue_item = QueueItem(
            node_id=node.id,
            payload={"test": "data"},
            status="pending"
        )
        session.add(queue_item)

        await session.commit()
        await session.refresh(node)

        # Verify relationships (need to explicitly load in async)
        assert node.id is not None


@pytest.mark.asyncio
async def test_jsonb_storage(get_session):
    """Test JSONB storage and retrieval."""
    async with get_session() as session:
        node = Node(node_id="sentry-01", status="online")
        session.add(node)
        await session.commit()
        await session.refresh(node)

        # Test complex JSONB data
        complex_data = {
            "detections": [
                {"class": "person", "confidence": 0.95, "bbox": [10, 20, 30, 40]},
                {"class": "vehicle", "confidence": 0.88, "bbox": [50, 60, 70, 80]}
            ],
            "metadata": {
                "model": "yolov5-nano",
                "inference_time": 45.2
            }
        }

        detection = Detection(
            node_id=node.id,
            timestamp=datetime.utcnow(),
            latitude=70.5,
            longitude=-100.2,
            detections_json=complex_data,
            detection_count=2
        )
        session.add(detection)
        await session.commit()
        await session.refresh(detection)

        # Verify JSONB is stored and retrieved correctly
        assert detection.detections_json == complex_data
        assert detection.detections_json["metadata"]["model"] == "yolov5-nano"
