"""Queue management with exponential backoff retry logic."""
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

from .database import AsyncSessionLocal
from .models import QueueItem


class QueueManager:
    """Manage message queue with database persistence."""

    def __init__(self, session_factory: Optional[Callable] = None):
        self.max_retries = 5
        self.base_retry_delay = 1  # seconds
        self._session_factory = session_factory or AsyncSessionLocal

    @asynccontextmanager
    async def _get_session(self):
        """Get database session."""
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def enqueue(self, node_id: int, payload: Dict[str, Any]) -> int:
        """
        Add message to queue.

        Args:
            node_id: Node ID
            payload: Message payload (will be stored as JSONB)

        Returns:
            Queue item ID
        """
        async with self._get_session() as session:
            queue_item = QueueItem(
                node_id=node_id,
                payload=payload,  # JSONB handles serialization automatically
                status="pending",
                retry_count=0
            )
            session.add(queue_item)
            await session.commit()
            await session.refresh(queue_item)
            return queue_item.id

    async def get_pending_items(self, node_id: int) -> List[Dict[str, Any]]:
        """Get all pending queue items for a node."""
        async with self._get_session() as session:
            result = await session.execute(
                select(QueueItem)
                .where(QueueItem.node_id == node_id)
                .where(QueueItem.status == "pending")
                .order_by(QueueItem.created_at)
            )
            items = result.scalars().all()

            return [
                {
                    "id": item.id,
                    "payload": item.payload,  # JSONB automatically deserialized
                    "retry_count": item.retry_count,
                    "created_at": item.created_at
                }
                for item in items
            ]

    async def mark_completed(self, item_id: int):
        """Mark queue item as completed."""
        async with self._get_session() as session:
            await session.execute(
                update(QueueItem)
                .where(QueueItem.id == item_id)
                .values(
                    status="completed",
                    processed_at=datetime.utcnow()
                )
            )
            await session.commit()

    async def mark_failed(self, item_id: int):
        """Mark queue item as failed and increment retry count."""
        async with self._get_session() as session:
            result = await session.execute(
                select(QueueItem).where(QueueItem.id == item_id)
            )
            item = result.scalar_one()

            item.retry_count += 1

            if item.retry_count >= self.max_retries:
                item.status = "failed"
            else:
                item.status = "pending"

            await session.commit()

    async def get_item(self, item_id: int) -> Optional[QueueItem]:
        """Get queue item by ID."""
        async with self._get_session() as session:
            result = await session.execute(
                select(QueueItem).where(QueueItem.id == item_id)
            )
            return result.scalar_one_or_none()

    async def process_queue(self, node_id: int):
        """
        Process all pending items in queue.

        Args:
            node_id: Node ID to process queue for
        """
        items = await self.get_pending_items(node_id)

        for item in items:
            # Calculate exponential backoff delay
            delay = self.base_retry_delay * (2 ** item["retry_count"])

            # Check if enough time has passed since creation
            time_since_creation = (datetime.utcnow() - item["created_at"]).total_seconds()

            if time_since_creation < delay:
                continue  # Skip, not ready yet

            try:
                # Process the message (would actually send to edge node here)
                # For now, just mark as completed
                await self.mark_completed(item["id"])
            except Exception as e:
                await self.mark_failed(item["id"])

    async def get_queue_stats(self) -> dict:
        """Get queue statistics."""
        async with self._get_session() as session:
            result = await session.execute(
                select(
                    QueueItem.status,
                    func.count(QueueItem.id).label("count")
                ).group_by(QueueItem.status)
            )
            stats = {row.status: row.count for row in result}
            return stats
