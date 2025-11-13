"""CoT XML validation against CoT 2.0 specification."""
from typing import Tuple, List
from datetime import datetime
from lxml import etree


class CoTValidator:
    """Validate CoT XML messages against CoT 2.0 specification.

    This validator performs structural and semantic validation of CoT XML,
    checking for required elements, attributes, and valid value ranges.

    Attributes:
        required_event_attrs: Required attributes for event element
        required_point_attrs: Required attributes for point element
    """

    def __init__(self):
        """Initialize CoT validator."""
        self.required_event_attrs = ['version', 'uid', 'type', 'time', 'start', 'stale']
        self.required_point_attrs = ['lat', 'lon', 'hae', 'ce', 'le']

    def validate(self, cot_xml: str) -> Tuple[bool, List[str]]:
        """Validate a CoT XML message.

        Args:
            cot_xml: CoT XML message as string

        Returns:
            Tuple of (is_valid, errors) where:
                - is_valid: True if valid, False otherwise
                - errors: List of error messages (empty if valid)

        Example:
            >>> validator = CoTValidator()
            >>> is_valid, errors = validator.validate(cot_xml)
            >>> if not is_valid:
            ...     print(f"Validation errors: {errors}")
        """
        errors = []

        # Check for empty input
        if not cot_xml or not cot_xml.strip():
            errors.append("CoT XML is empty")
            return False, errors

        # Parse XML
        try:
            root = etree.fromstring(cot_xml.encode('utf-8'))
        except etree.XMLSyntaxError as e:
            errors.append(f"Malformed XML: {str(e)}")
            return False, errors
        except Exception as e:
            errors.append(f"XML parsing error: {str(e)}")
            return False, errors

        # Check root element is 'event'
        if root.tag != 'event':
            errors.append(f"Root element must be 'event', got '{root.tag}'")
            return False, errors

        # Validate event attributes
        errors.extend(self._validate_event_attributes(root))

        # Validate point element
        point_errors = self._validate_point_element(root)
        errors.extend(point_errors)

        # Validate timestamps
        if not point_errors:  # Only if event attrs are valid
            errors.extend(self._validate_timestamps(root))

        return len(errors) == 0, errors

    def validate_batch(self, cot_messages: List[str]) -> List[Tuple[bool, List[str]]]:
        """Validate multiple CoT messages.

        Args:
            cot_messages: List of CoT XML messages

        Returns:
            List of (is_valid, errors) tuples for each message

        Example:
            >>> validator = CoTValidator()
            >>> results = validator.validate_batch(cot_messages)
            >>> for i, (is_valid, errors) in enumerate(results):
            ...     if not is_valid:
            ...         print(f"Message {i} invalid: {errors}")
        """
        return [self.validate(cot_xml) for cot_xml in cot_messages]

    def _validate_event_attributes(self, root: etree.Element) -> List[str]:
        """Validate required event element attributes.

        Args:
            root: Root event element

        Returns:
            List of error messages
        """
        errors = []

        for attr in self.required_event_attrs:
            if attr not in root.attrib:
                errors.append(f"Missing required attribute: {attr}")

        # Validate CoT version
        version = root.get('version')
        if version and version != '2.0':
            errors.append(f"Unsupported CoT version: {version} (expected 2.0)")

        return errors

    def _validate_point_element(self, root: etree.Element) -> List[str]:
        """Validate point element and coordinates.

        Args:
            root: Root event element

        Returns:
            List of error messages
        """
        errors = []

        # Check point element exists
        point = root.find('point')
        if point is None:
            errors.append("Missing required element: point")
            return errors

        # Check required attributes
        for attr in self.required_point_attrs:
            if attr not in point.attrib:
                errors.append(f"Missing required point attribute: {attr}")

        # Validate coordinate ranges
        try:
            lat = float(point.get('lat', '0'))
            if not -90.0 <= lat <= 90.0:
                errors.append(f"Latitude out of range: {lat} (must be -90 to 90)")
        except ValueError:
            errors.append(f"Invalid latitude value: {point.get('lat')}")

        try:
            lon = float(point.get('lon', '0'))
            if not -180.0 <= lon <= 180.0:
                errors.append(f"Longitude out of range: {lon} (must be -180 to 180)")
        except ValueError:
            errors.append(f"Invalid longitude value: {point.get('lon')}")

        # Validate other numeric attributes
        for attr in ['hae', 'ce', 'le']:
            value = point.get(attr)
            if value:
                try:
                    float(value)
                except ValueError:
                    errors.append(f"Invalid numeric value for {attr}: {value}")

        return errors

    def _validate_timestamps(self, root: etree.Element) -> List[str]:
        """Validate timestamp attributes.

        Args:
            root: Root event element

        Returns:
            List of error messages
        """
        errors = []

        for attr in ['time', 'start', 'stale']:
            timestamp = root.get(attr)
            if timestamp:
                try:
                    # Try to parse as ISO 8601
                    # Replace 'Z' with '+00:00' for parsing
                    timestamp_str = timestamp.replace('Z', '+00:00')
                    datetime.fromisoformat(timestamp_str)
                except (ValueError, TypeError) as e:
                    errors.append(f"Invalid timestamp format for {attr}: {timestamp}")

        return errors
