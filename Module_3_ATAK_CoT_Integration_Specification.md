# Module 3: ATAK/CoT Integration - Complete Implementation Specification

**Purpose:** Tactical data link compatibility via Cursor-on-Target (CoT) XML generation  
**Target:** Valid CoT messages, mock TAK server for testing, extensible for real TAK integration  
**Implementation Method:** Claude Code agent with TDD

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│            ATAK/CoT Integration Module               │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐         ┌──────────────┐         │
│  │     CoT      │────────▶│     CoT      │         │
│  │  Generator   │         │  Validator   │         │
│  └──────┬───────┘         └──────────────┘         │
│         │                                            │
│         ▼                                            │
│  ┌──────────────┐         ┌──────────────┐         │
│  │   Mock TAK   │         │   Real TAK   │         │
│  │    Server    │         │   (Future)   │         │
│  └──────────────┘         └──────────────┘         │
│                                                      │
└─────────────────────────────────────────────────────┘
         │                          │
         ▼                          ▼
    Testing/Demo              Production (Optional)
```

**Design Philosophy:**
- Core: CoT generation from Sentinel detections
- Testing: Mock TAK server validates transmission logic
- Extensibility: Architecture supports real TAK server integration
- Standards: Full CoT 2.0 schema compliance

---

## Technology Stack

**Core:**
- Python 3.11
- lxml 5.1+ (XML generation and validation)
- pydantic 2.5+ (data validation)

**Network (Mock TAK Server):**
- asyncio (async TCP server)
- socket (network communication)

**Testing:**
- pytest 7.4+
- pytest-asyncio 0.21+
- xmlschema 2.5+ (CoT schema validation)

**Utilities:**
- uuid (unique event IDs)
- datetime (timestamp handling)

---

## File Structure

```
atak-integration/
├── src/
│   ├── __init__.py
│   ├── cot_generator.py     # Core CoT XML generation
│   ├── cot_schemas.py       # Pydantic models for CoT structure
│   ├── cot_validator.py     # XML schema validation
│   ├── tak_client.py        # TAK server client (with mock)
│   ├── mock_tak_server.py   # Mock TAK server for testing
│   └── config.py            # Configuration management
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures
│   ├── test_cot_generator.py
│   ├── test_cot_validator.py
│   ├── test_tak_client.py
│   └── test_integration.py  # End-to-end tests
├── schemas/
│   └── cot_event.xsd        # CoT 2.0 XML schema
├── examples/
│   ├── sample_detection.json
│   ├── sample_cot.xml
│   └── multi_detection_cot.xml
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
├── .env.example
└── README.md
```

---

## CoT (Cursor on Target) Specification

### CoT Message Structure

CoT is a military XML standard for sharing situational awareness information. Core structure:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<event version="2.0" uid="SENTINEL-DET-{uuid}" type="a-f-G-E-S" 
       time="{timestamp}" start="{timestamp}" stale="{stale_time}">
  <point lat="{latitude}" lon="{longitude}" hae="{altitude}" 
         ce="{circular_error}" le="{linear_error}"/>
  <detail>
    <contact callsign="{node_id}"/>
    <remarks>{detection_summary}</remarks>
    <_flow-tags_ sentinel_version="2.0"/>
    <detection>
      <object_class>{class_name}</object_class>
      <confidence>{confidence}</confidence>
      <inference_time_ms>{inference_time}</inference_time_ms>
      <bbox xmin="{xmin}" ymin="{ymin}" xmax="{xmax}" ymax="{ymax}"/>
    </detection>
  </detail>
</event>
```

### CoT Type Taxonomy

**Format:** `a-{affiliation}-{battle_dimension}-{function}`

**For Sentinel detections:**
- **Affiliation:** `f` (friendly/neutral sensor)
- **Battle Dimension:** `G` (ground)
- **Function:** `E-S` (equipment-sensor)

**Full type:** `a-f-G-E-S` (friendly ground sensor equipment)

