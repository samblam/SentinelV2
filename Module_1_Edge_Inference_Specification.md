# Module 1: Edge Inference Engine - Complete Implementation Specification

**Purpose:** Lightweight object detection optimized for Arctic/SATCOM-constrained edge deployment  
**Target:** <100ms inference, <10MB model, bandwidth optimization (500x reduction)  
**Implementation Method:** Claude Code agent with TDD

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                 Edge Inference Node                  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐         ┌──────────────┐         │
│  │   FastAPI    │────────▶│  YOLOv5-nano │         │
│  │   Endpoints  │         │   Detector   │         │
│  └──────┬───────┘         └──────┬───────┘         │
│         │                        │                  │
│         ▼                        ▼                  │
│  ┌──────────────┐         ┌──────────────┐         │
│  │  Telemetry   │         │   Blackout   │         │
│  │  Generator   │         │     Mode     │         │
│  └──────────────┘         └──────────────┘         │
│                                                      │
└─────────────────────────────────────────────────────┘
         │
         ▼
    PostgreSQL + Local Queue
```

---

## Technology Stack

**Core:**
- Python 3.11
- FastAPI 0.111+ (async ASGI framework)
- Uvicorn 0.24+ (ASGI server)

**ML/Computer Vision:**
- torch 2.1.0 (PyTorch)
- torchvision 0.16.0
- ultralytics 8.0.200+ (YOLOv5)
- opencv-python 4.8.0+ (image preprocessing)
- Pillow 10.0+ (image handling)

**Data & Storage:**
- pydantic 2.5+ (data validation)
- pydantic-settings 2.1+ (configuration)
- aiosqlite 0.19+ (async SQLite for local queue)

**Testing:**
- pytest 7.4+
- pytest-asyncio 0.21+
- pytest-cov 4.1+
- httpx 0.25+ (async HTTP client for testing)

**Utilities:**
- python-multipart 0.0.6 (file upload handling)

---

## File Structure

```
edge-inference/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── inference.py         # YOLOv5-nano inference engine
│   ├── telemetry.py         # GPS mock + metadata generation
│   ├── blackout.py          # Blackout mode logic
│   ├── queue.py             # Local SQLite queue for offline operation
│   ├── config.py            # Configuration management
│   └── schemas.py           # Pydantic models
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures
│   ├── test_inference.py    # Unit tests for inference
│   ├── test_telemetry.py    # Unit tests for telemetry
│   ├── test_blackout.py     # Unit tests for blackout mode
│   ├── test_queue.py        # Unit tests for queue
│   ├── test_api.py          # Integration tests for API
│   └── test_e2e.py          # End-to-end tests
├── requirements.txt
├── requirements-dev.txt     # Development dependencies
├── Dockerfile
├── .dockerignore
├── pytest.ini
├── .env.example
└── README.md
```

---

## Test-Driven Development Plan

### Phase 1: Core Inference (TDD)

**Step 1: Write failing tests**
```python
# tests/test_inference.py
import pytest
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
    result = engine.detect("tests/fixtures/test_image.jpg")
    
    assert "detections" in result
    assert "inference_time_ms" in result
    assert "model" in result
    assert isinstance(result["detections"], list)
    
def test_inference_performance():
    """Test inference completes in <100ms"""
    engine = InferenceEngine()
    result = engine.detect("tests/fixtures/test_image.jpg")
    assert result["inference_time_ms"] < 100
```

**Step 2: Implement to pass tests**
```python
# src/inference.py
import torch
import time
from pathlib import Path
from typing import Dict, List, Any

