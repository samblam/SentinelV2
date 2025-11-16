"""
Burst Transmission Handler for Blackout Mode
Transmits queued detections to backend when exiting blackout
"""
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime


class BurstTransmissionError(Exception):
    """Raised when burst transmission fails"""
    pass


async def transmit_queued_detections(
    queued_detections: List[Dict[str, Any]],
    backend_url: str,
    node_id: str,
    batch_size: int = 10,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Transmit queued detections to backend in batches.

    Args:
        queued_detections: List of queued detection objects with 'id' and 'detection' keys
        backend_url: Backend API base URL (e.g., "http://localhost:8001")
        node_id: Edge node identifier
        batch_size: Number of detections to send per batch
        timeout: Request timeout in seconds

    Returns:
        Transmission summary with success/failure counts

    Raises:
        BurstTransmissionError: If transmission fails critically
    """
    if not queued_detections:
        return {
            "status": "success",
            "total": 0,
            "transmitted": 0,
            "failed": 0,
            "failed_ids": []
        }

    total = len(queued_detections)
    transmitted_ids = []
    failed_ids = []

    print(f"[BURST] Starting transmission of {total} queued detections")
    print(f"[BURST] Backend: {backend_url}")
    print(f"[BURST] Batch size: {batch_size}")

    async with aiohttp.ClientSession() as session:
        # Process in batches to avoid overwhelming backend
        for i in range(0, total, batch_size):
            batch = queued_detections[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total + batch_size - 1) // batch_size

            print(f"[BURST] Processing batch {batch_num}/{total_batches} ({len(batch)} detections)")

            for item in batch:
                detection_id = item['id']
                detection_data = item['detection']

                try:
                    # POST detection to backend
                    async with session.post(
                        f"{backend_url}/api/detections",
                        json=detection_data,
                        timeout=aiohttp.ClientTimeout(total=timeout)
                    ) as response:
                        if response.status in [200, 201]:
                            transmitted_ids.append(detection_id)
                        else:
                            error_text = await response.text()
                            print(f"[BURST] Failed to transmit detection {detection_id}: HTTP {response.status}")
                            print(f"[BURST] Error: {error_text}")
                            failed_ids.append(detection_id)

                except asyncio.TimeoutError:
                    print(f"[BURST] Timeout transmitting detection {detection_id}")
                    failed_ids.append(detection_id)

                except aiohttp.ClientError as e:
                    print(f"[BURST] Network error transmitting detection {detection_id}: {e}")
                    failed_ids.append(detection_id)

                except Exception as e:
                    print(f"[BURST] Unexpected error transmitting detection {detection_id}: {e}")
                    failed_ids.append(detection_id)

            # Small delay between batches to avoid overwhelming backend
            if i + batch_size < total:
                await asyncio.sleep(0.1)

    transmitted_count = len(transmitted_ids)
    failed_count = len(failed_ids)

    print(f"[BURST] Transmission complete:")
    print(f"[BURST]   Total: {total}")
    print(f"[BURST]   Transmitted: {transmitted_count}")
    print(f"[BURST]   Failed: {failed_count}")

    if failed_count > 0:
        print(f"[BURST] WARNING: {failed_count} detections failed to transmit")
        print(f"[BURST] Failed IDs: {failed_ids}")

    return {
        "status": "success" if failed_count == 0 else "partial",
        "total": total,
        "transmitted": transmitted_count,
        "transmitted_ids": transmitted_ids,
        "failed": failed_count,
        "failed_ids": failed_ids
    }


async def complete_blackout_deactivation(
    blackout_controller,
    backend_url: str,
    node_id: str,
    blackout_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Complete blackout deactivation workflow:
    1. Deactivate blackout mode
    2. Get queued detections
    3. Transmit to backend
    4. Mark as transmitted
    5. Clear transmitted detections

    Args:
        blackout_controller: BlackoutController instance
        backend_url: Backend API base URL
        node_id: Edge node identifier
        blackout_id: Backend blackout event ID

    Returns:
        Summary of deactivation and transmission
    """
    print(f"[BLACKOUT] Starting deactivation workflow for node {node_id}")

    # Get queued detections before deactivating
    queued = await blackout_controller.get_queued_detections()
    queued_count = len(queued)

    print(f"[BLACKOUT] Found {queued_count} queued detections")

    # Deactivate blackout mode
    await blackout_controller.deactivate()

    if queued_count == 0:
        print(f"[BLACKOUT] No detections to transmit")
        return {
            "status": "completed",
            "queued_count": 0,
            "transmitted_count": 0,
            "failed_count": 0
        }

    # Transmit queued detections
    transmission_result = await transmit_queued_detections(
        queued_detections=queued,
        backend_url=backend_url,
        node_id=node_id
    )

    # Mark transmitted detections
    if transmission_result['transmitted_ids']:
        await blackout_controller.mark_transmitted(transmission_result['transmitted_ids'])
        print(f"[BLACKOUT] Marked {len(transmission_result['transmitted_ids'])} detections as transmitted")

    # Clear transmitted detections from queue
    await blackout_controller.clear_transmitted()
    print(f"[BLACKOUT] Cleared transmitted detections from queue")

    # Notify backend of completion if blackout_id provided
    if blackout_id:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{backend_url}/api/nodes/{node_id}/blackout/complete",
                    json={
                        "blackout_id": blackout_id,
                        "transmitted_count": transmission_result['transmitted']
                    }
                ) as response:
                    if response.status == 200:
                        print(f"[BLACKOUT] Notified backend of completion")
                    else:
                        print(f"[BLACKOUT] Failed to notify backend: HTTP {response.status}")
        except Exception as e:
            print(f"[BLACKOUT] Error notifying backend: {e}")

    return {
        "status": "completed",
        "queued_count": queued_count,
        "transmitted_count": transmission_result['transmitted'],
        "failed_count": transmission_result['failed'],
        "failed_ids": transmission_result.get('failed_ids', [])
    }
