"""
Telemetry Generator for Arctic Deployment Simulation
Generates mock GPS coordinates and node identification
"""
import random
from datetime import datetime, timezone
from typing import Dict, Any, Optional


class TelemetryGenerator:
    """Generate mock telemetry for Arctic deployment simulation"""

    def __init__(self, base_lat: float = 70.0, base_lon: float = -100.0):
        """
        Initialize telemetry generator

        Args:
            base_lat: Base Arctic latitude (default: 70°N)
            base_lon: Base Arctic longitude (default: 100°W)
        """
        self.base_lat = base_lat
        self.base_lon = base_lon
        self.node_id = self.generate_node_id()

    def generate_gps(self) -> Dict[str, float]:
        """
        Generate mock Arctic GPS coordinates

        Returns:
            Dictionary with latitude, longitude, altitude, and accuracy
        """
        # Add small random offset to simulate multiple sensors
        lat_offset = random.uniform(-0.01, 0.01)  # ~1km variation
        lon_offset = random.uniform(-0.01, 0.01)

        return {
            "latitude": round(self.base_lat + lat_offset, 6),
            "longitude": round(self.base_lon + lon_offset, 6),
            "altitude_m": round(random.uniform(0, 100), 2),
            "accuracy_m": round(random.uniform(5, 20), 2)
        }

    def generate_node_id(self) -> str:
        """
        Generate mock edge node identifier

        Returns:
            Node ID string in format: {type}-{number}
        """
        node_types = ["sentry", "aerostat", "mobile", "fixed"]
        node_type = random.choice(node_types)
        node_num = random.randint(1, 99)
        return f"{node_type}-{node_num:02d}"

    def create_detection_message(
        self,
        detection_result: Dict[str, Any],
        node_id: Optional[str] = None,
        gps: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Create complete detection message with telemetry

        Args:
            detection_result: Output from InferenceEngine.detect()
            node_id: Optional node ID override
            gps: Optional GPS override

        Returns:
            Complete detection message with telemetry
        """
        if node_id is None:
            node_id = self.node_id

        if gps is None:
            gps = self.generate_gps()

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "node_id": node_id,
            "location": gps,
            "detections": detection_result["detections"],
            "detection_count": detection_result["count"],
            "inference_time_ms": detection_result["inference_time_ms"],
            "model": detection_result["model"]
        }
