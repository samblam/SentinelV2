"""Tests for CoT XML validation."""
import pytest
from lxml import etree


def test_validator_accepts_valid_cot(sample_sentinel_detection):
    """Test validator accepts properly formed CoT."""
    from src.cot_validator import CoTValidator
    from src.cot_generator import CoTGenerator
    from src.cot_schemas import SentinelDetection

    detection = SentinelDetection(**sample_sentinel_detection)
    generator = CoTGenerator()
    cot_xml = generator.generate(detection)

    validator = CoTValidator()
    is_valid, errors = validator.validate(cot_xml)

    assert is_valid
    assert len(errors) == 0


def test_validator_rejects_malformed_xml():
    """Test validator rejects malformed XML."""
    from src.cot_validator import CoTValidator

    malformed_xml = "<?xml version='1.0'?><event><unclosed>"

    validator = CoTValidator()
    is_valid, errors = validator.validate(malformed_xml)

    assert not is_valid
    assert len(errors) > 0
    assert "malformed" in errors[0].lower() or "parse" in errors[0].lower()


def test_validator_rejects_non_xml():
    """Test validator rejects non-XML content."""
    from src.cot_validator import CoTValidator

    not_xml = "This is not XML at all"

    validator = CoTValidator()
    is_valid, errors = validator.validate(not_xml)

    assert not is_valid
    assert len(errors) > 0


def test_validator_checks_required_event_attributes():
    """Test validator checks for required event attributes."""
    from src.cot_validator import CoTValidator

    # Missing required attributes (no version, uid, type)
    incomplete_xml = """<?xml version='1.0' encoding='UTF-8'?>
    <event>
        <point lat="70.0" lon="-100.0" hae="0.0" ce="10.0" le="9999999.0"/>
    </event>
    """

    validator = CoTValidator()
    is_valid, errors = validator.validate(incomplete_xml)

    assert not is_valid
    assert len(errors) > 0


def test_validator_checks_point_element():
    """Test validator checks for required point element."""
    from src.cot_validator import CoTValidator

    # Missing point element
    no_point_xml = """<?xml version='1.0' encoding='UTF-8'?>
    <event version="2.0" uid="TEST-123" type="a-f-G-E-S" time="2025-01-01T00:00:00Z" start="2025-01-01T00:00:00Z" stale="2025-01-01T00:05:00Z">
        <detail/>
    </event>
    """

    validator = CoTValidator()
    is_valid, errors = validator.validate(no_point_xml)

    assert not is_valid
    assert any("point" in error.lower() for error in errors)


def test_validator_checks_coordinate_ranges():
    """Test validator checks coordinate value ranges."""
    from src.cot_validator import CoTValidator

    # Invalid latitude (out of range)
    invalid_lat_xml = """<?xml version='1.0' encoding='UTF-8'?>
    <event version="2.0" uid="TEST-123" type="a-f-G-E-S" time="2025-01-01T00:00:00Z" start="2025-01-01T00:00:00Z" stale="2025-01-01T00:05:00Z">
        <point lat="95.0" lon="-100.0" hae="0.0" ce="10.0" le="9999999.0"/>
    </event>
    """

    validator = CoTValidator()
    is_valid, errors = validator.validate(invalid_lat_xml)

    assert not is_valid
    assert any("latitude" in error.lower() or "coordinate" in error.lower() for error in errors)


def test_validator_checks_longitude_range():
    """Test validator checks longitude value range."""
    from src.cot_validator import CoTValidator

    # Invalid longitude (out of range)
    invalid_lon_xml = """<?xml version='1.0' encoding='UTF-8'?>
    <event version="2.0" uid="TEST-123" type="a-f-G-E-S" time="2025-01-01T00:00:00Z" start="2025-01-01T00:00:00Z" stale="2025-01-01T00:05:00Z">
        <point lat="70.0" lon="-200.0" hae="0.0" ce="10.0" le="9999999.0"/>
    </event>
    """

    validator = CoTValidator()
    is_valid, errors = validator.validate(invalid_lon_xml)

    assert not is_valid
    assert any("longitude" in error.lower() or "coordinate" in error.lower() for error in errors)


