"""
Test suite for inference engine
Following TDD - these tests should fail initially
"""
import pytest
import time
from pathlib import Path

# Tests will fail until we implement src.inference
from src.inference import InferenceEngine


def test_engine_initializes():
    """Test that inference engine loads YOLOv5-nano model"""
    engine = InferenceEngine()
    assert engine.model is not None
    assert engine.device is not None


def test_inference_returns_correct_schema():
    """Test inference output matches expected schema"""
    engine = InferenceEngine()
    # Use a test image from tests/fixtures/
    test_image = Path(__file__).parent / "fixtures" / "test_image.jpg"
    result = engine.detect(str(test_image))

    assert "detections" in result
    assert "inference_time_ms" in result
    assert "model" in result
    assert "count" in result
    assert isinstance(result["detections"], list)
    assert result["model"] == "yolov5n"


def test_inference_performance():
    """Test inference completes in <100ms"""
    engine = InferenceEngine()
    test_image = Path(__file__).parent / "fixtures" / "test_image.jpg"
    result = engine.detect(str(test_image))
    assert result["inference_time_ms"] < 100, f"Inference took {result['inference_time_ms']}ms, expected <100ms"


def test_detection_format():
    """Test individual detection format"""
    engine = InferenceEngine()
    test_image = Path(__file__).parent / "fixtures" / "test_image.jpg"
    result = engine.detect(str(test_image))

    if result["count"] > 0:
        detection = result["detections"][0]
        assert "bbox" in detection
        assert "class" in detection
        assert "confidence" in detection
        assert "class_id" in detection

        # Check bbox format
        bbox = detection["bbox"]
        assert "xmin" in bbox
        assert "ymin" in bbox
        assert "xmax" in bbox
        assert "ymax" in bbox


def test_multiple_inferences():
    """Test model can handle multiple inferences"""
    engine = InferenceEngine()
    test_image = Path(__file__).parent / "fixtures" / "test_image.jpg"

    # Run 3 inferences
    results = []
    for _ in range(3):
        result = engine.detect(str(test_image))
        results.append(result)

    # All should complete successfully
    assert len(results) == 3
    for result in results:
        assert "detections" in result
        assert result["inference_time_ms"] < 100
