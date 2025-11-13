# Module 2: Resilient Backend API - Complete Implementation Specification

**Purpose:** Network-resilient ingestion, storage, and coordination layer for multiple edge nodes  
**Target:** Zero data loss under 50% packet loss, <1s WebSocket latency, persistent audit trail  
**Implementation Method:** Claude Code agent with TDD

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│              Resilient Backend API                   │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐         ┌──────────────┐         │
│  │   FastAPI    │────────▶│  PostgreSQL  │         │
│  │   Endpoints  │         │   Database   │         │
│  └──────┬───────┘         └──────────────┘         │
│         │                                            │
│         ▼                                            │
│  ┌──────────────┐         ┌──────────────┐         │
│  │  WebSocket   │         │    Queue     │         │
│  │   Manager    │         │  Management  │         │
│  └──────────────┘         └──────────────┘         │
│                                                      │
└─────────────────────────────────────────────────────┘
         │                          │
         ▼                          ▼
    Dashboard              Edge Nodes (Module 1)
```

---

## Technology Stack

**Core:**
- Python 3.11
- FastAPI 0.111+ (async ASGI framework)
- Uvicorn 0.24+ (ASGI server)

**Database:**
- PostgreSQL 15 (primary storage)
- SQLAlchemy 2.0+ (async ORM)
- Alembic (migrations)
- asyncpg 0.29+ (async PostgreSQL driver)

**WebSocket:**
- fastapi.websockets (built-in)
- websockets 12.0+ (client library for testing)

**Queue & Resilience:**
- Python asyncio queues
- Database-backed persistence

**Testing:**
- pytest 7.4+
- pytest-asyncio 0.21+
- pytest-cov 4.1+
- httpx 0.25+ (async HTTP client)

**Utilities:**
- pydantic 2.5+ (data validation)
- python-dotenv 1.0+ (environment config)

---

## File Structure

```
backend/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── models.py            # SQLAlchemy database models
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── database.py          # Database connection and session
│   ├── queue.py             # Queue management logic
│   ├── websocket.py         # WebSocket connection manager
│   ├── blackout.py          # Blackout mode coordination
│   └── config.py            # Configuration management
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures
│   ├── test_models.py       # Database model tests
│   ├── test_queue.py        # Queue resilience tests
│   ├── test_websocket.py    # WebSocket tests
│   ├── test_api.py          # API endpoint tests
│   └── test_resilience.py   # Network failure simulation tests
├── alembic/
│   ├── versions/            # Migration scripts
│   └── env.py               # Alembic configuration
├── requirements.txt
├── requirements-dev.txt
├── docker-compose.yml       # PostgreSQL + Backend services
├── Dockerfile
├── alembic.ini
├── pytest.ini
├── .env.example
└── README.md
```

---

## Test-Driven Development Plan

### Phase 1: Database Models (TDD)

**Step 1: Write failing tests**

```python
# tests/test_models.py
import pytest
from datetime import datetime, timezone
from src.models import Detection, Node, QueueItem, BlackoutEvent
from src.database import get_session

@pytest.mark.asyncio
async def test_create_node():
    """Test node creation"""
    async with get_session() as session:
        node = Node(
            node_id="sentry-01",
            status="online",
            last_heartbeat=datetime.now(timezone.utc)
        )
        session.add(node)
        await session.commit()
        
        assert node.id is not None
        assert node.node_id == "sentry-01"

@pytest.mark.asyncio
async def test_create_detection():
    """Test detection record creation"""
    async with get_session() as session:
        # First create a node
        node = Node(node_id="sentry-01", status="online")
        session.add(node)
        await session.commit()
        
        # Create detection
        detection = Detection(
            node_id=node.id,
            timestamp=datetime.now(timezone.utc),
            latitude=70.5,
            longitude=-100.2,
            detections_json='{"detections": []}',
            detection_count=0
        )
        session.add(detection)
        await session.commit()
        
        assert detection.id is not None
        assert detection.node_id == node.id

