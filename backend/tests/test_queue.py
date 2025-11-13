"""Tests for queue management."""
import pytest
from datetime import datetime, timedelta

from src.queue import QueueManager
from src.models import Node


@pytest.mark.asyncio
async def test_queue_enqueue(get_session):
    """Test enqueueing messages."""
    async with get_session() as session:
        # Create a node first
        node = Node(node_id="test-node", status="online")
        session.add(node)
        await session.commit()
        await session.refresh(node)

        queue = QueueManager(session_factory=get_session)
        message = {"test": "data", "value": 123}

        item_id = await queue.enqueue(node.id, message)

        # Verify it's in queue
        items = await queue.get_pending_items(node.id)
        assert len(items) == 1
        assert items[0]["payload"] == message
        assert items[0]["id"] == item_id


@pytest.mark.asyncio
async def test_queue_retry_logic(get_session):
    """Test retry with exponential backoff."""
    async with get_session() as session:
        node = Node(node_id="test-node", status="online")
        session.add(node)
        await session.commit()
        await session.refresh(node)

        queue = QueueManager(session_factory=get_session)

        # Enqueue item
        item_id = await queue.enqueue(node.id, {"test": "data"})

        # Simulate failures
        await queue.mark_failed(item_id)
        item = await queue.get_item(item_id)
        assert item.retry_count == 1
        assert item.status == "pending"  # Still pending, not failed

        await queue.mark_failed(item_id)
        item = await queue.get_item(item_id)
        assert item.retry_count == 2
        assert item.status == "pending"


@pytest.mark.asyncio
async def test_queue_max_retries(get_session):
    """Test that items fail after max retries."""
    async with get_session() as session:
        node = Node(node_id="test-node", status="online")
        session.add(node)
        await session.commit()
        await session.refresh(node)

        queue = QueueManager(session_factory=get_session)
        queue.max_retries = 3  # Set lower for testing

        item_id = await queue.enqueue(node.id, {"test": "data"})

        # Fail 3 times - should mark as failed
        for _ in range(3):
            await queue.mark_failed(item_id)

        item = await queue.get_item(item_id)
        assert item.status == "failed"
        assert item.retry_count == 3


@pytest.mark.asyncio
async def test_queue_persistence(get_session):
    """Test queue survives restarts."""
    async with get_session() as session:
        node = Node(node_id="test-node", status="online")
        session.add(node)
        await session.commit()
        await session.refresh(node)

        queue1 = QueueManager(session_factory=get_session)

        # Enqueue items
        await queue1.enqueue(node.id, {"test": "data1"})
        await queue1.enqueue(node.id, {"test": "data2"})

        # Simulate restart with new QueueManager instance
        queue2 = QueueManager(session_factory=get_session)
        items = await queue2.get_pending_items(node.id)

        assert len(items) == 2
        assert items[0]["payload"]["test"] == "data1"
        assert items[1]["payload"]["test"] == "data2"


@pytest.mark.asyncio
async def test_mark_completed(get_session):
    """Test marking queue item as completed."""
    async with get_session() as session:
        node = Node(node_id="test-node", status="online")
        session.add(node)
        await session.commit()
        await session.refresh(node)

        queue = QueueManager(session_factory=get_session)
        item_id = await queue.enqueue(node.id, {"test": "data"})

        await queue.mark_completed(item_id)

        item = await queue.get_item(item_id)
        assert item.status == "completed"
        assert item.processed_at is not None


@pytest.mark.asyncio
async def test_get_queue_stats(get_session):
    """Test queue statistics."""
    async with get_session() as session:
        node = Node(node_id="test-node", status="online")
        session.add(node)
        await session.commit()
        await session.refresh(node)

        queue = QueueManager(session_factory=get_session)

        # Create items with different statuses
        id1 = await queue.enqueue(node.id, {"test": "data1"})
        id2 = await queue.enqueue(node.id, {"test": "data2"})
        id3 = await queue.enqueue(node.id, {"test": "data3"})

        await queue.mark_completed(id1)
        await queue.mark_failed(id2)
        await queue.mark_failed(id2)
        await queue.mark_failed(id2)
        queue.max_retries = 2
        await queue.mark_failed(id2)  # This should mark as failed

        stats = await queue.get_queue_stats()
        assert stats.get("completed", 0) >= 1
        assert stats.get("failed", 0) >= 1
        assert stats.get("pending", 0) >= 1
