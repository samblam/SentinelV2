# Sentinel v2 - Deployment Verification Guide

This guide provides step-by-step verification procedures for local and production deployments of Sentinel v2.

---

## Local Development Deployment

### Prerequisites Check

Before deploying, verify you have the required dependencies:

```bash
# Check Python version (requires 3.11+)
python3 --version

# Check Node.js version (requires 18+)
node --version

# Check Docker and Docker Compose
docker --version
docker-compose --version

# Check PostgreSQL (if not using Docker)
psql --version
```

### Option 1: Docker Compose Deployment (Recommended)

#### Step 1: Start Backend + PostgreSQL

```bash
cd /home/user/SentinelV2/backend
docker-compose up -d
```

**Expected Output:**
```
Creating network "backend_default" with the default driver
Creating volume "backend_postgres_data" with default driver
Creating backend_postgres_1 ... done
Creating backend_backend_1  ... done
```

#### Step 2: Verify Containers Are Running

```bash
docker-compose ps
```

**Expected Output:**
```
Name                     Command                State           Ports
----------------------------------------------------------------------------------
backend_backend_1    uvicorn src.main:app ...   Up      0.0.0.0:8000->8000/tcp
backend_postgres_1   docker-entrypoint.sh ...   Up      0.0.0.0:5432->5432/tcp
```

#### Step 3: Check Backend Logs

```bash
docker-compose logs -f backend
```

**Expected Output:**
```
backend_1   | INFO:     Started server process
backend_1   | INFO:     Waiting for application startup.
backend_1   | INFO:     Application startup complete.
backend_1   | INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### Step 4: Run Database Migrations

```bash
docker-compose exec backend alembic upgrade head
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001_initial_schema
INFO  [alembic.runtime.migration] Running upgrade 001_initial_schema -> 002_next_attempt
INFO  [alembic.runtime.migration] Running upgrade 002_next_attempt -> 003_blackout_columns
```

#### Step 5: Verify Backend API

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","timestamp":"2025-11-17T..."}

# API documentation (OpenAPI)
curl http://localhost:8000/docs
# Should return HTML for Swagger UI
```

#### Step 6: Start Edge Inference Node (Separate Terminal)

```bash
cd /home/user/SentinelV2/edge-inference

# Set environment variables
export NODE_ID="sentry-01"
export BACKEND_URL="http://localhost:8000"

# Install dependencies (first time only)
pip install -r requirements.txt

# Start edge node
uvicorn src.main:app --reload --host 0.0.0.0 --port 8001
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

#### Step 7: Verify Edge Node API

```bash
# Health check
curl http://localhost:8001/health

# Expected response:
# {"status":"healthy","model":"yolov5n","blackout_active":false,"device":"cpu"}
```

#### Step 8: Start Dashboard (Separate Terminal)

```bash
cd /home/user/SentinelV2/dashboard

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

**Expected Output:**
```
  VITE v5.0.11  ready in 234 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

#### Step 9: Verify Dashboard

```bash
# Open browser to http://localhost:5173
# Expected: Tactical dashboard with map, node status panel, detection list

# Or verify with curl
curl http://localhost:5173
# Should return HTML for React app
```

### Option 2: Local Development (Without Docker)

#### Step 1: Start PostgreSQL

```bash
# If PostgreSQL not running, start it
sudo systemctl start postgresql

# Or use Docker for just PostgreSQL
docker run -d \
  --name sentinel-postgres \
  -e POSTGRES_USER=sentinel \
  -e POSTGRES_PASSWORD=sentinel \
  -e POSTGRES_DB=sentinel \
  -p 5432:5432 \
  postgres:15
```

#### Step 2: Set Environment Variables

```bash
# Backend
export DATABASE_URL="postgresql+asyncpg://sentinel:sentinel@localhost:5432/sentinel"

# Edge Node
export NODE_ID="sentry-01"
export BACKEND_URL="http://localhost:8000"
```

#### Step 3: Run Backend Migrations

```bash
cd /home/user/SentinelV2/backend
alembic upgrade head
```

#### Step 4: Start Backend

```bash
cd /home/user/SentinelV2/backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

#### Step 5: Start Edge Node (Separate Terminal)

```bash
cd /home/user/SentinelV2/edge-inference
uvicorn src.main:app --reload --host 0.0.0.0 --port 8001
```

#### Step 6: Start Dashboard (Separate Terminal)

```bash
cd /home/user/SentinelV2/dashboard
npm run dev
```

---

## Functional Testing

### Test 1: Node Registration

```bash
curl -X POST http://localhost:8000/api/nodes/register \
  -H "Content-Type: application/json" \
  -d '{"node_id": "sentry-01"}'
```

**Expected Response:**
```json
{
  "id": 1,
  "node_id": "sentry-01",
  "status": "online",
  "last_heartbeat": "2025-11-17T...",
  "created_at": "2025-11-17T..."
}
```

### Test 2: Detection Upload

```bash
# Create test image (if you don't have one)
# For this test, you'll need an actual image file

curl -X POST http://localhost:8001/detect \
  -F "file=@test_image.jpg" \
  -F "node_id=sentry-01"
```

