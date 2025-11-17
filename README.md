# Sentinel v2: Arctic Edge-Resilient Surveillance System

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg)](https://fastapi.tiangolo.com)
[![React 18](https://img.shields.io/badge/React-18.3-61DAFB.svg)](https://reactjs.org/)
[![PostgreSQL 15](https://img.shields.io/badge/PostgreSQL-15-336791.svg)](https://www.postgresql.org/)

**Edge-first, network-resilient surveillance system designed for Arctic/SATCOM-constrained operational environments.**

> **Note:** This is a proof-of-concept demonstration system. Production deployment would require comprehensive security hardening including authentication, encryption, network segmentation, and compliance with defense security standards.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Quick Start](#quick-start)
- [Module Documentation](#module-documentation)
- [API Reference](#api-reference)
- [Deployment](#deployment)
- [Testing](#testing)
- [Development](#development)
- [License](#license)

---

## Overview

Sentinel v2 is a distributed surveillance system that performs **ML inference at the edge** to overcome bandwidth constraints in remote operational environments. Instead of transmitting 500KB images over limited SATCOM links, Sentinel processes data locally and sends only 1KB detection summaries.

### Core Design Principles

1. **Edge-First Processing** - Compute at the sensor, transmit insights (not raw data)
2. **Network Resilience** - Operate through intermittent connectivity
3. **Tactical Deception** - Appear offline while continuing covert operations
4. **Operator Focus** - Built for military command & control workflows
5. **Standards Compliance** - Integrates with ATAK/TAK tactical systems

### Key Innovation: Blackout Mode

Sentinel's **Blackout Protocol** enables covert operations through apparent system failure:
- Operator activates blackout for specific edge nodes
- Nodes stop external transmissions (appear offline to adversaries)
- Continue local ML inference and queue detections in persistent storage
- When operator deactivates blackout, all queued data transmits in burst
- Adversary realizes they were under surveillance the entire time

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     ARCTIC ENVIRONMENT                           │
│  (SATCOM-Constrained, Intermittent Connectivity, -40°C to +20°C) │
└──────────────────────────┬──────────────────────────────────────┘
                           │
           ┌───────────────┴───────────────┐
           │                               │
    ┌──────▼─────────┐            ┌───────▼────────┐
    │  EDGE NODE 1   │            │  EDGE NODE 2   │
    │  (sentry-01)   │            │  (aerostat-01) │
    │                │            │                │
    │  YOLOv5-nano   │            │  YOLOv5-nano   │
    │  <100ms infer  │            │  <100ms infer  │
    │  SQLite queue  │            │  SQLite queue  │
    └──────┬─────────┘            └───────┬────────┘
           │                               │
           │  Detections (JSON, ~1KB)     │
           │  CoT XML Messages            │
           │                               │
           └───────────────┬───────────────┘
                           │
                ┌──────────▼──────────────┐
                │   BACKEND API           │
                │   (FastAPI + Postgres)  │
                │                         │
                │   - Ingest Detections   │
                │   - Queue Management    │
                │   - CoT Generation      │
                │   - Blackout Control    │
                │   - WebSocket Push      │
                └──────────┬──────────────┘
                           │
                           │  WebSocket
                           │
                ┌──────────▼──────────────┐
                │  OPERATOR DASHBOARD     │
                │  (React + TypeScript)   │
                │                         │
                │   - Tactical Map        │
                │   - Real-time Updates   │
                │   - Node Status         │
                │   - Blackout Control    │
                └─────────────────────────┘
```

### Information Flow

**Normal Operations:**
1. Edge node captures image
2. YOLOv5-nano runs inference locally (~87ms)
3. Detection result (~1KB JSON) transmitted to backend
4. Backend stores in PostgreSQL, generates CoT XML
5. Dashboard receives WebSocket update
6. Operator sees detection on tactical map in <1s

**Blackout Mode (Deceptive Operations):**
1. Operator activates "Blackout Mode" for specific nodes
2. Edge nodes stop external transmissions, appear offline
3. Continue local inference, queue results in SQLite
4. On deactivation: burst transmission of all queued data
5. Complete intelligence picture revealed at tactical moment

---

## Features

### Module 1: Edge Inference Engine
- **YOLOv5-nano** object detection (7.5MB model, ~87ms inference on CPU)
- **FastAPI** async REST endpoints for detection
- **Blackout mode** with local SQLite queueing
- **Burst transmission** with exponential backoff retry (max 3 attempts)
- **Structured logging** for production monitoring
- **GPS telemetry** generation and metadata enrichment

### Module 2: Resilient Backend API
- **PostgreSQL 15** persistence with async SQLAlchemy
- **WebSocket** real-time push to dashboard
- **Blackout coordination** across multiple edge nodes
- **Queue management** for network resilience
- **Stuck node recovery** (auto-recover nodes in "resuming" >5min)
- **Global exception handlers** (ValueError → HTTP 400)
- **Batch detection endpoint** for efficient burst transmission
- **Alembic migrations** for schema versioning

### Module 3: ATAK Integration
- **CoT 2.0 XML** generation from detections
- **Schema validation** for CoT compliance
- **TAK server client** for ATAK/TAK integration
- **Detection → CoT pipeline** with metadata preservation
- Compatible with military C2 systems

### Module 4: Operator Dashboard
- **Tactical map** (Leaflet) with Arctic focus
- **Real-time WebSocket updates**
- **Node status panel** (online/offline/covert)
- **Blackout control** with duration timer and reason logging
- **Detection list** with filtering and sorting
- **Dark tactical theme** optimized for field operations

### Module 5: Blackout Mode (Tactical Deception)
- **Multi-node coordination** via backend
- **Persistent local queue** (SQLite on edge nodes)
- **Burst transmission** on deactivation
- **Original timestamp preservation**
- **Operator-controlled intelligence revelation**
- **Stuck node recovery** for resilience

---

## Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** (for dashboard)
- **Docker & Docker Compose** (recommended)
- **PostgreSQL 15** (if not using Docker)

### Option 1: Docker Compose (Recommended)

```bash
# Clone repository
git clone https://github.com/samblam/SentinelV2.git
cd SentinelV2

# Start backend + PostgreSQL
cd backend
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Backend now running at http://localhost:8000
```

### Option 2: Local Development

#### Backend API

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://sentinel:sentinel@localhost:5432/sentinel"

# Run migrations
alembic upgrade head

# Start server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

#### Edge Inference Node

```bash
cd edge-inference

# Install dependencies (includes PyTorch, YOLOv5)
pip install -r requirements.txt

# Set environment variables
export NODE_ID="sentry-01"
export BACKEND_URL="http://localhost:8000"

# Start edge node
uvicorn src.main:app --reload --host 0.0.0.0 --port 8001
```

#### Dashboard

```bash
cd dashboard

# Install dependencies
npm install

# Start development server
npm run dev

# Dashboard now running at http://localhost:5173
```

### Testing the System

1. **Register an edge node:**
```bash
curl -X POST http://localhost:8000/api/nodes/register \
  -H "Content-Type: application/json" \
  -d '{"node_id": "sentry-01"}'
```

2. **Send a detection from edge node:**
```bash
curl -X POST http://localhost:8001/detect \
  -F "file=@test_image.jpg"
```

3. **View detections in dashboard:**
Open http://localhost:5173 in browser

4. **Activate blackout mode:**
```bash
curl -X POST http://localhost:8000/api/blackout/activate \
  -H "Content-Type: application/json" \
  -d '{"node_id": "sentry-01", "operator_id": "operator-123", "reason": "Testing blackout protocol"}'
```

5. **Deactivate and burst transmit:**
```bash
curl -X POST http://localhost:8000/api/blackout/deactivate \
  -H "Content-Type: application/json" \
  -d '{"node_id": "sentry-01"}'
```

---

## Module Documentation

### Edge Inference Engine (`edge-inference/`)

**Purpose:** Local object detection optimized for bandwidth-constrained environments

**Key Files:**
- `src/inference.py` - YOLOv5-nano inference engine
- `src/main.py` - FastAPI application with detection endpoints
- `src/blackout.py` - Blackout mode controller with SQLite queue
- `src/burst_transmission.py` - Retry logic with exponential backoff
- `src/telemetry.py` - GPS mock + metadata generation

**Configuration (`src/config.py`):**
```python
NODE_ID: str = "edge-node-01"  # Unique node identifier
BACKEND_URL: str = "http://localhost:8000"  # Backend API URL
MODEL_NAME: str = "yolov5n"  # YOLOv5 model (n/s/m/l/x)
CONFIDENCE_THRESHOLD: float = 0.25  # Detection confidence threshold
MAX_IMAGE_SIZE: int = 10 * 1024 * 1024  # Max image upload (10MB)
DEFAULT_LAT: float = 70.5  # Default GPS latitude
DEFAULT_LON: float = -100.2  # Default GPS longitude
```

### Backend API (`backend/`)

**Purpose:** Network-resilient ingestion, storage, and coordination layer

**Key Files:**
- `src/main.py` - FastAPI application with all endpoints
- `src/models.py` - SQLAlchemy database models (4 tables)
- `src/blackout.py` - BlackoutCoordinator for multi-node orchestration
- `src/queue.py` - QueueManager for network resilience
- `src/websocket.py` - ConnectionManager for real-time updates
- `alembic/versions/` - Database migrations

**Database Schema:**
```sql
-- Core tables
nodes            # Edge node registry (id, node_id, status, last_heartbeat)
detections       # Detection records with full metadata
queue_items      # Pending transmissions during network issues
blackout_events  # Blackout activation/deactivation log
```

### ATAK Integration (`atak_integration/`)

**Purpose:** Tactical data link compatibility with military C2 systems

**Key Files:**
- `src/cot_generator.py` - CoT 2.0 XML generation
- `src/cot_validator.py` - Schema validation
- `src/cot_schemas.py` - Pydantic schemas for CoT
- `src/tak_client.py` - TAK server client (TCP/UDP)
- `src/mock_tak_server.py` - Mock TAK server for testing

### Dashboard (`dashboard/`)

**Purpose:** Tactical command & control interface for operators

**Key Files:**
- `src/App.tsx` - Main application
- `src/components/TacticalMap.tsx` - Leaflet map with detections
- `src/components/NodeStatusPanel.tsx` - Node health indicators
- `src/components/DetectionList.tsx` - Sortable detection log
- `src/components/BlackoutControl.tsx` - Blackout activation UI
- `src/hooks/useWebSocket.ts` - WebSocket connection management
- `src/hooks/useDetections.ts` - Detection state management
- `src/hooks/useNodes.ts` - Node state management

---

## API Reference

### Edge Inference Endpoints

**Base URL:** `http://localhost:8001`

#### `POST /detect`
Upload image for object detection

**Request:**
```bash
curl -X POST http://localhost:8001/detect \
  -F "file=@image.jpg" \
  -F "node_id=sentry-01"
```

**Response:**
```json
{
  "node_id": "sentry-01",
  "timestamp": "2045-07-15T14:23:45.123456Z",
  "latitude": 70.5234,
  "longitude": -100.8765,
  "altitude_m": 45.2,
  "accuracy_m": 10.0,
  "detections": [
    {
      "class": "person",
      "confidence": 0.89,
      "bbox": [100, 150, 300, 400]
    }
  ],
  "detection_count": 1,
  "inference_time_ms": 87.3,
  "model": "yolov5n"
}
```

#### `POST /blackout/activate`
Activate blackout mode (stop transmissions, queue locally)

**Response:**
```json
{
  "status": "activated",
  "activated_at": "2045-07-15T14:30:00Z"
}
```

#### `POST /blackout/deactivate`
Deactivate blackout mode (return queued detections)

**Response:**
```json
{
  "status": "deactivated",
  "queued_detections": [...],
  "count": 42
}
```

#### `GET /blackout/status`
Get blackout mode status

**Response:**
```json
{
  "active": true,
  "activated_at": "2045-07-15T14:30:00Z",
  "queued_count": 42
}
```

### Backend API Endpoints

**Base URL:** `http://localhost:8000`

#### Node Management

##### `POST /api/nodes/register`
Register a new edge node

**Request:**
```json
{
  "node_id": "sentry-01"
}
```

**Response:**
```json
{
  "id": 1,
  "node_id": "sentry-01",
  "status": "online",
  "last_heartbeat": "2045-07-15T14:23:45Z",
  "created_at": "2045-07-15T10:00:00Z"
}
```

##### `POST /api/nodes/{node_id}/heartbeat`
Update node heartbeat timestamp

##### `GET /api/nodes`
Get all registered nodes

##### `GET /api/nodes/{node_id}/status`
Get specific node status

#### Detection Ingestion

##### `POST /api/detections`
Ingest detection from edge node

**Request:**
```json
{
  "node_id": "sentry-01",
  "timestamp": "2045-07-15T14:23:45Z",
  "latitude": 70.5234,
  "longitude": -100.8765,
  "detections": [...],
  "detection_count": 1
}
```

##### `POST /api/detections/batch`
Ingest multiple detections in single transaction (for burst transmission)

**Request:**
```json
[
  {...detection1...},
  {...detection2...},
  {...detection3...}
]
```

##### `GET /api/detections`
Query detection history with filtering

**Query Parameters:**
- `node_id` - Filter by node
- `start_time` - Filter by start timestamp
- `end_time` - Filter by end timestamp
- `min_confidence` - Minimum detection confidence
- `limit` - Max results (default: 100)

#### Blackout Mode

##### `POST /api/blackout/activate`
Activate blackout for node

**Request:**
```json
{
  "node_id": "sentry-01",
  "operator_id": "operator-123",
  "reason": "Suspected adversary EW activity"
}
```

##### `POST /api/blackout/deactivate`
Deactivate blackout for node

**Request:**
```json
{
  "node_id": "sentry-01"
}
```

##### `GET /api/nodes/{node_id}/blackout/status`
Get node blackout status

##### `POST /api/nodes/{node_id}/blackout/complete`
Complete blackout deactivation workflow

##### `GET /api/blackout/events`
Get all blackout events

##### `POST /api/blackout/recover-stuck`
Recover nodes stuck in "resuming" state >5 minutes

#### CoT Generation

##### `POST /api/cot/generate`
Generate CoT XML from detection

**Request:**
```json
{
  "node_id": "sentry-01",
  "timestamp": "2045-07-15T14:23:45Z",
  "latitude": 70.5234,
  "longitude": -100.8765,
  "detections": [...]
}
```

**Response:**
```xml
<?xml version="1.0"?>
<event version="2.0" uid="detection-123" type="a-f-G-E-S" time="2045-07-15T14:23:45Z">
  <point lat="70.5234" lon="-100.8765" hae="45.2" ce="10.0" le="9999999.0"/>
  <detail>
    <contact callsign="sentry-01"/>
    <remarks>YOLOv5 detection: person (confidence: 0.89)</remarks>
  </detail>
</event>
```

##### `POST /api/cot/send`
Generate and send CoT to TAK server

#### WebSocket

##### `WS /ws`
WebSocket connection for real-time updates

**Message Types:**
- `detection_created` - New detection ingested
- `node_status_changed` - Node status update
- `blackout_activated` - Blackout mode activated
- `blackout_deactivated` - Blackout mode deactivated

---

## Deployment

### Production Deployment Checklist

⚠️ **This is a proof-of-concept. Production requires:**

**Security:**
- [ ] mTLS for node authentication
- [ ] OAuth2 for operator authentication
- [ ] AES-256 encryption at rest
- [ ] HTTPS/TLS for all communications
- [ ] Network segmentation
- [ ] Rate limiting and DDoS protection
- [ ] Input sanitization and validation
- [ ] Audit logging
- [ ] Role-based access control (RBAC)

**Infrastructure:**
- [ ] Horizontal scaling (multiple backend instances)
- [ ] PostgreSQL replication (read replicas)
- [ ] Redis caching layer
- [ ] Message queue (RabbitMQ/Kafka) for high throughput
- [ ] CDN for dashboard assets
- [ ] Health checks and monitoring
- [ ] Automated backups
- [ ] Disaster recovery plan

**Performance:**
- [ ] Database indexing optimization
- [ ] Connection pooling
- [ ] Query optimization
- [ ] Asset compression and minification
- [ ] Image optimization for dashboard

### Docker Deployment

```bash
# Build and deploy all services
docker-compose up -d

# View logs
docker-compose logs -f

# Scale backend instances
docker-compose up -d --scale backend=3

# Stop all services
docker-compose down
```

### Environment Variables

**Backend (`backend/.env`):**
```bash
DATABASE_URL=postgresql+asyncpg://sentinel:sentinel@postgres:5432/sentinel
COT_ENABLED=true
COT_TYPE=a-f-G-E-S
COT_STALE_MINUTES=5
TAK_SERVER_ENABLED=false
TAK_SERVER_HOST=localhost
TAK_SERVER_PORT=8087
```

**Edge Node (`edge-inference/.env`):**
```bash
NODE_ID=sentry-01
BACKEND_URL=http://backend:8000
MODEL_NAME=yolov5n
CONFIDENCE_THRESHOLD=0.25
DEFAULT_LAT=70.5
DEFAULT_LON=-100.2
```

**Dashboard (`dashboard/.env`):**
```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

---

## Testing

### Run All Tests

```bash
# Python tests (backend + edge + atak)
./run_all_tests.sh

# Or run individual modules
cd backend && pytest tests/ -v
cd edge-inference && pytest tests/ -v
cd atak_integration && pytest tests/ -v
```

### Test Coverage

**Current Coverage:**
- **Backend:** 25 test files covering models, queue, blackout, API endpoints
- **Edge Inference:** Tests for inference, blackout, burst transmission
- **ATAK Integration:** Tests for CoT generation, validation
- **Integration Tests:** Multi-node blackout workflows, persistence, burst transmission

**Key Test Files:**
- `backend/tests/test_blackout.py` - 437 lines, 11 tests for BlackoutCoordinator
- `backend/tests/test_blackout_workflow.py` - End-to-end blackout workflow
- `backend/tests/test_blackout_persistence.py` - Queue persistence during blackout
- `backend/tests/test_blackout_multi_node.py` - Multi-node coordination

### Test Markers

```bash
# Run only unit tests
pytest -m "not integration and not slow"

# Run integration tests
pytest -m integration

# Run all tests including slow integration tests
pytest -m "integration or slow"
```

---

## Development

### Project Structure

```
SentinelV2/
├── backend/                 # Backend API (FastAPI + PostgreSQL)
│   ├── src/
│   │   ├── main.py         # FastAPI app with all endpoints
│   │   ├── models.py       # SQLAlchemy models
│   │   ├── blackout.py     # Blackout coordinator
│   │   ├── queue.py        # Queue manager
│   │   └── websocket.py    # WebSocket manager
│   ├── tests/              # 25 test files
│   ├── alembic/            # Database migrations
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
│
├── edge-inference/          # Edge ML inference node
│   ├── src/
│   │   ├── main.py         # FastAPI app
│   │   ├── inference.py    # YOLOv5-nano engine
│   │   ├── blackout.py     # Blackout controller
│   │   ├── burst_transmission.py  # Retry logic
│   │   └── telemetry.py    # GPS mock
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── atak_integration/        # CoT XML generation for ATAK
│   ├── src/
│   │   ├── cot_generator.py
│   │   ├── cot_validator.py
│   │   ├── tak_client.py
│   │   └── mock_tak_server.py
│   └── tests/
│
├── dashboard/               # React operator dashboard
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── lib/            # API client, types
│   │   └── App.tsx
│   ├── package.json
│   └── tailwind.config.js
│
├── run_all_tests.sh        # Comprehensive test runner
├── TEST_SUITE_REPORT.md    # Test documentation
└── README.md               # This file
```

### Adding a New Feature

1. **Define the feature** - Update strategy doc if needed
2. **Write tests first** - TDD approach (see TEST_SUITE_REPORT.md)
3. **Implement feature** - Follow existing patterns
4. **Update API docs** - Document new endpoints
5. **Test integration** - Run full test suite
6. **Update README** - Document new functionality

### Code Style

**Python:**
- Follow PEP 8
- Use type hints
- Use structured logging (`logger.info/warning/error`)
- Never use `print()` in production code
- Document all public functions with docstrings

**TypeScript:**
- Use TypeScript strict mode
- Follow React hooks best practices
- Use functional components
- Document complex logic with comments

### Database Migrations

```bash
# Create new migration
cd backend
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

---

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Inference Time | <100ms | ~87ms (YOLOv5-nano on CPU) |
| API Latency | <50ms | ~30ms (async FastAPI) |
| Dashboard Load | <2s | <1s (code splitting, lazy loading) |
| WebSocket Latency | <100ms | <50ms |
| Model Size | <10MB | 7.5MB (YOLOv5-nano) |
| Detection Accuracy | >75% mAP | ~75% (YOLOv5-nano standard) |
| Bandwidth Reduction | >100x | 500x (500KB image → 1KB detection) |
| Data Loss Rate | 0% | 0% (persistent queue, retry logic) |

---

## License

This project is a proof-of-concept demonstration system developed for the DND Polar Paradigms 2045 contest and defense technology job applications.

**Author:** Samuel Barefoot
**Date:** November 2025
**Contact:** [GitHub](https://github.com/samblam) | [LinkedIn](https://linkedin.com/in/samuel-barefoot)

---

## Acknowledgments

- **YOLOv5** by Ultralytics for efficient object detection
- **FastAPI** for high-performance async Python web framework
- **React** and **Leaflet** for interactive dashboard
- **PostgreSQL** for reliable data persistence
- **ATAK/TAK** community for CoT specifications

---

## Roadmap

**Completed:**
- ✅ Edge inference with YOLOv5-nano
- ✅ Network-resilient backend API
- ✅ ATAK/CoT integration
- ✅ Operator dashboard with real-time updates
- ✅ Blackout mode (tactical deception)
- ✅ Comprehensive test suite (25+ test files)
- ✅ Database migrations
- ✅ Docker containerization

**Future Enhancements:**
- [ ] End-to-end encryption (mTLS)
- [ ] Multi-operator support with RBAC
- [ ] Advanced detection filtering (by object type, confidence)
- [ ] Historical playback of blackout events
- [ ] Mobile-responsive dashboard
- [ ] Kubernetes deployment manifests
- [ ] Performance monitoring dashboard (Grafana)
- [ ] Automated deployment pipeline (GitHub Actions)

---

**Built with ❄️ for Arctic operations**
