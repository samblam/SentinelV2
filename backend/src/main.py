"""FastAPI application for Sentinel v2 Backend API."""
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Query, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select, desc
from sqlalchemy.orm import joinedload
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
from src.blackout import BlackoutCoordinator

# Import CoT integration (Module 3)
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from atak_integration.src.cot_generator import CoTGenerator
from atak_integration.src.cot_schemas import SentinelDetection as CoTSentinelDetection
from atak_integration.src.tak_client import TAKClient

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


def get_cot_generator():
    """Dependency for CoT generator."""
    if not hasattr(app.state, 'cot_generator'):
        # Initialize if not already set (e.g., in tests)
        if settings.COT_ENABLED:
            app.state.cot_generator = CoTGenerator(
                stale_minutes=settings.COT_STALE_MINUTES,
                cot_type=settings.COT_TYPE
            )
        else:
            app.state.cot_generator = None
    return app.state.cot_generator


def get_tak_client():
    """Dependency for TAK client."""
    if not hasattr(app.state, 'tak_client'):
        # Initialize if not already set (e.g., in tests)
        if settings.TAK_SERVER_ENABLED:
            app.state.tak_client = TAKClient(
                host=settings.TAK_SERVER_HOST,
                port=settings.TAK_SERVER_PORT
            )
        else:
            app.state.tak_client = None
    return app.state.tak_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Sentinel v2 Backend API...")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Database initialization skipped: {e}")

    # Initialize CoT generator
    if settings.COT_ENABLED:
        app.state.cot_generator = CoTGenerator(
            stale_minutes=settings.COT_STALE_MINUTES,
            cot_type=settings.COT_TYPE
        )
        logger.info("CoT generator initialized")
    else:
        app.state.cot_generator = None
        logger.info("CoT generation disabled")

    # Initialize TAK client
    if settings.TAK_SERVER_ENABLED:
        app.state.tak_client = TAKClient(
            host=settings.TAK_SERVER_HOST,
            port=settings.TAK_SERVER_PORT
        )
        # Connect to TAK server on startup
        try:
            await app.state.tak_client.connect()
            logger.info(f"Connected to TAK server at {settings.TAK_SERVER_HOST}:{settings.TAK_SERVER_PORT}")
        except Exception as e:
            logger.warning(f"Failed to connect to TAK server: {e}")
    else:
        app.state.tak_client = None
        logger.info("TAK server integration disabled")

    yield

    # Cleanup: disconnect TAK client
    if hasattr(app.state, 'tak_client') and app.state.tak_client:
        try:
            await app.state.tak_client.disconnect()
            logger.info("Disconnected from TAK server")
        except Exception as e:
            logger.warning(f"Error disconnecting from TAK server: {e}")

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