class InferenceEngine:
    """Lightweight inference engine using YOLOv5-nano"""
    
    def __init__(self, model_name: str = "yolov5n"):
        """
        Initialize inference engine
        
        Args:
            model_name: YOLOv5 model variant (default: yolov5n for nano)
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self._load_model(model_name)
        
    def _load_model(self, model_name: str):
        """Load YOLOv5 model from torch hub"""
        model = torch.hub.load(
            'ultralytics/yolov5',
            model_name,
            pretrained=True,
            verbose=False
        )
        model.to(self.device)
        model.conf = 0.25  # Confidence threshold
        model.iou = 0.45   # IoU threshold
        model.max_det = 100  # Maximum detections
        return model
    
    def detect(self, image_path: str) -> Dict[str, Any]:
        """
        Run object detection on image
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with detections and metadata
        """
        start_time = time.time()
        
        # Run inference
        results = self.model(image_path)
        
        # Extract detections
        detections = results.pandas().xyxy[0].to_dict('records')
        
        inference_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Format output
        formatted_detections = [
            {
                "bbox": {
                    "xmin": float(det["xmin"]),
                    "ymin": float(det["ymin"]),
                    "xmax": float(det["xmax"]),
                    "ymax": float(det["ymax"])
                },
                "class": det["name"],
                "confidence": float(det["confidence"]),
                "class_id": int(det["class"])
            }
            for det in detections
        ]
        
        return {
            "detections": formatted_detections,
            "count": len(formatted_detections),
            "inference_time_ms": round(inference_time, 2),
            "model": "yolov5n"
        }
```

**Step 3: Run tests, refactor**

---

### Phase 2: Telemetry Generation (TDD)

**Step 1: Write failing tests**
```python
# tests/test_telemetry.py
import pytest
from src.telemetry import TelemetryGenerator

def test_generates_arctic_coordinates():
    """Test GPS coordinates are in Arctic range"""
    generator = TelemetryGenerator()
    coords = generator.generate_gps()
    
    assert 60.0 <= coords["latitude"] <= 85.0  # Arctic range
    assert -180.0 <= coords["longitude"] <= 180.0
    assert "accuracy_m" in coords
    
def test_generates_unique_node_id():
    """Test node ID generation"""
    generator = TelemetryGenerator()
    node_id = generator.generate_node_id()
    
    assert isinstance(node_id, str)
    assert len(node_id) > 5  # e.g., "sentry-01"
    
def test_creates_detection_message():
    """Test complete detection message with telemetry"""
    generator = TelemetryGenerator()
    
    mock_detection = {
        "detections": [],
        "count": 0,
        "inference_time_ms": 87.5,
        "model": "yolov5n"
    }
    
    message = generator.create_detection_message(mock_detection)
    
    assert "timestamp" in message
    assert "node_id" in message
    assert "location" in message
    assert "detections" in message
```

**Step 2: Implement to pass tests**
```python
# src/telemetry.py
import random
from datetime import datetime, timezone
from typing import Dict, Any

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
        """Generate mock Arctic GPS coordinates"""
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
        """Generate mock edge node identifier"""
        node_types = ["sentry", "aerostat", "mobile", "fixed"]
        node_type = random.choice(node_types)
        node_num = random.randint(1, 99)
        return f"{node_type}-{node_num:02d}"
    
    def create_detection_message(
        self,
        detection_result: Dict[str, Any],
        node_id: str = None,
        gps: Dict = None
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
```

---

### Phase 3: Blackout Mode (TDD)

**Step 1: Write failing tests**
```python
# tests/test_blackout.py
import pytest
from src.blackout import BlackoutController

@pytest.mark.asyncio
async def test_blackout_activation():
    """Test blackout mode can be activated"""
    controller = BlackoutController()
    
    await controller.activate()
    
    assert controller.is_active == True
    assert controller.activated_at is not None
    
@pytest.mark.asyncio
async def test_blackout_queues_detections():
    """Test detections are queued during blackout"""
    controller = BlackoutController()
    
    await controller.activate()
    
    mock_detection = {"test": "data"}
    await controller.queue_detection(mock_detection)
    
    queued = await controller.get_queued_detections()
    assert len(queued) == 1
    assert queued[0]["test"] == "data"
    
@pytest.mark.asyncio
async def test_blackout_deactivation_returns_queue():
    """Test deactivation returns all queued detections"""
    controller = BlackoutController()
    
    await controller.activate()
    await controller.queue_detection({"id": 1})
    await controller.queue_detection({"id": 2})
    
    detections = await controller.deactivate()
    
    assert len(detections) == 2
    assert controller.is_active == False
```

**Step 2: Implement to pass tests**
```python
# src/blackout.py
import asyncio
import aiosqlite
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path

class BlackoutController:
    """Manage blackout mode for covert operations"""
    
    def __init__(self, db_path: str = "blackout_queue.db"):
        """
        Initialize blackout controller
        
        Args:
            db_path: Path to SQLite database for queue persistence
        """
        self.db_path = Path(db_path)
        self.is_active = False
        self.activated_at: Optional[datetime] = None
        self._initialized = False
        
    async def _init_db(self):
        """Initialize SQLite database for queue"""
        if self._initialized:
            return
            
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS queued_detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    queued_at TEXT NOT NULL,
                    detection_data TEXT NOT NULL
                )
            """)
            await db.commit()
        
        self._initialized = True
    
    async def activate(self):
        """Activate blackout mode"""
        await self._init_db()
        self.is_active = True
        self.activated_at = datetime.now(timezone.utc)
        
    async def deactivate(self) -> List[Dict[str, Any]]:
        """
        Deactivate blackout mode and return queued detections
        
        Returns:
            List of all queued detections
        """
        detections = await self.get_queued_detections()
        
        # Clear queue
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM queued_detections")
            await db.commit()
        
        self.is_active = False
        self.activated_at = None
        
        return detections
    
    async def queue_detection(self, detection: Dict[str, Any]):
        """
        Queue detection during blackout
        
        Args:
            detection: Detection message to queue
        """
        await self._init_db()
        
        import json
        detection_json = json.dumps(detection)
        queued_at = datetime.now(timezone.utc).isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO queued_detections (queued_at, detection_data) VALUES (?, ?)",
                (queued_at, detection_json)
            )
            await db.commit()
    
    async def get_queued_detections(self) -> List[Dict[str, Any]]:
        """
        Get all queued detections
        
        Returns:
            List of queued detection messages
        """
        await self._init_db()
        
        import json
        detections = []
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT detection_data FROM queued_detections ORDER BY id"
            ) as cursor:
                async for row in cursor:
                    detections.append(json.loads(row[0]))
        
        return detections
