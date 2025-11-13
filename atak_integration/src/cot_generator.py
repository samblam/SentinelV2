"""CoT (Cursor on Target) XML generation from Sentinel detections."""
import uuid
from datetime import datetime, timezone, timedelta
from typing import List
from lxml import etree

from .cot_schemas import SentinelDetection
from .config import settings


class CoTGenerator:
    """Generate CoT 2.0 XML messages from Sentinel detections.

    This class converts Sentinel detection events into Cursor-on-Target (CoT)
    XML messages compatible with ATAK and other TAK clients.

    Attributes:
        cot_type: CoT event type (default: a-f-G-E-S for friendly ground sensor)
        stale_minutes: Minutes until CoT message is considered stale (default: 5)
        sentinel_version: Sentinel system version for metadata
    """

    def __init__(
        self,
        cot_type: str = None,
        stale_minutes: int = None,
        sentinel_version: str = "2.0"
    ):
        """Initialize CoT generator.

        Args:
            cot_type: CoT event type (default from settings)
            stale_minutes: Stale time in minutes (default from settings)
            sentinel_version: Sentinel version for flow tags
        """
        self.cot_type = cot_type or settings.COT_TYPE
        self.stale_minutes = stale_minutes or settings.COT_STALE_MINUTES
        self.sentinel_version = sentinel_version

    def generate(self, detection: SentinelDetection) -> str:
        """Generate CoT XML message from a Sentinel detection.

        Args:
            detection: Sentinel detection event

        Returns:
            CoT XML message as string

        Example:
            >>> from src.cot_schemas import SentinelDetection
            >>> from datetime import datetime, timezone
            >>> detection = SentinelDetection(
            ...     node_id="sentry-01",
            ...     timestamp=datetime.now(timezone.utc),
            ...     latitude=70.5,
            ...     longitude=-100.2,
            ...     detections=[],
            ...     detection_count=0,
            ...     inference_time_ms=50.0
            ... )
            >>> generator = CoTGenerator()
            >>> cot_xml = generator.generate(detection)
        """
        # Create root event element
        event = etree.Element("event")
        event.set("version", "2.0")
        event.set("uid", self._generate_uid())
        event.set("type", self.cot_type)

        # Set timestamps
        time_str = self._format_timestamp(detection.timestamp)
        event.set("time", time_str)
        event.set("start", time_str)
        event.set("stale", self._calculate_stale_time(detection.timestamp))

        # Add point element (location)
        point = etree.SubElement(event, "point")
        point.set("lat", str(detection.latitude))
        point.set("lon", str(detection.longitude))
        point.set("hae", str(detection.altitude_m))
        point.set("ce", str(detection.accuracy_m))  # circular error
        point.set("le", "9999999.0")  # linear error (unknown)

        # Add detail element (metadata)
        detail = etree.SubElement(event, "detail")

        # Contact information
        contact = etree.SubElement(detail, "contact")
        contact.set("callsign", detection.node_id)

        # Remarks with detection summary
        remarks = etree.SubElement(detail, "remarks")
        remarks.text = self._create_remarks(detection)

        # Flow tags for Sentinel metadata
        flow_tags = etree.SubElement(detail, "_flow-tags_")
        flow_tags.set("sentinel_version", self.sentinel_version)

        # Add detection details for each detected object
        for det_dict in detection.detections:
            if self._validate_detection_dict(det_dict):
                self._add_detection_element(detail, det_dict, detection.inference_time_ms)

        # Convert to XML string
        xml_bytes = etree.tostring(
            event,
            encoding='UTF-8',
            xml_declaration=True,
            pretty_print=True
        )

        return xml_bytes.decode('utf-8')

    def generate_batch(self, detections: List[SentinelDetection]) -> List[str]:
        """Generate multiple CoT messages from a list of detections.

        Args:
            detections: List of Sentinel detection events

        Returns:
            List of CoT XML messages as strings

        Example:
            >>> detections = [detection1, detection2, detection3]
            >>> generator = CoTGenerator()
            >>> cot_messages = generator.generate_batch(detections)
            >>> len(cot_messages)
            3
        """
        return [self.generate(detection) for detection in detections]

    def _generate_uid(self) -> str:
        """Generate unique identifier for CoT message.

        Returns:
            UID string in format SENTINEL-DET-{uuid}
        """
        return f"SENTINEL-DET-{uuid.uuid4()}"

    def _format_timestamp(self, dt: datetime) -> str:
        """Format datetime as CoT-compatible ISO 8601 string.

        Args:
            dt: Datetime to format

        Returns:
            ISO 8601 formatted string with Z suffix
        """
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat().replace('+00:00', 'Z')

    def _calculate_stale_time(self, timestamp: datetime) -> str:
        """Calculate stale time for CoT message.

        Args:
            timestamp: Original detection timestamp

        Returns:
            ISO 8601 formatted stale time (timestamp + stale_minutes)
        """
        stale_dt = timestamp + timedelta(minutes=self.stale_minutes)
        return self._format_timestamp(stale_dt)

    def _create_remarks(self, detection: SentinelDetection) -> str:
        """Create remarks text summarizing the detection.

        Args:
            detection: Sentinel detection event

        Returns:
            Human-readable remarks string
        """
        if detection.detection_count == 0:
            return f"No detections from {detection.node_id}"

        if detection.detection_count == 1:
            det = detection.detections[0]
            class_name = det.get("class", "unknown")
            confidence = det.get("confidence", 0.0)
            return f"{class_name.capitalize()} detected (conf: {confidence:.2f})"

        # Multiple detections
        class_counts = {}
        for det in detection.detections:
            class_name = det.get("class", "unknown")
            class_counts[class_name] = class_counts.get(class_name, 0) + 1

        summary_parts = [f"{count} {cls}" for cls, count in class_counts.items()]
        return f"Multiple detections: {', '.join(summary_parts)}"

    def _validate_detection_dict(self, det_dict: dict) -> bool:
        """Validate detection dict structure before XML generation.

        Args:
            det_dict: Detection dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        # Check if it's a dictionary
        if not isinstance(det_dict, dict):
            return False

        # Required keys for valid detection
        required_keys = {"class", "confidence"}

        # Check for required keys
        if not required_keys.issubset(det_dict.keys()):
            return False

        # Validate confidence is numeric
        confidence = det_dict.get("confidence")
        if not isinstance(confidence, (int, float)):
            return False

        # Validate confidence range (0.0 to 1.0)
        if not 0.0 <= confidence <= 1.0:
            return False

        # Validate bbox if present
        if "bbox" in det_dict:
            bbox = det_dict["bbox"]
            if isinstance(bbox, dict):
                # Check bbox has required keys
                required_bbox_keys = {"xmin", "ymin", "xmax", "ymax"}
                if not required_bbox_keys.issubset(bbox.keys()):
                    return False
                # Validate all values are numeric
                for key in required_bbox_keys:
                    if not isinstance(bbox[key], (int, float)):
                        return False

        return True

    def _add_detection_element(
        self,
        parent: etree.Element,
        detection_dict: dict,
        inference_time_ms: float
    ) -> None:
        """Add detection sub-element to detail element.

        Args:
            parent: Parent XML element (detail)
            detection_dict: Detection dictionary with bbox, class, confidence
            inference_time_ms: Inference time in milliseconds
        """
        detection_elem = etree.SubElement(parent, "detection")

        # Object class
        object_class = etree.SubElement(detection_elem, "object_class")
        object_class.text = detection_dict.get("class", "unknown")

        # Confidence
        confidence = etree.SubElement(detection_elem, "confidence")
        confidence.text = str(detection_dict.get("confidence", 0.0))

        # Inference time
        inference = etree.SubElement(detection_elem, "inference_time_ms")
        inference.text = str(inference_time_ms)

        # Bounding box
        if bbox := detection_dict.get("bbox", {}):
            bbox_elem = etree.SubElement(detection_elem, "bbox")
            bbox_elem.set("xmin", str(bbox.get("xmin", 0)))
            bbox_elem.set("ymin", str(bbox.get("ymin", 0)))
            bbox_elem.set("xmax", str(bbox.get("xmax", 0)))
            bbox_elem.set("ymax", str(bbox.get("ymax", 0)))