**Alternative for detected objects:**
- Person: `a-n-G` (neutral ground entity)
- Vehicle: `a-n-G-E-V` (neutral ground equipment vehicle)
- Unknown: `a-u-G` (unknown ground entity)

### Timestamp Format

CoT uses ISO 8601 with timezone:
```python
from datetime import datetime, timezone, timedelta

time = datetime.now(timezone.utc).isoformat()
stale = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
```

---

## Test-Driven Development Plan

### Phase 1: CoT Generation (TDD)

**Step 1: Write failing tests**

```python
# tests/test_cot_generator.py
import pytest
from datetime import datetime, timezone
from src.cot_generator import CoTGenerator
from src.cot_schemas import SentinelDetection, BoundingBox

def test_cot_generator_creates_valid_xml():
    """Test basic CoT XML generation"""
    detection = SentinelDetection(
        node_id="sentry-01",
        timestamp=datetime.now(timezone.utc),
        latitude=70.5,
        longitude=-100.2,
        altitude_m=50.0,
        detections=[{
            "bbox": BoundingBox(xmin=100, ymin=150, xmax=300, ymax=400),
            "class": "person",
            "confidence": 0.89,
            "class_id": 0
        }],
        detection_count=1,
        inference_time_ms=87.5
    )
    
    generator = CoTGenerator()
    cot_xml = generator.generate(detection)
    
    assert cot_xml is not None
    assert "<?xml version" in cot_xml
    assert "event version=\"2.0\"" in cot_xml
    assert "a-f-G-E-S" in cot_xml

def test_cot_includes_detection_metadata():
    """Test CoT includes all detection details"""
    detection = create_sample_detection()
    
    generator = CoTGenerator()
    cot_xml = generator.generate(detection)
    
    assert "sentry-01" in cot_xml
    assert "person" in cot_xml
    assert "0.89" in cot_xml
    assert "lat=\"70.5\"" in cot_xml

def test_cot_generates_unique_uids():
    """Test each CoT event has unique UID"""
    detection = create_sample_detection()
    generator = CoTGenerator()
    
    cot1 = generator.generate(detection)
    cot2 = generator.generate(detection)
    
    # Extract UIDs and verify they're different
    import re
    uid1 = re.search(r'uid="([^"]+)"', cot1).group(1)
    uid2 = re.search(r'uid="([^"]+)"', cot2).group(1)
    
    assert uid1 != uid2

def test_cot_timestamp_format():
    """Test CoT uses correct ISO 8601 timestamp format"""
    detection = create_sample_detection()
    generator = CoTGenerator()
    cot_xml = generator.generate(detection)
    
    # Should match ISO 8601 with timezone
    import re
    timestamp_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+[+-]\d{2}:\d{2}'
    assert re.search(timestamp_pattern, cot_xml)

def test_cot_stale_time_future():
    """Test stale time is in the future"""
    detection = create_sample_detection()
    generator = CoTGenerator()
    cot_xml = generator.generate(detection)
    
    # Extract stale time and verify it's after current time
    import re
    from datetime import datetime
    stale_match = re.search(r'stale="([^"]+)"', cot_xml)
    stale_time = datetime.fromisoformat(stale_match.group(1))
    
    assert stale_time > datetime.now(timezone.utc)
```

**Step 2: Implement CoT generator**