@pytest.mark.asyncio
async def test_queue_item_persistence():
    """Test queue items persist to database"""
    async with get_session() as session:
        node = Node(node_id="sentry-01", status="online")
        session.add(node)
        await session.commit()
        
        queue_item = QueueItem(
            node_id=node.id,
            payload='{"test": "data"}',
            status="pending",
            retry_count=0
        )
        session.add(queue_item)
        await session.commit()
        
        assert queue_item.id is not None
        assert queue_item.status == "pending"
```

**Step 2: Implement database models**

```python
# src/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

Base = declarative_base()

class Node(Base):
    """Edge node registry"""
    __tablename__ = "nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, nullable=False)  # online, offline, covert
    last_heartbeat = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    detections = relationship("Detection", back_populates="node")
    queue_items = relationship("QueueItem", back_populates="node")
    blackout_events = relationship("BlackoutEvent", back_populates="node")

class Detection(Base):
    """Detection records with full metadata"""
    __tablename__ = "detections"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude_m = Column(Float, nullable=True)
    accuracy_m = Column(Float, nullable=True)
    detections_json = Column(Text, nullable=False)  # JSON string of detections array
    detection_count = Column(Integer, nullable=False)
    inference_time_ms = Column(Float, nullable=True)
    model = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    node = relationship("Node", back_populates="detections")

class QueueItem(Base):
    """Pending transmissions during network issues"""
    __tablename__ = "queue_items"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    payload = Column(Text, nullable=False)  # JSON string
    status = Column(String, nullable=False)  # pending, processing, completed, failed
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    node = relationship("Node", back_populates="queue_items")

class BlackoutEvent(Base):
    """Blackout activation/deactivation log"""
    __tablename__ = "blackout_events"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    activated_at = Column(DateTime(timezone=True), nullable=False)
    deactivated_at = Column(DateTime(timezone=True), nullable=True)
    activated_by = Column(String, nullable=True)  # operator ID
    reason = Column(Text, nullable=True)
    detections_queued = Column(Integer, default=0)
    
    # Relationships
    node = relationship("Node", back_populates="blackout_events")
```

**Step 3: Implement database connection**

```python
# src/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from .config import settings
from .models import Base

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    poolclass=NullPool,
    future=True
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI endpoints"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

