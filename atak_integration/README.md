# ATAK/CoT Integration Module

**Tactical data link compatibility for Sentinel v2 Arctic surveillance system**

Convert Sentinel detection events into Cursor-on-Target (CoT) XML messages compatible with ATAK (Android Tactical Assault Kit) and other TAK clients.

## Features

✅ **CoT 2.0 XML Generation** - Full specification compliance
✅ **Pydantic Data Validation** - Type-safe detection models
✅ **XML Validation** - Structural and semantic checking
✅ **Mock TAK Server** - Testing without real TAK infrastructure
✅ **Async TAK Client** - Non-blocking message transmission
✅ **Batch Processing** - Efficient multi-detection handling
✅ **98% Test Coverage** - Comprehensive test suite with TDD

---

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# For development/testing
pip install -r requirements-dev.txt
```

### Basic Usage

```python
from datetime import datetime, timezone
from src.cot_schemas import SentinelDetection
from src.cot_generator import CoTGenerator

# Create detection from Sentinel edge node
detection = SentinelDetection(
    node_id="arctic-sentry-01",
    timestamp=datetime.now(timezone.utc),
    latitude=70.5,
    longitude=-100.2,
    altitude_m=50.0,
    detections=[{
        "bbox": {"xmin": 100, "ymin": 150, "xmax": 300, "ymax": 400},
        "class": "person",
        "confidence": 0.89,
        "class_id": 0
    }],
    detection_count=1,
    inference_time_ms=87.5
)

# Generate CoT XML
generator = CoTGenerator()
cot_xml = generator.generate(detection)
print(cot_xml)
```

**Output:**
```xml
<?xml version='1.0' encoding='UTF-8'?>
<event version="2.0" uid="SENTINEL-DET-..." type="a-f-G-E-S" ...>
  <point lat="70.5" lon="-100.2" hae="50.0" ce="10.0" le="9999999.0"/>
  <detail>
    <contact callsign="arctic-sentry-01"/>
    <remarks>Person detected (conf: 0.89)</remarks>
    ...
  </detail>
</event>
```

---

## CoT Specification

### CoT Type Taxonomy

Sentinel uses **`a-f-G-E-S`** (friendly ground sensor equipment) for detection events:
- **a** = Atom (individual entity)
- **f** = Friendly/Neutral
- **G** = Ground
- **E** = Equipment
- **S** = Sensor

### Timestamp Format

ISO 8601 with timezone:
```python
time="2025-01-15T14:23:45.123456Z"
```

### Stale Time

Configurable via `COT_STALE_MINUTES` (default: 5 minutes)

---

## API Reference

### CoTGenerator

Generate CoT XML from Sentinel detections.

```python
from src.cot_generator import CoTGenerator

generator = CoTGenerator(
    cot_type="a-f-G-E-S",        # CoT event type
    stale_minutes=5,              # Stale time
    sentinel_version="2.0"        # Sentinel version tag
)

# Single detection
cot_xml = generator.generate(detection)

# Batch generation
cot_messages = generator.generate_batch(detections)
```

### CoTValidator

Validate CoT XML against specification.

```python
from src.cot_validator import CoTValidator

validator = CoTValidator()

# Validate single message
is_valid, errors = validator.validate(cot_xml)
if not is_valid:
    print(f"Validation errors: {errors}")

# Batch validation
results = validator.validate_batch(cot_messages)
for i, (is_valid, errors) in enumerate(results):
    if not is_valid:
        print(f"Message {i} errors: {errors}")
```

**Validation Checks:**
- XML well-formedness
- Required elements/attributes
- Coordinate ranges (lat: -90 to 90, lon: -180 to 180)
- Timestamp format (ISO 8601)
- CoT 2.0 structure

### Mock TAK Server

Async TCP server for testing.

```python
from src.mock_tak_server import MockTAKServer

# Start server
server = MockTAKServer(host='127.0.0.1', port=8089)
await server.start()

# Check status
print(f"Running: {server.is_running()}")
print(f"Connections: {server.get_connection_count()}")

# Get received messages
messages = server.get_received_messages()
print(f"Received {len(messages)} CoT messages")

# Clear and stop
server.clear_messages()
await server.stop()

# Or use context manager
async with MockTAKServer(host='127.0.0.1', port=8089) as server:
    # Server automatically starts/stops
    pass
```

### TAK Client

Async client for sending CoT to TAK servers.

```python
from src.tak_client import TAKClient

# Connect to TAK server
client = TAKClient(host='tak-server.example.com', port=8089)
await client.connect(timeout=5.0)

# Send CoT message
success = await client.send_cot(cot_xml)

# Batch send
results = await client.send_batch(cot_messages)

# Disconnect
await client.disconnect()

# Or use context manager
async with TAKClient(host='tak-server.example.com', port=8089) as client:
    await client.send_cot(cot_xml)
```

---

## Configuration

Environment variables (see `.env.example`):

```bash
# TAK Server Configuration
TAK_SERVER_ENABLED=false
TAK_SERVER_HOST=localhost
TAK_SERVER_PORT=8089

