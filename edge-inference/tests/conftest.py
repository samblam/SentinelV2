"""
Pytest configuration and fixtures
"""
import pytest
from pathlib import Path
from PIL import Image, ImageDraw
import io
from httpx import AsyncClient
import os


@pytest.fixture(scope="session")
def test_image_path():
    """Create a test image fixture"""
    fixtures_dir = Path(__file__).parent / "fixtures"
    fixtures_dir.mkdir(exist_ok=True)

    image_path = fixtures_dir / "test_image.jpg"

    # Create a simple test image with some shapes
    img = Image.new('RGB', (640, 480), color='blue')
    draw = ImageDraw.Draw(img)

    # Draw some rectangles to simulate objects
    draw.rectangle([50, 50, 150, 150], fill='red', outline='white')
    draw.rectangle([200, 200, 300, 350], fill='green', outline='white')
    draw.rectangle([400, 100, 550, 200], fill='yellow', outline='white')

    img.save(image_path)

    return str(image_path)


@pytest.fixture
def test_image_file(test_image_path):
    """Return test image as file-like object for API tests"""
    with open(test_image_path, 'rb') as f:
        return io.BytesIO(f.read())


@pytest.fixture
def sample_detection_result():
    """Sample detection result for testing telemetry"""
    return {
        "detections": [
            {
                "bbox": {
                    "xmin": 100.0,
                    "ymin": 100.0,
                    "xmax": 200.0,
                    "ymax": 200.0
                },
                "class": "person",
                "confidence": 0.85,
                "class_id": 0
            }
        ],
        "count": 1,
        "inference_time_ms": 87.5,
        "model": "yolov5n"
    }


@pytest.fixture
def empty_detection_result():
    """Empty detection result for testing"""
    return {
        "detections": [],
        "count": 0,
        "inference_time_ms": 45.2,
        "model": "yolov5n"
    }


@pytest.fixture
async def client():
    """Create async HTTP client for API testing"""
    # Import here to avoid circular imports
    from src.main import app

    # Clean up any existing blackout database before tests
    blackout_db = Path("blackout_queue.db")
    if blackout_db.exists():
        blackout_db.unlink()

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    # Cleanup after tests
    if blackout_db.exists():
        blackout_db.unlink()


@pytest.fixture
async def blackout_controller():
    """Create a BlackoutController for testing"""
    from src.blackout import BlackoutController
    import tempfile

    # Use a temporary database file
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    db_path = db_file.name
    db_file.close()

    controller = BlackoutController(db_path=db_path)
    yield controller

    # Cleanup
    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass
