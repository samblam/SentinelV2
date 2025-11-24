#!/usr/bin/env python3
"""
Multi-node blackout integration test.

Tests blackout coordination across multiple edge nodes:
1. Multiple nodes activated in blackout simultaneously
2. Each node queues detections independently
3. Nodes deactivated at different times
4. Backend tracks each node's blackout state separately
"""
import asyncio
import aiohttp
import pytest
from datetime import datetime, timezone

# Mark all tests in this module as integration tests
pytestmark = [pytest.mark.integration, pytest.mark.slow]


import uuid

BACKEND_URL = "http://localhost:8001"
# Use unique node IDs to avoid state collisions
NODE_IDS = [f"sentry-{uuid.uuid4().hex[:8]}", f"sentry-{uuid.uuid4().hex[:8]}", f"aerostat-{uuid.uuid4().hex[:8]}"]


async def wait_for_backend(timeout: int = 30):
    """Wait for backend to be ready."""
    start_time = asyncio.get_event_loop().time()
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(f"{BACKEND_URL}/health", timeout=aiohttp.ClientTimeout(total=2)) as response:
                    if response.status == 200:
                        return True
            except (aiohttp.ClientError, asyncio.TimeoutError):
                pass

            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError(f"Backend not ready after {timeout}s")

            await asyncio.sleep(1)


async def ensure_node_exists(session: aiohttp.ClientSession, node_id: str):
    """Ensure node exists in backend."""
    # Create node via register
    async with session.post(
        f"{BACKEND_URL}/api/nodes/register",
        json={"node_id": node_id}
    ) as response:
        if response.status in [200, 201]:
            print(f"  ✓ Node {node_id} ready")


