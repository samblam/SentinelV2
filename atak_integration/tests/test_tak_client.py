"""Tests for TAK client and mock TAK server."""
import pytest
import asyncio
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_mock_server_starts_and_stops():
    """Test mock TAK server can start and stop."""
    from src.mock_tak_server import MockTAKServer

    server = MockTAKServer(host='127.0.0.1', port=18089)

    # Start server
    await server.start()
    assert server.is_running()

    # Stop server
    await server.stop()
    assert not server.is_running()


@pytest.mark.asyncio
async def test_client_connects_to_server():
    """Test TAK client can connect to mock server."""
    from src.mock_tak_server import MockTAKServer
    from src.tak_client import TAKClient

    server = MockTAKServer(host='127.0.0.1', port=18090)
    await server.start()

    try:
        client = TAKClient(host='127.0.0.1', port=18090)
        await client.connect()

        assert client.is_connected()

        await client.disconnect()
        assert not client.is_connected()
    finally:
        await server.stop()


@pytest.mark.asyncio
async def test_client_sends_cot_message(sample_sentinel_detection):
    """Test TAK client can send CoT message."""
    from src.mock_tak_server import MockTAKServer
    from src.tak_client import TAKClient
    from src.cot_generator import CoTGenerator
    from src.cot_schemas import SentinelDetection

    server = MockTAKServer(host='127.0.0.1', port=18091)
    await server.start()

    try:
        # Generate CoT
        detection = SentinelDetection(**sample_sentinel_detection)
        generator = CoTGenerator()
        cot_xml = generator.generate(detection)

        # Connect and send
        client = TAKClient(host='127.0.0.1', port=18091)
        await client.connect()

        success = await client.send_cot(cot_xml)
        assert success

        # Give server time to process
        await asyncio.sleep(0.1)

        await client.disconnect()

        # Check server received it
        messages = server.get_received_messages()
        assert len(messages) == 1
        assert cot_xml in messages[0]
    finally:
        await server.stop()


@pytest.mark.asyncio
async def test_client_sends_batch_cot_messages():
    """Test TAK client can send batch of CoT messages."""
    from src.mock_tak_server import MockTAKServer
    from src.tak_client import TAKClient
    from src.cot_generator import CoTGenerator
    from src.cot_schemas import SentinelDetection
    from tests.helpers import create_sample_detection

    server = MockTAKServer(host='127.0.0.1', port=18092)
    await server.start()

    try:
        # Generate multiple CoT messages
        detections = [
            SentinelDetection(**create_sample_detection(node_id=f"sentry-{i}"))
            for i in range(3)
        ]
        generator = CoTGenerator()
        cot_messages = generator.generate_batch(detections)

        # Connect and send batch
        client = TAKClient(host='127.0.0.1', port=18092)
        await client.connect()

        results = await client.send_batch(cot_messages)
        assert len(results) == 3
        assert all(results)

        # Give server time to process all messages
        await asyncio.sleep(0.2)

        await client.disconnect()

        # Check server received all
        # Note: Messages may be concatenated if sent quickly
        messages = server.get_received_messages()
        all_messages = ''.join(messages)
        assert all_messages.count('<?xml') == 3  # Should have 3 XML declarations
        assert 'sentry-0' in all_messages
        assert 'sentry-1' in all_messages
        assert 'sentry-2' in all_messages
    finally:
        await server.stop()


@pytest.mark.asyncio
async def test_server_handles_multiple_clients():
    """Test mock server handles multiple simultaneous clients."""
    from src.mock_tak_server import MockTAKServer
    from src.tak_client import TAKClient
    from src.cot_generator import CoTGenerator
    from src.cot_schemas import SentinelDetection
    from tests.helpers import create_sample_detection

    server = MockTAKServer(host='127.0.0.1', port=18093)
    await server.start()

    try:
        # Create multiple clients
        clients = [
            TAKClient(host='127.0.0.1', port=18093)
            for _ in range(3)
        ]

        # Connect all clients
        await asyncio.gather(*[client.connect() for client in clients])

        # Each client sends a message
        detection = SentinelDetection(**create_sample_detection())
        generator = CoTGenerator()
        cot_xml = generator.generate(detection)

        send_tasks = [client.send_cot(cot_xml) for client in clients]
        results = await asyncio.gather(*send_tasks)
        assert all(results)

        # Disconnect all
        await asyncio.gather(*[client.disconnect() for client in clients])

        # Server should have received 3 messages
        messages = server.get_received_messages()
        assert len(messages) == 3
    finally:
        await server.stop()