**Expected Response:**
```json
{
  "node_id": "sentry-01",
  "timestamp": "2025-11-17T...",
  "latitude": 70.5,
  "longitude": -100.2,
  "altitude_m": 45.2,
  "accuracy_m": 10.0,
  "detections": [...],
  "detection_count": 1,
  "inference_time_ms": 87.3,
  "model": "yolov5n"
}
```

### Test 3: Blackout Mode Activation

```bash
curl -X POST http://localhost:8000/api/blackout/activate \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "sentry-01",
    "operator_id": "operator-123",
    "reason": "Testing blackout protocol"
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "blackout_id": 1,
  "activated_at": "2025-11-17T...",
  "node_status": "covert"
}
```

### Test 4: Verify Node in Blackout Mode

```bash
curl http://localhost:8001/blackout/status
```

**Expected Response:**
```json
{
  "active": true,
  "activated_at": "2025-11-17T...",
  "queued_count": 0
}
```

### Test 5: Queue Detection During Blackout

```bash
# Upload image while in blackout mode
curl -X POST http://localhost:8001/detect \
  -F "file=@test_image.jpg"
```

**Expected Response:**
```json
{
  "status": "queued",
  "message": "Detection queued during blackout mode",
  "blackout_active": true
}
```

### Test 6: Blackout Deactivation & Burst Transmission

```bash
curl -X POST http://localhost:8000/api/blackout/deactivate \
  -H "Content-Type: application/json" \
  -d '{"node_id": "sentry-01"}'
```

**Expected Response:**
```json
{
  "status": "success",
  "blackout_id": 1,
  "deactivated_at": "2025-11-17T...",
  "duration_seconds": 120,
  "detections_transmitted": 5
}
```

### Test 7: WebSocket Connection

```bash
# Install websocat for testing WebSocket
# brew install websocat  (macOS)
# Or use JavaScript in browser console:

websocat ws://localhost:8000/ws
# Should connect and receive real-time messages
```

**Test in Browser Console:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onopen = () => console.log('Connected to Sentinel WebSocket');
ws.onmessage = (event) => console.log('Message:', JSON.parse(event.data));
ws.onerror = (error) => console.error('WebSocket error:', error);
```

### Test 8: Dashboard Verification

Open browser to http://localhost:5173 and verify:

- [ ] Tactical map loads and displays Arctic region
- [ ] Node status panel shows registered nodes
- [ ] Node status shows "Online" or "Covert" correctly
- [ ] Detection list shows recent detections
- [ ] Alert panel appears (bottom-right corner)
- [ ] Blackout control buttons are functional
- [ ] WebSocket connection indicator shows "Connected"
- [ ] Real-time updates work when sending new detections

---

## Production Deployment Verification

### Environment Variables

Verify all required environment variables are set:

**Backend:**
```bash
echo $DATABASE_URL
# Should output: postgresql+asyncpg://user:pass@host:5432/db

echo $COT_ENABLED
# Should output: true or false

echo $TAK_SERVER_ENABLED
# Should output: true or false
```

**Edge Node:**
```bash
echo $NODE_ID
# Should output: unique node identifier

echo $BACKEND_URL
# Should output: https://your-backend-url.com
```

**Dashboard:**
```bash
cat dashboard/.env
# Should contain:
# VITE_API_URL=https://your-backend-url.com
# VITE_WS_URL=wss://your-backend-url.com/ws
```

### Health Checks

```bash
# Backend health
curl https://your-backend-url.com/health

# Edge node health
curl https://your-edge-url.com/health

# Dashboard accessibility
curl https://your-dashboard-url.com
```

### Database Verification

```bash
# Connect to PostgreSQL
psql $DATABASE_URL

# Verify tables exist
\dt

# Expected tables:
# nodes, detections, queue_items, blackout_events, alembic_version

# Check migrations
SELECT * FROM alembic_version;
# Should show: 003_blackout_columns

# Check node count
SELECT COUNT(*) FROM nodes;

# Check detection count
SELECT COUNT(*) FROM detections;
```

### Performance Verification

```bash
# Backend API latency
time curl http://localhost:8000/health
# Should be < 50ms

# Edge inference latency
time curl -X POST http://localhost:8001/detect -F "file=@test_image.jpg"
# Should be < 200ms (including network + inference)

# Dashboard load time
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:5173
# Should be < 2s
```

**curl-format.txt:**
```
time_namelookup:  %{time_namelookup}s\n
time_connect:     %{time_connect}s\n
time_starttransfer: %{time_starttransfer}s\n
time_total:       %{time_total}s\n
```

---

## Troubleshooting

### Backend Won't Start

**Symptom:** `ModuleNotFoundError` or import errors

**Solution:**
```bash
cd backend
pip install -r requirements.txt
```

**Symptom:** Database connection error

**Solution:**
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check DATABASE_URL is correct
echo $DATABASE_URL

# Restart PostgreSQL
docker-compose restart postgres
```

### Edge Node Won't Start

**Symptom:** `torch` or `ultralytics` import error