```

---

### Phase 4: FastAPI Endpoints (TDD)

**Step 1: Write failing tests**
```python
# tests/test_api.py
import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        
    assert response.status_code == 200
    assert "status" in response.json()
    
@pytest.mark.asyncio
async def test_detect_endpoint_requires_image():
    """Test detect endpoint rejects requests without image"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/detect")
        
    assert response.status_code == 422  # Unprocessable entity
    
@pytest.mark.asyncio
async def test_detect_endpoint_with_image(test_image_file):
    """Test detect endpoint processes image"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        files = {"file": ("test.jpg", test_image_file, "image/jpeg")}
        response = await client.post("/detect", files=files)
        
    assert response.status_code == 200
    data = response.json()
    assert "detections" in data
    assert "node_id" in data
    assert "location" in data
```

**Step 2: Implement to pass tests**
```python
# src/main.py
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
import tempfile
import os
from typing import Optional

from .inference import InferenceEngine
from .telemetry import TelemetryGenerator
from .blackout import BlackoutController
from .config import Settings

# Initialize FastAPI app
app = FastAPI(
    title="Sentinel Edge Inference API",
    description="Edge-resilient object detection for Arctic deployment",
    version="2.0.0"
)

# Initialize components
settings = Settings()
inference_engine = InferenceEngine()
telemetry = TelemetryGenerator()
blackout = BlackoutController()