```python
# src/cot_generator.py
from lxml import etree
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
import uuid

from .cot_schemas import SentinelDetection

class CoTGenerator:
    """Generate Cursor-on-Target (CoT) XML from Sentinel detections"""
    
    def __init__(self, stale_minutes: int = 5):
        """
        Initialize CoT generator.
        
        Args:
            stale_minutes: Minutes until CoT event is considered stale
        """
        self.stale_minutes = stale_minutes
    
    def generate(self, detection: SentinelDetection) -> str:
        """
        Generate CoT XML from Sentinel detection.
        
        Args:
            detection: Sentinel detection data
            
        Returns:
            CoT XML string
        """
        # Create root event element
        event = etree.Element("event")
        event.set("version", "2.0")
        event.set("uid", self._generate_uid())
        event.set("type", "a-f-G-E-S")  # Friendly ground sensor
        
        # Timestamps
        time_str = detection.timestamp.isoformat()
        stale_time = detection.timestamp + timedelta(minutes=self.stale_minutes)
        stale_str = stale_time.isoformat()
        
        event.set("time", time_str)
        event.set("start", time_str)
        event.set("stale", stale_str)
        
        # Point (location)
        point = etree.SubElement(event, "point")
        point.set("lat", f"{detection.latitude:.6f}")
        point.set("lon", f"{detection.longitude:.6f}")
        point.set("hae", f"{detection.altitude_m:.2f}")
        point.set("ce", f"{detection.accuracy_m:.2f}" if detection.accuracy_m else "10.0")
        point.set("le", "5.0")  # Default linear error
        
        # Detail section
        detail = etree.SubElement(event, "detail")
        
        # Contact
        contact = etree.SubElement(detail, "contact")
        contact.set("callsign", detection.node_id)
        
        # Remarks (human-readable summary)
        remarks = etree.SubElement(detail, "remarks")
        remarks_text = self._generate_remarks(detection)
        remarks.text = remarks_text
        
        # Flow tags (Sentinel metadata)
        flow_tags = etree.SubElement(detail, "_flow-tags_")
        flow_tags.set("sentinel_version", "2.0")
        
        # Detection details (for each detected object)
        for det in detection.detections:
            det_elem = etree.SubElement(detail, "detection")
            
            obj_class = etree.SubElement(det_elem, "object_class")
            obj_class.text = det["class"]
            
            confidence = etree.SubElement(det_elem, "confidence")
            confidence.text = f"{det['confidence']:.3f}"
            
            inference_time = etree.SubElement(det_elem, "inference_time_ms")
            inference_time.text = f"{detection.inference_time_ms:.2f}"
            
            bbox = etree.SubElement(det_elem, "bbox")
            bbox.set("xmin", str(det["bbox"].xmin))
            bbox.set("ymin", str(det["bbox"].ymin))
            bbox.set("xmax", str(det["bbox"].xmax))
            bbox.set("ymax", str(det["bbox"].ymax))
        
        # Convert to string with pretty printing
        xml_str = etree.tostring(
            event,
            pretty_print=True,
            xml_declaration=True,
            encoding="UTF-8"
        ).decode("utf-8")
        
        return xml_str
    
    def _generate_uid(self) -> str:
        """Generate unique event ID"""
        return f"SENTINEL-DET-{uuid.uuid4()}"
    
    def _generate_remarks(self, detection: SentinelDetection) -> str:
        """Generate human-readable remarks"""
        if detection.detection_count == 0:
            return f"Sentinel node {detection.node_id}: No detections"
        
        # Summarize detections
        classes = [det["class"] for det in detection.detections]
        class_counts = {}
        for cls in classes:
            class_counts[cls] = class_counts.get(cls, 0) + 1
        
        summary_parts = [f"{count} {cls}(s)" for cls, count in class_counts.items()]
        summary = ", ".join(summary_parts)
        
        return f"Sentinel node {detection.node_id}: Detected {summary}"
    
    def generate_batch(self, detections: list[SentinelDetection]) -> list[str]:
        """
        Generate CoT XML for multiple detections.
        
        Args:
            detections: List of Sentinel detections
            
        Returns:
            List of CoT XML strings
        """
        return [self.generate(det) for det in detections]
```

---

### Phase 2: Pydantic Schemas

