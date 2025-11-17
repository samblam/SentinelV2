"""
Burst Transmission Handler for Blackout Mode
Transmits queued detections to backend when exiting blackout
"""
import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BurstTransmissionError(Exception):
    """Raised when burst transmission fails"""
    pass


async def transmit_queued_detections(
    queued_detections: List[Dict[str, Any]],
    backend_url: str,
    node_id: str,
    batch_size: int = 10,
    timeout: int = 30,
    max_retries: int = 3,
    retry_backoff_base: float = 2.0
) -> Dict[str, Any]:
    """
    Transmit queued detections to backend in batches with retry logic.

    Args:
        queued_detections: List of queued detection objects with 'id' and 'detection' keys
        backend_url: Backend API base URL (e.g., "http://localhost:8001")
        node_id: Edge node identifier
        batch_size: Number of detections to send per batch
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts per detection (default: 3)
        retry_backoff_base: Base for exponential backoff calculation (default: 2.0)

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

    logger.info(f"[BURST] Starting transmission of {total} queued detections")
    logger.info(f"[BURST] Backend: {backend_url}")
    logger.info(f"[BURST] Batch size: {batch_size}")

    async with aiohttp.ClientSession() as session:
        # Process in batches to avoid overwhelming backend
        for i in range(0, total, batch_size):
            batch = queued_detections[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total + batch_size - 1) // batch_size

            logger.info(f"[BURST] Processing batch {batch_num}/{total_batches} ({len(batch)} detections)")

            for item in batch:
                detection_id = item['id']
                detection_data = item['detection']

                # Retry logic with exponential backoff
                success = False
                for attempt in range(max_retries):
                    try:
                        # POST detection to backend
                        async with session.post(
                            f"{backend_url}/api/detections",
                            json=detection_data,
                            timeout=aiohttp.ClientTimeout(total=timeout)
                        ) as response:
                            if response.status in [200, 201]:
                                transmitted_ids.append(detection_id)
                                success = True
                                break
                            else:
                                error_text = await response.text()
                                if attempt < max_retries - 1:
                                    backoff_time = retry_backoff_base ** attempt
                                    logger.warning(f"[BURST] Failed to transmit detection {detection_id}: HTTP {response.status}, retrying in {backoff_time}s (attempt {attempt + 1}/{max_retries})")
                                    await asyncio.sleep(backoff_time)
                                else:
                                    logger.error(f"[BURST] Failed to transmit detection {detection_id} after {max_retries} attempts: HTTP {response.status}")
                                    logger.error(f"[BURST] Error: {error_text}")

                    except asyncio.TimeoutError:
                        if attempt < max_retries - 1:
                            backoff_time = retry_backoff_base ** attempt
                            logger.warning(f"[BURST] Timeout transmitting detection {detection_id}, retrying in {backoff_time}s (attempt {attempt + 1}/{max_retries})")
                            await asyncio.sleep(backoff_time)
                        else:
                            logger.error(f"[BURST] Timeout transmitting detection {detection_id} after {max_retries} attempts")

                    except aiohttp.ClientError as e:
                        if attempt < max_retries - 1:
                            backoff_time = retry_backoff_base ** attempt
                            logger.warning(f"[BURST] Network error transmitting detection {detection_id}: {e}, retrying in {backoff_time}s (attempt {attempt + 1}/{max_retries})")
                            await asyncio.sleep(backoff_time)
                        else:
                            logger.error(f"[BURST] Network error transmitting detection {detection_id} after {max_retries} attempts: {e}")

                    except Exception as e:
                        # Unexpected errors shouldn't be retried
                        logger.error(f"[BURST] Unexpected error transmitting detection {detection_id}: {e}")
                        break

                # If all retries failed, add to failed_ids
                if not success:
                    failed_ids.append(detection_id)

            # Small delay between batches to avoid overwhelming backend
            if i + batch_size < total:
                await asyncio.sleep(0.1)

    transmitted_count = len(transmitted_ids)
    failed_count = len(failed_ids)

    logger.info(f"[BURST] Transmission complete:")
    logger.info(f"[BURST]   Total: {total}")
    logger.info(f"[BURST]   Transmitted: {transmitted_count}")
    logger.info(f"[BURST]   Failed: {failed_count}")

    if failed_count > 0:
        logger.warning(f"[BURST] WARNING: {failed_count} detections failed to transmit")
        logger.warning(f"[BURST] Failed IDs: {failed_ids}")

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
    logger.info(f"[BLACKOUT] Starting deactivation workflow for node {node_id}")

    # Get queued detections before deactivating
    queued = await blackout_controller.get_queued_detections()
    queued_count = len(queued)

    logger.info(f"[BLACKOUT] Found {queued_count} queued detections")

    # Deactivate blackout mode
    await blackout_controller.deactivate()

    if queued_count == 0:
        logger.info(f"[BLACKOUT] No detections to transmit")
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
        logger.info(f"[BLACKOUT] Marked {len(transmission_result['transmitted_ids'])} detections as transmitted")

    # Clear transmitted detections from queue
    await blackout_controller.clear_transmitted()
    logger.info(f"[BLACKOUT] Cleared transmitted detections from queue")

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
                        logger.info(f"[BLACKOUT] Notified backend of completion")
                    else:
                        logger.warning(f"[BLACKOUT] Failed to notify backend: HTTP {response.status}")
        except Exception as e:
            logger.error(f"[BLACKOUT] Error notifying backend: {e}")

    return {
        "status": "completed",
        "queued_count": queued_count,
        "transmitted_count": transmission_result['transmitted'],
        "failed_count": transmission_result['failed'],
        "failed_ids": transmission_result.get('failed_ids', [])
    }