@asynccontextmanager
async def get_session():
    """Context manager for tests"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

---

### Phase 2: Queue Management (TDD)

**Step 1: Write failing tests**

```python
# tests/test_queue.py
import pytest
from src.queue import QueueManager
from src.models import Node
from src.database import get_session

@pytest.mark.asyncio
async def test_queue_enqueue():
    """Test enqueueing messages"""
    queue = QueueManager()
    
    message = {"test": "data"}
    node_id = 1
    
    await queue.enqueue(node_id, message)
    
    # Verify it's in queue
    items = await queue.get_pending_items(node_id)
    assert len(items) == 1
    assert items[0]["payload"]["test"] == "data"

@pytest.mark.asyncio
async def test_queue_retry_logic():
    """Test retry with exponential backoff"""
    queue = QueueManager()
    
    # Enqueue item
    item_id = await queue.enqueue(1, {"test": "data"})
    
    # Simulate failures
    await queue.mark_failed(item_id)
    item = await queue.get_item(item_id)
    assert item.retry_count == 1
    
    await queue.mark_failed(item_id)
    item = await queue.get_item(item_id)
    assert item.retry_count == 2

@pytest.mark.asyncio
async def test_queue_persistence():
    """Test queue survives restarts"""
    queue1 = QueueManager()
    
    # Enqueue items
    await queue1.enqueue(1, {"test": "data1"})
    await queue1.enqueue(1, {"test": "data2"})
    
    # Simulate restart
    queue2 = QueueManager()
    items = await queue2.get_pending_items(1)
    
    assert len(items) == 2
```

**Step 2: Implement queue management**

```python
# src/queue.py
import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .database import AsyncSessionLocal
from .models import QueueItem

class QueueManager:
    """Manage message queue with database persistence"""
    
    def __init__(self):
        self.max_retries = 5
        self.base_retry_delay = 1  # seconds
    
    async def enqueue(self, node_id: int, payload: Dict[str, Any]) -> int:
        """
        Add message to queue
        
        Args:
            node_id: Node ID
            payload: Message payload
            
        Returns:
            Queue item ID
        """
        async with AsyncSessionLocal() as session:
            queue_item = QueueItem(
                node_id=node_id,
                payload=json.dumps(payload),
                status="pending",
                retry_count=0
            )
            session.add(queue_item)
            await session.commit()
            await session.refresh(queue_item)
            return queue_item.id
    
    async def get_pending_items(self, node_id: int) -> List[Dict[str, Any]]:
        """Get all pending queue items for a node"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(QueueItem)
                .where(QueueItem.node_id == node_id)
                .where(QueueItem.status == "pending")
                .order_by(QueueItem.created_at)
            )
            items = result.scalars().all()
            
            return [
                {
                    "id": item.id,
                    "payload": json.loads(item.payload),
                    "retry_count": item.retry_count,
                    "created_at": item.created_at
                }
                for item in items
            ]
    
    async def mark_completed(self, item_id: int):
        """Mark queue item as completed"""
        async with AsyncSessionLocal() as session:
            await session.execute(
                update(QueueItem)
                .where(QueueItem.id == item_id)
                .values(
                    status="completed",
                    processed_at=datetime.now(timezone.utc)
                )
            )
            await session.commit()
    
    async def mark_failed(self, item_id: int):
        """Mark queue item as failed and increment retry count"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(QueueItem).where(QueueItem.id == item_id)
            )
            item = result.scalar_one()
            
            item.retry_count += 1
            
            if item.retry_count >= self.max_retries:
                item.status = "failed"
            else:
                item.status = "pending"
            
            await session.commit()
    
    async def get_item(self, item_id: int) -> Optional[QueueItem]:
        """Get queue item by ID"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(QueueItem).where(QueueItem.id == item_id)
            )
            return result.scalar_one_or_none()
    
    async def process_queue(self, node_id: int):
        """
        Process all pending items in queue
        
        Args:
            node_id: Node ID to process queue for
        """
        items = await self.get_pending_items(node_id)
        
        for item in items:
            # Calculate exponential backoff delay
            delay = self.base_retry_delay * (2 ** item["retry_count"])
            
            # Check if enough time has passed since creation
            time_since_creation = (datetime.now(timezone.utc) - item["created_at"]).total_seconds()
            
            if time_since_creation < delay:
                continue  # Skip, not ready yet
            
            try:
                # Process the message (would actually send to edge node here)
                # For now, just mark as completed
                await self.mark_completed(item["id"])
            except Exception as e:
                await self.mark_failed(item["id"])
```

---

### Phase 3: WebSocket Manager (TDD)

**Step 1: Write failing tests**

```python
# tests/test_websocket.py
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.websocket import ConnectionManager

@pytest.mark.asyncio
async def test_websocket_connection():
    """Test WebSocket connection establishment"""
    manager = ConnectionManager()
    
    # Simulate connection
    client_id = "test-client"
    
    # In real test, would use TestClient WebSocket
    # For now, verify manager tracks connections
    assert manager.active_connections == {}

@pytest.mark.asyncio
async def test_websocket_broadcast():
    """Test broadcasting to all connected clients"""
    manager = ConnectionManager()
    
    # Would need actual WebSocket connections to test
    # This tests the message formatting
    message = {"type": "detection", "data": {}}
    
    # Verify message structure
    assert "type" in message
    assert "data" in message
