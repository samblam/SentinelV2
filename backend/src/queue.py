"""Queue management with exponential backoff retry logic."""
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone, timedelta
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
            # Calculate initial next_attempt_at based on base delay
            next_attempt = datetime.now(timezone.utc) + timedelta(seconds=self.base_retry_delay)

            queue_item = QueueItem(
                node_id=node_id,
                payload=payload,  # JSONB handles serialization automatically
                status="pending",
                retry_count=0,
                next_attempt_at=next_attempt
            )
            session.add(queue_item)
            await session.flush()  # Flush to assign ID before refresh
            await session.refresh(queue_item)
            return queue_item.id

    async def get_pending_items(self, node_id: int, for_update: bool = False) -> List[Dict[str, Any]]:
        """Get all pending queue items for a node.

        Args:
            node_id: Node ID to get items for
            for_update: If True, use row-level locking with SKIP LOCKED for concurrent processing

        Returns:
            List of pending queue items
        """
        async with self._get_session() as session:
            query = (
                select(QueueItem)
                .where(QueueItem.node_id == node_id)
                .where(QueueItem.status == "pending")
                .order_by(QueueItem.created_at)
            )

            # Add row-level locking for concurrent processing
            if for_update:
                query = query.with_for_update(skip_locked=True)

            result = await session.execute(query)
            items = result.scalars().all()

            return [
                {
                    "id": item.id,
                    "payload": item.payload,  # JSONB automatically deserialized
                    "retry_count": item.retry_count,
                    "created_at": item.created_at,
                    "next_attempt_at": item.next_attempt_at
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
                    processed_at=datetime.now(timezone.utc)
                )
            )
    async def mark_failed(self, item_id: int):
        """Mark queue item as failed and increment retry count."""
        async with self._get_session() as session:
            result = await session.execute(
                select(QueueItem).where(QueueItem.id == item_id)
            )
            item = result.scalar_one()

            item.retry_count += 1
            item.status = "failed" if item.retry_count >= self.max_retries else "pending"

            # Calculate next attempt time using exponential backoff
            if item.status == "pending":
                delay_seconds = self.base_retry_delay * (2 ** item.retry_count)
                item.next_attempt_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
            else:
                item.next_attempt_at = None  # Failed permanently, no retry

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
        items = await self.get_pending_items(node_id, for_update=True)

        for item in items:
            # Check if the item is ready to be retried
            if item["next_attempt_at"] is not None:
                next_attempt = item["next_attempt_at"]
                # Ensure timezone-aware comparison (SQLite stores naive datetimes)
                if next_attempt.tzinfo is None:
                    next_attempt = next_attempt.replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) < next_attempt:
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
            return {row.status: row.count for row in result}
