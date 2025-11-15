# Module 5: Blackout Mode - Complete Implementation Specification

**Purpose:** Deceptive edge architecture enabling covert surveillance operations  
**Target:** Coordinated blackout across all modules, zero detection loss, complete audit trail  
**Implementation Method:** Cross-module coordination with integration tests

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│              Blackout Mode Coordination              │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐         ┌──────────────┐         │
│  │  Dashboard   │────────▶│   Backend    │         │
│  │  (Trigger)   │         │ (Coordinate) │         │
│  └──────────────┘         └──────┬───────┘         │
│                                   │                  │
│                                   ▼                  │
│                          ┌──────────────┐           │
│                          │  Edge Nodes  │           │
│                          │   (Queue)    │           │
│                          └──────────────┘           │
│                                                      │
└─────────────────────────────────────────────────────┘

     ACTIVATION                  BLACKOUT               DEACTIVATION
         │                          │                        │
         ▼                          ▼                        ▼
    Stop RF → Continue Inference → Burst Transmission
```

**Design Philosophy:**
- **Operational Deception:** System appears failed while operating covertly
- **Operator Control:** Human decides when to activate/deactivate
- **Complete Persistence:** Zero detection loss during blackout
- **Tactical Timing:** Operator chooses moment to reveal intelligence

---

## Conceptual Model

### The Deceptive Edge Doctrine

**Problem:** Adversaries can detect and target surveillance systems through RF emissions

**Traditional Approach:** 
- Hardening against jamming
- Redundant communication paths
- Defensive electronic warfare

**Sentinel's Approach:**
- **Embrace apparent failure** as tactical advantage
- **Continue operations covertly** while appearing offline
- **Choose revelation timing** for maximum operational impact

### How It Works

**Normal Operations:**
```
Edge Node → [Detections] → Backend → Dashboard
  ↓
RF Signature Visible
Adversary knows you're watching
```

**Blackout Mode (Covert Ops):**
```
Edge Node → [Detections] → Local Queue (SQLite)
  ↓
No RF Signature
Adversary believes system is down
Continues operations freely
You watch everything
```

**Deactivation (Intelligence Revelation):**
```
Edge Node → [ALL Queued Detections] → Backend → Dashboard
  ↓
Adversary realizes deception
Complete surveillance history revealed
Operational advantage achieved
```

---

## Technology Stack

**Coordination Layer:**
- Python 3.11 (Backend coordination)
- FastAPI endpoints for blackout control
- WebSocket for real-time state updates

**Persistence:**
- SQLite (edge node local queue)
- PostgreSQL (backend blackout event log)

**State Management:**
- Backend: Database-backed state machine
- Edge: In-memory + SQLite persistence
- Dashboard: Zustand + WebSocket updates

**Testing:**
- pytest (integration tests)
- Playwright (E2E workflows)

---

## File Structure

```
blackout-mode/
├── backend/
│   ├── src/
│   │   ├── blackout.py          # Blackout coordination logic
│   │   └── blackout_routes.py   # API endpoints
│   └── tests/
│       ├── test_blackout_state.py
│       └── test_blackout_coordination.py
├── edge/
│   ├── src/
│   │   └── blackout.py          # Edge-side queue management
│   └── tests/
│       └── test_edge_blackout.py
├── dashboard/
│   ├── src/
│   │   └── components/
│   │       └── BlackoutControl.tsx
│   └── tests/
│       └── BlackoutControl.test.tsx
├── integration-tests/
│   ├── test_full_blackout_workflow.py
│   └── test_multi_node_blackout.py
└── README.md
```

---

## Backend Blackout Coordination

### Database Schema

**Add to Module 2's models.py:**

```python
# backend/src/models.py

class BlackoutEvent(Base):
    """Blackout activation/deactivation log"""
    __tablename__ = "blackout_events"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    
    # Timing
    activated_at = Column(DateTime(timezone=True), nullable=False)
    deactivated_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)  # Calculated on deactivation
    
    # Context
    activated_by = Column(String, nullable=True)  # Operator ID
    reason = Column(Text, nullable=True)  # Tactical justification
    
    # Metrics
    detections_queued = Column(Integer, default=0)
    detections_transmitted = Column(Integer, default=0)
    
    # Relationships
    node = relationship("Node", back_populates="blackout_events")
