# Sentinel v2 - Edge Inference Engine (Module 1)

## Overview

Lightweight object detection system optimized for Arctic/SATCOM-constrained edge deployment. Built using **Test-Driven Development (TDD)** methodology with YOLOv5-nano for <100ms inference and <10MB model size.

### Key Features

- **Fast Inference**: <100ms object detection using YOLOv5-nano
- **Compact Model**: 7.5MB model size for edge deployment
- **Arctic Telemetry**: Mock GPS generation for Arctic coordinates (60°N-85°N)
- **Blackout Mode**: Queue detections during communications blackout
- **Edge-Resilient**: SQLite-based persistent queue for offline operation
- **REST API**: FastAPI endpoints for detection and management

---

## Architecture

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
    SQLite Queue
```

---

## Technology Stack

### Core
- **Python 3.11**
- **FastAPI 0.111+** - Async ASGI framework
- **Uvicorn 0.24+** - ASGI server

### ML/Computer Vision
- **PyTorch 2.1.0** - Deep learning framework
- **Ultralytics 8.0+** - YOLOv5 implementation
- **OpenCV 4.8+** - Image preprocessing
- **Pillow 10+** - Image handling

### Data & Storage
- **Pydantic 2.5+** - Data validation
- **aiosqlite 0.19+** - Async SQLite for queue

### Testing
- **pytest 7.4+** - Test framework
- **pytest-asyncio 0.21+** - Async test support
- **pytest-cov 4.1+** - Coverage reporting
- **httpx 0.25+** - Async HTTP client for API tests

---

## Installation

### Prerequisites
- Python 3.11+
- pip

### Setup

```bash
# Clone repository
git clone <repository-url>
cd edge-inference

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (for testing)
pip install -r requirements-dev.txt
```

**Note**: Installing PyTorch and dependencies may take several minutes depending on your connection and system.

---

## Usage

### Starting the Server

```bash
# Development mode
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### API Endpoints

#### Health Check
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "model": "yolov5n",
  "blackout_active": false,
  "device": "cpu"
}
```

#### Object Detection
```bash
curl -X POST http://localhost:8000/detect \
  -F "file=@image.jpg"
```

Response:
```json
{
  "timestamp": "2025-11-13T12:00:00.000000+00:00",
  "node_id": "sentry-01",
  "location": {
    "latitude": 70.0045,
    "longitude": -100.0032,
    "altitude_m": 45.23,
    "accuracy_m": 12.5
  },
  "detections": [
    {
      "bbox": {
        "xmin": 100.5,
        "ymin": 200.3,
        "xmax": 350.7,
        "ymax": 450.2
      },
      "class": "person",
      "confidence": 0.89,
      "class_id": 0
    }
  ],
  "detection_count": 1,
  "inference_time_ms": 87.3,
  "model": "yolov5n"
}
```

#### Custom Node ID
```bash
curl -X POST "http://localhost:8000/detect?node_id=mobile-05" \
  -F "file=@image.jpg"
```

#### Blackout Mode

**Activate Blackout**:
```bash
curl -X POST http://localhost:8000/blackout/activate
```

**Check Status**:
```bash
curl http://localhost:8000/blackout/status
```

**Deactivate and Retrieve Queue**:
```bash
curl -X POST http://localhost:8000/blackout/deactivate
```

Response:
```json
{
  "status": "deactivated",
  "queued_detections": [
    { /* detection 1 */ },
    { /* detection 2 */ }
  ],
  "count": 2
}
```

---

## Testing

This project was built using **Test-Driven Development (TDD)**. All tests were written before implementation.

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=src --cov-report=html --cov-report=term-missing
```

### Run Specific Test Modules
```bash
# Test inference engine
pytest tests/test_inference.py

# Test telemetry
pytest tests/test_telemetry.py

# Test blackout mode
pytest tests/test_blackout.py

# Test API endpoints
pytest tests/test_api.py
```

### Test Coverage Requirements
- **Minimum**: 70% (enforced in pytest.ini)
- **Target**: >80%

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_inference.py        # Inference engine tests
├── test_telemetry.py        # Telemetry generation tests
├── test_blackout.py         # Blackout mode tests (async)
└── test_api.py              # API endpoint tests (async)
```

---

## Docker Deployment

### Build Image
```bash
docker build -t sentinel-edge-inference:v2 .
```

### Run Container
```bash
docker run -d \
  --name sentinel-edge \
  -p 8000:8000 \
  sentinel-edge-inference:v2
