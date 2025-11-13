"""FastAPI application for Sentinel v2 Backend API."""
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.database import get_db, init_db
from src.models import Node, Detection, BlackoutEvent, QueueItem
from src.schemas import (
    NodeRegister,
    NodeResponse,
    DetectionCreate,
    DetectionResponse,
    BlackoutActivate,
    BlackoutDeactivate,
)
from src.websocket import ConnectionManager
from src.queue import QueueManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize managers
manager = ConnectionManager()


def get_queue_manager():
    """Dependency for queue manager."""
    return QueueManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Sentinel v2 Backend API...")
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Database initialization skipped: {e}")
    yield
    logger.info("Shutting down Sentinel v2 Backend API...")


# Initialize FastAPI app
app = FastAPI(
    title="Sentinel v2 Backend API",
    description="Resilient backend API for edge surveillance network",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


# Node registration endpoint
@app.post("/api/nodes/register", response_model=NodeResponse)
async def register_node(
    node_data: NodeRegister,
    session: AsyncSession = Depends(get_db)
):
    """Register a new edge node or return existing one."""
    try:
        # Check if node already exists
        result = await session.execute(
            select(Node).where(Node.node_id == node_data.node_id)
        )
        existing_node = result.scalar_one_or_none()

        if existing_node:
            logger.info(f"Node {node_data.node_id} already registered")
            return existing_node

        # Create new node
        node = Node(
            node_id=node_data.node_id,
            status="online",
            last_heartbeat=datetime.now(timezone.utc)
        )
        session.add(node)
        await session.commit()
        await session.refresh(node)

        logger.info(f"Registered new node: {node_data.node_id}")
        return node

    except Exception as e:
        logger.error(f"Error registering node: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Failed to register node") from e


# Node heartbeat endpoint
@app.post("/api/nodes/{node_id}/heartbeat")
async def node_heartbeat(
    node_id: str,
    session: AsyncSession = Depends(get_db)
):
    """Update node heartbeat timestamp."""
    try:
        result = await session.execute(
            select(Node).where(Node.node_id == node_id)
        )
        node = result.scalar_one_or_none()

        if not node:
            raise HTTPException(status_code=404, detail="Node not found")

        node.last_heartbeat = datetime.now(timezone.utc)
        await session.commit()

        logger.debug(f"Heartbeat updated for node {node_id}")
        return {"status": "success", "timestamp": node.last_heartbeat.isoformat()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating heartbeat: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Failed to update heartbeat") from e


# Get node status endpoint
@app.get("/api/nodes/{node_id}/status", response_model=NodeResponse)
async def get_node_status(
    node_id: str,
    session: AsyncSession = Depends(get_db)
):
    """Get node status."""
    try:
        result = await session.execute(
            select(Node).where(Node.node_id == node_id)
        )
        node = result.scalar_one_or_none()

        if not node:
            raise HTTPException(status_code=404, detail="Node not found")

        return node

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting node status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get node status") from e


# Detection ingestion endpoint
@app.post("/api/detections", response_model=DetectionResponse)
async def ingest_detection(
    detection_data: DetectionCreate,
    session: AsyncSession = Depends(get_db),
    queue_mgr: QueueManager = Depends(get_queue_manager)
):
    """Ingest detection data from edge node."""
    try:
        # Get node by node_id string
        result = await session.execute(
            select(Node).where(Node.node_id == detection_data.node_id)
        )
        node = result.scalar_one_or_none()

        if not node:
            raise HTTPException(status_code=404, detail="Node not found")

        # Check if node is in blackout mode
        if node.status == "covert":
            logger.info(f"Node {node.node_id} in blackout mode, queuing detection")

            # Queue the detection
            detection_payload = {
                "node_id": node.id,
                "timestamp": detection_data.timestamp.isoformat(),
                "latitude": detection_data.location.get("latitude"),
                "longitude": detection_data.location.get("longitude"),
                "altitude_m": detection_data.location.get("altitude_m"),
                "accuracy_m": detection_data.location.get("accuracy_m"),
                "detections_json": detection_data.detections,
                "detection_count": detection_data.detection_count,
                "inference_time_ms": detection_data.inference_time_ms,
                "model": detection_data.model,
            }

            await queue_mgr.enqueue(node.id, detection_payload)

            # Return a response indicating queued status
            return {
                "id": 0,
                "node_id": node.id,
                "timestamp": detection_data.timestamp,
                "latitude": detection_data.location.get("latitude"),
                "longitude": detection_data.location.get("longitude"),
                "detection_count": detection_data.detection_count,
                "queued": True
            }

        # Normal mode - store detection immediately
        detection = Detection(
            node_id=node.id,
            timestamp=detection_data.timestamp,
            latitude=detection_data.location.get("latitude"),
            longitude=detection_data.location.get("longitude"),
            altitude_m=detection_data.location.get("altitude_m"),
            accuracy_m=detection_data.location.get("accuracy_m"),
            detections_json=detection_data.detections,
            detection_count=detection_data.detection_count,
            inference_time_ms=detection_data.inference_time_ms,
            model=detection_data.model,
        )
        session.add(detection)
        await session.commit()
        await session.refresh(detection)

        logger.info(f"Ingested detection from node {node.node_id}: {detection.id}")

        # Broadcast to WebSocket clients in background to avoid blocking
        asyncio.create_task(
            manager.broadcast({
                "type": "new_detection",
                "node_id": node.node_id,
                "detection_count": detection.detection_count,
                "timestamp": detection.timestamp.isoformat(),
                "location": {
                    "latitude": detection.latitude,
                    "longitude": detection.longitude
                }
            })
        )

        return detection

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting detection: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Failed to ingest detection") from e


# Get detections endpoint with pagination
@app.get("/api/detections", response_model=List[DetectionResponse])
async def get_detections(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db)
):
    """Get detections with pagination."""
    try:
        result = await session.execute(
            select(Detection)
            .order_by(desc(Detection.timestamp))
            .limit(limit)
            .offset(offset)
        )
        detections = result.scalars().all()
        return detections

    except Exception as e:
        logger.error(f"Error getting detections: {e}")
        raise HTTPException(status_code=500, detail="Failed to get detections") from e


# Blackout activation endpoint
@app.post("/api/blackout/activate")
async def activate_blackout(
    blackout_data: BlackoutActivate,
    session: AsyncSession = Depends(get_db)
):
    """Activate blackout mode for a node."""
    try:
        # Get node
        result = await session.execute(
            select(Node).where(Node.node_id == blackout_data.node_id)
        )
        node = result.scalar_one_or_none()

        if not node:
            raise HTTPException(status_code=404, detail="Node not found")

        # Check if already in blackout
        if node.status == "covert":
            logger.warning(f"Node {node.node_id} already in blackout mode")
            return {"status": "already_active", "node_id": node.node_id}

        # Update node status
        node.status = "covert"

        # Create blackout event
        blackout_event = BlackoutEvent(
            node_id=node.id,
            activated_at=datetime.now(timezone.utc),
            reason=blackout_data.reason,
        )
        session.add(blackout_event)
        await session.commit()

        logger.info(f"Activated blackout mode for node {node.node_id}")

        # Broadcast to WebSocket clients
        asyncio.create_task(
            manager.broadcast({
            "type": "blackout_activated",
            "node_id": node.node_id,
            "timestamp": blackout_event.activated_at.isoformat()
        })
        )

        return {
            "status": "blackout_activated",
            "node_id": node.node_id,
            "timestamp": blackout_event.activated_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating blackout: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Failed to activate blackout") from e


# Blackout deactivation endpoint
@app.post("/api/blackout/deactivate")
async def deactivate_blackout(
    blackout_data: BlackoutDeactivate,
    session: AsyncSession = Depends(get_db),
    queue_mgr: QueueManager = Depends(get_queue_manager)
):
    """Deactivate blackout mode and transmit queued detections."""
    try:
        # Get node
        result = await session.execute(
            select(Node).where(Node.node_id == blackout_data.node_id)
        )
        node = result.scalar_one_or_none()

        if not node:
            raise HTTPException(status_code=404, detail="Node not found")

        # Check if in blackout
        if node.status != "covert":
            logger.warning(f"Node {node.node_id} not in blackout mode")
            return {"status": "not_active", "node_id": node.node_id}

        # Get active blackout event
        result = await session.execute(
            select(BlackoutEvent)
            .where(BlackoutEvent.node_id == node.id)
            .where(BlackoutEvent.deactivated_at.is_(None))
            .order_by(desc(BlackoutEvent.activated_at))
        )
        blackout_event = result.scalar_one_or_none()

        # Process queued detections (with row-level locking for concurrency)
        queued_items = await queue_mgr.get_pending_items(node.id, for_update=True)
        detections_transmitted = 0

        for item in queued_items:
            try:
                payload = item["payload"]
                detection = Detection(
                    node_id=payload["node_id"],
                    timestamp=datetime.fromisoformat(payload["timestamp"]),
                    latitude=payload["latitude"],
                    longitude=payload["longitude"],
                    altitude_m=payload.get("altitude_m"),
                    accuracy_m=payload.get("accuracy_m"),
                    detections_json=payload["detections_json"],
                    detection_count=payload["detection_count"],
                    inference_time_ms=payload.get("inference_time_ms"),
                    model=payload.get("model"),
                )
                session.add(detection)
                await queue_mgr.mark_completed(item["id"])
                detections_transmitted += 1
            except Exception as e:
                logger.error(f"Error processing queued detection {item['id']}: {e}")
                await queue_mgr.mark_failed(item["id"])

        # Update node status
        node.status = "online"

        # Close blackout event
        if blackout_event:
            blackout_event.deactivated_at = datetime.now(timezone.utc)
            blackout_event.detections_queued = detections_transmitted

        await session.commit()

        logger.info(f"Deactivated blackout for node {node.node_id}, transmitted {detections_transmitted} detections")

        # Broadcast to WebSocket clients
        asyncio.create_task(
            manager.broadcast({
            "type": "blackout_deactivated",
            "node_id": node.node_id,
            "detections_transmitted": detections_transmitted,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        )

        return {
            "status": "blackout_deactivated",
            "node_id": node.node_id,
            "detections_transmitted": detections_transmitted,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating blackout: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Failed to deactivate blackout") from e


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, client_id: Optional[str] = Query(None)):
    """WebSocket endpoint for real-time updates."""
    if not client_id:
        await websocket.close(code=1008, reason="client_id required")
        return

    await manager.connect(client_id, websocket)

    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "client_id": client_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_json()
            logger.debug(f"Received from {client_id}: {data}")

            # Echo back for ping/pong
            if data.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        manager.disconnect(client_id)
