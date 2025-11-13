"""Mock TAK server for testing CoT message transmission."""
import asyncio
import logging
from typing import List, Set

logger = logging.getLogger(__name__)


class MockTAKServer:
    """Mock TAK server for testing.

    This server simulates a TAK server for testing purposes. It accepts
    TCP connections, receives CoT messages, and tracks received data.

    Attributes:
        host: Server host address
        port: Server port number
        server: AsyncIO server instance
        received_messages: List of received CoT messages
        connections: Set of active client connections
    """

    def __init__(self, host: str = '127.0.0.1', port: int = 8089):
        """Initialize mock TAK server.

        Args:
            host: Host address to bind to
            port: Port number to listen on
        """
        self.host = host
        self.port = port
        self.server = None
        self.received_messages: List[str] = []
        self.connections: Set[asyncio.StreamWriter] = set()
        self._running = False

    async def start(self):
        """Start the mock TAK server.

        Starts an async TCP server that accepts CoT messages.
        """
        self.server = await asyncio.start_server(
            self._handle_client,
            self.host,
            self.port
        )
        self._running = True
        logger.info(f"Mock TAK server started on {self.host}:{self.port}")

    async def stop(self):
        """Stop the mock TAK server.

        Closes all client connections and stops the server.
        """
        self._running = False

        # Close all client connections
        for writer in list(self.connections):
            try:
                writer.close()
                await writer.wait_closed()
            except Exception as e:
                logger.warning(f"Error closing client connection: {e}")

        self.connections.clear()

        # Stop server
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("Mock TAK server stopped")

    def is_running(self) -> bool:
        """Check if server is running.

        Returns:
            True if server is running, False otherwise
        """
        return self._running

    def get_received_messages(self) -> List[str]:
        """Get all received CoT messages.

        Returns:
            List of received CoT XML messages
        """
        return self.received_messages.copy()

    def clear_messages(self):
        """Clear all received messages."""
        self.received_messages.clear()

    def get_connection_count(self) -> int:
        """Get number of active connections.

        Returns:
            Number of currently connected clients
        """
        return len(self.connections)

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ):
        """Handle a client connection.

        Args:
            reader: Stream reader for receiving data
            writer: Stream writer for sending data
        """
        addr = writer.get_extra_info('peername')
        logger.debug(f"Client connected from {addr}")

        self.connections.add(writer)

        try:
            while self._running:
                # Read data from client
                # CoT messages are typically terminated with null byte
                data = await reader.read(8192)

                if not data:
                    break

                # Decode and store message
                message = data.decode('utf-8')
                self.received_messages.append(message)
                logger.debug(f"Received {len(message)} bytes from {addr}")

                # Send acknowledgment (optional)
                # For now, just continue reading

        except asyncio.CancelledError:
            logger.debug(f"Connection cancelled for {addr}")
        except Exception as e:
            logger.error(f"Error handling client {addr}: {e}")
        finally:
            self.connections.discard(writer)
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
            logger.debug(f"Client disconnected from {addr}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
