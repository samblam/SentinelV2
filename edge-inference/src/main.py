"""
Sentinel Edge Inference API
FastAPI application for edge-deployed object detection
"""
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
inference_engine = None  # Lazy initialization
telemetry = TelemetryGenerator(
    base_lat=settings.DEFAULT_LAT,
    base_lon=settings.DEFAULT_LON
)
blackout = BlackoutController()


def get_inference_engine():
    """Lazy initialization of inference engine"""
    global inference_engine
    if inference_engine is None:
        inference_engine = InferenceEngine(model_name=settings.MODEL_NAME)
    return inference_engine


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
    engine = get_inference_engine()
    return {
        "status": "healthy",
        "model": settings.MODEL_NAME,
        "blackout_active": blackout.is_active,
        "device": str(engine.device)
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
        engine = get_inference_engine()
        detection_result = engine.detect(tmp_path)

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
        return {"status": "not_active", "queued_detections": [], "count": 0}

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