```

### Blackout State Machine

```python
# backend/src/blackout.py

from enum import Enum
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from .models import Node, BlackoutEvent

class BlackoutState(Enum):
    """Blackout mode states"""
    NORMAL = "normal"              # Standard operation
    ACTIVATING = "activating"      # Transition to blackout
    ACTIVE = "active"              # In blackout mode
    DEACTIVATING = "deactivating"  # Transition back to normal
    RESUMING = "resuming"          # Burst transmission in progress

class BlackoutCoordinator:
    """Coordinate blackout mode across system"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def activate_blackout(
        self,
        node_id: str,
        operator_id: Optional[str] = None,
        reason: Optional[str] = None
    ) -> BlackoutEvent:
        """
        Activate blackout mode for a node.
        
        Args:
            node_id: Edge node identifier
            operator_id: ID of operator activating blackout
            reason: Tactical justification for blackout
            
        Returns:
            BlackoutEvent record
        """
        # Get node
        result = await self.db.execute(
            select(Node).where(Node.node_id == node_id)
        )
        node = result.scalar_one_or_none()
        
        if not node:
            raise ValueError(f"Node not found: {node_id}")
        
        if node.status == "blackout":
            raise ValueError(f"Node already in blackout: {node_id}")
        
        # Create blackout event
        blackout_event = BlackoutEvent(
            node_id=node.id,
            activated_at=datetime.now(timezone.utc),
            activated_by=operator_id,
            reason=reason
        )
        self.db.add(blackout_event)
        
        # Update node status
        node.status = "blackout"
        
        await self.db.commit()
        await self.db.refresh(blackout_event)
        
        return blackout_event
    
    async def deactivate_blackout(
        self,
        node_id: str
    ) -> dict:
        """
        Deactivate blackout mode for a node.
        
        Args:
            node_id: Edge node identifier
            
        Returns:
            Summary of blackout event
        """
        # Get node
        result = await self.db.execute(
            select(Node).where(Node.node_id == node_id)
        )
        node = result.scalar_one_or_none()
        
        if not node:
            raise ValueError(f"Node not found: {node_id}")
        
        if node.status != "blackout":
            raise ValueError(f"Node not in blackout: {node_id}")
        
        # Get active blackout event
        result = await self.db.execute(
            select(BlackoutEvent)
            .where(BlackoutEvent.node_id == node.id)
            .where(BlackoutEvent.deactivated_at.is_(None))
            .order_by(BlackoutEvent.activated_at.desc())
        )
        event = result.scalar_one_or_none()
        
        if not event:
            raise ValueError(f"No active blackout event for node: {node_id}")
        
        # Update blackout event
        now = datetime.now(timezone.utc)
        event.deactivated_at = now
        event.duration_seconds = int((now - event.activated_at).total_seconds())
        
        # Update node status
        node.status = "resuming"  # Temporary state during burst transmission
        
        await self.db.commit()
        
        return {
            "node_id": node_id,
            "blackout_id": event.id,
            "activated_at": event.activated_at.isoformat(),
            "deactivated_at": event.deactivated_at.isoformat(),
            "duration_seconds": event.duration_seconds,
            "detections_queued": event.detections_queued
        }
    
    async def update_detection_count(
        self,
        node_id: str,
        count: int
    ):
        """
        Update queued detection count for active blackout.
        
        Args:
            node_id: Edge node identifier
            count: Number of detections queued
        """
        result = await self.db.execute(
            select(Node).where(Node.node_id == node_id)
        )
        node = result.scalar_one_or_none()
        
        if not node or node.status != "blackout":
            return
        
        # Update active blackout event
        result = await self.db.execute(
            select(BlackoutEvent)
            .where(BlackoutEvent.node_id == node.id)
            .where(BlackoutEvent.deactivated_at.is_(None))
            .order_by(BlackoutEvent.activated_at.desc())
        )
        event = result.scalar_one_or_none()
        
        if event:
            event.detections_queued = count
            await self.db.commit()
    
    async def complete_resumption(
        self,
        node_id: str,
        transmitted_count: int
    ):
        """
        Mark blackout resumption as complete.
        
        Args:
            node_id: Edge node identifier
            transmitted_count: Number of detections transmitted
        """
        result = await self.db.execute(
            select(Node).where(Node.node_id == node_id)
        )
        node = result.scalar_one_or_none()
        
        if not node:
            return
        
        # Update blackout event
        result = await self.db.execute(
            select(BlackoutEvent)
            .where(BlackoutEvent.node_id == node.id)
            .where(BlackoutEvent.deactivated_at.is_not(None))
            .order_by(BlackoutEvent.deactivated_at.desc())
        )
        event = result.scalar_one_or_none()
        
        if event:
            event.detections_transmitted = transmitted_count
        
        # Update node status
        node.status = "online"
        
        await self.db.commit()
    
    async def get_blackout_status(
        self,
        node_id: str
    ) -> dict:
        """
        Get current blackout status for a node.
        
        Args:
            node_id: Edge node identifier
            
        Returns:
            Blackout status information
        """
        result = await self.db.execute(
            select(Node).where(Node.node_id == node_id)
        )
        node = result.scalar_one_or_none()
        
        if not node:
            return {"status": "node_not_found"}
        
        if node.status != "blackout":
            return {
                "status": "inactive",
                "node_status": node.status
            }
        
        # Get active blackout event
        result = await self.db.execute(
            select(BlackoutEvent)
            .where(BlackoutEvent.node_id == node.id)
            .where(BlackoutEvent.deactivated_at.is_(None))
            .order_by(BlackoutEvent.activated_at.desc())
        )
        event = result.scalar_one_or_none()
        
        if not event:
            return {"status": "error", "message": "Node in blackout but no event found"}
        
        duration = (datetime.now(timezone.utc) - event.activated_at).total_seconds()
        
        return {
            "status": "active",
            "blackout_id": event.id,
            "activated_at": event.activated_at.isoformat(),
            "duration_seconds": int(duration),
            "detections_queued": event.detections_queued,
            "activated_by": event.activated_by,
            "reason": event.reason
        }
```

### API Endpoints

**Add to Module 2's main.py:**

```python
# backend/src/main.py

from .blackout import BlackoutCoordinator

@app.post("/api/nodes/{node_id}/blackout/activate")
async def activate_node_blackout(
    node_id: str,
    operator_id: Optional[str] = None,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Activate blackout mode for a node"""
    coordinator = BlackoutCoordinator(db)
    
    try:
        event = await coordinator.activate_blackout(node_id, operator_id, reason)
        
        # Notify edge node via WebSocket
        await manager.send_to_node(node_id, {
            "type": "blackout_activate",
            "blackout_id": event.id
        })
        
        # Broadcast to dashboard
        await manager.broadcast({
            "type": "blackout_event",
            "action": "activated",
            "node_id": node_id,
            "blackout_id": event.id
        })
        
        return {
            "status": "activated",
            "blackout_id": event.id,
            "node_id": node_id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/nodes/{node_id}/blackout/deactivate")
async def deactivate_node_blackout(
    node_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Deactivate blackout mode and trigger burst transmission"""
    coordinator = BlackoutCoordinator(db)
    
    try:
        summary = await coordinator.deactivate_blackout(node_id)
        
        # Notify edge node via WebSocket
        await manager.send_to_node(node_id, {
            "type": "blackout_deactivate",
            "blackout_id": summary["blackout_id"]
        })
        
        # Broadcast to dashboard
        await manager.broadcast({
            "type": "blackout_event",
            "action": "deactivating",
            "node_id": node_id,
            "summary": summary
        })
        
        return summary
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/nodes/{node_id}/blackout/status")
async def get_node_blackout_status(
    node_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get blackout status for a node"""
    coordinator = BlackoutCoordinator(db)
    status = await coordinator.get_blackout_status(node_id)
    return status

@app.get("/api/blackout/events")
async def get_blackout_events(
    node_id: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Query blackout event history"""
    query = select(BlackoutEvent).order_by(BlackoutEvent.activated_at.desc()).limit(limit)
    
    if node_id:
        result = await db.execute(
            select(Node).where(Node.node_id == node_id)
        )
        node = result.scalar_one_or_none()
        if node:
            query = query.where(BlackoutEvent.node_id == node.id)
    
    result = await db.execute(query)
    events = result.scalars().all()
    
    return [
        {
            "id": event.id,
            "node_id": event.node.node_id,
            "activated_at": event.activated_at.isoformat(),
            "deactivated_at": event.deactivated_at.isoformat() if event.deactivated_at else None,
            "duration_seconds": event.duration_seconds,
            "detections_queued": event.detections_queued,
            "detections_transmitted": event.detections_transmitted,
            "activated_by": event.activated_by,
            "reason": event.reason
        }
        for event in events
    ]
```

---

## Edge Node Blackout Queue

**Extend Module 1's blackout.py:**

```python
# edge-inference/src/blackout.py

import aiosqlite
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

class EdgeBlackoutController:
    """Manage blackout mode at edge node"""
    
    def __init__(self, node_id: str, db_path: str = "blackout_queue.db"):
        self.node_id = node_id
        self.db_path = Path(db_path)
        self.is_active = False
        self.blackout_id: Optional[int] = None
        self.activated_at: Optional[datetime] = None
        self._initialized = False
    
    async def _init_db(self):
        """Initialize SQLite database for queue"""
        if self._initialized:
            return
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS queued_detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    queued_at TEXT NOT NULL,
                    detection_data TEXT NOT NULL,
                    transmitted BOOLEAN DEFAULT 0
                )
            """)
            await db.commit()
        
        self._initialized = True
    
    async def activate(self, blackout_id: int):
        """
        Activate blackout mode.
        
        Args:
            blackout_id: Backend blackout event ID
        """
        await self._init_db()
        
        self.is_active = True
        self.blackout_id = blackout_id
        self.activated_at = datetime.now(timezone.utc)
        
        print(f"[BLACKOUT] Node {self.node_id} entering blackout mode")
        print(f"[BLACKOUT] Detections will be queued locally")
        print(f"[BLACKOUT] RF signature suppressed")
    
    async def deactivate(self) -> List[Dict[str, Any]]:
        """
        Deactivate blackout mode and return queued detections.
        
        Returns:
            List of all queued detections for burst transmission
        """
        if not self.is_active:
            return []
        
        detections = await self.get_queued_detections()
        
        print(f"[BLACKOUT] Node {self.node_id} exiting blackout mode")
        print(f"[BLACKOUT] Transmitting {len(detections)} queued detections")
        
        self.is_active = False
        self.blackout_id = None
        self.activated_at = None
        
        return detections
    
    async def queue_detection(self, detection: Dict[str, Any]):
        """
        Queue detection during blackout.
        
        Args:
            detection: Detection data to queue
        """
        await self._init_db()
        
        detection_json = json.dumps(detection)
        queued_at = datetime.now(timezone.utc).isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO queued_detections (queued_at, detection_data) VALUES (?, ?)",
                (queued_at, detection_json)
            )
            await db.commit()
        
        # Periodic status update to backend
        count = len(await self.get_queued_detections())
        if count % 10 == 0:  # Every 10 detections
            print(f"[BLACKOUT] {count} detections queued")
    
    async def get_queued_detections(self) -> List[Dict[str, Any]]:
        """
        Get all queued detections.
        
        Returns:
            List of queued detection data
        """
        await self._init_db()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT id, queued_at, detection_data FROM queued_detections WHERE transmitted = 0"
            )
            rows = await cursor.fetchall()
        
        return [
            {
                "id": row[0],
                "queued_at": row[1],
                "detection": json.loads(row[2])
            }
            for row in rows
        ]
    
    async def mark_transmitted(self, detection_ids: List[int]):
        """
        Mark detections as transmitted.
        
        Args:
            detection_ids: List of detection IDs that were transmitted
        """
        await self._init_db()
        
        async with aiosqlite.connect(self.db_path) as db:
            for det_id in detection_ids:
                await db.execute(
                    "UPDATE queued_detections SET transmitted = 1 WHERE id = ?",
                    (det_id,)
                )
            await db.commit()
    
    async def clear_transmitted(self):
        """Clear transmitted detections from queue"""
        await self._init_db()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM queued_detections WHERE transmitted = 1")
            await db.commit()
    
    def get_status(self) -> dict:
        """Get current blackout status"""
        return {
            "active": self.is_active,
            "blackout_id": self.blackout_id,
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
            "duration_seconds": int((datetime.now(timezone.utc) - self.activated_at).total_seconds()) if self.activated_at else None
        }
```

---

## Dashboard Blackout Controls

**Enhanced BlackoutControl component:**

```typescript
// dashboard/src/components/BlackoutControl.tsx

import { useState } from 'react';
import { Node } from '@/lib/types';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, Eye, EyeOff, Timer } from 'lucide-react';

interface BlackoutControlProps {
  node: Node;
  onActivate: (nodeId: string, reason?: string) => Promise<void>;
  onDeactivate: (nodeId: string) => Promise<void>;
}

export function BlackoutControl({ node, onActivate, onDeactivate }: BlackoutControlProps) {
  const [showDialog, setShowDialog] = useState(false);
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  
  const handleActivate = async () => {
    setLoading(true);
    try {
      await onActivate(node.node_id, reason || undefined);
      setShowDialog(false);
      setReason('');
    } finally {
      setLoading(false);
    }
  };
  
  const handleDeactivate = async () => {
    setLoading(true);
    try {
      await onDeactivate(node.node_id);
    } finally {
      setLoading(false);
    }
  };
  
  if (node.status === 'blackout') {
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="bg-blue-500/10 text-blue-500 border-blue-500/30">
            <EyeOff className="w-3 h-3 mr-1" />
            COVERT OPS
          </Badge>
        </div>
        
        <div className="space-y-2 text-sm">
          <div className="flex items-center gap-2 text-tactical-textMuted">
            <Timer className="w-4 h-4" />
            <span>Duration: {/* Calculate from activated_at */}</span>
          </div>
          
          <div className="flex items-center gap-2 text-tactical-textMuted">
            <Eye className="w-4 h-4" />
            <span>Detections queued: {/* Show queued count */}</span>
          </div>
        </div>
        
        <Button
          onClick={handleDeactivate}
          disabled={loading}
          className="w-full"
          variant="outline"
        >
          Resume Transmission
        </Button>
      </div>
    );
  }
  
  return (
    <>
      <Button
        onClick={() => setShowDialog(true)}
        disabled={node.status !== 'online' || loading}
        variant="outline"
        className="w-full"
      >
        <EyeOff className="w-4 h-4 mr-2" />
        Activate Blackout
      </Button>
      
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-yellow-500" />
              Activate Blackout Mode
            </DialogTitle>
            <DialogDescription>
              Node {node.node_id} will appear offline while continuing covert surveillance.
              All detections will be queued locally until you resume transmission.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">
                Tactical Justification (Optional)
              </label>
              <Textarea
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Reason for activating blackout mode..."
                className="mt-2"
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleActivate} disabled={loading}>
              Activate Blackout
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
```

---

## Integration Testing

### Full Blackout Workflow Test

```python
# integration-tests/test_full_blackout_workflow.py

import pytest
import asyncio
from datetime import datetime, timezone

@pytest.mark.asyncio
async def test_full_blackout_workflow(
    edge_node,
    backend_api,
    dashboard_client
):
    """
    Test complete blackout workflow from activation to deactivation.
    
    Scenario:
    1. Operator activates blackout via dashboard
    2. Edge node receives blackout command
    3. Edge node queues detections locally (10 detections)
    4. Backend tracks node as in blackout
    5. Operator deactivates blackout
    6. Edge node transmits all queued detections
    7. Backend ingests burst with original timestamps
    8. Dashboard displays historical detections
    """
    node_id = "sentry-01"
    
    # Step 1: Activate blackout via dashboard
    response = await dashboard_client.post(
        f"/api/nodes/{node_id}/blackout/activate",
        json={"reason": "Enemy EW detected, activating covert mode"}
    )
    assert response.status_code == 200
    blackout_id = response.json()["blackout_id"]
    
    # Step 2: Edge node receives command
    await asyncio.sleep(0.5)  # Allow WebSocket propagation
    assert edge_node.blackout.is_active
    assert edge_node.blackout.blackout_id == blackout_id
    
    # Step 3: Generate 10 detections (queued locally)
    detections = []
    for i in range(10):
        detection = await edge_node.generate_detection()
        detections.append(detection)
        await asyncio.sleep(0.1)
    
    # Verify detections are queued, not transmitted
    queued = await edge_node.blackout.get_queued_detections()
    assert len(queued) == 10
    
    # Step 4: Backend shows node in blackout
    response = await backend_api.get(f"/api/nodes/{node_id}/status")
    assert response.json()["status"] == "blackout"
    
    # Step 5: Deactivate blackout
    response = await dashboard_client.post(
        f"/api/nodes/{node_id}/blackout/deactivate"
    )
    assert response.status_code == 200
    summary = response.json()
    assert summary["detections_queued"] == 10
    
    # Step 6: Edge node transmits burst
    await asyncio.sleep(2)  # Allow burst transmission
    
    # Step 7: Backend received all detections with original timestamps
    response = await backend_api.get(f"/api/detections?node_id={node_id}&limit=20")
    received_detections = response.json()
    
    assert len(received_detections) >= 10
    
    # Verify timestamps are original (during blackout period)
    for det in received_detections[-10:]:
        timestamp = datetime.fromisoformat(det["timestamp"])
        # Should be within blackout period
        assert summary["activated_at"] <= timestamp.isoformat() <= summary["deactivated_at"]
    
    # Step 8: Dashboard displays all detections
    # (Tested via E2E in dashboard tests)

@pytest.mark.asyncio
async def test_multi_node_blackout(edge_nodes, backend_api):
    """Test blackout coordination across multiple nodes"""
    node_ids = ["sentry-01", "sentry-02", "aerostat-01"]
    
    # Activate blackout for all nodes
    for node_id in node_ids:
        response = await backend_api.post(
            f"/api/nodes/{node_id}/blackout/activate",
            json={"reason": "Coordinated covert operation"}
        )
        assert response.status_code == 200
    
    # All nodes in blackout
    for node_id in node_ids:
        response = await backend_api.get(f"/api/nodes/{node_id}/status")
        assert response.json()["status"] == "blackout"
    
    # Generate detections on all nodes
    for node in edge_nodes:
        for _ in range(5):
            await node.generate_detection()
    
    # Deactivate all nodes
    for node_id in node_ids:
        response = await backend_api.post(
            f"/api/nodes/{node_id}/blackout/deactivate"
        )
        assert response.status_code == 200
    
    # All detections received
    response = await backend_api.get("/api/detections?limit=50")
    detections = response.json()
    assert len(detections) >= 15  # 3 nodes * 5 detections

@pytest.mark.asyncio
async def test_blackout_persistence_across_restart(edge_node):
    """Test that queued detections persist across edge node restart"""
    node_id = "sentry-01"
    
    # Activate blackout
    await edge_node.blackout.activate(blackout_id=1)
    
    # Generate detections
    for _ in range(5):
        detection = await edge_node.generate_detection()
        await edge_node.blackout.queue_detection(detection)
    
    # Simulate restart (close and reopen)
    await edge_node.shutdown()
    
    # New edge node instance
    new_node = EdgeNode(node_id=node_id)
    await new_node.startup()
    
    # Verify queue persisted
    queued = await new_node.blackout.get_queued_detections()
    assert len(queued) == 5
```

---

## E2E Dashboard Tests

```typescript
// dashboard/tests/e2e/blackout-workflow.spec.ts

import { test, expect } from '@playwright/test';

test.describe('Blackout Mode Workflow', () => {
  test('operator can activate and deactivate blackout', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Find node panel
    const nodeCard = page.locator('[data-testid="node-card-sentry-01"]');
    await expect(nodeCard).toBeVisible();
    
    // Verify initial online status
    await expect(nodeCard.locator('text=ONLINE')).toBeVisible();
    
    // Click activate blackout
    await nodeCard.locator('button:has-text("Activate Blackout")').click();
    
    // Fill in reason
    await page.fill('textarea[placeholder*="Reason"]', 'Testing blackout mode');
    
    // Confirm activation
    await page.click('button:has-text("Activate Blackout")');
    
    // Verify blackout status
    await expect(nodeCard.locator('text=COVERT OPS')).toBeVisible({ timeout: 5000 });
    
    // Verify timer appears
    await expect(nodeCard.locator('text=Duration:')).toBeVisible();
    
    // Verify queued count updates (wait for detections)
    await page.waitForTimeout(2000);
    await expect(nodeCard.locator('text=Detections queued:')).toBeVisible();
    
    // Deactivate blackout
    await nodeCard.locator('button:has-text("Resume Transmission")').click();
    
    // Verify status returns to online
    await expect(nodeCard.locator('text=ONLINE')).toBeVisible({ timeout: 5000 });
    
    // Verify detections appear on map (burst transmission)
    const markers = page.locator('.leaflet-marker-icon');
    await expect(markers.first()).toBeVisible({ timeout: 5000 });
  });
  
  test('detections continue to accumulate during blackout', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    const nodeCard = page.locator('[data-testid="node-card-sentry-01"]');
    
    // Activate blackout
    await nodeCard.locator('button:has-text("Activate Blackout")').click();
    await page.click('button:has-text("Activate Blackout")');
    
    // Wait and verify queued count increases
    await page.waitForTimeout(1000);
    const initialCount = await nodeCard.locator('[data-testid="queued-count"]').textContent();
    
    await page.waitForTimeout(2000);
    const laterCount = await nodeCard.locator('[data-testid="queued-count"]').textContent();
    
    expect(parseInt(laterCount!)).toBeGreaterThan(parseInt(initialCount!));
  });
});
```

---

## Documentation

### README.md

```markdown
# Module 5: Blackout Mode - Deceptive Edge Architecture

