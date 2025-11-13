"""
Blackout Mode Controller for Covert Operations
Manages detection queueing during communications blackout
"""
import asyncio
import aiosqlite
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path


class BlackoutController:
    """Manage blackout mode for covert operations"""

    def __init__(self, db_path: str = "blackout_queue.db"):
        """
        Initialize blackout controller

        Args:
            db_path: Path to SQLite database for queue persistence
        """
        self.db_path = Path(db_path)
        self.is_active = False
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
                    detection_data TEXT NOT NULL
                )
            """)
            await db.commit()

        self._initialized = True

    async def activate(self):
        """Activate blackout mode"""
        await self._init_db()
        self.is_active = True
        self.activated_at = datetime.now(timezone.utc)

    async def deactivate(self) -> List[Dict[str, Any]]:
        """
        Deactivate blackout mode and return queued detections

        Returns:
            List of all queued detections
        """
        detections = await self.get_queued_detections()

        # Clear queue
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM queued_detections")
            await db.commit()

        self.is_active = False
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
                "INSERT INTO queued_detections (queued_at, detection_data) VALUES (?, ?)",
                (queued_at, detection_json)
            )
            await db.commit()

    async def get_queued_detections(self) -> List[Dict[str, Any]]:
        """
        Get all queued detections

        Returns:
            List of queued detection messages
        """
        await self._init_db()

        detections = []

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT detection_data FROM queued_detections ORDER BY id"
            ) as cursor:
                async for row in cursor:
                    detections.append(json.loads(row[0]))

        return detections
