#!/usr/bin/env python3
"""Test WebSocket real-time broadcast of detections."""
import asyncio
import websockets
import json
import requests
from uuid import uuid4
from datetime import datetime, timezone

async def test_websocket_broadcast():
    """Test valid detection broadcast."""
    client_id = str(uuid4())
    uri = f"ws://localhost:8001/ws?client_id={client_id}"

    print("Connecting to WebSocket...")
    async with websockets.connect(uri) as websocket:
        # Receive connection message
        conn_msg = await websocket.recv()
        print(f"✓ Connected: {json.loads(conn_msg)['type']}")

        # Create a new detection via REST API
        print("\nCreating new detection via API...")
        detection_data = {
            "node_id": "sentry-01",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "location": {"latitude": 71.296, "longitude": -156.768, "altitude_m": 148.0, "accuracy_m": 7.0},
            "detections": [
                {"class": "person", "confidence": 0.94, "bbox": [110, 210, 310, 410]}
            ],
            "detection_count": 1,
            "inference_time_ms": 42.0,
            "model": "yolov8n"
        }

        response = requests.post(
            "http://localhost:8001/api/detections",
            json=detection_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"✓ Detection created: ID {response.json()['id']}")

        # Wait for WebSocket broadcast
        print("\nWaiting for WebSocket broadcast...")
        try:
            broadcast_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            msg = json.loads(broadcast_msg)
            print(f"✓ Received broadcast: type={msg['type']}")

            if msg['type'] == 'detection':
                print(f"  - Detection ID: {msg['data']['id']}")
                print(f"  - Node: {msg['data']['node_id']}")
                print(f"  - Detection count: {msg['data']['detection_count']}")
                print(f"  - Full detection objects included: {len(msg['data']['detections'])} objects")
                print("\n✓ Real-time WebSocket broadcast test PASSED!")
                return True
            else:
                print(f"✗ Unexpected message type: {msg['type']}")
                return False

        except asyncio.TimeoutError:
            print("✗ No broadcast received within 5 seconds")
            return False

async def test_invalid_payload():
    """Test that invalid detection payload doesn't cause broadcast."""
    client_id = str(uuid4())
    uri = f"ws://localhost:8001/ws?client_id={client_id}"

    print("\n\nTesting invalid payload handling...")
    print("Connecting to WebSocket...")
    async with websockets.connect(uri) as websocket:
        # Receive connection message
        conn_msg = await websocket.recv()
        print(f"✓ Connected: {json.loads(conn_msg)['type']}")

        # Submit invalid detection (missing required fields)
        print("\nSubmitting invalid detection payload...")
        invalid_data = {
            "node_id": "sentry-01",
            # Missing timestamp, location, detections, etc.
        }

        response = requests.post(
            "http://localhost:8001/api/detections",
            json=invalid_data,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code != 200:
            print(f"✓ Invalid payload rejected with status {response.status_code}")
        else:
            print(f"✗ Invalid payload was accepted (status {response.status_code})")
            return False

        # Verify no broadcast was sent
        print("Verifying no broadcast was sent...")
        try:
            broadcast_msg = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            print(f"✗ Unexpected broadcast received: {broadcast_msg}")
            return False
        except asyncio.TimeoutError:
            print("✓ No broadcast sent for invalid payload")
            print("\n✓ Invalid payload test PASSED!")
            return True

if __name__ == "__main__":
    result1 = asyncio.run(test_websocket_broadcast())
    result2 = asyncio.run(test_invalid_payload())
    exit(0 if (result1 and result2) else 1)