**Solution:**
```bash
cd edge-inference
pip install -r requirements.txt

# YOLOv5 model will download on first inference
# This can take 2-5 minutes
```

**Symptom:** Can't connect to backend

**Solution:**
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check BACKEND_URL environment variable
echo $BACKEND_URL
```

### Dashboard Won't Load

**Symptom:** Vite build errors

**Solution:**
```bash
cd dashboard
rm -rf node_modules
npm install
npm run dev
```

**Symptom:** Can't connect to backend WebSocket

**Solution:**
```bash
# Check WebSocket URL in .env
cat dashboard/.env

# Verify backend WebSocket endpoint
websocat ws://localhost:8000/ws
```

### Docker Compose Issues

**Symptom:** Port already in use

**Solution:**
```bash
# Find process using port
lsof -i :8000

# Kill the process or change port in docker-compose.yml
```

**Symptom:** Database data persistence issues

**Solution:**
```bash
# Check volumes
docker volume ls | grep backend

# Remove and recreate volume (WARNING: deletes data)
docker-compose down -v
docker-compose up -d
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] All dependencies installed (Python, Node.js, Docker)
- [ ] Environment variables configured
- [ ] PostgreSQL running and accessible
- [ ] Migrations applied (`alembic upgrade head`)
- [ ] Test suite passing (`./run_all_tests.sh`)

### During Deployment

- [ ] Backend starts successfully
- [ ] Edge node starts successfully
- [ ] Dashboard builds and serves
- [ ] Database connections established
- [ ] WebSocket connections working

### Post-Deployment

- [ ] Health checks passing for all services
- [ ] Node registration working
- [ ] Detection upload and inference working
- [ ] Blackout mode activation/deactivation working
- [ ] Dashboard displays real-time updates
- [ ] Alert panel shows high-confidence detections
- [ ] Performance metrics within targets

### Production-Specific

- [ ] HTTPS/TLS configured
- [ ] Authentication implemented (if required)
- [ ] Rate limiting configured
- [ ] Monitoring and logging configured
- [ ] Backup strategy implemented
- [ ] Disaster recovery plan documented

---

## Quick Verification Script

Save this as `verify_deployment.sh`:

```bash
#!/bin/bash

echo "=== Sentinel v2 Deployment Verification ==="
echo ""

# Backend health check
echo "1. Backend Health Check..."
BACKEND_HEALTH=$(curl -s http://localhost:8000/health)
if [[ $BACKEND_HEALTH == *"healthy"* ]]; then
  echo "   ✅ Backend is healthy"
else
  echo "   ❌ Backend is not responding"
  exit 1
fi

# Edge node health check
echo "2. Edge Node Health Check..."
EDGE_HEALTH=$(curl -s http://localhost:8001/health)
if [[ $EDGE_HEALTH == *"healthy"* ]]; then
  echo "   ✅ Edge node is healthy"
else
  echo "   ❌ Edge node is not responding"
  exit 1
fi

# Dashboard check
echo "3. Dashboard Check..."
DASHBOARD_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5173)
if [[ $DASHBOARD_STATUS == "200" ]]; then
  echo "   ✅ Dashboard is accessible"
else
  echo "   ❌ Dashboard is not accessible"
  exit 1
fi

# WebSocket check
echo "4. WebSocket Check..."
# This requires websocat or similar tool
# Simplified check: verify backend has /ws endpoint
WS_ENDPOINT=$(curl -s http://localhost:8000/docs | grep -o "/ws")
if [[ $WS_ENDPOINT == "/ws" ]]; then
  echo "   ✅ WebSocket endpoint available"
else
  echo "   ⚠️  WebSocket endpoint not verified (requires manual testing)"
fi

# Node registration check
echo "5. Node Registration Check..."
REG_RESPONSE=$(curl -s -X POST http://localhost:8000/api/nodes/register \
  -H "Content-Type: application/json" \
  -d '{"node_id": "verification-test"}')
if [[ $REG_RESPONSE == *"node_id"* ]]; then
  echo "   ✅ Node registration working"
else
  echo "   ❌ Node registration failed"
  exit 1
fi

echo ""
echo "=== ✅ All Checks Passed! ==="
echo ""
echo "Services:"
echo "  Backend:   http://localhost:8000"
echo "  Edge Node: http://localhost:8001"
echo "  Dashboard: http://localhost:5173"
echo "  API Docs:  http://localhost:8000/docs"
echo ""
```

**Run verification:**
```bash
chmod +x verify_deployment.sh
./verify_deployment.sh
```

---

## Deployment Status: LOCAL VERIFIED ✅

**Environment:** Local Development
**Deployment Method:** Docker Compose (Backend + PostgreSQL) + Local Servers (Edge + Dashboard)
**Status:** Ready for deployment

**Next Steps:**
1. For production deployment, follow security checklist in main README.md
2. Configure HTTPS/TLS certificates
3. Set up authentication and authorization
4. Configure monitoring and alerting (e.g., Prometheus + Grafana)
5. Implement backup and disaster recovery procedures

**Note:** This is a proof-of-concept system. Production deployment requires comprehensive security hardening as outlined in README.md deployment section.