```python
# src/cot_schemas.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class BoundingBox(BaseModel):
    """Bounding box coordinates"""
    xmin: int
    ymin: int
    xmax: int
    ymax: int

class Detection(BaseModel):
    """Single object detection"""
    bbox: BoundingBox
    class_name: str = Field(alias="class")
    confidence: float
    class_id: int
    
    class Config:
        populate_by_name = True

class SentinelDetection(BaseModel):
    """Sentinel detection input for CoT generation"""
    node_id: str
    timestamp: datetime
    latitude: float
    longitude: float
    altitude_m: float = 0.0
    accuracy_m: Optional[float] = 10.0
    detections: List[dict]
    detection_count: int
    inference_time_ms: float
    model: Optional[str] = "yolov5n"
```

---

### Phase 3: CoT Validation (TDD)

**Step 1: Write failing tests**

```python
# tests/test_cot_validator.py
import pytest
from src.cot_validator import CoTValidator
from src.cot_generator import CoTGenerator
from tests.conftest import create_sample_detection

def test_validator_accepts_valid_cot():
    """Test validator accepts properly formed CoT"""
    detection = create_sample_detection()
    generator = CoTGenerator()
    cot_xml = generator.generate(detection)
    
    validator = CoTValidator()
    is_valid, errors = validator.validate(cot_xml)
    
    assert is_valid
    assert len(errors) == 0

def test_validator_rejects_invalid_xml():
    """Test validator rejects malformed XML"""
    invalid_xml = "<event>incomplete"
    
    validator = CoTValidator()
    is_valid, errors = validator.validate(invalid_xml)
    
    assert not is_valid
    assert len(errors) > 0

def test_validator_checks_required_fields():
    """Test validator ensures required CoT fields present"""
    # Missing uid attribute
    invalid_cot = """<?xml version="1.0"?>
    <event version="2.0" type="a-f-G-E-S" time="2025-01-01T00:00:00Z">
        <point lat="70.0" lon="-100.0" hae="0" ce="10" le="5"/>
    </event>
    """
    
    validator = CoTValidator()
    is_valid, errors = validator.validate(invalid_cot)
    
    assert not is_valid
    assert any("uid" in err.lower() for err in errors)

def test_validator_checks_coordinate_ranges():
    """Test validator ensures lat/lon in valid ranges"""
    # Latitude out of range
    invalid_cot = """<?xml version="1.0"?>
    <event version="2.0" uid="test-123" type="a-f-G-E-S" time="2025-01-01T00:00:00Z">
        <point lat="91.0" lon="-100.0" hae="0" ce="10" le="5"/>
    </event>
    """
    
    validator = CoTValidator()
    is_valid, errors = validator.validate(invalid_cot)
    
    assert not is_valid
    assert any("latitude" in err.lower() for err in errors)
```

**Step 2: Implement validator**

```python
# src/cot_validator.py
from lxml import etree
from typing import Tuple, List
import os

class CoTValidator:
    """Validate CoT XML messages against schema and rules"""
    
    def __init__(self, schema_path: str = None):
        """
        Initialize validator.
        
        Args:
            schema_path: Path to CoT XSD schema file (optional)
        """
        self.schema_path = schema_path
        self.xmlschema = None
        
        if schema_path and os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                schema_doc = etree.parse(f)
                self.xmlschema = etree.XMLSchema(schema_doc)
    
    def validate(self, cot_xml: str) -> Tuple[bool, List[str]]:
        """
        Validate CoT XML message.
        
        Args:
            cot_xml: CoT XML string
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Parse XML
        try:
            doc = etree.fromstring(cot_xml.encode('utf-8'))
        except etree.XMLSyntaxError as e:
            return False, [f"XML syntax error: {str(e)}"]
        
        # Validate against schema if available
        if self.xmlschema:
            if not self.xmlschema.validate(doc):
                for error in self.xmlschema.error_log:
                    errors.append(f"Schema validation error: {error.message}")
        
        # Manual validation checks
        validation_errors = self._validate_structure(doc)
        errors.extend(validation_errors)
        
        return len(errors) == 0, errors
    
    def _validate_structure(self, doc: etree._Element) -> List[str]:
        """Validate CoT structure and required fields"""
        errors = []
        
        # Check root element
        if doc.tag != "event":
            errors.append("Root element must be 'event'")
            return errors
        
        # Check required attributes
        required_attrs = ["version", "uid", "type", "time"]
        for attr in required_attrs:
            if attr not in doc.attrib:
                errors.append(f"Missing required attribute: {attr}")
        
        # Check version
        if doc.get("version") != "2.0":
            errors.append("Only CoT version 2.0 is supported")
        
        # Check point element
        point = doc.find("point")
        if point is None:
            errors.append("Missing required 'point' element")
        else:
            # Validate coordinates
            try:
                lat = float(point.get("lat", "0"))
                lon = float(point.get("lon", "0"))
                
                if not (-90 <= lat <= 90):
                    errors.append(f"Latitude out of range: {lat}")
                if not (-180 <= lon <= 180):
                    errors.append(f"Longitude out of range: {lon}")
            except ValueError as e:
                errors.append(f"Invalid coordinate value: {str(e)}")
        
        return errors
    
    def validate_batch(self, cot_xmls: List[str]) -> List[Tuple[bool, List[str]]]:
        """Validate multiple CoT messages"""
        return [self.validate(xml) for xml in cot_xmls]
```

