"""Integration tests for end-to-end CoT pipeline."""
import pytest
import asyncio
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_full_pipeline_detection_to_tak(sample_sentinel_detection):
    """Test complete pipeline: detection → CoT → validate → send to TAK."""
    from src.cot_schemas import SentinelDetection
    from src.cot_generator import CoTGenerator
    from src.cot_validator import CoTValidator
    from src.mock_tak_server import MockTAKServer
    from src.tak_client import TAKClient

    # Step 1: Create detection
    detection = SentinelDetection(**sample_sentinel_detection)
    assert detection.node_id == "sentry-01"

    # Step 2: Generate CoT XML
    generator = CoTGenerator()
    cot_xml = generator.generate(detection)
    assert cot_xml is not None
    assert '<?xml version' in cot_xml

    # Step 3: Validate CoT
    validator = CoTValidator()
    is_valid, errors = validator.validate(cot_xml)
    assert is_valid, f"CoT validation failed: {errors}"

    # Step 4: Send to TAK server
    server = MockTAKServer(host='127.0.0.1', port=28089)
    await server.start()

    try:
        client = TAKClient(host='127.0.0.1', port=28089)
        await client.connect()

        success = await client.send_cot(cot_xml)
        assert success

        await asyncio.sleep(0.1)
        await client.disconnect()

        # Verify server received it
        messages = server.get_received_messages()
        assert len(messages) > 0
        assert 'sentry-01' in messages[0]
    finally:
        await server.stop()


@pytest.mark.asyncio
async def test_batch_processing_pipeline():
    """Test batch processing through full pipeline."""
    from src.cot_schemas import SentinelDetection
    from src.cot_generator import CoTGenerator
    from src.cot_validator import CoTValidator
    from src.mock_tak_server import MockTAKServer
    from src.tak_client import TAKClient
    from tests.helpers import create_sample_detection

    # Create multiple detections
    detections = [
        SentinelDetection(**create_sample_detection(
            node_id=f"arctic-sensor-{i}",
            latitude=70.0 + i * 0.1,
            longitude=-100.0 - i * 0.1
        ))
        for i in range(5)
    ]

    # Generate CoT messages
    generator = CoTGenerator()
    cot_messages = generator.generate_batch(detections)
    assert len(cot_messages) == 5

    # Validate all messages
    validator = CoTValidator()
    results = validator.validate_batch(cot_messages)
    assert all(is_valid for is_valid, _ in results)

    # Send to TAK server
    server = MockTAKServer(host='127.0.0.1', port=28090)
    await server.start()

    try:
        async with TAKClient(host='127.0.0.1', port=28090) as client:
            send_results = await client.send_batch(cot_messages)
            assert all(send_results)

        await asyncio.sleep(0.2)

        # Verify all received
        received = server.get_received_messages()
        all_data = ''.join(received)
        for i in range(5):
            assert f'arctic-sensor-{i}' in all_data
    finally:
        await server.stop()


@pytest.mark.asyncio
async def test_multi_detection_integration(sample_multi_detection):
    """Test integration with multiple objects in single detection."""
    from src.cot_schemas import SentinelDetection
    from src.cot_generator import CoTGenerator
    from src.cot_validator import CoTValidator
    from src.mock_tak_server import MockTAKServer
    from src.tak_client import TAKClient

    # Detection with 2 objects
    detection = SentinelDetection(**sample_multi_detection)
    assert detection.detection_count == 2

    # Generate and validate
    generator = CoTGenerator()
    cot_xml = generator.generate(detection)

    validator = CoTValidator()
    is_valid, errors = validator.validate(cot_xml)
    assert is_valid, f"Validation errors: {errors}"

    # Verify multiple detection elements
    assert cot_xml.count('<detection>') == 2
    assert 'person' in cot_xml
    assert 'vehicle' in cot_xml

    # Send to server
    server = MockTAKServer(host='127.0.0.1', port=28091)
    await server.start()

    try:
        async with TAKClient(host='127.0.0.1', port=28091) as client:
            await client.send_cot(cot_xml)

        await asyncio.sleep(0.1)

        received = server.get_received_messages()
        assert len(received) > 0
    finally:
        await server.stop()


@pytest.mark.asyncio
async def test_invalid_cot_handling():
    """Test pipeline handles invalid CoT properly."""
    from src.cot_validator import CoTValidator
    from src.tak_client import TAKClient

    # Create invalid CoT (malformed XML)
    invalid_cot = "<?xml version='1.0'?><event><unclosed>"

    # Validation should catch it
    validator = CoTValidator()
    is_valid, errors = validator.validate(invalid_cot)
    assert not is_valid
    assert len(errors) > 0

    # Don't attempt to send invalid CoT
    # (In production, validation would prevent this)