```

### Health Check
```bash
curl http://localhost:8000/health
```

---

## Configuration

Configuration via environment variables (create `.env` from `.env.example`):

```bash
# Model Settings
MODEL_NAME=yolov5n
CONFIDENCE_THRESHOLD=0.25
IOU_THRESHOLD=0.45
MAX_DETECTIONS=100

# Performance
DEVICE=cpu  # or 'cuda' for GPU

# API Settings
HOST=0.0.0.0
PORT=8000
MAX_IMAGE_SIZE=10485760  # 10MB

# Arctic Simulation
MOCK_GPS=true
DEFAULT_LAT=70.0
DEFAULT_LON=-100.0
```

---

## TDD Implementation

This module was implemented following strict Test-Driven Development:

### Phase 1: Core Inference
1. ✅ Write failing tests (`test_inference.py`)
2. ✅ Implement inference engine (`inference.py`)
3. ✅ Verify tests pass

### Phase 2: Telemetry
1. ✅ Write failing tests (`test_telemetry.py`)
2. ✅ Implement telemetry generator (`telemetry.py`)
3. ✅ Verify tests pass

### Phase 3: Blackout Mode
1. ✅ Write failing tests (`test_blackout.py`)
2. ✅ Implement blackout controller (`blackout.py`)
3. ✅ Verify tests pass

### Phase 4: API Endpoints
1. ✅ Write failing tests (`test_api.py`)
2. ✅ Implement FastAPI application (`main.py`)
3. ✅ Verify tests pass

### Phase 5: Configuration
1. ✅ Implement configuration (`config.py`)
2. ✅ Implement schemas (`schemas.py`)

---

## Performance Benchmarks

### Target Specifications
- **Inference Time**: <100ms
- **Model Size**: <10MB (YOLOv5-nano = 7.5MB)
- **Bandwidth Reduction**: 500x (send metadata instead of images)

### Expected Performance
- **CPU Inference**: 50-90ms (tested on modern CPUs)
- **GPU Inference**: 10-30ms (if CUDA available)
- **API Response**: <200ms (including I/O overhead)

---

## Project Structure

```
edge-inference/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── inference.py         # YOLOv5-nano inference engine
│   ├── telemetry.py         # GPS mock + metadata
│   ├── blackout.py          # Blackout mode with SQLite queue
│   ├── config.py            # Configuration management
│   └── schemas.py           # Pydantic models
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures
│   ├── test_inference.py    # Inference tests
│   ├── test_telemetry.py    # Telemetry tests
│   ├── test_blackout.py     # Blackout mode tests
│   └── test_api.py          # API integration tests
├── requirements.txt          # Production dependencies
├── requirements-dev.txt      # Development dependencies
├── Dockerfile               # Docker build configuration
├── .dockerignore
├── pytest.ini               # Pytest configuration
├── .env.example             # Example environment variables
└── README.md                # This file
```

---

## Design Decisions

### Why YOLOv5-nano?
- **Size**: Only 7.5MB vs 100MB+ for larger models
- **Speed**: <100ms inference on CPU
- **Accuracy**: Good enough for perimeter surveillance
- **Edge-Ready**: Runs on resource-constrained devices

### Why SQLite for Queue?
- **Zero Dependencies**: No external database required
- **Persistence**: Survives process restarts
- **Async Support**: aiosqlite for non-blocking I/O
- **Lightweight**: Perfect for edge deployment

### Why FastAPI?
- **Async**: Native async/await support
- **Fast**: One of the fastest Python frameworks
- **Type Safety**: Pydantic integration
- **OpenAPI**: Automatic API documentation

---

## Troubleshooting

### YOLOv5 Model Download
First run downloads the model from Ultralytics (may take a few minutes):
```python
import torch
torch.hub.load('ultralytics/yolov5', 'yolov5n', pretrained=True)
```

### GPU Support
If CUDA is available, set `DEVICE=cuda` in `.env`:
```bash
# Check GPU availability
python -c "import torch; print(torch.cuda.is_available())"
```

### Test Failures
Ensure all dependencies are installed:
```bash
pip install -r requirements.txt -r requirements-dev.txt
```

---

## Next Steps

### Module 2: Backend API
- Central aggregation server
- PostgreSQL database
- WebSocket for real-time updates
- Integration with Module 1

### Module 3: Frontend Dashboard
- React-based monitoring interface
- Real-time detection visualization
- Arctic map integration

---

## License

© 2025 Sentinel v2 - Arctic Surveillance System

---

## Contact

For issues and feature requests, please open an issue on GitHub.
