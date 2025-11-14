#!/usr/bin/env python3
"""Test WebSocket real-time broadcast of detections."""
import asyncio
import websockets
import json
import requests
from uuid import uuid4
from datetime import datetime

async def test_websocket_broadcast():
    client_id = str(uuid4())
    uri = f"ws://localhost:8001/ws?client_id={client_id}"

    print(f"Connecting to WebSocket...")
    async with websockets.connect(uri) as websocket:
        # Receive connection message
        conn_msg = await websocket.recv()
        print(f"✓ Connected: {json.loads(conn_msg)['type']}")

        # Create a new detection via REST API
        print("\nCreating new detection via API...")
        detection_data = {
            "node_id": "sentry-01",
            "timestamp": datetime.utcnow().isoformat(),
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

if __name__ == "__main__":
    result = asyncio.run(test_websocket_broadcast())
    exit(0 if result else 1)
