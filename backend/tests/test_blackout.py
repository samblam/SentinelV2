"""
Unit tests for BlackoutCoordinator.

Tests blackout mode coordination logic with mocked database.
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.blackout import BlackoutCoordinator, BlackoutState
from src.models import Node, BlackoutEvent


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def coordinator(mock_db):
    """Create BlackoutCoordinator with mocked database."""
    return BlackoutCoordinator(mock_db)


class TestBlackoutActivation:
    """Test blackout activation functionality."""

    @pytest.mark.asyncio
    async def test_activate_blackout_success(self, coordinator, mock_db):
        """Test successful blackout activation."""
        # Setup mock node
        node = Node(
            id=1,
            node_id="test-node-01",
            status="online"
        )

        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = node
        mock_db.execute.return_value = mock_result

        # Activate blackout
        event = await coordinator.activate_blackout(
            node_id="test-node-01",
            operator_id="operator-123",
            reason="Test activation"
        )

        # Verify node status changed
        assert node.status == "covert"

        # Verify blackout event created
        assert mock_db.add.called
        blackout_event_call = mock_db.add.call_args[0][0]
        assert isinstance(blackout_event_call, BlackoutEvent)
        assert blackout_event_call.node_id == 1
        assert blackout_event_call.activated_by == "operator-123"
        assert blackout_event_call.reason == "Test activation"

        # Verify commit called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_activate_blackout_node_not_found(self, coordinator, mock_db):
        """Test activation fails when node doesn't exist."""
        # Mock database query - node not found
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Should raise ValueError
        with pytest.raises(ValueError, match="Node not found"):
            await coordinator.activate_blackout(node_id="nonexistent-node")

    @pytest.mark.asyncio
    async def test_activate_blackout_already_active(self, coordinator, mock_db):
        """Test activation fails when node already in blackout."""
        # Setup mock node already in covert mode
        node = Node(
            id=1,
            node_id="test-node-01",
            status="covert"
        )

        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = node
        mock_db.execute.return_value = mock_result

        # Should raise ValueError
        with pytest.raises(ValueError, match="already in blackout"):
            await coordinator.activate_blackout(node_id="test-node-01")


class TestBlackoutDeactivation:
    """Test blackout deactivation functionality."""

    @pytest.mark.asyncio
    async def test_deactivate_blackout_success(self, coordinator, mock_db):
        """Test successful blackout deactivation."""
        # Setup mock node
        node = Node(
            id=1,
            node_id="test-node-01",
            status="covert"
        )

        # Setup mock blackout event
        event = BlackoutEvent(
            id=1,
            node_id=1,
            activated_at=datetime.now(timezone.utc) - timedelta(minutes=10),
            detections_queued=5
        )

        # Mock database queries
        mock_node_result = AsyncMock()
        mock_node_result.scalar_one_or_none.return_value = node

        mock_event_result = AsyncMock()
        mock_event_result.scalar_one_or_none.return_value = event

        mock_db.execute.side_effect = [mock_node_result, mock_event_result]

        # Deactivate blackout
        summary = await coordinator.deactivate_blackout(node_id="test-node-01")

        # Verify node status changed to resuming
        assert node.status == "resuming"

        # Verify event updated
        assert event.deactivated_at is not None
        assert event.duration_seconds > 0

        # Verify summary returned
        assert summary["node_id"] == "test-node-01"
        assert summary["blackout_id"] == 1
        assert summary["detections_queued"] == 5

        # Verify commit called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_deactivate_blackout_not_in_blackout(self, coordinator, mock_db):
        """Test deactivation fails when node not in blackout."""
        # Setup mock node not in covert mode
        node = Node(
            id=1,
            node_id="test-node-01",
            status="online"
        )

        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = node
        mock_db.execute.return_value = mock_result

        # Should raise ValueError
        with pytest.raises(ValueError, match="not in blackout"):
            await coordinator.deactivate_blackout(node_id="test-node-01")


