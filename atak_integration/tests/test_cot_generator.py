"""Tests for CoT XML generation."""
import pytest
from datetime import datetime, timezone, timedelta
from lxml import etree


def test_cot_generator_creates_valid_xml(sample_sentinel_detection):
    """Test basic CoT XML generation."""
    from src.cot_generator import CoTGenerator
    from src.cot_schemas import SentinelDetection

    detection = SentinelDetection(**sample_sentinel_detection)
    generator = CoTGenerator()
    cot_xml = generator.generate(detection)

    assert cot_xml is not None
    assert '<?xml version' in cot_xml
    assert 'event version="2.0"' in cot_xml
    assert 'a-f-G-E-S' in cot_xml


def test_cot_xml_is_well_formed(sample_sentinel_detection):
    """Test CoT XML is well-formed and parseable."""
    from src.cot_generator import CoTGenerator
    from src.cot_schemas import SentinelDetection

    detection = SentinelDetection(**sample_sentinel_detection)
    generator = CoTGenerator()
    cot_xml = generator.generate(detection)

    # Should parse without errors
    root = etree.fromstring(cot_xml.encode('utf-8'))
    assert root.tag == 'event'
    assert root.get('version') == '2.0'


def test_cot_includes_detection_metadata(sample_sentinel_detection):
    """Test CoT includes all detection details."""
    from src.cot_generator import CoTGenerator
    from src.cot_schemas import SentinelDetection

    detection = SentinelDetection(**sample_sentinel_detection)
    generator = CoTGenerator()
    cot_xml = generator.generate(detection)

    assert "sentry-01" in cot_xml  # node_id/callsign
    assert "person" in cot_xml  # class name
    assert "0.89" in cot_xml  # confidence


def test_cot_uid_uniqueness():
    """Test each CoT message has unique UID."""
    from src.cot_generator import CoTGenerator
    from src.cot_schemas import SentinelDetection
    from tests.conftest import create_sample_detection

    detection1 = SentinelDetection(**create_sample_detection())
    detection2 = SentinelDetection(**create_sample_detection())

    generator = CoTGenerator()
    cot_xml1 = generator.generate(detection1)
    cot_xml2 = generator.generate(detection2)

    # Extract UIDs
    root1 = etree.fromstring(cot_xml1.encode('utf-8'))
    root2 = etree.fromstring(cot_xml2.encode('utf-8'))

    uid1 = root1.get('uid')
    uid2 = root2.get('uid')

    assert uid1 != uid2
    assert uid1.startswith('SENTINEL-DET-')
    assert uid2.startswith('SENTINEL-DET-')


def test_cot_timestamp_format(sample_sentinel_detection):
    """Test CoT timestamps are properly formatted."""
    from src.cot_generator import CoTGenerator
    from src.cot_schemas import SentinelDetection

    detection = SentinelDetection(**sample_sentinel_detection)
    generator = CoTGenerator()
    cot_xml = generator.generate(detection)

    root = etree.fromstring(cot_xml.encode('utf-8'))

    # Check timestamp attributes exist
    assert root.get('time') is not None
    assert root.get('start') is not None
    assert root.get('stale') is not None

    # Timestamps should be ISO 8601 format
    time_str = root.get('time')
    assert 'T' in time_str  # ISO 8601 has 'T' separator
    assert 'Z' in time_str or '+' in time_str  # Timezone indicator


def test_cot_point_element(sample_sentinel_detection):
    """Test CoT point element has correct coordinates."""
    from src.cot_generator import CoTGenerator
    from src.cot_schemas import SentinelDetection

    detection = SentinelDetection(**sample_sentinel_detection)
    generator = CoTGenerator()
    cot_xml = generator.generate(detection)

    root = etree.fromstring(cot_xml.encode('utf-8'))
    point = root.find('point')

    assert point is not None
    assert point.get('lat') == '70.5'
    assert point.get('lon') == '-100.2'
    assert point.get('hae') == '50.0'
    assert point.get('ce') is not None  # circular error
    assert point.get('le') is not None  # linear error


def test_cot_detail_element(sample_sentinel_detection):
    """Test CoT detail element structure."""
    from src.cot_generator import CoTGenerator
    from src.cot_schemas import SentinelDetection

    detection = SentinelDetection(**sample_sentinel_detection)
    generator = CoTGenerator()
    cot_xml = generator.generate(detection)

    root = etree.fromstring(cot_xml.encode('utf-8'))
    detail = root.find('detail')

    assert detail is not None

    # Check contact
    contact = detail.find('contact')
    assert contact is not None
    assert contact.get('callsign') == 'sentry-01'

    # Check remarks
    remarks = detail.find('remarks')
    assert remarks is not None
    assert remarks.text is not None