@pytest.mark.asyncio
async def test_client_handles_connection_failure():
    """Test TAK client handles connection failure gracefully."""
    from src.tak_client import TAKClient

    # Try to connect to non-existent server
    client = TAKClient(host='127.0.0.1', port=19999)

    with pytest.raises(ConnectionError):
        await client.connect(timeout=1.0)

    assert not client.is_connected()


@pytest.mark.asyncio
async def test_client_cannot_send_when_disconnected(sample_sentinel_detection):
    """Test client cannot send when disconnected."""
    from src.tak_client import TAKClient
    from src.cot_generator import CoTGenerator
    from src.cot_schemas import SentinelDetection

    detection = SentinelDetection(**sample_sentinel_detection)
    generator = CoTGenerator()
    cot_xml = generator.generate(detection)

    client = TAKClient(host='127.0.0.1', port=18094)

    with pytest.raises((ConnectionError, RuntimeError)):
        await client.send_cot(cot_xml)


@pytest.mark.asyncio
async def test_server_connection_count():
    """Test server tracks connected client count."""
    from src.mock_tak_server import MockTAKServer
    from src.tak_client import TAKClient

    server = MockTAKServer(host='127.0.0.1', port=18095)
    await server.start()

    try:
        assert server.get_connection_count() == 0

        # Connect first client
        client1 = TAKClient(host='127.0.0.1', port=18095)
        await client1.connect()
        await asyncio.sleep(0.1)  # Give server time to register

        assert server.get_connection_count() == 1

        # Connect second client
        client2 = TAKClient(host='127.0.0.1', port=18095)
        await client2.connect()
        await asyncio.sleep(0.1)

        assert server.get_connection_count() == 2

        # Disconnect first
        await client1.disconnect()
        await asyncio.sleep(0.1)

        assert server.get_connection_count() == 1

        await client2.disconnect()
    finally:
        await server.stop()


@pytest.mark.asyncio
async def test_server_clears_messages():
    """Test server can clear received messages."""
    from src.mock_tak_server import MockTAKServer
    from src.tak_client import TAKClient
    from src.cot_generator import CoTGenerator
    from src.cot_schemas import SentinelDetection
    from tests.helpers import create_sample_detection

    server = MockTAKServer(host='127.0.0.1', port=18096)
    await server.start()

    try:
        detection = SentinelDetection(**create_sample_detection())
        generator = CoTGenerator()
        cot_xml = generator.generate(detection)

        client = TAKClient(host='127.0.0.1', port=18096)
        await client.connect()
        await client.send_cot(cot_xml)

        # Give server time to process
        await asyncio.sleep(0.1)

        messages = server.get_received_messages()
        assert len(messages) == 1

        # Clear messages
        server.clear_messages()
        messages = server.get_received_messages()
        assert len(messages) == 0

        await client.disconnect()
    finally:
        await server.stop()


@pytest.mark.asyncio
async def test_client_with_context_manager():
    """Test TAK client works with async context manager."""
    from src.mock_tak_server import MockTAKServer
    from src.tak_client import TAKClient
    from src.cot_generator import CoTGenerator
    from src.cot_schemas import SentinelDetection
    from tests.helpers import create_sample_detection

    server = MockTAKServer(host='127.0.0.1', port=18097)
    await server.start()

    try:
        detection = SentinelDetection(**create_sample_detection())
        generator = CoTGenerator()
        cot_xml = generator.generate(detection)

        async with TAKClient(host='127.0.0.1', port=18097) as client:
            assert client.is_connected()
            success = await client.send_cot(cot_xml)
            assert success

        # Client should be disconnected after context
        assert not client.is_connected()
    finally:
        await server.stop()


@pytest.mark.asyncio
async def test_server_with_context_manager():
    """Test mock server works with async context manager."""
    from src.mock_tak_server import MockTAKServer
    from src.tak_client import TAKClient

    async with MockTAKServer(host='127.0.0.1', port=18098) as server:
        assert server.is_running()

        client = TAKClient(host='127.0.0.1', port=18098)
        await client.connect()
        await client.disconnect()

    # Server should be stopped after context
    assert not server.is_running()


@pytest.mark.asyncio
async def test_client_reconnect():
    """Test TAK client can reconnect after disconnect."""
    from src.mock_tak_server import MockTAKServer
    from src.tak_client import TAKClient

    server = MockTAKServer(host='127.0.0.1', port=18099)
    await server.start()

    try:
        client = TAKClient(host='127.0.0.1', port=18099)

        # First connection
        await client.connect()
        assert client.is_connected()
        await client.disconnect()
        assert not client.is_connected()

        # Reconnect
        await client.connect()
        assert client.is_connected()
        await client.disconnect()
    finally:
        await server.stop()
