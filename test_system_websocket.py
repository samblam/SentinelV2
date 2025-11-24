import pytest
import asyncio
import aiohttp
import websockets
import json
import uuid
from datetime import datetime, timezone

# Configuration
BACKEND_URL = "http://localhost:8001"
WS_URL = "ws://localhost:8001/ws"

# Mark all tests as async
pytestmark = [pytest.mark.asyncio, pytest.mark.integration]

@pytest.fixture
async def unique_node_id():
    """Fixture to register a unique node ID for each test."""
    node_id = f"sentry-{uuid.uuid4().hex[:8]}"
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BACKEND_URL}/api/nodes/register", 
            json={"node_id": node_id}
        ) as resp:
            assert resp.status in [200, 201], f"Failed to register node: {await resp.text()}"
    return node_id

async def create_detection(node_id: str):
    """Helper to create a detection via REST API."""
    detection_data = {
        "node_id": node_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "location": {
            "latitude": 71.297, 
            "longitude": -156.769, 
            "altitude_m": 149.0, 
            "accuracy_m": 7.5
        },
        "detections": [
            {"class": "person", "confidence": 0.95, "bbox": [100, 200, 300, 400]}
        ],
        "detection_count": 1,
        "inference_time_ms": 42.0,
        "model": "yolov8n"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BACKEND_URL}/api/detections", 
            json=detection_data
        ) as resp:
            assert resp.status == 200, f"Failed to create detection: {await resp.text()}"
            return await resp.json()

async def test_websocket_connection():
    """Test that a client can connect and receives the welcome message."""
    client_id = str(uuid.uuid4())
    uri = f"{WS_URL}?client_id={client_id}"
    
    print(f"Connecting to {uri}...")
    async with websockets.connect(uri) as websocket:
        message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
        data = json.loads(message)
        
        print(f"Received: {data}")
        assert data["type"] == "connection_established"
        assert data["client_id"] == client_id

async def test_websocket_broadcast_single_client(unique_node_id):
    """Test that a single client receives a detection broadcast."""
    client_id = str(uuid.uuid4())
    uri = f"{WS_URL}?client_id={client_id}"
    
    async with websockets.connect(uri) as websocket:
        # 1. Wait for handshake
        await websocket.recv()
        
        # 2. Create detection
        print(f"Creating detection for node {unique_node_id}...")
        detection_resp = await create_detection(unique_node_id)
        detection_id = detection_resp["id"]
        
        # 3. Wait for broadcast
        print("Waiting for broadcast...")
        message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
        data = json.loads(message)
        
        print(f"Received broadcast: {data}")
        assert data["type"] == "detection"
        assert data["data"]["id"] == detection_id
        assert data["data"]["node_id"] == unique_node_id

async def test_websocket_broadcast_multi_client(unique_node_id):
    """Test that multiple clients ALL receive the same broadcast."""
    num_clients = 3
    connections = []
    
    try:
        # 1. Connect all clients
        print(f"Connecting {num_clients} clients...")
        for _ in range(num_clients):
            cid = str(uuid.uuid4())
            ws = await websockets.connect(f"{WS_URL}?client_id={cid}")
            # Read handshake to ensure connection is established
            await ws.recv()
            connections.append(ws)
            
        # 2. Create detection
        print(f"Creating detection for node {unique_node_id}...")
        detection_resp = await create_detection(unique_node_id)
        detection_id = detection_resp["id"]
        
        # 3. Verify all clients receive it
        print("Verifying broadcasts...")
        for i, ws in enumerate(connections):
            message = await asyncio.wait_for(ws.recv(), timeout=5.0)
            data = json.loads(message)
            
            print(f"Client {i} received: {data['type']}")
            assert data["type"] == "detection"
            assert data["data"]["id"] == detection_id
            
    finally:
        # Cleanup connections
        for ws in connections:
            await ws.close()
