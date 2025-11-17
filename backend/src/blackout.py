"""
Blackout Mode Coordination
Manages tactical deception through covert surveillance operations
"""
from enum import Enum
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from .models import Node, BlackoutEvent


class BlackoutState(Enum):
    """Blackout mode states"""
    NORMAL = "normal"              # Standard operation
    ACTIVATING = "activating"      # Transition to blackout
    ACTIVE = "active"              # In blackout mode (covert)
    DEACTIVATING = "deactivating"  # Transition back to normal
    RESUMING = "resuming"          # Burst transmission in progress


class BlackoutCoordinator:
    """Coordinate blackout mode across system"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def activate_blackout(
        self,
        node_id: str,
        operator_id: Optional[str] = None,
        reason: Optional[str] = None
    ) -> BlackoutEvent:
        """
        Activate blackout mode for a node.

        Args:
            node_id: Edge node identifier
            operator_id: ID of operator activating blackout
            reason: Tactical justification for blackout

        Returns:
            BlackoutEvent record

        Raises:
            ValueError: If node not found or already in blackout
        """
        # Get node
        result = await self.db.execute(
            select(Node).where(Node.node_id == node_id)
        )
        node = result.scalar_one_or_none()

        if not node:
            raise ValueError(f"Node not found: {node_id}")

        if node.status == "covert":
            raise ValueError(f"Node already in blackout: {node_id}")

        # Create blackout event
        blackout_event = BlackoutEvent(
            node_id=node.id,
            activated_at=datetime.now(timezone.utc),
            activated_by=operator_id,
            reason=reason
        )
        self.db.add(blackout_event)

        # Update node status
        node.status = "covert"

        await self.db.commit()
        await self.db.refresh(blackout_event)

        return blackout_event

    async def deactivate_blackout(
        self,
        node_id: str
    ) -> dict:
        """
        Deactivate blackout mode for a node.

        Args:
            node_id: Edge node identifier

        Returns:
            Summary of blackout event

        Raises:
            ValueError: If node not found or not in blackout
        """
        # Get node
        result = await self.db.execute(
            select(Node).where(Node.node_id == node_id)
        )
        node = result.scalar_one_or_none()

        if not node:
            raise ValueError(f"Node not found: {node_id}")

        if node.status != "covert":
            raise ValueError(f"Node not in blackout: {node_id}")

        # Get active blackout event
        result = await self.db.execute(
            select(BlackoutEvent)
            .where(BlackoutEvent.node_id == node.id)
            .where(BlackoutEvent.deactivated_at.is_(None))
            .order_by(desc(BlackoutEvent.activated_at))
        )
        event = result.scalar_one_or_none()

        if not event:
            raise ValueError(f"No active blackout event for node: {node_id}")

        # Update blackout event
        now = datetime.now(timezone.utc)
        event.deactivated_at = now

        # Ensure activated_at is timezone-aware (handle both aware and naive datetimes)
        activated_at = event.activated_at
        if activated_at.tzinfo is None:
            # If naive, assume UTC
            activated_at = activated_at.replace(tzinfo=timezone.utc)

        event.duration_seconds = int((now - activated_at).total_seconds())

        # Update node status to resuming (temporary during burst transmission)
        node.status = "resuming"

        await self.db.commit()

        return {
            "node_id": node_id,
            "blackout_id": event.id,
            "activated_at": event.activated_at.isoformat(),
            "deactivated_at": event.deactivated_at.isoformat(),
            "duration_seconds": event.duration_seconds,
            "detections_queued": event.detections_queued
        }

    async def update_detection_count(
        self,
        node_id: str,
        count: int
    ):
        """
        Update queued detection count for active blackout.

        Args:
            node_id: Edge node identifier
            count: Number of detections queued
        """
        result = await self.db.execute(
            select(Node).where(Node.node_id == node_id)
        )
        node = result.scalar_one_or_none()

        if not node or node.status != "covert":
            return

        # Update active blackout event
        result = await self.db.execute(
            select(BlackoutEvent)
            .where(BlackoutEvent.node_id == node.id)
            .where(BlackoutEvent.deactivated_at.is_(None))
            .order_by(desc(BlackoutEvent.activated_at))
        )
        event = result.scalar_one_or_none()

        if event:
            event.detections_queued = count
            await self.db.commit()

    async def complete_resumption(
        self,
        node_id: str,
        transmitted_count: int
    ):
        """
        Mark blackout resumption as complete.

        Args:
            node_id: Edge node identifier
            transmitted_count: Number of detections transmitted
        """
        result = await self.db.execute(
            select(Node).where(Node.node_id == node_id)
        )
        node = result.scalar_one_or_none()

        if not node:
            return

        # Update blackout event
        result = await self.db.execute(
            select(BlackoutEvent)
            .where(BlackoutEvent.node_id == node.id)
            .where(BlackoutEvent.deactivated_at.is_not(None))
            .order_by(desc(BlackoutEvent.deactivated_at))
        )
        event = result.scalar_one_or_none()

        if event:
            event.detections_transmitted = transmitted_count

        # Update node status back to online
        node.status = "online"

        await self.db.commit()

    async def get_blackout_status(
        self,
        node_id: str
    ) -> dict:
        """
        Get current blackout status for a node.

        Args:
            node_id: Edge node identifier

        Returns:
            Blackout status information
        """
        result = await self.db.execute(
            select(Node).where(Node.node_id == node_id)
        )
        node = result.scalar_one_or_none()

        if not node:
            return {"status": "node_not_found"}

        if node.status != "covert":
            return {
                "status": "inactive",
                "node_status": node.status
            }

        # Get active blackout event
        result = await self.db.execute(
            select(BlackoutEvent)
            .where(BlackoutEvent.node_id == node.id)
            .where(BlackoutEvent.deactivated_at.is_(None))
            .order_by(desc(BlackoutEvent.activated_at))
        )
        event = result.scalar_one_or_none()

        if not event:
            return {"status": "error", "message": "Node in covert status but no event found"}

        duration = (datetime.now(timezone.utc) - event.activated_at).total_seconds()

        return {
            "status": "active",
            "blackout_id": event.id,
            "activated_at": event.activated_at.isoformat(),
            "duration_seconds": int(duration),
            "detections_queued": event.detections_queued,
            "activated_by": event.activated_by,
            "reason": event.reason
        }

    async def recover_stuck_resuming_nodes(
        self,
        timeout_minutes: int = 5
    ) -> List[dict]:
        """
        Detect and recover nodes stuck in 'resuming' state.

        If a node has been in 'resuming' state for longer than the timeout,
        force it back to 'online' status.

        Args:
            timeout_minutes: Maximum time a node should stay in 'resuming' state

        Returns:
            List of recovered nodes with details
        """
        timeout_threshold = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)

        # Find nodes in resuming state with deactivated blackout events
        result = await self.db.execute(
            select(Node, BlackoutEvent)
            .join(BlackoutEvent, Node.id == BlackoutEvent.node_id)
            .where(Node.status == "resuming")
            .where(BlackoutEvent.deactivated_at.is_not(None))
            .where(BlackoutEvent.deactivated_at < timeout_threshold)
        )

        stuck_pairs = result.all()
        recovered = []

        for node, event in stuck_pairs:
            # Force node back to online
            node.status = "online"

            recovered.append({
                "node_id": node.node_id,
                "blackout_id": event.id,
                "deactivated_at": event.deactivated_at.isoformat(),
                "stuck_duration_minutes": int((datetime.now(timezone.utc) - event.deactivated_at).total_seconds() / 60)
            })

        if recovered:
            await self.db.commit()

        return recovered
