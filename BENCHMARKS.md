# Performance Benchmarks

This document describes how to run performance benchmarks for Sentinel v2.

---

## Overview

Sentinel v2 includes comprehensive performance benchmarks for all major components:

1. **Backend API** - Endpoint latency, throughput, database performance
2. **Edge Inference** - YOLOv5 inference speed, memory usage, throughput
3. **Dashboard** - Load time, interactivity, Core Web Vitals (Lighthouse)

---

## Quick Start

```bash
# Run all benchmarks
./run_all_benchmarks.sh

# Or run individually:
python3 backend/benchmarks/benchmark_api.py
python3 edge-inference/benchmarks/benchmark_inference.py
bash dashboard/benchmarks/lighthouse.sh
```

---

## 1. Backend API Benchmarks

**Script:** `backend/benchmarks/benchmark_api.py`

### Prerequisites

```bash
# Backend must be running
cd backend
docker-compose up -d

# Or locally:
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### Run Benchmark

```bash
python3 backend/benchmarks/benchmark_api.py
```

### What It Tests

- **Health endpoint** latency (`GET /health`)
- **Node registration** latency (`POST /api/nodes/register`)
- **Detection ingestion** latency (`POST /api/detections`)
- **Concurrent request** handling
- **Throughput** (requests per second)

### Output

- `backend/benchmarks/results.json` - Raw benchmark data
- `backend/benchmarks/PERFORMANCE_REPORT.md` - Markdown report

### Sample Results

```
Backend API Performance Benchmark
Target: http://localhost:8000
Requests per test: 1000

1. Health Endpoint Latency Test...
   Mean: 28.34ms
   P95:  45.12ms

2. Node Registration Latency Test...
   Mean: 52.78ms
   P95:  89.23ms

3. Detection Ingestion Latency Test...
   Mean: 64.12ms
   P95:  102.45ms
```

---

## 2. Edge Inference Benchmarks

**Script:** `edge-inference/benchmarks/benchmark_inference.py`

### Prerequisites

```bash
# Install dependencies
cd edge-inference
pip install -r requirements.txt
pip install psutil  # For memory monitoring
```

### Run Benchmark

```bash
python3 edge-inference/benchmarks/benchmark_inference.py
```

### What It Tests

- **Inference latency** (mean, P95, P99)
- **Throughput** (inferences per second)
- **Memory usage** (delta per inference)
- **Model size**

### Output

- `edge-inference/benchmarks/results.json` - Raw benchmark data
- `edge-inference/benchmarks/PERFORMANCE_REPORT.md` - Markdown report
- `test_images/` - Synthetic test images (auto-generated)

### Sample Results

```
Edge Inference Performance Benchmark

1. Inference Latency Test...
   Running 100 inferences...
   Mean Latency: 87.23ms
   P95 Latency:  103.45ms

2. Memory Usage Test...
   Mean Memory Delta: 12.34MB

3. Throughput Test (10 second duration)...
   Throughput: 11.47 inferences/second

4. Model Size: 7.50MB
```

---

## 3. Dashboard Benchmarks

**Script:** `dashboard/benchmarks/lighthouse.sh`

### Prerequisites

```bash
# Install Lighthouse globally
npm install -g lighthouse @lhci/cli

# Or use npx (no installation required)
# Script will use npx automatically if lighthouse not found

# Dashboard must be running
cd dashboard
npm run dev
```

### Run Benchmark

```bash
bash dashboard/benchmarks/lighthouse.sh
```

### What It Tests

- **Performance score** (Lighthouse)
- **Accessibility score**
- **Best practices score**
- **SEO score**
- **Core Web Vitals:**
  - First Contentful Paint (FCP)
  - Largest Contentful Paint (LCP)
  - Time to Interactive (TTI)
  - Total Blocking Time (TBT)
  - Cumulative Layout Shift (CLS)
  - Speed Index

### Output

- `dashboard/benchmarks/results.json` - Full Lighthouse JSON report
- `dashboard/benchmarks/PERFORMANCE_REPORT.md` - Markdown report

### Sample Results

```
Dashboard Performance Benchmark (Lighthouse)
Target URL: http://localhost:5173

Running Lighthouse audit...
✅ Lighthouse audit complete

Lighthouse Scores:
🚀 Performance:     92/100 ✅
♿ Accessibility:    95/100 ✅
🔧 Best Practices:  100/100 ✅
🔍 SEO:             90/100 ✅