@pytest.mark.asyncio
async def test_concurrent_clients_integration():
    """Test multiple concurrent clients sending CoT."""
    from src.cot_schemas import SentinelDetection
    from src.cot_generator import CoTGenerator
    from src.mock_tak_server import MockTAKServer
    from src.tak_client import TAKClient
    from tests.helpers import create_sample_detection

    server = MockTAKServer(host='127.0.0.1', port=28092)
    await server.start()

    try:
        # Create multiple clients
        num_clients = 3
        tasks = []

        for i in range(num_clients):
            # Each client sends its own detection
            detection = SentinelDetection(**create_sample_detection(
                node_id=f"concurrent-node-{i}"
            ))
            generator = CoTGenerator()
            cot_xml = generator.generate(detection)

            # Create async task for sending
            async def send_cot(cot, client_id):
                async with TAKClient(host='127.0.0.1', port=28092) as client:
                    return await client.send_cot(cot)

            tasks.append(send_cot(cot_xml, i))

        # Send all concurrently
        results = await asyncio.gather(*tasks)
        assert all(results)

        await asyncio.sleep(0.2)

        # Verify all received
        received = server.get_received_messages()
        all_data = ''.join(received)
        for i in range(num_clients):
            assert f'concurrent-node-{i}' in all_data
    finally:
        await server.stop()


@pytest.mark.asyncio
async def test_real_time_detection_stream():
    """Test streaming detections in real-time."""
    from src.cot_schemas import SentinelDetection
    from src.cot_generator import CoTGenerator
    from src.mock_tak_server import MockTAKServer
    from src.tak_client import TAKClient
    from tests.helpers import create_sample_detection

    server = MockTAKServer(host='127.0.0.1', port=28093)
    await server.start()

    try:
        generator = CoTGenerator()

        async with TAKClient(host='127.0.0.1', port=28093) as client:
            # Simulate real-time detection stream
            for i in range(5):
                # New detection arrives
                detection = SentinelDetection(**create_sample_detection(
                    node_id=f"stream-node-{i}",
                    timestamp=datetime.now(timezone.utc)
                ))

                # Generate and send immediately
                cot_xml = generator.generate(detection)
                success = await client.send_cot(cot_xml)
                assert success

                # Small delay between detections
                await asyncio.sleep(0.05)

        await asyncio.sleep(0.2)

        # Verify all received
        received = server.get_received_messages()
        all_data = ''.join(received)
        assert all_data.count('stream-node-') == 5
    finally:
        await server.stop()


@pytest.mark.asyncio
async def test_pipeline_with_context_managers():
    """Test pipeline using context managers throughout."""
    from src.cot_schemas import SentinelDetection
    from src.cot_generator import CoTGenerator
    from src.cot_validator import CoTValidator
    from src.mock_tak_server import MockTAKServer
    from src.tak_client import TAKClient
    from tests.helpers import create_sample_detection

    async with MockTAKServer(host='127.0.0.1', port=28094) as server:
        # Generate detection
        detection = SentinelDetection(**create_sample_detection())
        generator = CoTGenerator()
        cot_xml = generator.generate(detection)

        # Validate
        validator = CoTValidator()
        is_valid, _ = validator.validate(cot_xml)
        assert is_valid

        # Send using context manager
        async with TAKClient(host='127.0.0.1', port=28094) as client:
            success = await client.send_cot(cot_xml)
            assert success

        await asyncio.sleep(0.1)

        # Verify received
        received = server.get_received_messages()
        assert len(received) > 0


@pytest.mark.asyncio
async def test_edge_case_arctic_coordinates():
    """Test integration with extreme Arctic coordinates."""
    from src.cot_schemas import SentinelDetection
    from src.cot_generator import CoTGenerator
    from src.cot_validator import CoTValidator
    from tests.helpers import create_sample_detection

    # Extreme Arctic location (near North Pole)
    detection_data = create_sample_detection(
        node_id="north-pole-station",
        latitude=89.9,  # Very far north
        longitude=-45.0,
        altitude_m=0.0  # Sea level ice
    )

    detection = SentinelDetection(**detection_data)
    generator = CoTGenerator()
    cot_xml = generator.generate(detection)

    # Should validate successfully
    validator = CoTValidator()
    is_valid, errors = validator.validate(cot_xml)
    assert is_valid, f"Arctic coordinates should be valid: {errors}"

    # Verify coordinates in XML
    assert 'lat="89.9"' in cot_xml
    assert 'lon="-45.0"' in cot_xml


def test_complete_module_imports():
    """Test all module components can be imported together."""
    from src.cot_schemas import BoundingBox, Detection, SentinelDetection
    from src.cot_generator import CoTGenerator
    from src.cot_validator import CoTValidator
    from src.mock_tak_server import MockTAKServer
    from src.tak_client import TAKClient
    from src.config import settings

    # All imports should work
    assert BoundingBox is not None
    assert Detection is not None
    assert SentinelDetection is not None
    assert CoTGenerator is not None
    assert CoTValidator is not None
    assert MockTAKServer is not None
    assert TAKClient is not None
    assert settings is not None
