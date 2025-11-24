#!/usr/bin/env python3
"""
Blackout queue persistence test.

Tests that queued detections persist across edge node restarts:
1. Activate blackout mode
2. Queue detections locally in SQLite
3. Verify queue contents
4. Simulate edge node restart (SQLite persistence check)
5. Verify queue still contains detections after restart
6. Deactivate and transmit queued detections
"""
import asyncio
import aiosqlite
import os
import pytest
from pathlib import Path
from datetime import datetime, timezone

# Mark all tests in this module as integration tests
pytestmark = [pytest.mark.integration, pytest.mark.slow]


import tempfile

TEST_DB_PATH = Path(tempfile.gettempdir()) / "test_blackout_queue.db"


async def init_blackout_db(db_path: Path):
    """Initialize SQLite database for blackout queue."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS queued_detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                queued_at TEXT NOT NULL,
                detection_data TEXT NOT NULL,
                transmitted BOOLEAN DEFAULT 0
            )
        """)
        await db.commit()


async def queue_detection(db_path: Path, detection: dict):
    """Queue a detection in SQLite."""
    import json
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO queued_detections (queued_at, detection_data, transmitted) VALUES (?, ?, 0)",
            (datetime.now(timezone.utc).isoformat(), json.dumps(detection))
        )
        await db.commit()


async def get_queued_count(db_path: Path) -> int:
    """Get count of untransmitted queued detections."""
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM queued_detections WHERE transmitted = 0"
        )
        row = await cursor.fetchone()
        return row[0] if row else 0


async def get_all_queued(db_path: Path) -> list:
    """Get all untransmitted queued detections."""
    import json
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "SELECT id, queued_at, detection_data FROM queued_detections WHERE transmitted = 0 ORDER BY id"
        )
        rows = await cursor.fetchall()

    return [
        {
            "id": row[0],
            "queued_at": row[1],
            "detection": json.loads(row[2])
        }
        for row in rows
    ]


async def mark_transmitted(db_path: Path, detection_ids: list):
    """Mark detections as transmitted."""
    async with aiosqlite.connect(db_path) as db:
        for det_id in detection_ids:
            await db.execute(
                "UPDATE queued_detections SET transmitted = 1 WHERE id = ?",
                (det_id,)
            )
        await db.commit()