Key Metrics:
First Contentful Paint (FCP): 1200ms ✅
Largest Contentful Paint (LCP): 1800ms ✅
Time to Interactive (TTI): 2100ms ✅
```

---

## Performance Targets

Based on Sentinel v2 strategy document:

| Metric | Target | Component |
|--------|--------|-----------|
| **Inference Time** | <100ms | Edge |
| **API Latency** | <50ms | Backend |
| **Dashboard Load** | <2s | Dashboard |
| **WebSocket Latency** | <100ms | Backend |
| **Model Size** | <10MB | Edge |
| **Detection Accuracy** | >75% mAP | Edge |
| **Bandwidth Reduction** | >100x | System |
| **Data Loss Rate** | 0% | System |

---

## Interpreting Results

### Backend API

**Good Performance:**
- Health endpoint: <30ms mean
- Detection ingestion: <70ms P95
- Throughput: >100 req/s

**Acceptable Performance:**
- Health endpoint: <50ms mean
- Detection ingestion: <100ms P95
- Throughput: >50 req/s

**Needs Improvement:**
- Health endpoint: >50ms mean
- Detection ingestion: >100ms P95
- Throughput: <50 req/s

### Edge Inference

**Good Performance:**
- Inference: <90ms mean
- Throughput: >10 fps
- Memory: <20MB delta

**Acceptable Performance:**
- Inference: <100ms mean
- Throughput: >5 fps
- Memory: <50MB delta

**Needs Improvement:**
- Inference: >100ms mean
- Throughput: <5 fps
- Memory: >50MB delta

### Dashboard

**Good Performance:**
- Performance score: >90
- LCP: <2.5s
- FCP: <1.8s
- TTI: <3.8s

**Acceptable Performance:**
- Performance score: >50
- LCP: <4.0s
- FCP: <3.0s
- TTI: <7.3s

**Needs Improvement:**
- Performance score: <50
- LCP: >4.0s
- FCP: >3.0s
- TTI: >7.3s

---

## Optimization Tips

### Backend API

1. **Database indexing** - Ensure all foreign keys and frequently queried columns are indexed
2. **Connection pooling** - Use SQLAlchemy async connection pool
3. **Query optimization** - Use `select` carefully, avoid N+1 queries
4. **Caching** - Add Redis for frequently accessed data

### Edge Inference

1. **GPU acceleration** - Use CUDA for 5-10x speedup (if GPU available)
2. **Model quantization** - INT8 quantization for 2-3x speedup on CPU
3. **Batch inference** - Process multiple images in batches
4. **Model optimization** - Use TorchScript for faster inference

### Dashboard

1. **Code splitting** - Already implemented with Vite
2. **Lazy loading** - Use React.lazy() for route-based splitting
3. **Asset compression** - Enable gzip/brotli compression
4. **Image optimization** - Use WebP format, compress tactical icons
5. **Bundle analysis** - Run `npm run build && du -sh dist/`

---

## Continuous Monitoring

### Local Development

Run benchmarks before committing major changes:

```bash
# Quick check
python3 backend/benchmarks/benchmark_api.py

# Full benchmark suite
./run_all_benchmarks.sh
```

### CI/CD Integration

Benchmarks are integrated into GitHub Actions (see `.github/workflows/benchmark.yml`).

Runs automatically on:
- Pull requests to main branch
- Release tags
- Manual trigger

---

## Troubleshooting

### Backend Benchmark Fails

**Error:** `Connection refused`

**Solution:** Ensure backend is running:
```bash
cd backend
docker-compose up -d
curl http://localhost:8000/health
```

### Edge Benchmark Fails

**Error:** `ModuleNotFoundError: No module named 'torch'`

**Solution:** Install dependencies:
```bash
cd edge-inference
pip install -r requirements.txt
```

### Dashboard Benchmark Fails

**Error:** `Dashboard not accessible`

**Solution:** Start dashboard dev server:
```bash
cd dashboard
npm run dev
```

**Error:** `lighthouse: command not found`

**Solution:** Install Lighthouse:
```bash
npm install -g lighthouse @lhci/cli
# Or let script use npx automatically
```

---

## Contributing

When adding new features:

1. Run benchmarks before and after changes
2. Document performance impact in PR description
3. Update performance targets if needed
4. Add new benchmark tests for new critical paths

---

## References

- [Google Lighthouse Documentation](https://developers.google.com/web/tools/lighthouse)
- [Core Web Vitals](https://web.dev/vitals/)
- [YOLOv5 Performance](https://github.com/ultralytics/yolov5)
- [FastAPI Performance](https://fastapi.tiangolo.com/benchmarks/)