def test_cot_detection_elements(sample_sentinel_detection):
    """Test CoT includes detection sub-elements."""
    from src.cot_generator import CoTGenerator
    from src.cot_schemas import SentinelDetection

    detection = SentinelDetection(**sample_sentinel_detection)
    generator = CoTGenerator()
    cot_xml = generator.generate(detection)

    root = etree.fromstring(cot_xml.encode('utf-8'))
    detail = root.find('detail')

    # Check detection element exists
    detection_elem = detail.find('detection')
    assert detection_elem is not None

    # Check detection children
    object_class = detection_elem.find('object_class')
    assert object_class is not None
    assert object_class.text == 'person'

    confidence = detection_elem.find('confidence')
    assert confidence is not None
    assert confidence.text == '0.89'


def test_cot_multiple_detections(sample_multi_detection):
    """Test CoT generation with multiple detected objects."""
    from src.cot_generator import CoTGenerator
    from src.cot_schemas import SentinelDetection

    detection = SentinelDetection(**sample_multi_detection)
    generator = CoTGenerator()
    cot_xml = generator.generate(detection)

    root = etree.fromstring(cot_xml.encode('utf-8'))
    detail = root.find('detail')

    # Should have multiple detection elements
    detections = detail.findall('detection')
    assert len(detections) == 2

    # Check first detection
    assert detections[0].find('object_class').text == 'person'
    assert detections[0].find('confidence').text == '0.92'

    # Check second detection
    assert detections[1].find('object_class').text == 'vehicle'
    assert detections[1].find('confidence').text == '0.85'


def test_cot_stale_time_calculation(sample_sentinel_detection):
    """Test CoT stale time is properly calculated."""
    from src.cot_generator import CoTGenerator
    from src.cot_schemas import SentinelDetection

    detection = SentinelDetection(**sample_sentinel_detection)
    generator = CoTGenerator()
    cot_xml = generator.generate(detection)

    root = etree.fromstring(cot_xml.encode('utf-8'))

    time_str = root.get('time')
    stale_str = root.get('stale')

    # Parse timestamps
    time_dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
    stale_dt = datetime.fromisoformat(stale_str.replace('Z', '+00:00'))

    # Stale should be after time
    assert stale_dt > time_dt

    # Stale should be approximately 5 minutes after time (default)
    time_diff = (stale_dt - time_dt).total_seconds()
    assert 290 <= time_diff <= 310  # 5 minutes ±10 seconds tolerance


def test_cot_type_attribute(sample_sentinel_detection):
    """Test CoT type attribute is correct."""
    from src.cot_generator import CoTGenerator
    from src.cot_schemas import SentinelDetection

    detection = SentinelDetection(**sample_sentinel_detection)
    generator = CoTGenerator()
    cot_xml = generator.generate(detection)

    root = etree.fromstring(cot_xml.encode('utf-8'))

    # Default type should be friendly ground sensor
    assert root.get('type') == 'a-f-G-E-S'


def test_cot_generator_with_minimal_detection():
    """Test CoT generation with minimal detection (defaults)."""
    from src.cot_generator import CoTGenerator
    from src.cot_schemas import SentinelDetection

    minimal = {
        "node_id": "test-node",
        "timestamp": datetime.now(timezone.utc),
        "latitude": 70.0,
        "longitude": -100.0,
        "detections": [],
        "detection_count": 0,
        "inference_time_ms": 50.0
    }

    detection = SentinelDetection(**minimal)
    generator = CoTGenerator()
    cot_xml = generator.generate(detection)

    # Should generate valid XML even with no detections
    root = etree.fromstring(cot_xml.encode('utf-8'))
    assert root.get('version') == '2.0'
    assert root.find('point') is not None


def test_cot_generator_batch_generation():
    """Test batch generation of multiple CoT messages."""
    from src.cot_generator import CoTGenerator
    from src.cot_schemas import SentinelDetection
    from tests.conftest import create_sample_detection

    detections = [
        SentinelDetection(**create_sample_detection(node_id=f"sentry-{i}"))
        for i in range(5)
    ]

    generator = CoTGenerator()
    cot_messages = generator.generate_batch(detections)

    assert len(cot_messages) == 5

    # Each should be unique and valid
    uids = set()
    for cot_xml in cot_messages:
        root = etree.fromstring(cot_xml.encode('utf-8'))
        uid = root.get('uid')
        assert uid not in uids
        uids.add(uid)


def test_cot_flow_tags_element(sample_sentinel_detection):
    """Test CoT includes _flow-tags_ for metadata."""
    from src.cot_generator import CoTGenerator
    from src.cot_schemas import SentinelDetection

    detection = SentinelDetection(**sample_sentinel_detection)
    generator = CoTGenerator()
    cot_xml = generator.generate(detection)

    root = etree.fromstring(cot_xml.encode('utf-8'))
    detail = root.find('detail')

    # Check _flow-tags_
    flow_tags = detail.find('_flow-tags_')
    assert flow_tags is not None
    assert flow_tags.get('sentinel_version') is not None