---

### Phase 4: Mock TAK Server (TDD)

**Step 1: Write failing tests**

```python
# tests/test_tak_client.py
import pytest
import asyncio
from src.tak_client import TAKClient
from src.mock_tak_server import MockTAKServer
from src.cot_generator import CoTGenerator
from tests.conftest import create_sample_detection

@pytest.mark.asyncio
async def test_tak_client_connects():
    """Test TAK client can connect to mock server"""
    server = MockTAKServer(port=8089)
    await server.start()
    
    try:
        client = TAKClient(host="localhost", port=8089)
        connected = await client.connect()
        assert connected
        await client.disconnect()
    finally:
        await server.stop()

@pytest.mark.asyncio
async def test_tak_client_sends_cot():
    """Test TAK client can send CoT messages"""
    server = MockTAKServer(port=8089)
    await server.start()
    
    try:
        # Generate CoT
        detection = create_sample_detection()
        generator = CoTGenerator()
        cot_xml = generator.generate(detection)
        
        # Send via client
        client = TAKClient(host="localhost", port=8089)
        await client.connect()
        success = await client.send_cot(cot_xml)
        
        assert success
        
        # Verify server received it
        received = server.get_received_messages()
        assert len(received) == 1
        assert "SENTINEL-DET" in received[0]
        
        await client.disconnect()
    finally:
        await server.stop()

@pytest.mark.asyncio
async def test_tak_client_handles_disconnect():
    """Test TAK client handles disconnection gracefully"""
    server = MockTAKServer(port=8089)
    await server.start()
    
    client = TAKClient(host="localhost", port=8089)
    await client.connect()
    
    # Stop server (simulate disconnect)
    await server.stop()
    
    # Client should detect disconnect
    cot_xml = "<event></event>"
    success = await client.send_cot(cot_xml)
    
    assert not success
    assert not client.is_connected()
```

**Step 2: Implement mock TAK server**

```python
# src/mock_tak_server.py
import asyncio
from typing import List
import logging

logger = logging.getLogger(__name__)

class MockTAKServer:
    """Mock TAK server for testing CoT transmission"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8089):
        """
        Initialize mock TAK server.
        
        Args:
            host: Host to bind to
            port: Port to listen on
        """
        self.host = host
        self.port = port
        self.server = None
        self.received_messages: List[str] = []
        self.clients = []
    
    async def start(self):
        """Start the mock TAK server"""
        self.server = await asyncio.start_server(
            self._handle_client,
            self.host,
            self.port
        )
        logger.info(f"Mock TAK server started on {self.host}:{self.port}")
    
    async def stop(self):
        """Stop the mock TAK server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("Mock TAK server stopped")
    
    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle client connection"""
        addr = writer.get_extra_info('peername')
        logger.info(f"Client connected: {addr}")
        self.clients.append((reader, writer))
        
        try:
            while True:
                # Read CoT message (assumes newline-delimited)
                data = await reader.readline()
                if not data:
                    break
                
                message = data.decode('utf-8').strip()
                logger.info(f"Received CoT message ({len(message)} bytes)")
                self.received_messages.append(message)
                
                # Send acknowledgment
                writer.write(b"ACK\n")
                await writer.drain()
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            logger.info(f"Client disconnected: {addr}")
            writer.close()
            await writer.wait_closed()
    
    def get_received_messages(self) -> List[str]:
        """Get all received CoT messages"""
        return self.received_messages.copy()
    
    def clear_messages(self):
        """Clear received messages"""
        self.received_messages.clear()
```