# Global exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Convert ValueError to HTTP 400 Bad Request globally."""
    logger.warning(f"ValueError on {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
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


# Get all nodes endpoint
@app.get("/api/nodes", response_model=List[NodeResponse])
async def get_nodes(
    session: AsyncSession = Depends(get_db)
):
    """Get all registered nodes."""
    try:
        result = await session.execute(
            select(Node).order_by(Node.created_at)
        )
        return result.scalars().all()

    except Exception as e:
        logger.error(f"Error getting nodes: {e}")
        raise HTTPException(status_code=500, detail="Failed to get nodes") from e


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
    background_tasks: BackgroundTasks,
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

            # Increment the detections_queued counter on the active blackout event
            result = await session.execute(
                select(BlackoutEvent)
                .where(BlackoutEvent.node_id == node.id)
                .where(BlackoutEvent.deactivated_at.is_(None))
                .order_by(desc(BlackoutEvent.activated_at))
            )
            active_event = result.scalar_one_or_none()
            if active_event:
                active_event.detections_queued += 1
                await session.commit()


            # Return a response indicating queued status
            return DetectionResponse(
                id=0,
                node_id=node.node_id,  # String node_id
                timestamp=detection_data.timestamp,
                latitude=detection_data.location.get("latitude"),
                longitude=detection_data.location.get("longitude"),
                altitude_m=detection_data.location.get("altitude_m"),
                accuracy_m=detection_data.location.get("accuracy_m"),
                detections=detection_data.detections,
                detection_count=detection_data.detection_count,
                inference_time_ms=detection_data.inference_time_ms,
                model=detection_data.model,
                queued=True
            )

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

        # Construct response
        response = DetectionResponse(
            id=detection.id,
            node_id=node.node_id,  # String node_id
            timestamp=detection.timestamp,
            latitude=detection.latitude,
            longitude=detection.longitude,
            altitude_m=detection.altitude_m,
            accuracy_m=detection.accuracy_m,
            detections=detection.detections_json,
            detection_count=detection.detection_count,
            inference_time_ms=detection.inference_time_ms,
            model=detection.model
        )

        # Broadcast to WebSocket clients in background to avoid blocking
        asyncio.create_task(
            manager.broadcast({
                "type": "detection",  # Changed from "new_detection"
                "data": {
                    "id": detection.id,
                    "node_id": node.node_id,
                    "timestamp": detection.timestamp.isoformat(),
                    "latitude": detection.latitude,
                    "longitude": detection.longitude,
                    "altitude_m": detection.altitude_m,
                    "accuracy_m": detection.accuracy_m,
                    "detections": detection.detections_json,
                    "detection_count": detection.detection_count,
                    "inference_time_ms": detection.inference_time_ms,
                    "model": detection.model
                }
            })
        )

        # Process CoT update in background
        if settings.COT_ENABLED and settings.TAK_SERVER_ENABLED:
            background_tasks.add_task(process_cot_update, detection, node)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting detection: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Failed to ingest detection") from e


# Batch detection ingestion endpoint
@app.post(
    "/api/detections/batch",
    summary="Batch Ingest Detections",
    description="""
    Ingest multiple detections in a single request for improved efficiency.

    This endpoint is optimized for burst transmission after blackout mode,
    allowing edge nodes to send all queued detections efficiently.

    Processes all detections in a single database transaction for atomicity.
    """,
    tags=["Detections"],
    responses={
        200: {
            "description": "Batch ingestion summary",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "ingested": 15,
                        "failed": 0,
                        "detection_ids": [1, 2, 3, 4, 5]
                    }
                }
            }
        }
    }
)
async def ingest_detections_batch(
    detections: List[DetectionCreate],
    session: AsyncSession = Depends(get_db)
):
    """Ingest multiple detections in a single batch."""
    try:
        ingested_ids = []
        failed_count = 0

        for detection_data in detections:
            try:
                # Get node by node_id string
                result = await session.execute(
                    select(Node).where(Node.node_id == detection_data.node_id)
                )
                node = result.scalar_one_or_none()

                if not node:
                    logger.warning(f"Node not found for batch detection: {detection_data.node_id}")
                    failed_count += 1
                    continue

                # Create detection
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
                await session.flush()  # Get detection ID without committing
                ingested_ids.append(detection.id)

            except Exception as e:
                logger.error(f"Error processing detection in batch: {e}")
                failed_count += 1

        # Commit all detections at once
        await session.commit()

        logger.info(f"Batch ingested {len(ingested_ids)} detections, {failed_count} failed")

        return {
            "status": "success" if failed_count == 0 else "partial",
            "ingested": len(ingested_ids),
            "failed": failed_count,
            "detection_ids": ingested_ids
        }

    except Exception as e:
        logger.error(f"Error in batch detection ingestion: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Failed to ingest detection batch") from e


# Get detections endpoint with pagination
@app.get("/api/detections", response_model=List[DetectionResponse])
async def get_detections(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db)
):
    """Get detections with pagination."""
    try:
        from sqlalchemy.orm import joinedload

        result = await session.execute(
            select(Detection)
            .options(joinedload(Detection.node))  # Load node relationship
            .order_by(desc(Detection.timestamp))
            .limit(limit)
            .offset(offset)
        )
        detections = result.scalars().unique().all()

        # Manually construct responses with string node_id
        return [
            DetectionResponse(
                id=detection.id,
                node_id=detection.node.node_id,  # String node_id from relationship
                timestamp=detection.timestamp,
                latitude=detection.latitude,
                longitude=detection.longitude,
                altitude_m=detection.altitude_m,
                accuracy_m=detection.accuracy_m,
                detections=detection.detections_json,  # Rename from detections_json
                detection_count=detection.detection_count,
                inference_time_ms=detection.inference_time_ms,
                model=detection.model
            )
            for detection in detections
        ]

    except Exception as e:
        logger.error(f"Error getting detections: {e}")
        raise HTTPException(status_code=500, detail="Failed to get detections") from e


