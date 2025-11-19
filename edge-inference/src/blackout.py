"""
Blackout Mode Controller for Covert Operations
Manages detection queueing during communications blackout
"""
import asyncio
import aiosqlite
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class BlackoutController:
    """Manage blackout mode for covert operations (Module 5 enhanced)"""

    def __init__(self, node_id: str, db_path: str = "blackout_queue.db"):
        """
        Initialize blackout controller

        Args:
            node_id: Edge node identifier
            db_path: Path to SQLite database for queue persistence
        """
        self.node_id = node_id
        self.db_path = Path(db_path)
        self.is_active = False
        self.blackout_id: Optional[int] = None
        self.activated_at: Optional[datetime] = None
        self._initialized = False

    async def _init_db(self):
        """Initialize SQLite database for queue"""
        if self._initialized:
            return

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS queued_detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    queued_at TEXT NOT NULL,
                    detection_data TEXT NOT NULL,
                    transmitted BOOLEAN DEFAULT 0
                )
            """)
            await db.commit()

        self._initialized = True

    async def activate(self, blackout_id: Optional[int] = None):
        """
        Activate blackout mode

        Args:
            blackout_id: Backend blackout event ID
        """
        await self._init_db()
        self.is_active = True
        self.blackout_id = blackout_id
        self.activated_at = datetime.now(timezone.utc)

        logger.info(f"[BLACKOUT] Node {self.node_id} entering blackout mode")
        logger.info(f"[BLACKOUT] Blackout ID: {blackout_id}")
        logger.info(f"[BLACKOUT] Detections will be queued locally")
        logger.info(f"[BLACKOUT] RF signature suppressed")

    async def deactivate(self) -> List[Dict[str, Any]]:
        """
        Deactivate blackout mode and return queued detections for burst transmission

        Returns:
            List of all queued detections
        """
        if not self.is_active:
            return []

        detections = await self.get_queued_detections()

        # Mark as transmitted since we are returning them for burst transmission
        if detections:
            ids = [d['id'] for d in detections]
            await self.mark_transmitted(ids)

        logger.info(f"[BLACKOUT] Node {self.node_id} exiting blackout mode")
        logger.info(f"[BLACKOUT] Transmitting {len(detections)} queued detections")

        self.is_active = False
        self.blackout_id = None
        self.activated_at = None

        return detections

    async def queue_detection(self, detection: Dict[str, Any]):
        """
        Queue detection during blackout

        Args:
            detection: Detection message to queue
        """
        await self._init_db()

        detection_json = json.dumps(detection)
        queued_at = datetime.now(timezone.utc).isoformat()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO queued_detections (queued_at, detection_data, transmitted) VALUES (?, ?, 0)",
                (queued_at, detection_json)
            )
            await db.commit()

        # Periodic status update (every 10 detections)
        count = await self.get_queued_count()
        if count % 10 == 0:
            logger.info(f"[BLACKOUT] {count} detections queued")

    async def get_queued_detections(self) -> List[Dict[str, Any]]:
        """
        Get all untransmitted queued detections

        Returns:
            List of queued detection data with IDs
        """
        await self._init_db()

        async with aiosqlite.connect(self.db_path) as db:
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

    async def get_queued_count(self) -> int:
        """
        Get count of untransmitted queued detections

        Returns:
            Number of queued detections
        """
        await self._init_db()

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM queued_detections WHERE transmitted = 0"
            )
            row = await cursor.fetchone()

        return row[0] if row else 0

    async def mark_transmitted(self, detection_ids: List[int]):
        """
        Mark detections as transmitted

        Args:
            detection_ids: List of detection IDs that were successfully transmitted
        """
        await self._init_db()

        async with aiosqlite.connect(self.db_path) as db:
            for det_id in detection_ids:
                await db.execute(
                    "UPDATE queued_detections SET transmitted = 1 WHERE id = ?",
                    (det_id,)
                )
            await db.commit()

    async def clear_transmitted(self):
        """Clear transmitted detections from queue"""
        await self._init_db()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM queued_detections WHERE transmitted = 1")
            await db.commit()

    def get_status(self) -> dict:
        """Get current blackout status"""
        return {
            "active": self.is_active,
            "blackout_id": self.blackout_id,
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
            "duration_seconds": int((datetime.now(timezone.utc) - self.activated_at).total_seconds()) if self.activated_at else None
        }
