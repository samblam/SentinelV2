#!/usr/bin/env python3
"""Test WebSocket connection to backend."""
import asyncio
import websockets
import json
from uuid import uuid4

async def test_websocket():
    client_id = str(uuid4())
    uri = f"ws://localhost:8001/ws?client_id={client_id}"

    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print(f"✓ Connected successfully with client_id: {client_id}")

            # Wait for messages for 5 seconds
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"✓ Received message: {message}")
            except asyncio.TimeoutError:
                print("✓ No messages received (expected for empty system)")

            print("✓ WebSocket connection test passed!")

    except Exception as e:
        print(f"✗ WebSocket connection failed: {e}")
        return False

    return True

if __name__ == "__main__":
    result = asyncio.run(test_websocket())
    exit(0 if result else 1)