**Step 3: Implement TAK client**

```python
# src/tak_client.py
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TAKClient:
    """Client for sending CoT messages to TAK server"""
    
    def __init__(self, host: str = "localhost", port: int = 8089):
        """
        Initialize TAK client.
        
        Args:
            host: TAK server host
            port: TAK server port
        """
        self.host = host
        self.port = port
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
    
    async def connect(self) -> bool:
        """
        Connect to TAK server.
        
        Returns:
            True if connected successfully
        """
        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.host,
                self.port
            )
            logger.info(f"Connected to TAK server at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to TAK server: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from TAK server"""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
            logger.info("Disconnected from TAK server")
    
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self.writer is not None and not self.writer.is_closing()
    
    async def send_cot(self, cot_xml: str) -> bool:
        """
        Send CoT message to TAK server.
        
        Args:
            cot_xml: CoT XML string
            
        Returns:
            True if sent successfully
        """
        if not self.is_connected():
            logger.error("Not connected to TAK server")
            return False
        
        try:
            # Send CoT message (newline-delimited)
            message = cot_xml.strip() + "\n"
            self.writer.write(message.encode('utf-8'))
            await self.writer.drain()
            
            # Wait for acknowledgment (optional)
            ack = await asyncio.wait_for(self.reader.readline(), timeout=5.0)
            if ack:
                logger.info("CoT message sent and acknowledged")
                return True
            else:
                logger.warning("No acknowledgment received")
                return False
                
        except asyncio.TimeoutError:
            logger.error("Timeout waiting for acknowledgment")
            return False
        except Exception as e:
            logger.error(f"Error sending CoT message: {e}")
            return False
    
    async def send_batch(self, cot_xmls: list[str]) -> int:
        """
        Send multiple CoT messages.
        
        Args:
            cot_xmls: List of CoT XML strings
            
        Returns:
            Number of messages sent successfully
        """
        success_count = 0
        for cot_xml in cot_xmls:
            if await self.send_cot(cot_xml):
                success_count += 1
        return success_count
```

---

### Phase 5: Integration with Module 2

**Backend API endpoints to add:**