# Blackout Mode Endpoints (Module 5)

@app.post(
    "/api/nodes/{node_id}/blackout/activate",
    summary="Activate Blackout Mode",
    description="""
    Activate blackout mode for an edge node, enabling covert surveillance operations.

    When blackout mode is activated:
    - Node stops transmitting detections to backend (appears offline)
    - Detections are queued locally in SQLite database
    - Node status changes to 'covert'
    - Blackout event is logged with operator and reason for audit trail

    This allows the system to continue surveillance while appearing failed to adversaries.
    """,
    response_description="Blackout activation confirmation with event ID",
    tags=["Blackout Mode"],
    responses={
        200: {
            "description": "Blackout mode successfully activated",
            "content": {
                "application/json": {
                    "example": {
                        "status": "activated",
                        "blackout_id": 1,
                        "node_id": "sentry-01"
                    }
                }
            }
        },
        400: {
            "description": "Node not found or already in blackout",
            "content": {
                "application/json": {
                    "example": {"detail": "Node already in blackout: sentry-01"}
                }
            }
        }
    }
)
async def activate_node_blackout(
    node_id: str,
    blackout_data: Optional[BlackoutActivate] = None,
    session: AsyncSession = Depends(get_db)
):
    """Activate blackout mode for an edge node."""
    coordinator = BlackoutCoordinator(session)

    try:
        operator_id = blackout_data.operator_id if blackout_data else None
        reason = blackout_data.reason if blackout_data else None

        event = await coordinator.activate_blackout(node_id, operator_id, reason)

        # Broadcast to dashboard
        asyncio.create_task(
            manager.broadcast({
                "type": "blackout_event",
                "action": "activated",
                "node_id": node_id,
                "blackout_id": event.id
            })
        )

        logger.info(f"Activated blackout mode for node {node_id}")

        return {
            "status": "activated",
            "blackout_id": event.id,
            "node_id": node_id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error activating blackout: {e}")
        raise HTTPException(status_code=500, detail="Failed to activate blackout") from e


@app.post(
    "/api/nodes/{node_id}/blackout/deactivate",
    summary="Deactivate Blackout Mode",
    description="""
    Deactivate blackout mode and resume normal operations.

    When blackout mode is deactivated:
    - Node status changes to 'resuming'
    - Backend processes all queued detections from local queue
    - Blackout event is closed with duration and detection counts
    - Node returns to 'online' status after completion

    All queued detections are transmitted with their original timestamps.
    """,
    response_description="Blackout deactivation summary",
    tags=["Blackout Mode"],
    responses={
        200: {
            "description": "Blackout mode successfully deactivated",
            "content": {
                "application/json": {
                    "example": {
                        "node_id": "sentry-01",
                        "blackout_id": 1,
                        "activated_at": "2025-01-17T12:00:00Z",
                        "deactivated_at": "2025-01-17T12:30:00Z",
                        "duration_seconds": 1800,
                        "detections_queued": 15
                    }
                }

    try:
        summary = await coordinator.deactivate_blackout(node_id)

        # Process queued detections (with row-level locking for concurrency)
        result = await session.execute(
            select(Node).where(Node.node_id == node_id)
        )
        node = result.scalar_one_or_none()

        if node:
            queued_items = await queue_mgr.get_pending_items(node.id, for_update=True)
            detections_transmitted = 0

            for item in queued_items:
                try:
                    payload = item["payload"]
                    detection = Detection(
                        node_id=node.id,
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

            await session.commit()

            # Complete resumption
            await coordinator.complete_resumption(node_id, detections_transmitted)

            logger.info(f"Deactivated blackout for node {node_id}, transmitted {detections_transmitted} detections")

        # Broadcast to dashboard
        asyncio.create_task(
            manager.broadcast({
                "type": "blackout_event",
                "action": "deactivated",
                "node_id": node_id,
                "summary": summary
            })
        )

        return summary
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deactivating blackout: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Failed to deactivate blackout") from e


@app.get("/api/nodes/{node_id}/blackout/status")
async def get_node_blackout_status(
    node_id: str,
    session: AsyncSession = Depends(get_db)
):
    """Get blackout status for a node"""
    coordinator = BlackoutCoordinator(session)
    status = await coordinator.get_blackout_status(node_id)
    return status


@app.post("/api/nodes/{node_id}/blackout/complete")
async def complete_node_blackout_resumption(
    node_id: str,
    completion_data: dict,
    session: AsyncSession = Depends(get_db)
):
    """
    Complete blackout resumption after edge burst transmission.

    Called by edge node after it successfully transmits queued detections.

    Args:
        node_id: Edge node identifier
        completion_data: Dict with blackout_id and transmitted_count
    """
    coordinator = BlackoutCoordinator(session)

    try:
        transmitted_count = completion_data.get("transmitted_count", 0)
        await coordinator.complete_resumption(node_id, transmitted_count)

        logger.info(f"Completed blackout resumption for node {node_id}, {transmitted_count} detections transmitted")

        # Broadcast to dashboard
        asyncio.create_task(
            manager.broadcast({
                "type": "blackout_event",
                "action": "completed",
                "node_id": node_id,
                "transmitted_count": transmitted_count
            })
        )

        return {
            "status": "completed",
            "node_id": node_id,
            "transmitted_count": transmitted_count
        }
    except Exception as e:
        logger.error(f"Error completing blackout resumption: {e}")
        raise HTTPException(status_code=500, detail="Failed to complete resumption") from e


@app.get("/api/blackout/events")
async def get_blackout_events(
    node_id: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    session: AsyncSession = Depends(get_db)
):
    """Query blackout event history"""
    query = select(BlackoutEvent).options(joinedload(BlackoutEvent.node)).order_by(desc(BlackoutEvent.activated_at)).limit(limit)

    if node_id:
        result = await session.execute(
            select(Node).where(Node.node_id == node_id)
        )
        node = result.scalar_one_or_none()
        if node:
            query = query.where(BlackoutEvent.node_id == node.id)

    result = await session.execute(query)
    events = result.scalars().all()

    return [
        {
            "id": event.id,
            "node_id": event.node.node_id,
            "activated_at": event.activated_at.isoformat(),
            "deactivated_at": event.deactivated_at.isoformat() if event.deactivated_at else None,
            "duration_seconds": event.duration_seconds,
            "detections_queued": event.detections_queued,
            "detections_transmitted": event.detections_transmitted,
            "activated_by": event.activated_by,
            "reason": event.reason
        }
        for event in events
    ]


@app.post("/api/blackout/recover-stuck")
async def recover_stuck_resuming_nodes(
    timeout_minutes: int = Query(default=5, ge=1, le=60, description="Timeout in minutes for stuck resuming state"),
    session: AsyncSession = Depends(get_db)
):
    """
    Detect and recover nodes stuck in 'resuming' state.

    Nodes that have been in 'resuming' state for longer than the timeout
    are automatically recovered back to 'online' status.

    This endpoint can be called manually or triggered by monitoring systems.
    """
    coordinator = BlackoutCoordinator(session)
    recovered = await coordinator.recover_stuck_resuming_nodes(timeout_minutes)

    if recovered:
        logger.warning(f"Recovered {len(recovered)} stuck nodes: {[n['node_id'] for n in recovered]}")
    else:
        logger.info("No stuck nodes found")

    return {
        "status": "success",
        "recovered_count": len(recovered),
        "recovered_nodes": recovered
    }


# Legacy endpoints for backward compatibility



# Helper functions for CoT integration
async def fetch_detection_with_node(
    detection_id: int,
    session: AsyncSession
) -> tuple[Detection, Node]:
    """Fetch detection and its associated node from database.

    Args:
        detection_id: Detection ID to fetch
        session: Database session

    Returns:
        Tuple of (detection, node)

    Raises:
        HTTPException: If detection or node not found
    """
    # Fetch detection
    result = await session.execute(
        select(Detection).where(Detection.id == detection_id)
    )
    detection = result.scalar_one_or_none()

    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")

    # Fetch associated node
    result = await session.execute(
        select(Node).where(Node.id == detection.node_id)
    )
    node = result.scalar_one_or_none()

    if not node:
        raise HTTPException(status_code=404, detail="Associated node not found")

    return detection, node


def detection_to_cot_format(detection: Detection, node: Node) -> dict:
    """Convert database Detection model to CoT SentinelDetection format."""
    return {
        "node_id": node.node_id,
        "timestamp": detection.timestamp,
        "latitude": detection.latitude,
        "longitude": detection.longitude,
        "altitude_m": detection.altitude_m or 0.0,
        "accuracy_m": detection.accuracy_m or 10.0,
        "detections": detection.detections_json,
        "detection_count": detection.detection_count,
        "inference_time_ms": detection.inference_time_ms or 0.0,
        "model": detection.model or "unknown"
    }


# CoT generation endpoint
@app.post("/api/cot/generate")
async def generate_cot(
    detection_id: int = Query(..., description="Detection ID to generate CoT for"),
    session: AsyncSession = Depends(get_db),
    cot_gen: Optional[CoTGenerator] = Depends(get_cot_generator)
):
    """Generate CoT XML for a specific detection."""
    if not settings.COT_ENABLED or cot_gen is None:
        raise HTTPException(status_code=503, detail="CoT generation is disabled")

    try:
        # Fetch detection and node
        detection, node = await fetch_detection_with_node(detection_id, session)

        # Convert to CoT format
        cot_data = detection_to_cot_format(detection, node)
        cot_detection = CoTSentinelDetection(**cot_data)

        # Generate CoT XML
        cot_xml = cot_gen.generate(cot_detection)

        logger.info(f"Generated CoT for detection {detection_id}")

        return {
            "status": "success",
            "detection_id": detection_id,
            "node_id": node.node_id,
            "cot_xml": cot_xml,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating CoT: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate CoT: {str(e)}") from e


# CoT send endpoint
@app.post("/api/cot/send")
async def send_cot_to_tak(
    detection_id: int = Query(..., description="Detection ID to send to TAK server"),
    session: AsyncSession = Depends(get_db),
    cot_gen: Optional[CoTGenerator] = Depends(get_cot_generator),
    tak: Optional[TAKClient] = Depends(get_tak_client)
):
    """Generate CoT XML and send to TAK server."""
    if not settings.COT_ENABLED or cot_gen is None:
        raise HTTPException(status_code=503, detail="CoT generation is disabled")

    if not settings.TAK_SERVER_ENABLED or tak is None:
        raise HTTPException(status_code=503, detail="TAK server integration is disabled")

    try:
        # Fetch detection and node
        detection, node = await fetch_detection_with_node(detection_id, session)

        # Convert to CoT format
        cot_data = detection_to_cot_format(detection, node)
        cot_detection = CoTSentinelDetection(**cot_data)

        # Generate CoT XML
        cot_xml = cot_gen.generate(cot_detection)

        # Connect to TAK server if not connected
        if not tak.is_connected():
            await tak.connect()

        # Send to TAK server
        success = await tak.send_cot(cot_xml)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to send CoT to TAK server")

        logger.info(f"Sent CoT for detection {detection_id} to TAK server")

        return {
            "status": "sent",
            "detection_id": detection_id,
            "node_id": node.node_id,
            "tak_server": f"{settings.TAK_SERVER_HOST}:{settings.TAK_SERVER_PORT}",
            "cot_xml": cot_xml,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending CoT to TAK: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send CoT to TAK: {str(e)}") from e


# Helper functions for CoT integration
async def fetch_detection_with_node(
    detection_id: int,
    session: AsyncSession
) -> tuple[Detection, Node]:
    """Fetch detection and its associated node from database.

    Args:
        detection_id: Detection ID to fetch
        session: Database session

    Returns:
        Tuple of (detection, node)

    Raises:
        HTTPException: If detection or node not found
    """
    # Fetch detection
    result = await session.execute(
        select(Detection).where(Detection.id == detection_id)
    )
    detection = result.scalar_one_or_none()

    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")

    # Fetch associated node
    result = await session.execute(
        select(Node).where(Node.id == detection.node_id)
    )
    node = result.scalar_one_or_none()

    if not node:
        raise HTTPException(status_code=404, detail="Associated node not found")

    return detection, node


def detection_to_cot_format(detection: Detection, node: Node) -> dict:
    """Convert database Detection model to CoT SentinelDetection format."""
    return {
        "node_id": node.node_id,
        "timestamp": detection.timestamp,
        "latitude": detection.latitude,
        "longitude": detection.longitude,
        "altitude_m": detection.altitude_m or 0.0,
        "accuracy_m": detection.accuracy_m or 10.0,
        "detections": detection.detections_json,
        "detection_count": detection.detection_count,
        "inference_time_ms": detection.inference_time_ms or 0.0,
        "model": detection.model or "unknown"
    }


# CoT generation endpoint
@app.post("/api/cot/generate")
async def generate_cot(
    detection_id: int = Query(..., description="Detection ID to generate CoT for"),
    session: AsyncSession = Depends(get_db),
    cot_gen: Optional[CoTGenerator] = Depends(get_cot_generator)
):
    """Generate CoT XML for a specific detection."""
    if not settings.COT_ENABLED or cot_gen is None:
        raise HTTPException(status_code=503, detail="CoT generation is disabled")

    try:
        # Fetch detection and node
        detection, node = await fetch_detection_with_node(detection_id, session)

        # Convert to CoT format
        cot_data = detection_to_cot_format(detection, node)
        cot_detection = CoTSentinelDetection(**cot_data)

        # Generate CoT XML
        cot_xml = cot_gen.generate(cot_detection)

        logger.info(f"Generated CoT for detection {detection_id}")

        return {
            "status": "success",
            "detection_id": detection_id,
            "node_id": node.node_id,
            "cot_xml": cot_xml,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating CoT: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate CoT: {str(e)}") from e


# CoT send endpoint
@app.post("/api/cot/send")
async def send_cot_to_tak(
    detection_id: int = Query(..., description="Detection ID to send to TAK server"),
    session: AsyncSession = Depends(get_db),
    cot_gen: Optional[CoTGenerator] = Depends(get_cot_generator),
    tak: Optional[TAKClient] = Depends(get_tak_client)
):
    """Generate CoT XML and send to TAK server."""
    if not settings.COT_ENABLED or cot_gen is None:
        raise HTTPException(status_code=503, detail="CoT generation is disabled")

    if not settings.TAK_SERVER_ENABLED or tak is None:
        raise HTTPException(status_code=503, detail="TAK server integration is disabled")

    try:
        # Fetch detection and node
        detection, node = await fetch_detection_with_node(detection_id, session)

        # Convert to CoT format
        cot_data = detection_to_cot_format(detection, node)
        cot_detection = CoTSentinelDetection(**cot_data)

        # Generate CoT XML
        cot_xml = cot_gen.generate(cot_detection)

        # Connect to TAK server if not connected
        if not tak.is_connected():
            await tak.connect()

        # Send to TAK server
        success = await tak.send_cot(cot_xml)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to send CoT to TAK server")

        logger.info(f"Sent CoT for detection {detection_id} to TAK server")

        return {
            "status": "sent",
            "detection_id": detection_id,
            "node_id": node.node_id,
            "tak_server": f"{settings.TAK_SERVER_HOST}:{settings.TAK_SERVER_PORT}",
            "cot_xml": cot_xml,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending CoT to TAK: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send CoT to TAK: {str(e)}") from e


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


async def process_cot_update(detection: Detection, node: Node):
    """
    Process detection for CoT generation and transmission.
    Filters based on COT_TARGET_CLASSES.
    """
    try:
        # Check if detection contains any target classes
        has_target_class = False
        
        # Handle empty target classes (send everything)
        if not settings.COT_TARGET_CLASSES:
            has_target_class = True
        else:
            # Check each detected object
            for det in detection.detections_json:
                if det.get("class") in settings.COT_TARGET_CLASSES:
                    has_target_class = True
                    break
        
        if not has_target_class:
            return

        # Initialize dependencies manually since we're in a background task
        cot_gen = CoTGenerator(
            stale_minutes=settings.COT_STALE_MINUTES,
            cot_type=settings.COT_TYPE
        )
        
        tak_client = TAKClient(
            host=settings.TAK_SERVER_HOST,
            port=settings.TAK_SERVER_PORT
        )

        # Convert to CoT format
        cot_data = detection_to_cot_format(detection, node)
        cot_detection = CoTSentinelDetection(**cot_data)

        # Generate CoT XML
        cot_xml = cot_gen.generate(cot_detection)

        # Send to TAK server
        async with tak_client:
            await tak_client.connect()
            await tak_client.send_cot(cot_xml)
            
        logger.info(f"Auto-sent CoT for detection {detection.id} (matched target classes)")

    except Exception as e:
        logger.error(f"Error in background CoT processing: {e}")
