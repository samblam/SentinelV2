#!/usr/bin/env python3
"""
Backend API Performance Benchmark Script

Tests API endpoint latency, throughput, and database performance.
Generates performance report for README documentation.

Usage:
    python3 backend/benchmarks/benchmark_api.py
"""

import asyncio
import time
import statistics
import json
from typing import List, Dict
import aiohttp

# Configuration
BACKEND_URL = "http://localhost:8000"
NUM_REQUESTS = 1000
CONCURRENT_REQUESTS = 10


async def benchmark_health_endpoint(session: aiohttp.ClientSession, num_requests: int) -> List[float]:
    """Benchmark /health endpoint latency."""
    latencies = []

    for _ in range(num_requests):
        start = time.perf_counter()
        async with session.get(f"{BACKEND_URL}/health") as response:
            await response.json()
        latency = (time.perf_counter() - start) * 1000  # Convert to ms
        latencies.append(latency)

    return latencies


async def benchmark_node_registration(session: aiohttp.ClientSession, num_requests: int) -> List[float]:
    """Benchmark /api/nodes/register endpoint."""
    latencies = []

    for i in range(num_requests):
        node_data = {"node_id": f"benchmark-node-{i:04d}"}
        start = time.perf_counter()
        async with session.post(
            f"{BACKEND_URL}/api/nodes/register",
            json=node_data
        ) as response:
            await response.json()
        latency = (time.perf_counter() - start) * 1000
        latencies.append(latency)

    return latencies


async def benchmark_detection_ingestion(session: aiohttp.ClientSession, num_requests: int) -> List[float]:
    """Benchmark /api/detections endpoint."""
    latencies = []

    # First, register a test node
    await session.post(
        f"{BACKEND_URL}/api/nodes/register",
        json={"node_id": "benchmark-node"}
    )

    detection_data = {
        "node_id": "benchmark-node",
        "timestamp": "2025-11-17T10:00:00Z",
        "latitude": 70.5234,
        "longitude": -100.8765,
        "altitude_m": 45.2,
        "accuracy_m": 10.0,
        "detections": [
            {
                "class": "person",
                "confidence": 0.89,
                "bbox": [100, 150, 300, 400],
                "class_id": 0
            }
        ],
        "detection_count": 1,
        "inference_time_ms": 87.3,
        "model": "yolov5n"
    }

    for _ in range(num_requests):
        start = time.perf_counter()
        async with session.post(
            f"{BACKEND_URL}/api/detections",
            json=detection_data
        ) as response:
            await response.json()
        latency = (time.perf_counter() - start) * 1000
        latencies.append(latency)

    return latencies


async def benchmark_concurrent_requests(session: aiohttp.ClientSession, num_concurrent: int) -> Dict:
    """Benchmark concurrent request handling."""
    async def single_request():
        start = time.perf_counter()
        async with session.get(f"{BACKEND_URL}/health") as response:
            await response.json()
        return (time.perf_counter() - start) * 1000

    start_time = time.perf_counter()
    latencies = await asyncio.gather(*[single_request() for _ in range(num_concurrent)])
    total_time = time.perf_counter() - start_time

    return {
        "latencies": latencies,
        "total_time_ms": total_time * 1000,
        "requests_per_second": num_concurrent / total_time
    }


def calculate_statistics(latencies: List[float]) -> Dict:
    """Calculate performance statistics."""
    return {
        "count": len(latencies),
        "mean_ms": statistics.mean(latencies),
        "median_ms": statistics.median(latencies),
        "stdev_ms": statistics.stdev(latencies) if len(latencies) > 1 else 0,
        "min_ms": min(latencies),
        "max_ms": max(latencies),
        "p95_ms": statistics.quantiles(latencies, n=20)[18] if len(latencies) > 20 else max(latencies),
        "p99_ms": statistics.quantiles(latencies, n=100)[98] if len(latencies) > 100 else max(latencies),
    }


async def run_benchmarks():
    """Run all benchmarks and generate report."""
    print("=" * 70)
    print("Backend API Performance Benchmark")
    print("=" * 70)
    print(f"Target: {BACKEND_URL}")
    print(f"Requests per test: {NUM_REQUESTS}")
    print()

    results = {}

    async with aiohttp.ClientSession() as session:
        # Test 1: Health endpoint latency
        print("1. Health Endpoint Latency Test...")
        health_latencies = await benchmark_health_endpoint(session, NUM_REQUESTS)
        results["health_endpoint"] = calculate_statistics(health_latencies)
        print(f"   Mean: {results['health_endpoint']['mean_ms']:.2f}ms")
        print(f"   P95:  {results['health_endpoint']['p95_ms']:.2f}ms")

        # Test 2: Node registration
        print("\n2. Node Registration Latency Test...")
        registration_latencies = await benchmark_node_registration(session, 100)  # Fewer to avoid duplicate keys
        results["node_registration"] = calculate_statistics(registration_latencies)
        print(f"   Mean: {results['node_registration']['mean_ms']:.2f}ms")
        print(f"   P95:  {results['node_registration']['p95_ms']:.2f}ms")

        # Test 3: Detection ingestion
        print("\n3. Detection Ingestion Latency Test...")
        detection_latencies = await benchmark_detection_ingestion(session, NUM_REQUESTS)
        results["detection_ingestion"] = calculate_statistics(detection_latencies)
        print(f"   Mean: {results['detection_ingestion']['mean_ms']:.2f}ms")
        print(f"   P95:  {results['detection_ingestion']['p95_ms']:.2f}ms")

        # Test 4: Concurrent request handling
        print("\n4. Concurrent Request Handling Test...")
        concurrent_results = await benchmark_concurrent_requests(session, CONCURRENT_REQUESTS)
        results["concurrent_requests"] = concurrent_results
        print(f"   Total Time: {concurrent_results['total_time_ms']:.2f}ms")
        print(f"   Throughput: {concurrent_results['requests_per_second']:.2f} req/s")

    # Save results to JSON
    with open("backend/benchmarks/results.json", "w") as f:
        json.dump(results, f, indent=2)

    # Generate markdown report
    generate_markdown_report(results)

    print("\n" + "=" * 70)
    print("Benchmark Complete!")
    print("Results saved to:")
    print("  - backend/benchmarks/results.json")
    print("  - backend/benchmarks/PERFORMANCE_REPORT.md")
    print("=" * 70)