```python
# In Module 2's src/main.py - add these endpoints

from atak_integration.src.cot_generator import CoTGenerator
from atak_integration.src.tak_client import TAKClient

cot_generator = CoTGenerator()
tak_client = None  # Optional: initialize if real TAK server configured

@app.post("/api/cot/generate")
async def generate_cot(detection_id: int, db: AsyncSession = Depends(get_db)):
    """Generate CoT XML for a specific detection"""
    result = await db.execute(
        select(Detection).where(Detection.id == detection_id)
    )
    detection = result.scalar_one_or_none()
    
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")
    
    # Convert to Sentinel detection format
    sentinel_det = SentinelDetection(
        node_id=detection.node.node_id,
        timestamp=detection.timestamp,
        latitude=detection.latitude,
        longitude=detection.longitude,
        altitude_m=detection.altitude_m or 0.0,
        accuracy_m=detection.accuracy_m,
        detections=json.loads(detection.detections_json),
        detection_count=detection.detection_count,
        inference_time_ms=detection.inference_time_ms or 0.0,
        model=detection.model
    )
    
    # Generate CoT
    cot_xml = cot_generator.generate(sentinel_det)
    
    return {
        "detection_id": detection_id,
        "cot_xml": cot_xml,
        "cot_size_bytes": len(cot_xml.encode('utf-8'))
    }

@app.post("/api/cot/send")
async def send_cot_to_tak(detection_id: int, db: AsyncSession = Depends(get_db)):
    """Generate and send CoT to TAK server (if configured)"""
    if tak_client is None or not tak_client.is_connected():
        raise HTTPException(
            status_code=503,
            detail="TAK server not configured or not connected"
        )
    
    # Generate CoT (reuse logic from above)
    cot_response = await generate_cot(detection_id, db)
    cot_xml = cot_response["cot_xml"]
    
    # Send to TAK
    success = await tak_client.send_cot(cot_xml)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send CoT to TAK server")
    
    return {
        "detection_id": detection_id,
        "sent": True,
        "cot_size_bytes": cot_response["cot_size_bytes"]
    }
```

---

## Configuration

```python
# src/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Configuration for ATAK/CoT integration"""
    
    # CoT generation
    COT_STALE_MINUTES: int = 5
    COT_VERSION: str = "2.0"
    
    # TAK server (optional)
    TAK_SERVER_HOST: str = "localhost"
    TAK_SERVER_PORT: int = 8089
    TAK_SERVER_ENABLED: bool = False
    
    # Mock server (for testing)
    MOCK_TAK_ENABLED: bool = True
    MOCK_TAK_PORT: int = 8089
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
```

---

## Requirements Files

**requirements.txt:**
```
lxml==5.1.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
```

**requirements-dev.txt:**
```
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
xmlschema==2.5.0
```

---

## pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = 
    --verbose
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=85
```

---

## Example Files

**examples/sample_detection.json:**
```json
{
  "node_id": "sentry-01",
  "timestamp": "2025-07-15T14:23:45.123456+00:00",
  "latitude": 70.5234,
  "longitude": -100.8765,
  "altitude_m": 45.2,
  "accuracy_m": 10.0,
  "detections": [
    {
      "bbox": {
        "xmin": 100,
        "ymin": 150,
        "xmax": 300,
        "ymax": 400
      },
      "class": "person",
      "confidence": 0.89,
      "class_id": 0
    }
  ],
  "detection_count": 1,
  "inference_time_ms": 87.5,
  "model": "yolov5n"
}
```

**examples/sample_cot.xml:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<event version="2.0" uid="SENTINEL-DET-a1b2c3d4-e5f6-7890-abcd-ef1234567890" 
       type="a-f-G-E-S" 
       time="2025-07-15T14:23:45.123456+00:00" 
       start="2025-07-15T14:23:45.123456+00:00" 
       stale="2025-07-15T14:28:45.123456+00:00">
  <point lat="70.523400" lon="-100.876500" hae="45.20" ce="10.00" le="5.0"/>
  <detail>
    <contact callsign="sentry-01"/>
    <remarks>Sentinel node sentry-01: Detected 1 person(s)</remarks>
    <_flow-tags_ sentinel_version="2.0"/>
    <detection>
      <object_class>person</object_class>
      <confidence>0.890</confidence>
      <inference_time_ms>87.50</inference_time_ms>
      <bbox xmin="100" ymin="150" xmax="300" ymax="400"/>
    </detection>
  </detail>
</event>
```

---

## Claude Code Implementation Prompts

### Session 1: Core CoT Generation