@app.on_event("startup")
async def startup():
    """Initialize resources on startup"""
    await blackout._init_db()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Sentinel Edge Inference",
        "version": "2.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model": "yolov5n",
        "blackout_active": blackout.is_active,
        "device": str(inference_engine.device)
    }

@app.post("/detect")
async def detect(
    file: UploadFile = File(...),
    node_id: Optional[str] = Query(None, description="Override node ID")
):
    """
    Detect objects in uploaded image
    
    Args:
        file: Image file (JPEG, PNG)
        node_id: Optional node ID override
        
    Returns:
        Detection results with telemetry
    """
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Save to temporary file
    contents = await file.read()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    
    try:
        # Run inference
        detection_result = inference_engine.detect(tmp_path)
        
        # Create message with telemetry
        message = telemetry.create_detection_message(
            detection_result,
            node_id=node_id
        )
        
        # Handle blackout mode
        if blackout.is_active:
            await blackout.queue_detection(message)
            return JSONResponse(content={
                "status": "queued",
                "message": "Detection queued during blackout mode",
                "blackout_active": True
            })
        
        return JSONResponse(content=message)
        
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

@app.post("/blackout/activate")
async def activate_blackout():
    """Activate blackout mode"""
    if blackout.is_active:
        return {"status": "already_active"}
    
    await blackout.activate()
    return {
        "status": "activated",
        "activated_at": blackout.activated_at.isoformat()
    }

@app.post("/blackout/deactivate")
async def deactivate_blackout():
    """Deactivate blackout mode and return queued detections"""
    if not blackout.is_active:
        return {"status": "not_active"}
    
    queued = await blackout.deactivate()
    
    return {
        "status": "deactivated",
        "queued_detections": queued,
        "count": len(queued)
    }

@app.get("/blackout/status")
async def blackout_status():
    """Get blackout mode status"""
    return {
        "active": blackout.is_active,
        "activated_at": blackout.activated_at.isoformat() if blackout.activated_at else None,
        "queued_count": len(await blackout.get_queued_detections())
    }
```

---

### Phase 5: Configuration & Schemas (TDD)

**Step 1: Write tests**
```python
# tests/test_config.py
import pytest
from src.config import Settings

def test_settings_load_defaults():
    """Test default settings load correctly"""
    settings = Settings()
    
    assert settings.MODEL_NAME == "yolov5n"
    assert settings.CONFIDENCE_THRESHOLD == 0.25
    assert settings.DEVICE == "cpu"
```

**Step 2: Implement**
```python
# src/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Configuration settings for edge inference"""
    
    # Model settings
    MODEL_NAME: str = "yolov5n"
    CONFIDENCE_THRESHOLD: float = 0.25
    IOU_THRESHOLD: float = 0.45
    MAX_DETECTIONS: int = 100
    
    # Performance settings
    DEVICE: str = "cpu"  # "cuda" if GPU available
    
    # API settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    MAX_IMAGE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Arctic simulation settings
    MOCK_GPS: bool = True
    DEFAULT_LAT: float = 70.0  # Arctic latitude
    DEFAULT_LON: float = -100.0  # Arctic longitude
    
    model_config = SettingsConfigDict(env_file=".env")

# src/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class BBox(BaseModel):
    """Bounding box coordinates"""
    xmin: float
    ymin: float
    xmax: float
    ymax: float

class Detection(BaseModel):
    """Single object detection"""
    bbox: BBox
    class_name: str = Field(..., alias="class")
    confidence: float
    class_id: int

class Location(BaseModel):
    """GPS location"""
    latitude: float
    longitude: float
    altitude_m: float
    accuracy_m: float

class DetectionMessage(BaseModel):
    """Complete detection message with telemetry"""
    timestamp: datetime
    node_id: str
    location: Location
    detections: List[Detection]
    detection_count: int
    inference_time_ms: float
    model: str