class TestBlackoutStatus:
    """Test blackout status queries."""

    @pytest.mark.asyncio
    async def test_get_status_active(self, coordinator, mock_db):
        """Test getting status for active blackout."""
        # Setup mock node
        node = Node(
            id=1,
            node_id="test-node-01",
            status="covert"
        )

        # Setup mock blackout event
        event = BlackoutEvent(
            id=1,
            node_id=1,
            activated_at=datetime.now(timezone.utc) - timedelta(minutes=5),
            activated_by="operator-123",
            reason="Test",
            detections_queued=3
        )

        # Mock database queries
        mock_node_result = AsyncMock()
        mock_node_result.scalar_one_or_none.return_value = node

        mock_event_result = AsyncMock()
        mock_event_result.scalar_one_or_none.return_value = event

        mock_db.execute.side_effect = [mock_node_result, mock_event_result]

        # Get status
        status = await coordinator.get_blackout_status(node_id="test-node-01")

        # Verify status
        assert status["status"] == "active"
        assert status["blackout_id"] == 1
        assert status["detections_queued"] == 3
        assert status["activated_by"] == "operator-123"

    @pytest.mark.asyncio
    async def test_get_status_inactive(self, coordinator, mock_db):
        """Test getting status for inactive node."""
        # Setup mock node
        node = Node(
            id=1,
            node_id="test-node-01",
            status="online"
        )

        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = node
        mock_db.execute.return_value = mock_result

        # Get status
        status = await coordinator.get_blackout_status(node_id="test-node-01")

        # Verify status
        assert status["status"] == "inactive"
        assert status["node_status"] == "online"


class TestStuckNodeRecovery:
    """Test recovery of stuck resuming nodes."""

    @pytest.mark.asyncio
    async def test_recover_stuck_nodes(self, coordinator, mock_db):
        """Test recovery of nodes stuck in resuming state."""
        # Setup stuck node
        node = Node(
            id=1,
            node_id="stuck-node-01",
            status="resuming"
        )

        # Setup blackout event that's been stuck for 10 minutes
        event = BlackoutEvent(
            id=1,
            node_id=1,
            activated_at=datetime.now(timezone.utc) - timedelta(minutes=20),
            deactivated_at=datetime.now(timezone.utc) - timedelta(minutes=10)
        )

        # Mock database query
        mock_result = AsyncMock()
        mock_result.all.return_value = [(node, event)]
        mock_db.execute.return_value = mock_result

        # Recover stuck nodes
        recovered = await coordinator.recover_stuck_resuming_nodes(timeout_minutes=5)

        # Verify node recovered
        assert len(recovered) == 1
        assert recovered[0]["node_id"] == "stuck-node-01"
        assert recovered[0]["blackout_id"] == 1

        # Verify node status changed to online
        assert node.status == "online"

        # Verify commit called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_no_stuck_nodes(self, coordinator, mock_db):
        """Test when no nodes are stuck."""
        # Mock database query - no stuck nodes
        mock_result = AsyncMock()
        mock_result.all.return_value = []
        mock_db.execute.return_value = mock_result

        # Recover stuck nodes
        recovered = await coordinator.recover_stuck_resuming_nodes(timeout_minutes=5)

        # Verify no nodes recovered
        assert len(recovered) == 0

        # Verify commit not called
        assert not mock_db.commit.called


class TestDetectionCountUpdate:
    """Test detection count updates."""

    @pytest.mark.asyncio
    async def test_update_detection_count(self, coordinator, mock_db):
        """Test updating queued detection count."""
        # Setup mock node
        node = Node(
            id=1,
            node_id="test-node-01",
            status="covert"
        )

        # Setup mock blackout event
        event = BlackoutEvent(
            id=1,
            node_id=1,
            activated_at=datetime.now(timezone.utc),
            detections_queued=0
        )

        # Mock database queries
        mock_node_result = AsyncMock()
        mock_node_result.scalar_one_or_none.return_value = node

        mock_event_result = AsyncMock()
        mock_event_result.scalar_one_or_none.return_value = event

        mock_db.execute.side_effect = [mock_node_result, mock_event_result]

        # Update count
        await coordinator.update_detection_count(node_id="test-node-01", count=10)

        # Verify event updated
        assert event.detections_queued == 10

        # Verify commit called
        assert mock_db.commit.called


class TestCompleteResumption:
    """Test completing resumption after burst transmission."""

    @pytest.mark.asyncio
    async def test_complete_resumption(self, coordinator, mock_db):
        """Test completing blackout resumption."""
        # Setup mock node
        node = Node(
            id=1,
            node_id="test-node-01",
            status="resuming"
        )

        # Setup mock blackout event
        event = BlackoutEvent(
            id=1,
            node_id=1,
            activated_at=datetime.now(timezone.utc) - timedelta(minutes=10),
            deactivated_at=datetime.now(timezone.utc),
            detections_transmitted=0
        )

        # Mock database queries
        mock_node_result = AsyncMock()
        mock_node_result.scalar_one_or_none.return_value = node

        mock_event_result = AsyncMock()
        mock_event_result.scalar_one_or_none.return_value = event

        mock_db.execute.side_effect = [mock_node_result, mock_event_result]

        # Complete resumption
        await coordinator.complete_resumption(node_id="test-node-01", transmitted_count=15)

        # Verify event updated
        assert event.detections_transmitted == 15

        # Verify node status changed to online
        assert node.status == "online"

        # Verify commit called
        assert mock_db.commit.called
