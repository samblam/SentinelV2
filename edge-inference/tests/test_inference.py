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
    """Test detection format structure (validates format when detections exist)"""
    engine = InferenceEngine()
    test_image = Path(__file__).parent / "fixtures" / "test_image.jpg"
    result = engine.detect(str(test_image))

    # Verify result always has count field
    assert "count" in result
    assert result["count"] >= 0
    assert len(result["detections"]) == result["count"]

    # If there are detections, validate their format
    # (Note: test image might not trigger detections from YOLOv5)
    for detection in result["detections"]:
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


@pytest.mark.parametrize("run_number", [1, 2, 3])
def test_multiple_inferences(run_number):
    """Test model can handle multiple inferences (parametrized to avoid loops)"""
    engine = InferenceEngine()
    test_image = Path(__file__).parent / "fixtures" / "test_image.jpg"

    # Each run should complete successfully
    result = engine.detect(str(test_image))
    assert "detections" in result
    assert result["inference_time_ms"] < 100


def test_inference_nonexistent_image():
    """Test inference raises ImageLoadError for non-existent file"""
    from src.inference import ImageLoadError

    engine = InferenceEngine()

    with pytest.raises(ImageLoadError, match="Image file not found"):
        engine.detect("/nonexistent/path/image.jpg")


def test_inference_corrupted_image():
    """Test inference handles corrupted image gracefully"""
    from src.inference import ImageLoadError
    import tempfile

    engine = InferenceEngine()

    # Create a corrupted "image" file with invalid data
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(b"This is not a valid image file, just random text")
        tmp_path = tmp.name

    try:
        with pytest.raises(ImageLoadError, match="Failed to load image"):
            engine.detect(tmp_path)
    finally:
        Path(tmp_path).unlink()


def test_inference_invalid_file_type():
    """Test inference rejects non-image files"""
    from src.inference import ImageLoadError
    import tempfile

    engine = InferenceEngine()

    # Create a text file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w') as tmp:
        tmp.write("This is a text file, not an image")
        tmp_path = tmp.name

    try:
        with pytest.raises(ImageLoadError):
            engine.detect(tmp_path)
    finally:
        Path(tmp_path).unlink()