# Mock TAK Server (for testing)
MOCK_TAK_SERVER_HOST=127.0.0.1
MOCK_TAK_SERVER_PORT=8089

# CoT Configuration
COT_STALE_MINUTES=5
COT_TYPE=a-f-G-E-S
```

---

## Integration with Module 2 (Backend)

### Option 1: Direct Integration

```python
from src.cot_generator import CoTGenerator
from src.tak_client import TAKClient
from backend.src.models import Detection

async def send_detection_to_tak(detection: Detection):
    """Send detection to TAK server as CoT."""
    # Convert backend detection to Sentinel format
    sentinel_detection = SentinelDetection(
        node_id=detection.node.node_id,
        timestamp=detection.timestamp,
        latitude=detection.latitude,
        longitude=detection.longitude,
        altitude_m=detection.altitude_m or 0.0,
        detections=detection.detections_json,
        detection_count=detection.detection_count,
        inference_time_ms=detection.inference_time_ms or 0.0
    )

    # Generate and send CoT
    generator = CoTGenerator()
    cot_xml = generator.generate(sentinel_detection)

    async with TAKClient() as client:
        await client.send_cot(cot_xml)
```

### Option 2: Background Task

```python
import asyncio
from fastapi import BackgroundTasks

@app.post("/api/detections")
async def ingest_detection(
    detection: DetectionCreate,
    background_tasks: BackgroundTasks
):
    # Store in database...

    # Send to TAK in background
    if settings.TAK_SERVER_ENABLED:
        background_tasks.add_task(send_to_tak, detection)

    return {"status": "success"}

async def send_to_tak(detection):
    """Background task to send to TAK."""
    generator = CoTGenerator()
    cot_xml = generator.generate(detection)

    try:
        async with TAKClient() as client:
            await client.send_cot(cot_xml)
    except Exception as e:
        logger.error(f"Failed to send to TAK: {e}")
```

---

## Testing

Run the full test suite:

```bash
# All tests with coverage
pytest

# Specific test file
pytest tests/test_cot_generator.py -v

# Integration tests only
pytest tests/test_integration.py -v

# With coverage report
pytest --cov=src --cov-report=html
```

**Test Results:**
- 63 tests (schemas, generator, validator, client/server, integration)
- 90%+ code coverage
- All edge cases covered

---

## Examples

See `examples/` directory:
- `sample_detection.json` - Example detection input
- `sample_cot.xml` - Single detection CoT output
- `multi_detection_cot.xml` - Multiple objects in one CoT

### Example: Full Pipeline

```python
import asyncio
from src.cot_schemas import SentinelDetection
from src.cot_generator import CoTGenerator
from src.cot_validator import CoTValidator
from src.tak_client import TAKClient

async def main():
    # 1. Create detection
    detection = SentinelDetection(...)

    # 2. Generate CoT
    generator = CoTGenerator()
    cot_xml = generator.generate(detection)

    # 3. Validate
    validator = CoTValidator()
    is_valid, errors = validator.validate(cot_xml)

    if not is_valid:
        print(f"Validation failed: {errors}")
        return

    # 4. Send to TAK server
    async with TAKClient(host='tak.example.com') as client:
        success = await client.send_cot(cot_xml)
        print(f"Sent to TAK: {success}")

asyncio.run(main())
```

---

## Real TAK Server Setup (Optional)

When ready to connect to a real TAK server:

### 1. Install FreeTAKServer

```bash
pip install FreeTAKServer
fts --help
```

### 2. Configure Environment

```bash
TAK_SERVER_ENABLED=true
TAK_SERVER_HOST=your-tak-server.com
TAK_SERVER_PORT=8089
```

### 3. Update Application

```python
from src.config import settings
from src.tak_client import TAKClient

if settings.TAK_SERVER_ENABLED:
    client = TAKClient(
        host=settings.TAK_SERVER_HOST,
        port=settings.TAK_SERVER_PORT
    )
    # Connect and send...
```

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│         ATAK/CoT Integration Module                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Detection → CoTGenerator → CoTValidator            │
│                      ↓                              │
│                 TAK Client                          │
│                      ↓                              │
│            ┌─────────┴─────────┐                   │
│            ↓                   ↓                    │
│     Mock TAK Server      Real TAK Server            │
│     (Testing)            (Production)               │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Connection Timeout

```python
# Increase timeout
await client.connect(timeout=10.0)
```

### Validation Errors

```python
validator = CoTValidator()
is_valid, errors = validator.validate(cot_xml)
for error in errors:
    print(f"Error: {error}")
```

### Server Not Receiving Messages

```python
# Add small delay after sending
await client.send_cot(cot_xml)
await asyncio.sleep(0.1)  # Allow server to process
```

---

## License

Part of Sentinel v2 Arctic surveillance system.

---

## Contributing

1. Write tests first (TDD)
2. Maintain >85% coverage
3. Follow async/await patterns
4. Update README for new features

---

## Support

For issues or questions about ATAK/CoT integration, see:
- CoT specification: [CoT 2.0 docs]
- ATAK documentation: [ATAK Wiki]
- FreeTAKServer: [FreeTAK GitHub]
