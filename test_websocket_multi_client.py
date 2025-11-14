#!/usr/bin/env python3
"""Test WebSocket broadcast to multiple clients."""
import asyncio
import websockets
import json
import requests
from uuid import uuid4
from datetime import datetime, timezone

async def listen_for_broadcast(client_id, uri, received_messages):
    """Connect and listen for broadcast messages."""
    async with websockets.connect(uri) as websocket:
        # Receive connection message
        conn_msg = await websocket.recv()
        msg = json.loads(conn_msg)
        assert msg['type'] == 'connection_established'
        print(f"✓ Client {client_id[:8]} connected")

        # Wait for detection broadcast
        try:
            broadcast_msg = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            msg = json.loads(broadcast_msg)
            received_messages[client_id] = msg
            print(f"✓ Client {client_id[:8]} received broadcast: {msg['type']}")
        except asyncio.TimeoutError:
            print(f"✗ Client {client_id[:8]} timed out waiting for broadcast")

async def test_multi_client_broadcast():
    """Test that multiple WebSocket clients receive the same broadcast."""
    # Create 3 clients
    num_clients = 3
    client_ids = [str(uuid4()) for _ in range(num_clients)]
    uris = [f"ws://localhost:8001/ws?client_id={cid}" for cid in client_ids]
    received_messages = {}

    print(f"\nConnecting {num_clients} WebSocket clients...")

    # Start all clients listening in parallel
    listen_tasks = [
        listen_for_broadcast(client_ids[i], uris[i], received_messages)
        for i in range(num_clients)
    ]

    # Give clients time to connect
    await asyncio.sleep(1)

    # Create a detection via REST API
    print("\nCreating detection via API...")
    detection_data = {
        "node_id": "sentry-01",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "location": {"latitude": 71.297, "longitude": -156.769, "altitude_m": 149.0, "accuracy_m": 7.5},
        "detections": [
            {"class": "vehicle", "confidence": 0.96, "bbox": [120, 220, 320, 420]}
        ],
        "detection_count": 1,
        "inference_time_ms": 41.5,
        "model": "yolov8n"
    }

    response = requests.post(
        "http://localhost:8001/api/detections",
        json=detection_data,
        headers={"Content-Type": "application/json"}
    )
    detection_id = response.json()['id']
    print(f"✓ Detection created: ID {detection_id}")

    # Wait for all clients to receive the broadcast
    await asyncio.gather(*listen_tasks)

    # Verify all clients received the same message
    print(f"\n Verifying broadcast received by all {num_clients} clients...")

    if len(received_messages) != num_clients:
        print(f"✗ Only {len(received_messages)}/{num_clients} clients received broadcast")
        return False

    # Check all messages are detection type with same ID
    for client_id, msg in received_messages.items():
        if msg.get('type') != 'detection':
            print(f"✗ Client {client_id[:8]} received wrong type: {msg.get('type')}")
            return False
        if msg.get('data', {}).get('id') != detection_id:
            print(f"✗ Client {client_id[:8]} received wrong detection ID")
            return False

    print(f"✓ All {num_clients} clients received the same detection broadcast")
    print(f"  - Detection ID: {detection_id}")
    print(f"  - Node: {received_messages[client_ids[0]]['data']['node_id']}")
    print(f"  - Detection count: {received_messages[client_ids[0]]['data']['detection_count']}")
    print("\n✓ Multi-client WebSocket broadcast test PASSED!")
    return True

if __name__ == "__main__":
    result = asyncio.run(test_multi_client_broadcast())
    exit(0 if result else 1)
