# Sentinel v2: Complete Strategy Document
**Arctic Edge-Resilient Surveillance System**

**Author:** Samuel Barefoot  
**Date:** November 12, 2025  
**Purpose:** Defense tech job applications + DND Polar Paradigms 2045 contest  
**Timeline:** Nov 13-25 (implementation) | Jan 16, 2026 (contest deadline)  
**Implementation Method:** Claude Code agent-driven development

---

## Table of Contents

1. [Strategic Overview](#strategic-overview)
2. [The Big Picture: How Everything Fits Together](#the-big-picture)
3. [System Architecture](#system-architecture)
4. [Module Breakdown with Rationale](#module-breakdown)
5. [Test-Driven Development Structure](#test-driven-development-structure)
6. [DND Contest Alignment](#dnd-contest-alignment)
7. [Job Application Strategy](#job-application-strategy)
8. [Implementation Timeline](#implementation-timeline)
9. [Technical Specifications Summary](#technical-specifications-summary)
10. [Success Criteria](#success-criteria)

---

## Strategic Overview

### The Three-Part Strategy

```
                    ┌─────────────────────────────┐
                    │   SENTINEL v2 DEMO          │
                    │   (Technical Proof)         │
                    └──────────┬──────────────────┘
                               │
                ┏━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━┓
                ▼                              ▼
    ┌───────────────────────┐      ┌──────────────────────┐
    │  DND CONTEST ESSAY    │      │  JOB APPLICATIONS    │
    │  (Strategic Vision)   │      │  (Career Outcome)    │
    └───────────────────────┘      └──────────────────────┘
           January 2026              November-December 2025
```

**Core Insight:** Build one system that serves three purposes simultaneously.

### What Makes This Work

1. **Sentinel v2** = Technical credibility (proves you can build)
2. **DND Essay** = Strategic thinking (proves you understand operations)
3. **Job Applications** = Career execution (proves you're serious about defense tech)

**Key Principle:** Each artifact reinforces the others. You're not just applying for jobs - you're demonstrating sustained interest in Arctic defense technology through multiple complementary efforts.

---

## The Big Picture: How Everything Fits Together

### The Narrative Arc

**Phase 1: Technical Foundation (Nov 13-18)**
- Build working Sentinel v2 demo
- Deploy publicly with clean documentation
- Burn Claude Code credits before Nov 18 expiration

**Phase 2: Strategic Articulation (Nov 19-25)**
- Write DND contest essay using Sentinel as technical reference
- Position: "I built this to explore edge computing for Arctic ops"
- Integrate "Blackout Protocol" concept as deceptive architecture

**Phase 3: Career Execution (Nov 25-Dec 31)**
- Reach out to Dominion founders with demo + essay
- Frame as: "Built this independently, submitting to DND contest, thought you'd find it relevant"
- Let them discover you're a perfect hire organically
- Standard applications as backup plan

### Why This Order Matters

**Demo First:**
- "Here's what I built" > "Here's what I could build"
- Live system = credible technical capability
- Working code = serious engineer, not just idea person

**Essay Second:**
- Uses Sentinel as proof-of-concept
- Demonstrates strategic thinking beyond implementation
- Shows you understand operational context, not just code

**Outreach Third:**
- You have receipts (working demo + contest submission)
- Natural conversation starter (not cold application)
- High-signal approach (shows initiative + domain interest)

---

## System Architecture

### Conceptual Model

Sentinel v2 is an **edge-first, network-resilient surveillance system** designed for Arctic/SATCOM-constrained operational environments.

**Core Design Principles:**

1. **Edge-First Processing** - Compute at the sensor, transmit insights (not raw data)
2. **Network Resilience** - Operate through intermittent connectivity
3. **Tactical Deception** - Appear offline while continuing covert operations
4. **Operator Focus** - Built for military command & control workflows
5. **Standards Compliance** - Integrates with existing tactical systems (ATAK/TAK)

### System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        ARCTIC ENVIRONMENT                        │
│  (SATCOM-Constrained, Intermittent Connectivity, -40°C to +20°C)│
└──────────────────────────┬──────────────────────────────────────┘
                           │
           ┌───────────────┴───────────────┐
           │                               │
    ┌──────▼─────────┐            ┌───────▼────────┐
    │  EDGE NODE 1   │            │  EDGE NODE 2   │
    │  (sentry-01)   │            │  (aerostat-01) │
    └──────┬─────────┘            └───────┬────────┘
           │                               │
           │  Detections (JSON, ~1KB)     │
           │  CoT XML Messages            │
           │                               │
           └───────────────┬───────────────┘
                           │
                ┌──────────▼──────────────┐
                │   BACKEND API           │
                │   (FastAPI + Postgres)  │
                │                         │
                │   - Telemetry Ingestion │
                │   - Queue Management    │
                │   - CoT Generation      │
                │   - Blackout Mode       │
                └──────────┬──────────────┘
                           │
                           │  WebSocket
                           │
                ┌──────────▼──────────────┐
                │  OPERATOR DASHBOARD     │
                │  (React + TypeScript)   │
                │                         │
                │   - Tactical Map        │
                │   - Real-time Updates   │
                │   - Node Status         │
                │   - Blackout Control    │
                └─────────────────────────┘
```

### Information Flow

**Normal Operations:**
1. Edge node captures image
2. YOLOv5-nano runs inference locally (87ms)
3. Detection result (~1KB JSON) transmitted to backend
4. Backend stores in PostgreSQL, generates CoT XML
5. Dashboard receives WebSocket update
6. Operator sees detection on tactical map in <1s

**Blackout Mode (Deceptive Operations):**
1. Operator activates "Blackout Mode" for specific nodes
2. Edge nodes stop external transmissions
3. Continue local inference and data collection
4. Queue results in local storage
5. Appear "offline" to adversary (no RF emissions)
6. When operator deactivates blackout:
   - All queued data transmits in burst
   - Adversary realizes they were monitored the entire time

**Key Innovation:** System appears failed while actually operating covertly.

---

## Module Breakdown with Rationale

### Module 1: Edge Inference Engine

**Purpose:** Local object detection optimized for bandwidth-constrained environments

**Technology:**
- Python 3.11
- YOLOv5-nano (7.5MB model, ~87ms inference on CPU)
- FastAPI (async REST endpoints)
- Docker containerization

**Why This Exists:**
- **Bandwidth Optimization:** 500x reduction (send 1KB detection vs 500KB image)
- **Sovereignty:** No cloud dependency, all processing local
- **Real-time:** <100ms latency enables immediate tactical response
- **Resilience:** Continues working when central systems unavailable

**What It Proves:**
- Edge ML is viable for Arctic deployment
- Constrained compute sufficient for surveillance
- Bandwidth limitations overcome through local processing

**Key Files:**
```
edge-inference/
├── src/
│   ├── inference.py      # YOLOv5-nano inference logic
│   ├── api.py            # FastAPI endpoints
│   ├── telemetry.py      # GPS mock + metadata generation
│   └── config.py         # Configuration management
├── tests/
│   ├── test_inference.py # Unit tests for ML pipeline
│   └── test_api.py       # Integration tests for endpoints
├── Dockerfile
└── requirements.txt
```

**API Endpoints:**
- `POST /detect` - Object detection on uploaded image
- `GET /health` - System health check
- `GET /status` - Node operational status
- `POST /blackout` - Enable/disable blackout mode

**Test Coverage:**
- Unit: Inference logic, telemetry generation, config loading
- Integration: API endpoints, file upload handling
- E2E: Complete detection flow with mock images

---

### Module 2: Resilient Backend API

**Purpose:** Network-resilient ingestion, storage, and coordination layer

**Technology:**
- Python 3.11 + FastAPI
- PostgreSQL 15 (persistent storage)
- WebSocket support (real-time push)
- Redis (optional, for caching)

**Why This Exists:**
- **Data Persistence:** Survive node failures, connectivity loss
- **Coordination:** Multiple edge nodes → single operational picture
- **Queue Management:** Handle intermittent connectivity gracefully
- **Audit Trail:** Complete detection history for after-action review

**What It Proves:**
- System remains operational during SATCOM outages
- Data integrity maintained across network failures
- Operator never loses situational awareness

**Key Files:**
```
backend/
├── src/
│   ├── api.py            # Main FastAPI application
│   ├── models.py         # SQLAlchemy database models
│   ├── queue.py          # Queue management logic
│   ├── websocket.py      # Real-time push to dashboard
│   └── blackout.py       # Blackout mode coordination
├── tests/
│   ├── test_queue.py     # Queue resilience tests
│   ├── test_models.py    # Database model tests
│   └── test_websocket.py # WebSocket functionality tests
├── alembic/              # Database migrations
└── docker-compose.yml    # Multi-service orchestration
```

**Database Schema:**
```sql
-- Core tables
detections       # Detection records with full metadata
nodes            # Edge node registry
queue_items      # Pending transmissions during blackout
blackout_events  # Blackout activation/deactivation log
```

**API Endpoints:**
- `POST /api/detections` - Ingest detection from edge node
- `GET /api/detections` - Query detection history
- `POST /api/nodes/register` - Register new edge node
- `GET /api/nodes/{id}/status` - Node health status
- `POST /api/blackout/activate` - Activate blackout for node
- `POST /api/blackout/deactivate` - Deactivate blackout
- `WS /ws` - WebSocket connection for real-time updates

**Test Coverage:**
- Unit: Queue logic, database models, blackout coordination
- Integration: API endpoints, database operations
- Resilience: Network failure simulation, data integrity verification

---

### Module 3: ATAK Integration (CoT XML)

**Purpose:** Tactical data link compatibility with military C2 systems

**Technology:**
- Python 3.11
- XML generation (CoT schema)
- ATAK/TAK protocol understanding

**Why This Exists:**
- **Interoperability:** Defense systems use ATAK/TAK extensively
- **Credibility:** Shows understanding of military workflows
- **Standards:** Demonstrates professional military software practices
- **Dominion Fit:** ATAK mentioned explicitly in Full Stack job posting

**What It Proves:**
- You understand tactical C2 systems
- You can integrate with existing military infrastructure
- You think beyond consumer tech patterns

**CoT XML Schema Example:**
```xml
<?xml version="1.0"?>
<event version="2.0" uid="detection-123" type="a-f-G-E-S" time="2045-07-15T14:23:45Z">
  <point lat="70.5234" lon="-100.8765" hae="45.2" ce="10.0" le="5.0"/>
  <detail>
    <contact callsign="sentry-01"/>
    <track speed="0.0" course="0.0"/>
    <remarks>YOLOv5 detection: person (confidence: 0.89)</remarks>
    <detection>
      <class>person</class>
      <confidence>0.89</confidence>
      <bbox xmin="100" ymin="150" xmax="300" ymax="400"/>
    </detection>
  </detail>
</event>
```

**Key Files:**
```
atak-integration/
├── src/
│   ├── cot_generator.py  # CoT XML generation
│   ├── schemas.py        # CoT schema definitions
│   └── validator.py      # CoT message validation
├── tests/
│   ├── test_cot.py       # CoT generation tests
│   └── test_validator.py # Schema validation tests
└── examples/
    └── sample_cot.xml    # Example CoT messages
```

**Functions:**
- `generate_cot_from_detection()` - Convert detection JSON to CoT XML
- `validate_cot_message()` - Ensure CoT schema compliance
- `send_cot_to_tak_server()` - Transmit to ATAK/TAK server (if available)

**Test Coverage:**
- Unit: CoT generation, schema validation
- Integration: Detection → CoT conversion pipeline
- Validation: CoT messages parse correctly in ATAK (if possible)

---

### Module 4: Operator Dashboard

**Purpose:** Tactical command & control interface for military operators

**Technology:**
- React 18 + TypeScript
- Vite (build tool)
- Tailwind CSS (tactical dark theme)
- Leaflet (map rendering)
- WebSocket client (real-time updates)

**Why This Exists:**
- **Operator Focus:** Built for military decision-makers, not consumers
- **Situational Awareness:** Real-time tactical picture
- **Blackout Control:** Interface to activate deceptive operations
- **Professional UI:** Demonstrates full-stack capability

**What It Proves:**
- You can build professional operator interfaces
- You understand tactical workflows
- You're full-stack capable (not just backend)

**Key Files:**
```
dashboard/
├── src/
│   ├── components/
│   │   ├── TacticalMap.tsx       # Leaflet map with detections
│   │   ├── NodeStatus.tsx        # Edge node health indicators
│   │   ├── DetectionList.tsx     # Sortable detection log
│   │   ├── BlackoutControl.tsx   # Blackout activation UI
│   │   └── AlertPanel.tsx        # High-confidence detection alerts
│   ├── hooks/
│   │   ├── useWebSocket.ts       # WebSocket connection management
│   │   └── useDetections.ts      # Detection state management
│   ├── lib/
│   │   ├── api.ts                # Backend API client
│   │   └── types.ts              # TypeScript type definitions
│   └── App.tsx                   # Main application
├── tests/
│   ├── TacticalMap.test.tsx
│   └── useWebSocket.test.ts
└── tailwind.config.js            # Dark tactical theme
```

**UI Components:**

1. **Tactical Map (Primary View)**
   - Leaflet map centered on Arctic
   - Detection markers (color-coded by confidence)
   - Node location indicators
   - Real-time updates

2. **Node Status Panel**
   - Online/Offline/Blackout status
   - Last heartbeat timestamp
   - Detection count
   - Blackout activation controls

3. **Detection List**
   - Sortable table (time, confidence, class, node)
   - Filter by object type, confidence threshold, time range
   - Click to highlight on map

4. **Blackout Control**
   - Per-node blackout activation
   - Duration timer
   - Queued detection count
   - "Resume Transmission" button

5. **Alert Panel**
   - High-confidence detections (>0.85)
   - Acoustic alert option
   - Acknowledge/dismiss interface

**Design Aesthetic:**
- Dark theme (low-light operational environment)
- High contrast (readability in field conditions)
- Minimal distractions (tactical focus)
- Military color palette (blues, grays, red for alerts)

**Test Coverage:**
- Unit: Component rendering, state management
- Integration: WebSocket updates, API calls
- E2E: Complete operator workflows (Cypress/Playwright)

---

### Module 5: Blackout Mode (Deceptive Edge Architecture)

**Purpose:** Covert operations through apparent system failure

**Technology:**
- Coordination layer across all modules
- State management in backend
- Queue persistence in edge nodes
- UI controls in dashboard

**Why This Exists:**
- **Strategic Innovation:** Your unique contribution
- **Operational Deception:** Adversary thinks sensors offline
- **DND Essay Core:** Technical implementation of "Blackout Protocol"
- **Differentiator:** Nobody else has this in their demo

**What It Proves:**
- You think about operational art, not just engineering
- You understand deception as a tactical capability
- You innovate beyond standard surveillance patterns

**How It Works:**

**Activation Sequence:**
1. Operator identifies tactical need for deception
2. Dashboard: Select node(s), click "Activate Blackout"
3. Backend: Update node status to `BLACKOUT_ACTIVE`
4. WebSocket: Push blackout command to edge node(s)
5. Edge Node: 
   - Stop external transmissions
   - Continue inference locally
   - Queue all detections in local SQLite
   - Stop heartbeat pings (appear offline)
6. Dashboard: Display node as "COVERT" (operator knows) vs "OFFLINE" (adversary sees)

**Deactivation Sequence:**
1. Operator determines tactical moment for intelligence revelation
2. Dashboard: Click "Resume Transmission" for node(s)
3. Backend: Update node status to `BLACKOUT_RESUMING`
4. WebSocket: Push resume command to edge node(s)
5. Edge Node:
   - Transmit all queued detections in burst
   - Resume normal heartbeat
   - Return to standard operation
6. Backend: Ingest burst of historical detections with original timestamps
7. Dashboard: Display "replay" of all missed detections

**Adversary Perspective:**
- Detects edge node RF signature (sensor is online)
- Launches EW attack or physical disruption attempt
- RF signature disappears (success!)
- ... time passes ...
- Discovers 48 hours of surveillance data was collected
- Realizes deception: node was always operational

**Operator Perspective:**
- Full awareness of node status (covert vs. offline vs. online)
- Control over intelligence revelation timing
- Complete detection history maintained
- Strategic deception capability available

**Key Files:**
```
# Backend blackout coordination
backend/src/blackout.py

# Edge node blackout logic
edge-inference/src/blackout.py

# Dashboard controls
dashboard/src/components/BlackoutControl.tsx

# Database schema
CREATE TABLE blackout_events (
  id SERIAL PRIMARY KEY,
  node_id INTEGER REFERENCES nodes(id),
  activated_at TIMESTAMP,
  deactivated_at TIMESTAMP,
  activated_by TEXT,  -- operator ID
  reason TEXT,        -- tactical justification
  detections_queued INTEGER
);
```

**Test Coverage:**
- Unit: Blackout state transitions, queue management
- Integration: Multi-node coordination, burst transmission
- Simulation: Network failure vs. intentional blackout differentiation

---

## Test-Driven Development Structure

### Testing Philosophy

**Why TDD for Sentinel v2:**

1. **Claude Code works better with tests** - Clear success criteria for agent
2. **Defense applications require reliability** - No room for bugs in tactical systems
3. **Portfolio demonstration** - Shows professional engineering practices
4. **Burn credits efficiently** - Test generation uses Claude Code credits productively

**Test Pyramid:**

```
           ┌─────────────┐
           │     E2E     │  <- Few (5-10 tests)
           │   Tests     │
           └─────────────┘
         ┌─────────────────┐
         │   Integration   │  <- Some (20-30 tests)
         │     Tests       │
         └─────────────────┘
      ┌──────────────────────┐
      │     Unit Tests       │  <- Many (50-100 tests)
      │                      │
      └──────────────────────┘
```

### Testing Approach Per Module

#### Module 1: Edge Inference Engine

**Unit Tests (Python + pytest):**
```python
# tests/test_inference.py
def test_yolo_model_loads()
def test_inference_under_100ms()
def test_inference_returns_correct_schema()
def test_confidence_threshold_filtering()
def test_mock_gps_generation()
def test_node_id_generation()
def test_telemetry_metadata()

# tests/test_api.py
def test_detect_endpoint_accepts_image()
def test_detect_endpoint_rejects_invalid_file()
def test_detect_endpoint_returns_json()
def test_health_endpoint()
def test_status_endpoint()
```

**Integration Tests:**
```python
# tests/integration/test_full_detection_flow.py
def test_upload_image_returns_detections()
def test_detection_includes_telemetry()
def test_api_performance_under_load()
```

**Coverage Target:** 80% for core inference logic, 60% overall

---

#### Module 2: Backend API

**Unit Tests (Python + pytest):**
```python
# tests/test_models.py
def test_detection_model_creation()
def test_node_registration()
def test_queue_item_persistence()
def test_blackout_event_logging()

# tests/test_queue.py
def test_queue_enqueue()
def test_queue_dequeue_fifo()
def test_queue_persistence_on_restart()
def test_queue_retry_logic()

# tests/test_blackout.py
def test_blackout_activation()
def test_blackout_deactivation()
def test_queued_detection_burst_transmission()
```

**Integration Tests:**
```python
# tests/integration/test_api_endpoints.py
def test_detection_ingestion()
def test_detection_query_filtering()
def test_node_registration_flow()
def test_websocket_connection()
def test_websocket_message_push()

# tests/integration/test_resilience.py
def test_database_connection_recovery()
def test_queue_survives_restart()
def test_websocket_reconnection()
```

**Resilience Tests:**
```python
# tests/resilience/test_network_failure.py
def test_detection_queued_when_db_unavailable()
def test_automatic_retry_on_connection_restore()
def test_no_data_loss_during_outage()
def test_burst_transmission_after_blackout()
```

**Coverage Target:** 75% overall, 90% for critical queue logic

---

#### Module 3: ATAK Integration

**Unit Tests (Python + pytest):**
```python
# tests/test_cot_generator.py
def test_cot_xml_generation()
def test_cot_schema_compliance()
def test_detection_to_cot_conversion()
def test_cot_timestamp_format()
def test_cot_coordinate_conversion()

# tests/test_validator.py
def test_valid_cot_passes_validation()
def test_invalid_cot_fails_validation()
def test_cot_uid_uniqueness()
```

**Integration Tests:**
```python
# tests/integration/test_cot_pipeline.py
def test_detection_generates_valid_cot()
def test_cot_includes_all_metadata()
def test_cot_transmission_to_tak_server()  # if TAK server available
```

**Coverage Target:** 85% (XML generation is critical)

---

#### Module 4: Dashboard

**Unit Tests (TypeScript + Vitest/Jest):**
```typescript
// tests/TacticalMap.test.tsx
test('map renders with correct center')
test('detection markers appear on map')
test('marker click shows detection details')
test('map updates on new detection')

// tests/NodeStatus.test.tsx
test('node status displays correctly')
test('blackout button appears for online nodes')
test('offline nodes show last heartbeat')

// tests/useWebSocket.test.ts
test('websocket connects on mount')
test('websocket reconnects on disconnect')
test('websocket processes detection messages')
```

**Integration Tests:**
```typescript
// tests/integration/App.test.tsx
test('full detection flow from ws to map')
test('blackout activation workflow')
test('detection filtering and sorting')
```

**E2E Tests (Cypress/Playwright):**
```typescript
// e2e/operator_workflow.spec.ts
test('operator activates blackout for node')
test('operator views queued detections')
test('operator deactivates blackout and sees burst')
test('operator filters detections by time range')
```

**Coverage Target:** 70% (focus on critical workflows)

---

#### Module 5: Blackout Mode

**Integration Tests (Python + pytest):**
```python
# tests/integration/test_blackout_coordination.py
def test_blackout_activation_across_all_components()
def test_edge_node_stops_transmission_during_blackout()
def test_backend_tracks_blackout_state()
def test_dashboard_displays_covert_status()
def test_burst_transmission_on_deactivation()
def test_detection_timestamps_preserved_during_blackout()
```

**E2E Tests:**
```python
# tests/e2e/test_blackout_scenario.py
def test_full_blackout_deception_workflow():
    """
    Scenario: Operator activates blackout, edge node queues detections,
    operator deactivates, all detections appear with original timestamps
    """
    # 1. Activate blackout via dashboard
    # 2. Edge node receives blackout command
    # 3. Edge node queues 10 detections locally
    # 4. Backend shows node as "covert"
    # 5. Deactivate blackout via dashboard
    # 6. Edge node transmits all 10 detections
    # 7. Dashboard displays all 10 with original timestamps
    # 8. Assert: No detections lost, all timestamps correct
```

**Coverage Target:** 80% (blackout is your differentiator)

---

### Test Execution Strategy

**During Development (Nov 13-17):**
- Claude Code generates tests alongside implementation
- Run tests after each module completion
- Fix failing tests before moving to next module

**Pre-Deployment (Nov 18):**
- Full test suite execution
- Coverage report generation
- Fix critical failures, document known issues for non-critical

**Post-Deployment (Nov 19+):**
- Smoke tests on deployed system
- Performance validation
- Integration verification

---

### Test Infrastructure

**Python Testing:**
```bash
# pytest configuration
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --cov=src
    --cov-report=html
    --cov-report=term
    --verbose
```

**TypeScript Testing:**
```json
// vitest.config.ts
export default {
  test: {
    globals: true,
    environment: 'jsdom',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      exclude: ['node_modules/', 'tests/']
    }
  }
}
```

**CI/CD (GitHub Actions - Optional):**
```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Python tests
        run: |
          pip install -r requirements.txt
          pytest
      - name: Run TypeScript tests
        run: |
          npm install
          npm test
```

---

## DND Contest Alignment

### How Sentinel v2 Supports Your Essay

**DND Contest Focus:** Arctic logistics sustainment with emerging technologies (2045 timeframe)

**Your Essay Angle:** Logistics officer using edge computing for covert surveillance to support sustainment operations

**Sentinel v2 Role:** Technical proof-of-concept demonstrating feasibility

### Mapping System Features to Essay Themes

| Sentinel v2 Feature | Essay Theme | How They Connect |
|---------------------|-------------|------------------|
| Edge Inference | Bandwidth Optimization | "We can't send 500KB images over SATCOM, so we process at the edge and send 1KB insights" |
| Resilient Queue | SATCOM Denial Operations | "When adversary jams communications, we queue locally and continue operations" |
| Blackout Mode | Deceptive Architecture | "Our sensors appear offline to adversary while continuing covert surveillance" |
| ATAK Integration | Tactical C2 Integration | "Intelligence immediately available to commanders in standard tactical displays" |
| PostgreSQL Storage | Audit Trail & After-Action | "Complete detection history for logistics planning and threat assessment" |

### Essay Structure Aligned with Technical Implementation

**Act 1: Setup (Pages 1-5)**
- Logistics officer arrives in Arctic
- Discovers inadequate surveillance coverage for supply routes
- Enemy probing defenses, testing response times
- **Technical Reference:** "We deployed edge computing sensors along supply corridors"

**Act 2: Complication (Pages 6-10)**
- Enemy launches EW attack on sensor network
- Sensors appear to go offline (RF signatures disappear)
- Logistics officer realizes this is an opportunity
- **Technical Reference:** "We activated blackout protocol - sensors continued operating covertly"

**Act 3: Resolution (Pages 11-15)**
- Enemy moves freely, believing surveillance is down
- Actually mapping enemy logistics and movement patterns
- 72 hours of covert intelligence collected
- **Technical Reference:** "Edge inference continued, all detections queued locally with GPS timestamps"

**Act 4: Climax (Pages 16-20)**
- Logistics officer chooses tactical moment to reveal intel
- Dumps 72 hours of surveillance data to command
- Enemy realizes deception: they were watched the entire time
- **Technical Reference:** "Burst transmission over restored SATCOM - complete enemy logistics picture"

**Epilogue (Page 21+)**
- Reflection on deceptive architecture as operational capability
- Edge computing as strategic asset, not just technical solution
- Human decision-making remains central (officer chose when to reveal intel)

### Key Essay Quotes Supported by Sentinel

**On Bandwidth Constraints:**
> "Traditional surveillance would require 500 kilobytes per image transmitted over SATCOM - impossible with our 1Mbps connection shared across the entire task force. Edge inference reduced this to 1 kilobyte per detection, enabling real-time situational awareness despite bandwidth scarcity."

**On Network Resilience:**
> "When the enemy jammed our communications, traditional systems would have been blind. Our edge architecture continued operating autonomously, queuing intelligence locally until connectivity restored."

**On Deceptive Architecture:**
> "We designed our sensors to fail gracefully - or so it appeared. The adversary's EW attack successfully suppressed RF emissions, convincing them we were blind. In reality, edge inference continued silently, accumulating a detailed intelligence picture we could reveal at the moment of maximum operational advantage."

**On Human-Machine Teaming:**
> "The system didn't decide when to reveal our intelligence - I did. Edge computing provided the technical capability, but operational art remained fundamentally human. We watched the enemy for 72 hours, waiting for the precise moment when revelation would shatter their confidence and enable our logistics operations."

### Evaluation Criteria Mapping

**Operational Insight and Strategic Impact (25 points):**
- ✅ Clearly defines challenge: SATCOM bandwidth + EW threats
- ✅ Innovative solution: Deceptive edge architecture
- ✅ Provocative thinking: Sensors designed to appear vulnerable
- ✅ Feasible: Sentinel proves technical viability

**Scientific Credibility (25 points):**
- ✅ Emerging tech: Edge computing, AI inference
- ✅ R&D sources: YOLOv5, ATAK/CoT protocols, Arctic research
- ✅ Sentinel v2 = proof-of-concept

**Clarity and Research Integration (10 points):**
- ✅ Well-organized narrative
- ✅ Integrates Arctic ops research
- ✅ Technical details grounded in reality (Sentinel implementation)

**Compliance and Ethical Framing (10 points):**
- ✅ Human-centric: Operator controls deception
- ✅ Ethical: Deception is defensive, not offensive
- ✅ Indigenous: Sensors respect sovereignty, enable defense

**Creativity and Vision (15 points):**
- ✅ Novel concept: Architecture as deception mechanism
- ✅ Reimagines surveillance: Not just detection, but strategic timing

**Writing Quality (15 points):**
- ✅ Compelling narrative: Adversary thinks they won, discovers deception
- ✅ Emotional arc: Logistics officer's strategic decision-making
- ✅ Lasting impression: Edge computing as operational art

**Expected Score: 85-95/100 (well above 70-point threshold)**

---

## Job Application Strategy

### The Personal Outreach Approach

**Why This Works Better Than Standard Applications:**

1. **Signal vs. Noise:** Dominion likely received 100+ applications for each posting
2. **Demonstration:** You have working code + strategic thinking (essay)
3. **Authentic Interest:** Not just job-seeking, genuinely exploring Arctic defense
4. **Founder-Friendly:** Startups respond to builders who ship
5. **Multiple Touchpoints:** Demo + essay + background = complete picture

### Timeline

**Week of Nov 25 (After Sentinel + Essay Complete):**

**Monday Nov 25:**
- Ensure Sentinel v2 deployed and stable
- Ensure DND essay draft complete (80-90%)
- Prepare outreach materials

**Tuesday Nov 26:**
- LinkedIn research on Dominion founders
- Identify: Co-founders, VP Engineering, VP Software
- Find personal connection points (shared interests, background)

**Wednesday Nov 27:**
- Send LinkedIn connection requests with personalized notes
- Wait for acceptance before sending pitch

**Friday Nov 29:**
- Send outreach message (assuming connection accepted)

### Outreach Message (LinkedIn DM)

**Subject:** Arctic edge computing demo + DND contest submission

**Body:**
```
Hi [Name],

I've been following Dominion's work on Arctic sovereignty - the JADC2aaS vision really resonates with me.

I recently built "Sentinel" - an edge-resilient surveillance system designed for SATCOM-constrained Arctic operations. It's a working demo exploring how edge computing enables covert surveillance through apparent system failure (sensors appear offline while continuing operations).

I'm currently refining the concept for DND's Polar Paradigms 2045 contest, but thought you might find it interesting given Dominion's focus.

Demo: [sentinel.yourdomain.com]
Technical write-up: [essay draft link or brief summary]

Context on me: 8 years building distributed systems, government security background (Parliament, PPS), currently at Avanade leading edge compute projects. Based in Montreal but spent years in Ottawa for government work.

Happy to discuss if useful. No expectations - genuinely just sharing work I think aligns with Dominion's mission.

Cheers,
Sam

github.com/yourusername
linkedin.com/in/samuel-barefoot
```

**Why This Message Works:**
- ✅ Shows, doesn't tell (working demo)
- ✅ Demonstrates sustained interest (DND contest)
- ✅ Establishes credibility (government background)
- ✅ No pressure (genuine sharing, not "please hire me")
- ✅ Location transparency (Montreal + Ottawa history)
- ✅ Makes it easy to respond (clear links, context)

### Follow-Up Strategy

**If They Respond Positively:**
- Offer technical deep-dive call
- Share additional context on implementation decisions
- Ask about Dominion's technical challenges
- **Still don't explicitly ask for job** - let them make the move

**If They Mention "Are You Looking?":**
- "Yes, actively exploring senior roles in Canadian defense tech"
- "Montreal-based, but highly flexible for Ottawa/Toronto presence + Arctic field deployments"
- "Drawn to Dominion's mission + technical challenges + founding team stage"

**If No Response After 1 Week:**
- Follow-up: "Happy to do a brief technical walkthrough if helpful - built some interesting network resilience patterns"
- If still no response after another week: Standard application as backup

### Backup Plan: Standard Applications

**If Personal Outreach Fails:**

**Week of Dec 9 (Two weeks after outreach):**
- Apply through Ashby to **Full Stack** and **Network** roles
- Use demo + essay as application materials
- Cover letter emphasizes:
  - Working demo (not just talk)
  - DND contest submission (sustained interest)
  - Montreal + Ottawa flexibility
  - Field deployment readiness

**Resume Updates:**
- Add "Sentinel - Arctic Edge Surveillance System" to projects
- Add "DND Polar Paradigms 2045 Contest Submission" to achievements
- Emphasize government security background
- Highlight distributed systems + edge computing experience

### Other Defense Tech Applications

**Also Apply To (Dec 1-15):**

1. **Tactiql (Ottawa, Remote)** - Senior Engineer
   - Why: Remote-first, perfect fit, NATO-backed
   - Strategy: Same personal outreach approach

2. **General Dynamics Mission Systems (Montreal)** - Senior C4ISR Engineer
   - Why: Montreal-based, stable, large projects
   - Strategy: Standard application, mention local presence

3. **Rheinmetall Canada (Montreal/Ottawa)** - Senior Systems Engineer
   - Why: Defense contractor, Quebec presence
   - Strategy: Standard application, emphasize government experience

4. **Palantir (if hiring in Canada)** - Forward Deployed Engineer (Senior)
   - Why: Top-tier comp, defense focus
   - Strategy: Aggressive application, Sentinel as portfolio

**Total Applications Target: 6-10 by end of December**

### What Success Looks Like

**Ideal Outcome (70% probability):**
- Personal outreach → conversation → interview → offer from Dominion or Tactiql
- Timeline: Offer by mid-January, start February

**Good Outcome (20% probability):**
- Standard application → interview → offer from GD or Rheinmetall
- Timeline: Offer by late January, start March

**Acceptable Outcome (10% probability):**
- Multiple interviews, no offers by February
- Continue building Sentinel, apply to US remote roles
- Reapply to Canadian companies in March with enhanced demo

---

## Implementation Timeline

### Week 1: Nov 13-18 (Claude Code Implementation)

**Nov 13 (Wednesday) - Claude Code Setup**
- Morning: Create specifications documents (you + me)
- Afternoon: First Claude Code session (Module 1 setup)
- Evening: Module 1 core inference logic

**Nov 14 (Thursday) - Module 1 + 2 Start**
- **You're busy with family - Claude Code works autonomously**
- Claude Code: Complete Module 1 implementation
- Claude Code: Start Module 2 backend API
- You: Minimal supervision, review PRs when available

**Nov 15 (Friday) - Module 2 + 3**
- Morning: Review Claude Code output from Nov 13-14
- Afternoon: Claude Code continues Module 2
- Evening: Module 3 ATAK integration

**Nov 16 (Saturday) - Module 4 Start**
- Morning: Claude Code starts React dashboard
- Afternoon: Integration testing between modules
- Evening: Fix critical bugs from integration

**Nov 17 (Sunday) - Module 5 + Integration**
- Morning: Claude Code implements Blackout Mode
- Afternoon: Full system integration
- Evening: End-to-end testing, fix issues

**Nov 18 (Monday) - Deployment + Polish**
- Morning: Deploy to Railway/Fly.io
- Afternoon: Smoke tests on deployed system
- Evening: Final README polish, burn remaining credits
- **Credits expire tonight - ensure all used**

### Week 2: Nov 19-25 (Essay + Outreach)

**Nov 19-20 (Tue-Wed) - Essay First Draft**
- Read Sentinel codebase to refresh on implementation details
- Write 3000-word first draft following structure above
- Focus on narrative, less on technical perfection

**Nov 21-22 (Thu-Fri) - Essay Refinement**
- Add technical details and citations
- Ensure alignment with DND evaluation criteria
- Proofread for clarity and flow
- Aim for 4500 words

**Nov 23-24 (Sat-Sun) - Essay Final Polish**
- Complete to 5000 words
- Add references section (max 1000 words)
- Final proofreading
- Ask friend to review (optional)

**Nov 25 (Monday) - Outreach Preparation**
- Finalize Sentinel documentation
- Prepare demo video (2-minute walkthrough)
- Research Dominion founders
- Draft LinkedIn messages

**Nov 26-29 (Tue-Fri) - Execute Outreach**
- Send connection requests (Tue)
- Wait for acceptance (Wed-Thu)
- Send outreach message (Fri)

### Week 3-4: Dec 1-15 (Application Phase)

**Dec 1-7 - Wait for Dominion Response**
- If response: Engage in technical discussions
- If no response: Prepare standard applications
- Continue refining essay based on feedback

**Dec 8-15 - Backup Applications**
- If Dominion interested: Focus on that process
- If no Dominion response: Apply to 4-6 other companies
- Submit standard applications with Sentinel as portfolio

### Week 5+: Dec 16 - Jan 16 (Interview + Essay Submission)

**December - Interview Season**
- Expect 2-4 weeks for interview responses
- Technical screens likely in mid-December
- Final rounds in early January

**January 1-16 - Essay Final Submission**
- Polish essay one final time
- Ensure all references formatted correctly (Chicago style)
- Submit to DND contest before Jan 16 deadline

**Expected Outcome Timeline:**
- **Early January:** Job offers
- **Mid-January:** DND essay submitted
- **Late January:** Accept job offer, give notice
- **February:** Start new job
- **Spring 2026:** DND contest results (if you win, great PR for new employer)

---

## Technical Specifications Summary

### Technology Stack

**Edge Inference:**
- Python 3.11
- PyTorch 2.0+
- YOLOv5 (Ultralytics)
- FastAPI 0.104+
- Uvicorn (ASGI server)
- Pillow (image processing)
- Docker

**Backend API:**
- Python 3.11
- FastAPI 0.104+
- PostgreSQL 15
- SQLAlchemy 2.0 (ORM)
- Alembic (migrations)
- WebSocket support
- Docker Compose

**ATAK Integration:**
- Python 3.11
- XML generation (lxml)
- CoT schema validation

**Dashboard:**
- React 18
- TypeScript 5
- Vite 5 (build tool)
- Tailwind CSS 3
- Leaflet (maps)
- shadcn/ui components
- WebSocket client
- Zustand (state management)

**Deployment:**
- Railway (recommended) or Fly.io
- Docker + Docker Compose
- PostgreSQL managed instance
- Vercel for dashboard (optional separate deployment)

### Performance Targets

| Metric | Target | How We'll Achieve It |
|--------|--------|---------------------|
| Inference Time | <100ms | YOLOv5-nano on CPU, optimized preprocessing |
| API Latency | <50ms | FastAPI async, database indexing |
| Dashboard Load | <2s | Code splitting, lazy loading, CDN |
| WebSocket Latency | <100ms | Direct connection, minimal serialization |
| Model Size | <10MB | YOLOv5-nano (7.5MB compressed) |
| Detection Accuracy | >75% mAP | YOLOv5-nano standard performance |
| System Uptime | >99% | Health checks, automatic restart |
| Data Loss Rate | 0% | Persistent queue, database transactions |

### Security Considerations

**Not Implementing (Demo System):**
- Authentication/authorization
- Encryption in transit (HTTPS)
- Encryption at rest
- Rate limiting
- Input sanitization (basic only)

**Future Production Requirements:**
- mTLS for node authentication
- OAuth2 for operator authentication
- AES-256 encryption at rest
- Network segmentation
- Audit logging
- Role-based access control

**Demo Disclaimer in README:**
> "This is a proof-of-concept demonstration system. Production deployment would require comprehensive security hardening including authentication, encryption, network segmentation, and compliance with defense security standards."

### Scalability Considerations

**Current Demo (Single Deployment):**
- 1-5 edge nodes
- 1 backend instance
- 1 PostgreSQL instance
- 1-10 concurrent operators

**Production Scaling Path:**
- Horizontal: Multiple backend instances (load balanced)
- Database: PostgreSQL replication (read replicas)
- Edge: 100+ nodes (distributed geographically)
- Operators: 50+ concurrent (WebSocket scaling)

**Documented but Not Implemented:**
- Kubernetes deployment manifests
- Redis caching layer
- Message queue (RabbitMQ/Kafka) for high throughput
- CDN for dashboard assets

---

## Success Criteria

### Technical Success

**Minimum Viable Demo:**
- ✅ Edge inference works (detects objects in <100ms)
- ✅ Backend API accepts detections
- ✅ Dashboard displays detections on map
- ✅ System deployed and publicly accessible
- ✅ README with quick start instructions

**Good Demo:**
- ✅ All 5 modules functional
- ✅ WebSocket real-time updates working
- ✅ Blackout mode demonstrates covertly
- ✅ ATAK CoT generation working
- ✅ Test coverage >70%
- ✅ Clean, professional documentation

**Exceptional Demo:**
- ✅ All good demo criteria +
- ✅ Video walkthrough (2-3 minutes)
- ✅ Performance benchmarks documented
- ✅ Architecture diagrams in README
- ✅ Test coverage >80%
- ✅ CI/CD pipeline (GitHub Actions)

### DND Essay Success

**Minimum Viable Essay:**
- ✅ 5000 words
- ✅ Meets all mandatory criteria
- ✅ Score >70/100
- ✅ Submitted before deadline

**Good Essay:**
- ✅ Score >80/100
- ✅ Compelling narrative with emotional arc
- ✅ Strong technical grounding (references Sentinel)
- ✅ Clear operational insight
- ✅ Original thinking on deceptive architecture

**Exceptional Essay:**
- ✅ Score >90/100
- ✅ Top 10 finalist
- ✅ Memorable story that changes how evaluators think
- ✅ Publishable quality
- ✅ Generates interest from DND

### Career Success

**Minimum Viable Outcome:**
- ✅ 1 offer at $140K+
- ✅ Defense tech company
- ✅ Technically interesting work
- ✅ Better than current role

**Good Outcome:**
- ✅ 2-3 offers
- ✅ Best offer $160K+
- ✅ Senior or Staff level
- ✅ Startup or fast-moving contractor
- ✅ Remote-friendly or Montreal-based

**Exceptional Outcome:**
- ✅ 3+ offers
- ✅ Best offer $180K+ (or significant equity)
- ✅ Dominion Dynamics or equivalent startup
- ✅ Staff/Senior level with ownership
- ✅ Mission-driven work you're excited about
- ✅ DND contest finalist = PR boost for employer

---

## Risk Mitigation

### Technical Risks

**Risk: Claude Code generates buggy/incomplete code**
- Mitigation: TDD approach with clear tests
- Mitigation: Manual review after each module
- Mitigation: Simple, well-documented patterns (not clever code)
- Backup: You can fix bugs manually if needed

**Risk: Integration between modules fails**
- Mitigation: Clear API contracts defined upfront
- Mitigation: Integration tests for each interface
- Mitigation: Modular design = isolate failures
- Backup: Can demo modules independently if integration incomplete

**Risk: Deployment issues on Nov 18**
- Mitigation: Test deployment early (Nov 16)
- Mitigation: Simple deployment (Railway = low complexity)
- Mitigation: Docker Compose = portable, testable locally
- Backup: Can demo locally via screen recording

**Risk: Credits run out before completion**
- Mitigation: Use credits efficiently (focus on implementation, not exploration)
- Mitigation: Generate tests alongside code (burns credits productively)
- Mitigation: Prioritize: Modules 1-3 essential, 4-5 nice-to-have
- Backup: You can complete remaining work manually

### Career Risks

**Risk: No response from Dominion founders**
- Mitigation: Have 5-10 backup companies identified
- Mitigation: Standard applications as fallback
- Mitigation: Outreach to multiple companies simultaneously
- Timing: Start backup applications Dec 9 (two weeks after outreach)

**Risk: All offers below $150K**
- Mitigation: Negotiate aggressively (you have alternatives)
- Mitigation: Consider equity compensation at startups
- Mitigation: Stay at current job if offers insufficient
- Reality check: $120K → $150K = 25% raise, reasonable ask

**Risk: Location inflexibility kills opportunities**
- Mitigation: Emphasize "Montreal-based, Ottawa-flexible" in all comms
- Mitigation: Reference previous Ottawa work (Parliament, PPS)
- Mitigation: Offer "weekly Ottawa presence" as compromise
- Backup: Expand search to US remote roles if Canadian market too constrained

### Essay Risks

**Risk: DND essay doesn't score >70**
- Mitigation: Follow evaluation criteria exactly
- Mitigation: Have friend proofread before submission
- Mitigation: Use Sentinel technical details for credibility
- Reality: Even if you don't win, essay still valuable for job applications

**Risk: Blackout Protocol concept too abstract/unrealistic**
- Mitigation: Ground in real technical implementation (Sentinel)
- Mitigation: Reference real EW/deception doctrine
- Mitigation: Emphasize human decision-making (not autonomous)
- Backup: Can pivot essay focus to pure edge computing if needed

---

## Conclusion: Why This Strategy Works

### Three Reinforcing Pillars

```
Technical Capability     Strategic Thinking     Career Execution
        ↓                        ↓                      ↓
   Sentinel v2              DND Essay            Job Applications
        ↓                        ↓                      ↓
    "I can build"          "I can think"         "I'm serious"
        └────────────────────────┴──────────────────────┘
                                 │
                                 ▼
                    "Hire this person immediately"
```

### The Synergy Effect

**Why This Is Better Than Just Applying:**

1. **Demonstration > Description**
   - Most candidates: "I can build distributed systems"
   - You: "Here's a distributed system I built"

2. **Sustained Interest > Job Hunting**
   - Most candidates: "I want a defense tech job"
   - You: "I've been exploring Arctic defense independently, including DND contest submission"

3. **Strategic Thinking > Pure Engineering**
   - Most candidates: Code samples
   - You: Code + operational doctrine + strategic analysis

4. **Multiple Touchpoints > Single Application**
   - Most candidates: Resume + cover letter
   - You: Resume + demo + essay + personal outreach

### The Timeline Works

**Nov 13-18:** Implementation (Claude Code does heavy lifting while you're busy)
**Nov 19-25:** Essay + outreach (you're available for writing)
**Dec 1-15:** Applications + interviews (timing aligns with holiday hiring)
**Jan 1-16:** Essay submission + offer negotiation
**Feb 1+:** Start new job with DND contest still pending

### The Failure Modes Are Acceptable

**If Sentinel v2 incomplete:** You still have modules 1-3, sufficient for demo
**If DND essay doesn't win:** Still valuable portfolio piece + shows initiative
**If personal outreach fails:** Standard applications work fine
**If no offers by January:** Continue building, reapply in spring with even better demo

### The Upside Is Significant

**Best case scenario:**
- Senior role at Dominion ($170K+ with equity)
- DND contest finalist (visibility to defense decision-makers)
- Published essay (professional credibility)
- Open-source project (portfolio for future opportunities)

**This is achievable.** You have the skills, the time, the tools (Claude Code credits), and the strategy.

---

## Next Steps: Implementation Begins

### What Happens Now

1. **You confirm this strategy** ("Yes, proceed")
2. **I create Module Specifications** (detailed implementation guides for Claude Code)
3. **You begin Claude Code sessions** (Nov 13, following specifications)
4. **Claude Code generates code** (Nov 13-18, using $250 credits)
5. **You integrate and test** (Nov 15-18, 3 days)
6. **You deploy and document** (Nov 18, final day)
7. **You write essay** (Nov 19-25, 1 week)
8. **You execute outreach** (Nov 25-29, 4 days)

### Your Decision Point

**Do you approve this strategy?**

If yes, I'll immediately create:
1. **Module 1 Specification** (Edge Inference Engine)
2. **Module 2 Specification** (Backend API)
3. **Module 3 Specification** (ATAK Integration)
4. **Module 4 Specification** (Dashboard)
5. **Module 5 Specification** (Blackout Mode)
6. **Integration Guide** (How modules connect)
7. **Deployment Guide** (Railway/Fly.io setup)
8. **Claude Code Prompts** (Optimized for agent execution)

Each specification will be a complete implementation guide that Claude Code can execute autonomously.

**Ready to begin?**
