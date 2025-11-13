# Sentinel v2 Backend API

Resilient backend API for edge surveillance network with offline queue management and blackout coordination.

## Overview

The Sentinel v2 Backend API is a FastAPI-based service designed to handle detection data from edge nodes in challenging network environments. It features:

- **Resilient Queue Management**: Persistent queue with exponential backoff for network failures
- **Blackout Mode Coordination**: Covert operation support with queued transmission
- **WebSocket Real-time Updates**: Live detection broadcasts to connected clients
- **PostgreSQL with JSONB**: Efficient storage of complex detection data
- **Comprehensive Testing**: 54 tests with 67% code coverage

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌───────────┐
│ Edge Nodes  │─────▶│  FastAPI     │─────▶│PostgreSQL │
│             │◀─────│  Backend     │◀─────│ + JSONB   │
└─────────────┘      └──────────────┘      └───────────┘
                           │
                           ├─ Queue Manager
                           ├─ WebSocket Manager
                           └─ Blackout Coordinator
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15
- Docker & Docker Compose (optional)

### Installation

1. **Clone the repository**
   ```bash
   cd SentinelV2/backend
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

5. **Start the server**
   ```bash
   uvicorn src.main:app --reload
   ```

### Docker Deployment

```bash
docker-compose up -d
```

This starts:
- FastAPI backend on port 8000
- PostgreSQL 15 on port 5432

## API Endpoints

### Node Management

#### Register Node
```
POST /api/nodes/register
Content-Type: application/json

{
  "node_id": "sentinel-edge-001"
}
```

#### Node Heartbeat
```
POST /api/nodes/{node_id}/heartbeat
```

#### Get Node Status
```
GET /api/nodes/{node_id}/status
```

### Detection Ingestion

#### Submit Detection
```
POST /api/detections
Content-Type: application/json

{
  "node_id": "sentinel-edge-001",
  "timestamp": "2025-01-13T10:30:00Z",
  "location": {
    "latitude": 37.7749,
    "longitude": -122.4194,
    "altitude_m": 10.5,
    "accuracy_m": 5.0
  },
  "detections": [
    {"class": "person", "confidence": 0.95},
    {"class": "vehicle", "confidence": 0.87}
  ],
  "detection_count": 2,
  "inference_time_ms": 45.2,
  "model": "yolov8n"
}
```

#### Get Detections
```
GET /api/detections?limit=100&offset=0
```

### Blackout Mode

#### Activate Blackout
```
POST /api/blackout/activate
Content-Type: application/json

{
  "node_id": "sentinel-edge-001",
  "reason": "Operational security"
}
```

#### Deactivate Blackout
```
POST /api/blackout/deactivate
Content-Type: application/json

{
  "node_id": "sentinel-edge-001"
}
```

During blackout mode, detections are queued and transmitted when deactivated.

### WebSocket

```
WS /ws?client_id=dashboard-001
```

Receives real-time detection events and blackout status changes.

### Health Check

```
GET /health
```

## Database Schema

### Nodes
- `id`: Primary key
- `node_id`: Unique node identifier
- `status`: online | offline | covert
- `last_heartbeat`: Last heartbeat timestamp
- `created_at`: Node registration time

### Detections
- `id`: Primary key
- `node_id`: Foreign key to nodes
- `timestamp`: Detection timestamp
- `latitude`, `longitude`: GPS coordinates
- `altitude_m`, `accuracy_m`: Optional location metadata
- `detections_json`: JSONB array of detection objects
- `detection_count`: Number of detections
- `inference_time_ms`: Model inference time
- `model`: Model identifier
- `created_at`: Record creation time

### Queue Items
- `id`: Primary key
- `node_id`: Foreign key to nodes
- `payload`: JSONB message payload
- `status`: pending | processing | completed | failed
- `retry_count`: Retry attempts
- `created_at`: Queue entry time
- `processed_at`: Processing completion time

### Blackout Events
- `id`: Primary key
- `node_id`: Foreign key to nodes
- `activated_at`: Blackout start time
- `deactivated_at`: Blackout end time
- `activated_by`: Operator identifier
- `reason`: Blackout reason
- `detections_queued`: Number of detections queued

## Queue Management

The queue system provides resilience during network failures:

- **Persistent Storage**: All queue items stored in PostgreSQL
- **Exponential Backoff**: Retry delays increase exponentially (1s, 2s, 4s, 8s, 16s)
- **Max Retries**: Configurable (default: 5)
- **Status Tracking**: pending → processing → completed | failed

## Testing

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_api.py -v
```

### Test Coverage

- **Total Coverage**: 67% (54 tests, all passing)
- **Models**: 100%
- **Queue**: 93%
- **Schemas**: 100%
- **Config**: 100%
- **Main API**: 46% (uncovered: error handlers, PostgreSQL init)
- **Database**: 43% (uncovered: PostgreSQL-specific initialization)
- **WebSocket**: 64% (uncovered: error handlers)

## Configuration

Environment variables (`.env`):

```env
# Database
DATABASE_URL=postgresql+asyncpg://sentinel:password@localhost:5432/sentinel_v2

# API
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# Queue
MAX_RETRIES=5
BASE_RETRY_DELAY=1

# Logging
LOG_LEVEL=INFO
```

## Development

### Project Structure

```
backend/
├── src/
│   ├── main.py              # FastAPI application
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── database.py          # Database connection
│   ├── queue.py             # Queue manager
│   ├── websocket.py         # WebSocket manager
│   └── config.py            # Configuration
├── tests/
│   ├── conftest.py          # Test fixtures
│   ├── test_api.py          # API endpoint tests
│   ├── test_models.py       # Model tests
│   ├── test_queue.py        # Queue tests
│   ├── test_edge_cases.py   # Edge case tests
│   ├── test_coverage_boost.py
│   └── test_queue_processing.py
├── alembic/
│   ├── versions/            # Database migrations
│   └── env.py               # Alembic configuration
├── Dockerfile               # Container image
├── docker-compose.yml       # Multi-container setup
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
├── pytest.ini               # Pytest configuration
└── alembic.ini             # Alembic configuration
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1

# View migration history
alembic history
```

## Security Considerations

- **Non-root Container**: Docker image uses non-root user
- **Input Validation**: Pydantic schemas validate all inputs
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection
- **CORS**: Configurable CORS middleware
- **Rate Limiting**: Should be implemented at reverse proxy level
- **Authentication**: Should be added for production deployment

## Performance

- **Async I/O**: Full async/await throughout the stack
- **Connection Pooling**: Configured via SQLAlchemy
- **JSONB Indexing**: PostgreSQL JSONB for fast queries
- **WebSocket**: Efficient real-time updates

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

### Queue Statistics

Available via `QueueManager.get_queue_stats()`:
- Pending items count
- Completed items count
- Failed items count

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose ps

# View logs
docker-compose logs postgres

# Test connection
psql -h localhost -U sentinel -d sentinel_v2
```

### Test Failures

```bash
# Run tests with verbose output
pytest tests/ -v -s

# Run specific failing test
pytest tests/test_api.py::test_name -v -s
```

## License

[Project License]

## Contributors

[Contributors List]

## Version

**Module 2**: v2.0.0 - Resilient Backend API
- Completed: January 13, 2025
- Tests: 54/54 passing
- Coverage: 67%