@pytest.mark.asyncio
async def test_multi_node_blackout():
    """
    Test blackout coordination across multiple nodes.
    """
    print("\n" + "=" * 70)
    print("MULTI-NODE BLACKOUT COORDINATION TEST")
    print("=" * 70)

    # Step 0: Wait for backend
    print("\n[STEP 0] Waiting for backend to be ready...")
    await wait_for_backend()
    print("✓ Backend is ready")

    async with aiohttp.ClientSession() as session:
        # Step 0.5: Ensure all nodes exist
        print(f"\n[STEP 0.5] Ensuring {len(NODE_IDS)} nodes exist...")
        await asyncio.gather(*[
            ensure_node_exists(session, node_id)
            for node_id in NODE_IDS
        ])

        # Step 1: Activate blackout for all nodes
        print(f"\n[STEP 1] Activating blackout for all {len(NODE_IDS)} nodes...")
        activation_results = []
        for i, node_id in enumerate(NODE_IDS):
            async with session.post(
                f"{BACKEND_URL}/api/nodes/{node_id}/blackout/activate",
                json={
                    "reason": "Coordinated covert operation",
                    "operator_id": "operator-bravo"
                }
            ) as response:
                assert response.status == 200, f"Failed to activate {node_id}: {await response.text()}"
                data = await response.json()
                activation_results.append({
                    "node_id": node_id,
                    "blackout_id": data["blackout_id"]
                })
                print(f"  ✓ {node_id}: blackout_id={data['blackout_id']}")

        await asyncio.sleep(1.5)

        # Step 2: Verify all nodes in covert mode
        print(f"\n[STEP 2] Verifying all nodes are in covert mode...")
        async with session.get(f"{BACKEND_URL}/api/nodes") as response:
            nodes = await response.json()
            for node_id in NODE_IDS:
                node = next((n for n in nodes if n['node_id'] == node_id), None)
                assert node is not None, f"Node {node_id} not found"
                assert node['status'] == 'covert', \
                    f"{node_id}: Expected 'covert', got '{node['status']}'"
                print(f"  ✓ {node_id}: status={node['status']}")

        # Step 3: Check individual blackout statuses
        print(f"\n[STEP 3] Checking blackout status for each node...")
        for result in activation_results:
            node_id = result['node_id']
            blackout_id = result['blackout_id']

            async with session.get(
                f"{BACKEND_URL}/api/nodes/{node_id}/blackout/status"
            ) as response:
                status = await response.json()
                assert status['status'] == 'active'
                assert status['blackout_id'] == blackout_id
                print(f"  ✓ {node_id}: active (duration={status.get('duration_seconds', 0)}s)")

        # Step 4: Deactivate first node only
        print(f"\n[STEP 4] Deactivating blackout for {NODE_IDS[0]} only...")
        async with session.post(
            f"{BACKEND_URL}/api/nodes/{NODE_IDS[0]}/blackout/deactivate"
        ) as response:
            assert response.status == 200
            summary = await response.json()
            print(f"  ✓ {NODE_IDS[0]} deactivated (duration={summary['duration_seconds']}s)")

        await asyncio.sleep(0.5)

        # Step 5: Verify first node back to normal, others still covert
        print(f"\n[STEP 5] Verifying mixed node states...")
        async with session.get(f"{BACKEND_URL}/api/nodes") as response:
            nodes = await response.json()

            # First node should be resuming or online
            node = next((n for n in nodes if n['node_id'] == NODE_IDS[0]), None)
            assert node is not None
            assert node['status'] in ['online', 'resuming', 'offline'], \
                f"Expected online/resuming/offline, got '{node['status']}'"
            print(f"  ✓ {NODE_IDS[0]}: {node['status']}")

            # Other nodes should still be covert
            for node_id in NODE_IDS[1:]:
                node = next((n for n in nodes if n['node_id'] == node_id), None)
                assert node is not None
                assert node['status'] == 'covert', \
                    f"{node_id}: Expected 'covert', got '{node['status']}'"
                print(f"  ✓ {node_id}: {node['status']}")

        # Step 6: Deactivate remaining nodes
        print(f"\n[STEP 6] Deactivating remaining nodes...")
        for node_id in NODE_IDS[1:]:
            async with session.post(
                f"{BACKEND_URL}/api/nodes/{node_id}/blackout/deactivate"
            ) as response:
                assert response.status == 200
                summary = await response.json()
                print(f"  ✓ {node_id} deactivated (duration={summary['duration_seconds']}s)")

        await asyncio.sleep(1)

        # Step 7: Verify all blackout events recorded
        print(f"\n[STEP 7] Verifying blackout event history...")
        async with session.get(f"{BACKEND_URL}/api/blackout/events?limit=50") as response:
            events = await response.json()
            assert len(events) >= len(NODE_IDS), \
                f"Expected at least {len(NODE_IDS)} events, got {len(events)}"

            # Verify each node has a completed blackout event
            for result in activation_results:
                node_id = result['node_id']
                blackout_id = result['blackout_id']

                event = next((e for e in events if e['id'] == blackout_id), None)
                assert event is not None, f"Event {blackout_id} for {node_id} not found"
                assert event['deactivated_at'] is not None, \
                    f"{node_id}: Event not completed"
                assert event['duration_seconds'] > 0, \
                    f"{node_id}: Invalid duration"
                print(f"  ✓ {node_id}: event_id={blackout_id}, duration={event['duration_seconds']}s")

        # Step 8: Verify node statuses returned to normal
        print(f"\n[STEP 8] Verifying all nodes returned to normal...")
        async with session.get(f"{BACKEND_URL}/api/nodes") as response:
            nodes = await response.json()
            for node_id in NODE_IDS:
                node = next((n for n in nodes if n['node_id'] == node_id), None)
                assert node is not None
                assert node['status'] in ['online', 'offline'], \
                    f"{node_id}: Expected online/offline, got '{node['status']}'"
                print(f"  ✓ {node_id}: {node['status']}")

    print("\n" + "=" * 70)
    print("✓ MULTI-NODE BLACKOUT TEST PASSED")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_multi_node_blackout())