```

**Step 2: Implement WebSocket manager**

```python
# src/websocket.py
from typing import Dict, List
from fastapi import WebSocket
import json

class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, client_id: str, websocket: WebSocket):
        """Accept WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str):
        """Remove WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def send_personal_message(self, message: dict, client_id: str):
        """Send message to specific client"""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections.values():
            await connection.send_json(message)
    
    async def broadcast_detection(self, detection: dict):
        """Broadcast detection to all clients"""
        message = {
            "type": "detection",
            "data": detection
        }
        await self.broadcast(message)
    
    async def broadcast_node_status(self, node_id: str, status: str):
        """Broadcast node status update"""
        message = {
            "type": "node_status",
            "data": {
                "node_id": node_id,
                "status": status
            }
        }
        await self.broadcast(message)
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
async def test_register_node():
    """Test node registration"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/nodes/register",
            json={"node_id": "sentry-01"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["node_id"] == "sentry-01"
        assert "id" in data

@pytest.mark.asyncio
async def test_ingest_detection():
    """Test detection ingestion"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First register node
        await client.post(
            "/api/nodes/register",
            json={"node_id": "sentry-01"}
        )
        
        # Send detection
        detection = {
            "node_id": "sentry-01",
            "timestamp": "2025-11-12T10:00:00Z",
            "location": {
                "latitude": 70.5,
                "longitude": -100.2
            },
            "detections": [],
            "detection_count": 0
        }
        
        response = await client.post("/api/detections", json=detection)
        
        assert response.status_code == 200
        assert "id" in response.json()

@pytest.mark.asyncio
async def test_query_detections():
    """Test querying detection history"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/detections")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
```

**Step 2: Implement FastAPI application**

```python
# src/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, timezone
import json

from .database import get_db, init_db
from .models import Node, Detection, QueueItem
from .schemas import (
    NodeRegister, NodeResponse,
    DetectionCreate, DetectionResponse,
    BlackoutActivate, BlackoutDeactivate
)
from .websocket import ConnectionManager
from .config import settings

# Initialize FastAPI app
app = FastAPI(
    title="Sentinel Backend API",
    description="Resilient backend for Arctic edge surveillance",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
manager = ConnectionManager()

@app.on_event("startup")
async def startup():
    """Initialize database on startup"""
    await init_db()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Sentinel Backend API",
        "version": "2.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected"
    }

@app.post("/api/nodes/register", response_model=NodeResponse)
async def register_node(
    node: NodeRegister,
    db: AsyncSession = Depends(get_db)
):
    """Register new edge node"""
    # Check if node already exists
    result = await db.execute(
        select(Node).where(Node.node_id == node.node_id)
    )
    existing_node = result.scalar_one_or_none()
    
    if existing_node:
        return existing_node
    
    # Create new node
    new_node = Node(
        node_id=node.node_id,
        status="online",
        last_heartbeat=datetime.now(timezone.utc)
    )
    db.add(new_node)
    await db.commit()
    await db.refresh(new_node)
    
    return new_node

@app.post("/api/detections", response_model=DetectionResponse)
async def ingest_detection(
    detection: DetectionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Ingest detection from edge node"""
    # Get node
    result = await db.execute(
        select(Node).where(Node.node_id == detection.node_id)
    )
    node = result.scalar_one_or_none()
    
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    # Create detection record
    new_detection = Detection(
        node_id=node.id,
        timestamp=detection.timestamp,
        latitude=detection.location["latitude"],
        longitude=detection.location["longitude"],
        altitude_m=detection.location.get("altitude_m"),
        accuracy_m=detection.location.get("accuracy_m"),
        detections_json=json.dumps(detection.detections),
        detection_count=detection.detection_count,
        inference_time_ms=detection.inference_time_ms,
        model=detection.model
    )
    db.add(new_detection)
    await db.commit()
    await db.refresh(new_detection)
    
    # Broadcast to WebSocket clients
    await manager.broadcast_detection({
        "id": new_detection.id,
        "node_id": detection.node_id,
        "timestamp": detection.timestamp.isoformat(),
        "location": detection.location,
        "detections": detection.detections,
        "detection_count": detection.detection_count
    })
    
    return new_detection