```
Create Module 3 (ATAK/CoT Integration) for Sentinel v2 Arctic surveillance system.

REQUIREMENTS:
- Python 3.11 with lxml for XML generation
- Pydantic for data validation
- Test-driven development (write tests first)
- Full CoT 2.0 compliance

STEP 1: Project Setup
1. Create the directory structure shown in specification
2. Create requirements.txt and requirements-dev.txt
3. Create pytest.ini configuration
4. Create .env.example

STEP 2: TDD - Pydantic Schemas
1. Create tests/test_cot_schemas.py
2. Implement src/cot_schemas.py with all data models
3. Run pytest and verify tests pass

STEP 3: TDD - CoT Generator
1. Create tests/test_cot_generator.py with comprehensive tests for:
   - Basic XML generation
   - UID uniqueness
   - Timestamp formatting
   - Detection metadata inclusion
   - Batch generation
2. Implement src/cot_generator.py
3. Run pytest and verify all tests pass

Success criteria:
- All tests pass
- Test coverage >85%
- Generated CoT XML is valid and well-formed
```

### Session 2: Validation & Mock Server

```
Continue Module 3 - Add validation and mock TAK server.

STEP 4: TDD - CoT Validator
1. Create tests/test_cot_validator.py with tests for:
   - Valid CoT acceptance
   - Invalid XML rejection
   - Required field checking
   - Coordinate range validation
2. Implement src/cot_validator.py
3. Verify tests pass

STEP 5: TDD - Mock TAK Server
1. Create tests/test_tak_client.py with async tests for:
   - Client connection
   - CoT transmission
   - Disconnect handling
   - Batch sending
2. Implement src/mock_tak_server.py
3. Implement src/tak_client.py
4. Verify all async tests pass

Success criteria:
- All async tests pass
- Mock server handles multiple clients
- TAK client can send and receive acknowledgments
- Test coverage >85%
```

### Session 3: Integration & Documentation

```
Finalize Module 3 - Integration examples and documentation.

STEP 6: Integration Tests
1. Create tests/test_integration.py for end-to-end flows:
   - Detection → CoT generation → validation → transmission
2. Verify full pipeline works

STEP 7: Examples & Documentation
1. Create example files (sample_detection.json, sample_cot.xml)
2. Create comprehensive README.md with:
   - CoT specification overview
   - Quick start guide
   - API usage examples
   - Integration with Module 2
   - TAK server setup (optional)
3. Add inline docstrings to all functions

Success criteria:
- Integration tests pass
- Examples are clear and runnable
- README includes curl/Python examples
- All code has docstrings
```

---

## Success Criteria

**Must Have:**
- ✅ All tests pass (pytest)
- ✅ Test coverage >85%
- ✅ CoT XML generation working
- ✅ CoT validation functional
- ✅ Mock TAK server for testing
- ✅ TAK client can connect and send

**Should Have:**
- ✅ Type hints on all functions
- ✅ Comprehensive docstrings
- ✅ Example files demonstrating usage
- ✅ Integration with Module 2 documented

**Nice to Have:**
- ✅ Real TAK server connection documented
- ✅ CoT XSD schema validation
- ✅ Batch processing optimizations

---

## Real TAK Server Integration (Future)

**When you're ready to connect to a real TAK server:**

1. **Set up TAK server:**
   - Download FreeTAKServer or use a managed TAK instance
   - Configure network access

2. **Update configuration:**
   ```bash
   TAK_SERVER_ENABLED=true
   TAK_SERVER_HOST=your-tak-server.com
   TAK_SERVER_PORT=8089
   ```

3. **Initialize TAK client in Module 2:**
   ```python
   if settings.TAK_SERVER_ENABLED:
       tak_client = TAKClient(
           host=settings.TAK_SERVER_HOST,
           port=settings.TAK_SERVER_PORT
       )
       await tak_client.connect()
   ```

4. **Automatic CoT transmission:**
   - Hook into detection ingestion endpoint
   - Generate and send CoT for each detection
   - Or: batch send every N seconds

---

## Next Steps After Module 3

Once Module 3 is complete and tested:
1. Integrate with Module 2 backend (add CoT endpoints)
2. Test end-to-end: Edge detection → Backend → CoT generation
3. Create Module 4 (Dashboard with CoT display option)
4. Document ATAK integration in main README

**End of Module 3 Specification**