async def clear_transmitted(db_path: Path):
    """Clear transmitted detections from queue."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute("DELETE FROM queued_detections WHERE transmitted = 1")
        await db.commit()


def create_test_detection(index: int) -> dict:
    """Create a test detection message."""
    return {
        "node_id": "test-sentry-01",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "latitude": 71.297 + (index * 0.001),
        "longitude": -156.769 + (index * 0.001),
        "altitude_m": 149.0,
        "accuracy_m": 7.5,
        "detections": [
            {
                "class": "vehicle",
                "confidence": 0.90 + (index * 0.01),
                "bbox": [100 + index*10, 150, 250, 350]
            }
        ],
        "detection_count": 1,
        "inference_time_ms": 40.0 + index,
        "model": "yolov8n"
    }


@pytest.mark.asyncio
async def test_blackout_queue_persistence():
    """
    Test that blackout queue persists across restarts.
    """
    print("\n" + "=" * 70)
    print("BLACKOUT QUEUE PERSISTENCE TEST")
    print("=" * 70)

    # Clean up any existing test database
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
        print(f"✓ Cleaned up existing test database")

    # Step 1: Initialize database
    print("\n[STEP 1] Initializing SQLite blackout queue...")
    await init_blackout_db(TEST_DB_PATH)
    assert TEST_DB_PATH.exists(), "Database file not created"
    print(f"✓ Database created at {TEST_DB_PATH}")

    # Step 2: Queue detections
    print("\n[STEP 2] Queueing 5 detections...")
    detections_queued = []
    for i in range(5):
        detection = create_test_detection(i)
        await queue_detection(TEST_DB_PATH, detection)
        detections_queued.append(detection)
        print(f"  ✓ Queued detection {i+1}/5")

    # Step 3: Verify detections are queued
    print("\n[STEP 3] Verifying queue contents...")
    count = await get_queued_count(TEST_DB_PATH)
    assert count == 5, f"Expected 5 queued, got {count}"
    print(f"✓ Queue contains {count} detections")

    queued = await get_all_queued(TEST_DB_PATH)
    assert len(queued) == 5, f"Expected 5 queued items, got {len(queued)}"
    for i, item in enumerate(queued):
        assert item['detection']['node_id'] == detections_queued[i]['node_id']
        print(f"  ✓ Detection {i+1}: id={item['id']}, queued_at={item['queued_at'][:19]}")

    # Step 4: Simulate restart (close and reopen database connection)
    print("\n[STEP 4] Simulating edge node restart...")
    print("  (SQLite database persists on disk)")
    await asyncio.sleep(0.1)  # Simulate downtime
    print("✓ Node restarted")

    # Step 5: Verify queue persisted after restart
    print("\n[STEP 5] Verifying queue persisted after restart...")
    count_after_restart = await get_queued_count(TEST_DB_PATH)
    assert count_after_restart == 5, \
        f"Expected 5 queued after restart, got {count_after_restart}"
    print(f"✓ Queue still contains {count_after_restart} detections")

    queued_after_restart = await get_all_queued(TEST_DB_PATH)
    assert len(queued_after_restart) == 5, \
        f"Expected 5 queued items after restart, got {len(queued_after_restart)}"

    # Verify same IDs and data
    for i in range(5):
        assert queued_after_restart[i]['id'] == queued[i]['id'], \
            f"Detection {i} ID mismatch"
        assert queued_after_restart[i]['detection']['node_id'] == \
            queued[i]['detection']['node_id'], \
            f"Detection {i} data mismatch"
    print("✓ All detections preserved with correct data")

    # Step 6: Mark first 3 as transmitted
    print("\n[STEP 6] Marking first 3 detections as transmitted...")
    transmitted_ids = [item['id'] for item in queued_after_restart[:3]]
    await mark_transmitted(TEST_DB_PATH, transmitted_ids)
    print(f"✓ Marked {len(transmitted_ids)} detections as transmitted")

    # Step 7: Verify only 2 untransmitted remain
    print("\n[STEP 7] Verifying untransmitted count...")
    count_untransmitted = await get_queued_count(TEST_DB_PATH)
    assert count_untransmitted == 2, \
        f"Expected 2 untransmitted, got {count_untransmitted}"
    print(f"✓ {count_untransmitted} untransmitted detections remain")

    # Step 8: Clear transmitted detections
    print("\n[STEP 8] Clearing transmitted detections...")
    await clear_transmitted(TEST_DB_PATH)
    print("✓ Transmitted detections cleared")

    # Step 9: Verify final count
    print("\n[STEP 9] Verifying final queue state...")
    final_count = await get_queued_count(TEST_DB_PATH)
    assert final_count == 2, f"Expected 2 remaining, got {final_count}"
    print(f"✓ Final queue contains {final_count} detections")

    final_queued = await get_all_queued(TEST_DB_PATH)
    assert len(final_queued) == 2
    assert final_queued[0]['id'] == queued[3]['id']
    assert final_queued[1]['id'] == queued[4]['id']
    print("✓ Correct detections remain in queue")

    # Step 10: Simulate another restart to verify persistence
    print("\n[STEP 10] Simulating second restart...")
    await asyncio.sleep(0.1)
    count_final = await get_queued_count(TEST_DB_PATH)
    assert count_final == 2, f"Expected 2 after second restart, got {count_final}"
    print(f"✓ Queue still contains {count_final} detections after second restart")

    # Cleanup
    print("\n[CLEANUP] Removing test database...")
    TEST_DB_PATH.unlink()
    print("✓ Test database removed")

    print("\n" + "=" * 70)
    print("✓ BLACKOUT QUEUE PERSISTENCE TEST PASSED")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_blackout_queue_persistence())
