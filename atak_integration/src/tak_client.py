"""TAK server client for sending CoT messages."""
import asyncio
import logging
from typing import List

logger = logging.getLogger(__name__)


class TAKClient:
    """Client for connecting to TAK server and sending CoT messages.

    This client establishes a TCP connection to a TAK server and sends
    CoT XML messages.

    Attributes:
        host: TAK server host address
        port: TAK server port number
        reader: StreamReader for receiving data
        writer: StreamWriter for sending data
    """

    def __init__(self, host: str = 'localhost', port: int = 8089):
        """Initialize TAK client.

        Args:
            host: TAK server host address
            port: TAK server port number
        """
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None

    async def connect(self, timeout: float = 5.0):
        """Connect to TAK server.

        Args:
            timeout: Connection timeout in seconds

        Raises:
            ConnectionError: If connection fails
        """
        try:
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=timeout
            )
            logger.info(f"Connected to TAK server at {self.host}:{self.port}")
        except asyncio.TimeoutError as e:
            raise ConnectionError(f"Connection to {self.host}:{self.port} timed out") from e
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {self.host}:{self.port}: {e}") from e

    async def disconnect(self):
        """Disconnect from TAK server.

        Closes the connection gracefully.
        """
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
                logger.info("Disconnected from TAK server")
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self.reader = None
                self.writer = None

    def is_connected(self) -> bool:
        """Check if connected to TAK server.

        Returns:
            True if connected, False otherwise
        """
        return self.writer is not None and not self.writer.is_closing()

    async def send_cot(self, cot_xml: str) -> bool:
        """Send a CoT XML message to TAK server.

        Args:
            cot_xml: CoT XML message to send

        Returns:
            True if sent successfully, False otherwise

        Raises:
            ConnectionError: If not connected
            RuntimeError: If send fails
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to TAK server")

        try:
            # Encode and send with null terminator for message framing
            data = cot_xml.encode('utf-8') + b'\x00'
            self.writer.write(data)
            await self.writer.drain()

            logger.debug(f"Sent {len(data)} bytes to TAK server")
            return True

        except Exception as e:
            logger.error(f"Error sending CoT message: {e}")
            raise RuntimeError(f"Failed to send CoT message: {e}") from e

    async def send_batch(self, cot_messages: List[str]) -> List[bool]:
        """Send multiple CoT messages to TAK server.

        Args:
            cot_messages: List of CoT XML messages

        Returns:
            List of success status for each message

        Raises:
            ConnectionError: If not connected
        """
        results = []
        for cot_xml in cot_messages:
            try:
                success = await self.send_cot(cot_xml)
                results.append(success)
            except Exception as e:
                logger.error(f"Error in batch send: {e}")
                results.append(False)

        return results

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