## Overview

Blackout Mode enables tactical deception through apparent system failure. Edge nodes continue surveillance operations while appearing offline to adversaries, queuing detections locally until the operator chooses to reveal intelligence.

## Concept

Traditional surveillance systems can be detected and targeted through RF emissions. Blackout Mode turns this weakness into a tactical advantage by:

1. **Stopping external transmissions** (appears offline)
2. **Continuing local operations** (covert surveillance)
3. **Queuing all detections** (zero loss)
4. **Operator-controlled revelation** (tactical timing)

## Architecture

```
Activation → Covert Ops → Deactivation → Intelligence Revelation
```

### Normal Operations
- Edge node transmits detections to backend
- RF signature visible to adversary
- Real-time situational awareness

### Blackout Mode
- Edge node suppresses RF emissions
- Detections queued in local SQLite
- Appears offline to adversary
- Operator maintains awareness of covert status

### Deactivation
- Burst transmission of all queued detections
- Original timestamps preserved
- Complete surveillance history revealed
- Adversary realizes deception

## Implementation

### Backend Coordination
- **File:** `backend/src/blackout.py`
- State machine for blackout lifecycle
- PostgreSQL event logging
- WebSocket coordination

### Edge Queue Management
- **File:** `edge-inference/src/blackout.py`
- SQLite persistence during blackout
- Detection queueing
- Burst transmission on deactivation