def generate_markdown_report(results: Dict):
    """Generate markdown performance report."""
    report = f"""# Backend API Performance Benchmark Results

**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}
**Backend URL:** {BACKEND_URL}
**Requests per Test:** {NUM_REQUESTS}

---

## Summary

| Endpoint | Mean Latency | P95 Latency | P99 Latency | Min | Max |
|----------|--------------|-------------|-------------|-----|-----|
| Health Check | {results['health_endpoint']['mean_ms']:.2f}ms | {results['health_endpoint']['p95_ms']:.2f}ms | {results['health_endpoint']['p99_ms']:.2f}ms | {results['health_endpoint']['min_ms']:.2f}ms | {results['health_endpoint']['max_ms']:.2f}ms |
| Node Registration | {results['node_registration']['mean_ms']:.2f}ms | {results['node_registration']['p95_ms']:.2f}ms | {results['node_registration']['p99_ms']:.2f}ms | {results['node_registration']['min_ms']:.2f}ms | {results['node_registration']['max_ms']:.2f}ms |
| Detection Ingestion | {results['detection_ingestion']['mean_ms']:.2f}ms | {results['detection_ingestion']['p95_ms']:.2f}ms | {results['detection_ingestion']['p99_ms']:.2f}ms | {results['detection_ingestion']['min_ms']:.2f}ms | {results['detection_ingestion']['max_ms']:.2f}ms |

---

## Detailed Results

### 1. Health Endpoint (`GET /health`)

- **Requests:** {results['health_endpoint']['count']}
- **Mean Latency:** {results['health_endpoint']['mean_ms']:.2f}ms ± {results['health_endpoint']['stdev_ms']:.2f}ms
- **Median Latency:** {results['health_endpoint']['median_ms']:.2f}ms
- **95th Percentile:** {results['health_endpoint']['p95_ms']:.2f}ms
- **99th Percentile:** {results['health_endpoint']['p99_ms']:.2f}ms
- **Min/Max:** {results['health_endpoint']['min_ms']:.2f}ms / {results['health_endpoint']['max_ms']:.2f}ms

### 2. Node Registration (`POST /api/nodes/register`)

- **Requests:** {results['node_registration']['count']}
- **Mean Latency:** {results['node_registration']['mean_ms']:.2f}ms ± {results['node_registration']['stdev_ms']:.2f}ms
- **Median Latency:** {results['node_registration']['median_ms']:.2f}ms
- **95th Percentile:** {results['node_registration']['p95_ms']:.2f}ms
- **99th Percentile:** {results['node_registration']['p99_ms']:.2f}ms
- **Min/Max:** {results['node_registration']['min_ms']:.2f}ms / {results['node_registration']['max_ms']:.2f}ms

### 3. Detection Ingestion (`POST /api/detections`)

- **Requests:** {results['detection_ingestion']['count']}
- **Mean Latency:** {results['detection_ingestion']['mean_ms']:.2f}ms ± {results['detection_ingestion']['stdev_ms']:.2f}ms
- **Median Latency:** {results['detection_ingestion']['median_ms']:.2f}ms
- **95th Percentile:** {results['detection_ingestion']['p95_ms']:.2f}ms
- **99th Percentile:** {results['detection_ingestion']['p99_ms']:.2f}ms
- **Min/Max:** {results['detection_ingestion']['min_ms']:.2f}ms / {results['detection_ingestion']['max_ms']:.2f}ms

### 4. Concurrent Request Handling

- **Concurrent Requests:** {CONCURRENT_REQUESTS}
- **Total Time:** {results['concurrent_requests']['total_time_ms']:.2f}ms
- **Throughput:** {results['concurrent_requests']['requests_per_second']:.2f} requests/second
- **Mean Latency:** {statistics.mean(results['concurrent_requests']['latencies']):.2f}ms

---

## Performance Assessment

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| API Latency (Mean) | <50ms | {results['health_endpoint']['mean_ms']:.2f}ms | {'✅ PASS' if results['health_endpoint']['mean_ms'] < 50 else '⚠️  WARNING'} |
| Detection Ingestion (P95) | <100ms | {results['detection_ingestion']['p95_ms']:.2f}ms | {'✅ PASS' if results['detection_ingestion']['p95_ms'] < 100 else '⚠️  WARNING'} |
| Throughput | >100 req/s | {results['concurrent_requests']['requests_per_second']:.2f} req/s | {'✅ PASS' if results['concurrent_requests']['requests_per_second'] > 100 else '⚠️  WARNING'} |

---

## Test Environment

- **Python:** 3.11+
- **FastAPI:** 0.111.0
- **PostgreSQL:** 15
- **Database:** Async PostgreSQL (asyncpg)

---

**Generated by:** `backend/benchmarks/benchmark_api.py`
"""

    with open("backend/benchmarks/PERFORMANCE_REPORT.md", "w") as f:
        f.write(report)


if __name__ == "__main__":
    asyncio.run(run_benchmarks())
