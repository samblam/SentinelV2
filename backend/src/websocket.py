"""WebSocket connection manager for real-time updates."""
from typing import Dict
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        """Accept WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket client {client_id} connected. Total: {len(self.active_connections)}")

    def disconnect(self, client_id: str):
        """Remove WebSocket connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket client {client_id} disconnected. Total: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, client_id: str):
        """Send message to specific client."""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = []
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to client {client_id}: {e}")
                disconnected.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)

    async def broadcast_detection(self, detection: dict):
        """Broadcast detection to all clients."""
        message = {
            "type": "detection",
            "data": detection
        }
        await self.broadcast(message)

    async def broadcast_node_status(self, node_id: str, status: str):
        """Broadcast node status update."""
        message = {
            "type": "node_status",
            "data": {
                "node_id": node_id,
                "status": status
            }
        }
        await self.broadcast(message)

    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)