def test_validator_checks_timestamp_format():
    """Test validator checks timestamp format."""
    from src.cot_validator import CoTValidator

    # Invalid timestamp format
    invalid_time_xml = """<?xml version='1.0' encoding='UTF-8'?>
    <event version="2.0" uid="TEST-123" type="a-f-G-E-S" time="not-a-timestamp" start="2025-01-01T00:00:00Z" stale="2025-01-01T00:05:00Z">
        <point lat="70.0" lon="-100.0" hae="0.0" ce="10.0" le="9999999.0"/>
    </event>
    """

    validator = CoTValidator()
    is_valid, errors = validator.validate(invalid_time_xml)

    assert not is_valid
    assert any("time" in error.lower() or "timestamp" in error.lower() for error in errors)


def test_validator_accepts_edge_case_coordinates():
    """Test validator accepts edge case valid coordinates."""
    from src.cot_validator import CoTValidator

    # Edge case: exactly at boundaries
    edge_xml = """<?xml version='1.0' encoding='UTF-8'?>
    <event version="2.0" uid="TEST-123" type="a-f-G-E-S" time="2025-01-01T00:00:00Z" start="2025-01-01T00:00:00Z" stale="2025-01-01T00:05:00Z">
        <point lat="90.0" lon="180.0" hae="0.0" ce="10.0" le="9999999.0"/>
    </event>
    """

    validator = CoTValidator()
    is_valid, errors = validator.validate(edge_xml)

    assert is_valid
    assert len(errors) == 0


def test_validator_with_detail_element(sample_sentinel_detection):
    """Test validator accepts CoT with detail element."""
    from src.cot_validator import CoTValidator
    from src.cot_generator import CoTGenerator
    from src.cot_schemas import SentinelDetection

    # Generate full CoT with detail
    detection = SentinelDetection(**sample_sentinel_detection)
    generator = CoTGenerator()
    cot_xml = generator.generate(detection)

    validator = CoTValidator()
    is_valid, errors = validator.validate(cot_xml)

    assert is_valid
    assert len(errors) == 0


def test_validator_provides_helpful_error_messages():
    """Test validator provides clear error messages."""
    from src.cot_validator import CoTValidator

    invalid_xml = """<?xml version='1.0' encoding='UTF-8'?>
    <event version="2.0" type="a-f-G-E-S">
        <point lat="70.0" lon="-100.0"/>
    </event>
    """

    validator = CoTValidator()
    is_valid, errors = validator.validate(invalid_xml)

    assert not is_valid
    assert len(errors) > 0
    # Errors should be strings
    for error in errors:
        assert isinstance(error, str)
        assert len(error) > 0


def test_validator_batch_validation():
    """Test validator can validate multiple CoT messages."""
    from src.cot_validator import CoTValidator
    from src.cot_generator import CoTGenerator
    from src.cot_schemas import SentinelDetection
    from tests.helpers import create_sample_detection

    detections = [
        SentinelDetection(**create_sample_detection(node_id=f"sentry-{i}"))
        for i in range(3)
    ]

    generator = CoTGenerator()
    cot_messages = generator.generate_batch(detections)

    validator = CoTValidator()
    results = validator.validate_batch(cot_messages)

    assert len(results) == 3
    for is_valid, errors in results:
        assert is_valid
        assert len(errors) == 0


def test_validator_empty_string():
    """Test validator handles empty string."""
    from src.cot_validator import CoTValidator

    validator = CoTValidator()
    is_valid, errors = validator.validate("")

    assert not is_valid
    assert len(errors) > 0


def test_validator_missing_stale_time():
    """Test validator checks for stale time."""
    from src.cot_validator import CoTValidator

    # Missing stale attribute
    no_stale_xml = """<?xml version='1.0' encoding='UTF-8'?>
    <event version="2.0" uid="TEST-123" type="a-f-G-E-S" time="2025-01-01T00:00:00Z" start="2025-01-01T00:00:00Z">
        <point lat="70.0" lon="-100.0" hae="0.0" ce="10.0" le="9999999.0"/>
    </event>
    """

    validator = CoTValidator()
    is_valid, errors = validator.validate(no_stale_xml)

    assert not is_valid
    assert any("stale" in error.lower() for error in errors)