### Dashboard Controls
- **File:** `dashboard/src/components/BlackoutControl.tsx`
- Activation with tactical justification
- Real-time status monitoring
- Deactivation trigger

## Usage

### Activating Blackout

**Via API:**
```bash
curl -X POST http://localhost:8001/api/nodes/sentry-01/blackout/activate \
  -H "Content-Type: application/json" \
  -d '{"reason": "Enemy EW detected"}'
```

**Via Dashboard:**
1. Navigate to node status panel
2. Click "Activate Blackout" for target node
3. Provide tactical justification (optional)
4. Confirm activation

### Monitoring Blackout

**Via API:**
```bash
curl http://localhost:8001/api/nodes/sentry-01/blackout/status
```

**Via Dashboard:**
- Node status shows "COVERT OPS"
- Duration timer displayed
- Queued detection count updates in real-time

### Deactivating Blackout

**Via API:**
```bash
curl -X POST http://localhost:8001/api/nodes/sentry-01/blackout/deactivate
```

**Via Dashboard:**
1. Click "Resume Transmission"
2. Watch burst transmission complete
3. Historical detections appear on map

## Testing

Run integration tests:
```bash
pytest integration-tests/test_full_blackout_workflow.py -v
```

Run E2E tests:
```bash
npx playwright test tests/e2e/blackout-workflow.spec.ts
```

## Operational Considerations

### When to Use Blackout Mode

- **Enemy EW Attack:** Adversary attempting to jam communications
- **Covert Intelligence:** Need to monitor without revealing capability
- **Tactical Deception:** Want adversary to believe sensors are disabled

### Limitations

- No real-time updates during blackout
- Requires SQLite storage capacity at edge
- Burst transmission may be detectable (timing-based)

### Best Practices

- Document tactical justification for auditing
- Monitor queued detection count
- Plan deactivation for optimal tactical timing
- Ensure adequate edge storage capacity

## For DND Essay

This implementation provides technical grounding for "The Deceptive Edge Doctrine" essay concept:

> "We designed our sensors to fail gracefully - or so it appeared. The adversary's EW attack successfully suppressed RF emissions, convincing them we were blind. In reality, edge inference continued silently, accumulating a detailed intelligence picture we could reveal at the moment of maximum operational advantage."

## Next Steps

1. Deploy Module 5 alongside Modules 1-4
2. Test complete blackout workflow
3. Document operational procedures
4. Integrate into DND contest essay
```

---

## Success Criteria

**Must Have:**
- ✅ Backend blackout coordination working
- ✅ Edge node queue persistence functional
- ✅ Dashboard controls operational
- ✅ Full integration test passing
- ✅ Zero detection loss during blackout

**Should Have:**
- ✅ WebSocket state synchronization
- ✅ Multi-node blackout support
- ✅ Blackout event audit trail
- ✅ E2E dashboard tests passing

**Nice to Have:**
- ✅ Blackout analytics (average duration, detection count)
- ✅ Scheduled blackout activation
- ✅ Blackout status dashboard widget

---

## Claude Code Implementation Notes

**This module is primarily INTEGRATION work, not new code:**

1. **Backend:** Add blackout coordination logic to existing Module 2
2. **Edge:** Extend existing Module 1 blackout controller
3. **Dashboard:** Enhance existing Module 4 BlackoutControl component
4. **Testing:** Create new integration test suite

**Estimated Effort:**
- Backend additions: 1 session
- Edge enhancements: 1 session
- Dashboard polish: 0.5 sessions
- Integration tests: 1-2 sessions

**Total: 3-4 Claude Code sessions**

---

## Deployment

Module 5 doesn't deploy independently - it's integrated across all modules:

1. Deploy Module 2 (backend) with blackout endpoints
2. Deploy Module 1 (edge) with enhanced blackout queue
3. Deploy Module 4 (dashboard) with blackout controls
4. Test full workflow end-to-end

**End of Module 5 Specification**