```

---

## Requirements Files

**requirements.txt:**
```
torch==2.1.0
torchvision==0.16.0
ultralytics==8.0.200
opencv-python==4.8.1
Pillow==10.1.0
fastapi==0.111.0
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pydantic==2.5.0
pydantic-settings==2.1.0
aiosqlite==0.19.0
```

**requirements-dev.txt:**
```
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.2
```

---

## Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download YOLOv5 model
RUN python -c "import torch; torch.hub.load('ultralytics/yolov5', 'yolov5n', pretrained=True)"

# Copy application
COPY src/ ./src/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
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
    --cov-fail-under=70
```

---

## Claude Code Implementation Prompts

### Session 1: Setup + Core Inference

```
Create Module 1 (Edge Inference Engine) for Sentinel v2 Arctic surveillance system.

REQUIREMENTS:
- Python 3.11 with FastAPI
- YOLOv5-nano for edge inference (<100ms target)
- Test-driven development (write tests first)
- All code must have type hints

STEP 1: Project Setup
1. Create the directory structure shown in specification
2. Create requirements.txt with exact versions
3. Create pytest.ini configuration
4. Create .env.example

STEP 2: TDD - Core Inference
1. Create tests/test_inference.py with tests for:
   - Model loading
   - Inference execution
   - Output schema validation
   - Performance (<100ms)
2. Implement src/inference.py to pass tests
3. Run pytest and verify all tests pass

Success criteria:
- All tests pass
- Test coverage >70%
- Inference time <100ms on test images
```

### Session 2: Telemetry + Blackout

```
Continue Module 1 - Add telemetry and blackout mode.

STEP 3: TDD - Telemetry Generation
1. Create tests/test_telemetry.py
2. Implement src/telemetry.py
3. Verify tests pass

STEP 4: TDD - Blackout Mode
1. Create tests/test_blackout.py with async tests
2. Implement src/blackout.py with SQLite queue
3. Verify tests pass

Success criteria:
- All async tests pass
- Blackout queue persists to SQLite
- Test coverage >75%
```

### Session 3: API Endpoints

```
Continue Module 1 - Build FastAPI endpoints.

STEP 5: TDD - API Endpoints
1. Create tests/test_api.py with async HTTP client tests
2. Implement src/main.py with all endpoints
3. Create conftest.py with test fixtures
4. Verify all API tests pass

STEP 6: Configuration & Schemas
1. Create src/config.py with pydantic-settings
2. Create src/schemas.py with pydantic models
3. Add tests for configuration

Success criteria:
- All API tests pass
- Health check returns 200
- /detect endpoint processes images
- Blackout endpoints functional
- Overall test coverage >70%
```

### Session 4: Docker + Documentation

```
Finalize Module 1 - Docker and README.

STEP 7: Containerization
1. Create Dockerfile with model pre-download
2. Create .dockerignore
3. Test Docker build and run
4. Verify health check works in container

STEP 8: Documentation
1. Create comprehensive README.md with:
   - Quick start
   - API documentation
   - Performance benchmarks
   - Design decisions
2. Add inline docstrings to all functions

Success criteria:
- Docker image builds successfully
- Container passes health checks
- README includes curl examples
- All code has docstrings
```

---

## Success Criteria

**Must Have:**
- ✅ All tests pass (pytest)
- ✅ Test coverage >70%
- ✅ Inference time <100ms
- ✅ Model size <10MB (YOLOv5-nano = 7.5MB)
- ✅ Docker image builds
- ✅ API endpoints functional
- ✅ Blackout mode works

**Should Have:**
- ✅ Test coverage >80%
- ✅ Type hints on all functions
- ✅ Comprehensive docstrings
- ✅ Health checks pass
- ✅ Clean pytest output

**Nice to Have:**
- ✅ GitHub Actions CI/CD
- ✅ Async optimization throughout
- ✅ Detailed logging

---

## Next Steps After Module 1

Once Module 1 is complete and tested:
1. Deploy to Railway/Fly.io for testing
2. Create Module 2 (Backend API)
3. Integrate Module 1 → Module 2

**End of Module 1 Specification**
