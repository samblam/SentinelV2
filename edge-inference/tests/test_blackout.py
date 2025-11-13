"""
Test suite for blackout mode functionality
Following TDD - these tests should fail initially
"""
import pytest
import tempfile
import os
from pathlib import Path

from src.blackout import BlackoutController


@pytest.fixture
async def blackout_controller():
    """Create a blackout controller with temporary database"""
    # Use temporary database for testing
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_db.close()

    controller = BlackoutController(db_path=temp_db.name)

    yield controller

    # Cleanup
    if os.path.exists(temp_db.name):
        os.unlink(temp_db.name)


@pytest.mark.asyncio
async def test_blackout_activation(blackout_controller):
    """Test blackout mode can be activated"""
    controller = blackout_controller

    await controller.activate()

    assert controller.is_active == True
    assert controller.activated_at is not None


@pytest.mark.asyncio
async def test_blackout_initial_state(blackout_controller):
    """Test initial state is inactive"""
    controller = blackout_controller

    assert controller.is_active == False
    assert controller.activated_at is None


@pytest.mark.asyncio
async def test_blackout_queues_detections(blackout_controller):
    """Test detections are queued during blackout"""
    controller = blackout_controller

    await controller.activate()

    mock_detection = {"test": "data", "id": 1}
    await controller.queue_detection(mock_detection)

    queued = await controller.get_queued_detections()
    assert len(queued) == 1
    assert queued[0]["test"] == "data"
    assert queued[0]["id"] == 1


@pytest.mark.asyncio
async def test_blackout_deactivation_returns_queue(blackout_controller):
    """Test deactivation returns all queued detections"""
    controller = blackout_controller

    await controller.activate()
    await controller.queue_detection({"id": 1})
    await controller.queue_detection({"id": 2})

    detections = await controller.deactivate()

    assert len(detections) == 2
    assert controller.is_active == False
    assert controller.activated_at is None


@pytest.mark.asyncio
async def test_blackout_deactivation_clears_queue(blackout_controller):
    """Test deactivation clears the queue"""
    controller = blackout_controller

    await controller.activate()
    await controller.queue_detection({"id": 1})
    await controller.deactivate()

    # Queue should be empty after deactivation
    queued = await controller.get_queued_detections()
    assert len(queued) == 0


@pytest.mark.asyncio
async def test_blackout_multiple_detections(blackout_controller):
    """Test multiple detections can be queued"""
    controller = blackout_controller

    await controller.activate()

    # Queue multiple detections
    for i in range(5):
        await controller.queue_detection({"id": i, "value": f"detection_{i}"})

    queued = await controller.get_queued_detections()
    assert len(queued) == 5

    # Verify order is preserved
    for i, detection in enumerate(queued):
        assert detection["id"] == i


@pytest.mark.asyncio
async def test_blackout_persistence(blackout_controller):
    """Test queue persists in database"""
    controller = blackout_controller
    db_path = controller.db_path

    await controller.activate()
    await controller.queue_detection({"persistent": "data"})

    # Create new controller instance with same database
    new_controller = BlackoutController(db_path=str(db_path))
    queued = await new_controller.get_queued_detections()

    assert len(queued) == 1
    assert queued[0]["persistent"] == "data"


@pytest.mark.asyncio
async def test_blackout_queue_before_activation(blackout_controller):
    """Test queueing works even if not explicitly activated"""
    controller = blackout_controller

    # Queue without activation (should still work due to auto-init)
    await controller.queue_detection({"test": "data"})

    queued = await controller.get_queued_detections()
    assert len(queued) == 1


@pytest.mark.asyncio
async def test_blackout_empty_queue(blackout_controller):
    """Test getting empty queue"""
    controller = blackout_controller

    queued = await controller.get_queued_detections()
    assert len(queued) == 0
    assert isinstance(queued, list)


@pytest.mark.asyncio
async def test_blackout_reactivation(blackout_controller):
    """Test blackout can be reactivated after deactivation"""
    controller = blackout_controller

    # First cycle
    await controller.activate()
    await controller.queue_detection({"cycle": 1})
    await controller.deactivate()

    # Second cycle
    await controller.activate()
    assert controller.is_active == True
    await controller.queue_detection({"cycle": 2})

    queued = await controller.get_queued_detections()
    assert len(queued) == 1
    assert queued[0]["cycle"] == 2