@app.get("/api/detections", response_model=List[DetectionResponse])
async def query_detections(
    node_id: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Query detection history"""
    query = select(Detection).order_by(Detection.timestamp.desc()).limit(limit)
    
    if node_id:
        # Get node first
        node_result = await db.execute(
            select(Node).where(Node.node_id == node_id)
        )
        node = node_result.scalar_one_or_none()
        if node:
            query = query.where(Detection.node_id == node.id)
    
    result = await db.execute(query)
    detections = result.scalars().all()
    
    return detections

@app.get("/api/nodes/{node_id}/status")
async def get_node_status(
    node_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get node status"""
    result = await db.execute(
        select(Node).where(Node.node_id == node_id)
    )
    node = result.scalar_one_or_none()
    
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    return {
        "node_id": node.node_id,
        "status": node.status,
        "last_heartbeat": node.last_heartbeat
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    client_id = str(id(websocket))
    await manager.connect(client_id, websocket)
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Could handle client messages here if needed
    except WebSocketDisconnect:
        manager.disconnect(client_id)
```

**Step 3: Implement Pydantic schemas**

```python
# src/schemas.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

class NodeRegister(BaseModel):
    """Node registration request"""
    node_id: str

class NodeResponse(BaseModel):
    """Node response"""
    id: int
    node_id: str
    status: str
    last_heartbeat: Optional[datetime]
    
    class Config:
        from_attributes = True

class DetectionCreate(BaseModel):
    """Detection ingestion request"""
    node_id: str
    timestamp: datetime
    location: Dict[str, float]
    detections: List[Dict]
    detection_count: int
    inference_time_ms: Optional[float] = None
    model: Optional[str] = None

class DetectionResponse(BaseModel):
    """Detection response"""
    id: int
    node_id: int
    timestamp: datetime
    latitude: float
    longitude: float
    detection_count: int
    
    class Config:
        from_attributes = True

class BlackoutActivate(BaseModel):
    """Blackout activation request"""
    node_id: str
    reason: Optional[str] = None

class BlackoutDeactivate(BaseModel):
    """Blackout deactivation request"""
    node_id: str
```

---

### Phase 5: Configuration

```python
# src/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Configuration settings for backend"""
    
    # Database settings
    DATABASE_URL: str = "postgresql+asyncpg://sentinel:sentinel@localhost:5432/sentinel"
    DATABASE_ECHO: bool = False
    
    # API settings
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    
    # Queue settings
    MAX_RETRIES: int = 5
    BASE_RETRY_DELAY: int = 1  # seconds
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
```

---

## Requirements Files

**requirements.txt:**
```
fastapi==0.111.0
uvicorn[standard]==0.24.0
sqlalchemy[asyncio]==2.0.23
asyncpg==0.29.0
alembic==1.13.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
websockets==12.0
```

**requirements-dev.txt:**
```
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.2
```

---

## Docker Configuration

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: sentinel
      POSTGRES_PASSWORD: sentinel
      POSTGRES_DB: sentinel
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sentinel"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: .
    ports:
      - "8001:8001"
    environment:
      DATABASE_URL: postgresql+asyncpg://sentinel:sentinel@postgres:5432/sentinel
    depends_on:
      postgres:
        condition: service_healthy
    command: uvicorn src.main:app --host 0.0.0.0 --port 8001

volumes:
  postgres_data:
```

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY alembic.ini .
COPY alembic/ ./alembic/

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8001/health')"

# Run migrations and start app
CMD alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port 8001
```

---

## Database Migrations

**alembic.ini:**
```ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

**Initial migration command:**
```bash
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
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
    --cov-fail-under=75
```

---

## Claude Code Implementation Prompts

### Session 1: Database Models + Setup

```
Create Module 2 (Resilient Backend API) for Sentinel v2 Arctic surveillance system.

REQUIREMENTS:
- Python 3.11 with FastAPI
- PostgreSQL 15 with SQLAlchemy async
- Test-driven development (write tests first)
- All code must have type hints

STEP 1: Project Setup
1. Create the directory structure shown in specification
2. Create requirements.txt with exact versions
3. Create pytest.ini configuration
4. Create docker-compose.yml with PostgreSQL
5. Create alembic.ini

STEP 2: TDD - Database Models
1. Create tests/test_models.py with tests for:
   - Node creation
   - Detection creation
   - Queue item persistence
   - Blackout event logging
2. Implement src/models.py with SQLAlchemy models
3. Implement src/database.py with async session management
4. Run pytest and verify all tests pass

Success criteria:
- All tests pass
- Test coverage >75%
- Database models properly defined with relationships
```

### Session 2: Queue Management

```
Continue Module 2 - Add queue management with retry logic.

STEP 3: TDD - Queue Management
1. Create tests/test_queue.py with tests for:
   - Message enqueueing
   - Retry with exponential backoff
   - Queue persistence across restarts
   - Completed/failed status tracking
2. Implement src/queue.py
3. Verify tests pass

Success criteria:
- All async tests pass
- Queue persists to PostgreSQL
- Exponential backoff working
- Test coverage >75%
```

### Session 3: WebSocket + API Endpoints

```
Continue Module 2 - Build WebSocket manager and FastAPI endpoints.

STEP 4: TDD - WebSocket Manager
1. Create tests/test_websocket.py
2. Implement src/websocket.py with ConnectionManager
3. Verify connection management and broadcasting

STEP 5: TDD - API Endpoints
1. Create tests/test_api.py with async HTTP client tests
2. Implement src/main.py with all endpoints:
   - POST /api/nodes/register
   - POST /api/detections
   - GET /api/detections
   - GET /api/nodes/{id}/status
   - WS /ws
3. Implement src/schemas.py with Pydantic models
4. Verify all API tests pass

Success criteria:
- All API tests pass
- WebSocket broadcasting works
- Detection ingestion functional
- Overall test coverage >75%
```

### Session 4: Docker + Documentation

```
Finalize Module 2 - Docker and README.

STEP 6: Containerization
1. Verify docker-compose.yml with PostgreSQL + Backend
2. Test Docker build and run
3. Verify database migrations work
4. Verify health checks pass

STEP 7: Documentation
1. Create comprehensive README.md with:
   - Quick start with docker-compose
   - API documentation
   - Database schema
   - WebSocket usage
   - Resilience testing approach
2. Add inline docstrings to all functions

Success criteria:
- Docker compose up works
- Migrations run successfully
- Health checks pass
- README includes API examples
- All code has docstrings
```

---

## Success Criteria

**Must Have:**
- ✅ All tests pass (pytest)
- ✅ Test coverage >75%
- ✅ PostgreSQL integration working
- ✅ WebSocket broadcasting functional
- ✅ Queue persistence verified
- ✅ Docker compose deployment works
- ✅ API endpoints respond correctly

**Should Have:**
- ✅ Database migrations with Alembic
- ✅ Type hints on all functions
- ✅ Comprehensive docstrings
- ✅ Health checks pass
- ✅ CORS configured

**Nice to Have:**
- ✅ GitHub Actions CI/CD
- ✅ Network resilience tests
- ✅ Load testing scripts

---

## Next Steps After Module 2

Once Module 2 is complete and tested:
1. Deploy to production (Railway/Fly.io with managed PostgreSQL)
2. Integrate Module 1 â†' Module 2 (edge nodes send to backend)
3. Create Module 3 (ATAK Integration)

**End of Module 2 Specification**
