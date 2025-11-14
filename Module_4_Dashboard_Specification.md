# Module 4: Operator Dashboard - Complete Implementation Specification

**Purpose:** Tactical command & control interface for military operators  
**Target:** Real-time situational awareness, <1s update latency, tactical dark theme  
**Implementation Method:** Claude Code agent with component-driven development

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│              Operator Dashboard                      │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐         ┌──────────────┐         │
│  │  Tactical    │────────▶│  Detection   │         │
│  │     Map      │         │     List     │         │
│  └──────────────┘         └──────────────┘         │
│         │                         │                 │
│         ▼                         ▼                 │
│  ┌──────────────┐         ┌──────────────┐         │
│  │    Node      │         │   Blackout   │         │
│  │   Status     │         │   Control    │         │
│  └──────────────┘         └──────────────┘         │
│                                                      │
└─────────────────────────────────────────────────────┘
         │                          │
         ▼                          ▼
    WebSocket                  Backend API
   (Real-time)                (REST + WS)
```

**Design Philosophy:**
- Operator-first: Built for military decision-makers, not consumers
- Tactical aesthetics: Dark theme, high contrast, minimal distractions
- Real-time awareness: WebSocket updates with <1s latency
- Mission focus: Every UI element serves operational purpose

---

## Technology Stack

**Core Framework:**
- React 18.3+
- TypeScript 5.3+
- Vite 5.0+ (build tool)

**UI Components:**
- Tailwind CSS 3.4+ (styling)
- shadcn/ui (component library)
- Lucide React (icons)

**Mapping:**
- Leaflet 1.9+ (map library)
- react-leaflet 4.2+ (React bindings)

**State Management:**
- Zustand 4.4+ (lightweight state)
- React Query / TanStack Query 5.0+ (server state)

**Real-time:**
- Native WebSocket API
- Reconnection logic

**Testing:**
- Vitest 1.0+ (unit tests)
- Testing Library (React)
- Playwright 1.40+ (E2E tests)

---

## File Structure

```
dashboard/
├── src/
│   ├── components/
│   │   ├── ui/                    # shadcn/ui base components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── table.tsx
│   │   │   ├── dialog.tsx
│   │   │   └── alert.tsx
│   │   ├── TacticalMap.tsx        # Main map component
│   │   ├── DetectionMarker.tsx    # Map marker for detections
│   │   ├── NodeMarker.tsx         # Map marker for edge nodes
│   │   ├── DetectionList.tsx      # Sortable detection table
│   │   ├── DetectionFilters.tsx   # Filter controls
│   │   ├── NodeStatusPanel.tsx    # Node health indicators
│   │   ├── NodeStatusCard.tsx     # Individual node status
│   │   ├── BlackoutControl.tsx    # Blackout activation UI
│   │   ├── AlertPanel.tsx         # High-confidence alerts
│   │   └── ConnectionStatus.tsx   # WebSocket status indicator
│   ├── hooks/
│   │   ├── useWebSocket.ts        # WebSocket connection
│   │   ├── useDetections.ts       # Detection data management
│   │   ├── useNodes.ts            # Node status management
│   │   └── useFilters.ts          # Filter state
│   ├── lib/
│   │   ├── api.ts                 # Backend API client
│   │   ├── websocket.ts           # WebSocket utilities
│   │   ├── types.ts               # TypeScript types
│   │   └── utils.ts               # Utility functions
│   ├── store/
│   │   └── useStore.ts            # Zustand global state
│   ├── App.tsx                    # Main application
│   ├── main.tsx                   # Entry point
│   └── index.css                  # Global styles
├── public/
│   └── tactical-icon.svg          # Application icon
├── tests/
│   ├── components/
│   │   ├── TacticalMap.test.tsx
│   │   ├── DetectionList.test.tsx
│   │   └── BlackoutControl.test.tsx
│   ├── hooks/
│   │   ├── useWebSocket.test.ts
│   │   └── useDetections.test.ts
│   └── e2e/
│       └── operator-workflow.spec.ts
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── vitest.config.ts
├── playwright.config.ts
└── README.md
```

---

## Component Specifications

### 1. TacticalMap Component

**Purpose:** Primary visualization of detections and nodes on Arctic map

**Props:**
```typescript
interface TacticalMapProps {
  detections: Detection[];
  nodes: Node[];
  onDetectionClick?: (detection: Detection) => void;
  onNodeClick?: (node: Node) => void;
  selectedDetection?: Detection | null;
}
```

**Features:**
- Leaflet map centered on Arctic (70°N, -100°W)
- Detection markers color-coded by confidence:
  - High (>0.85): Red
  - Medium (0.7-0.85): Orange
  - Low (<0.7): Yellow
- Node markers showing online/offline/blackout status
- Click to select detection/node
- Zoom controls
- Layer controls (detections, nodes, grid)

**Map Layers:**
- Base: OpenStreetMap or satellite imagery
- Detections layer (clustered if >50)
- Nodes layer
- Grid overlay (Arctic coordinates)

---

### 2. DetectionList Component

**Purpose:** Sortable, filterable table of all detections

**Props:**
```typescript
interface DetectionListProps {
  detections: Detection[];
  onDetectionClick: (detection: Detection) => void;
  selectedDetection?: Detection | null;
}
```

**Columns:**
- Timestamp (sortable)
- Node ID (filterable)
- Object Class (filterable)
- Confidence (sortable)
- Location (lat/lon)
- Actions (view on map)

**Features:**
- Sort by any column
- Filter by:
  - Object class (person, vehicle, etc.)
  - Confidence threshold (slider)
  - Time range (last hour, 6 hours, 24 hours, custom)
  - Node ID (multi-select)
- Pagination (50 per page)
- Export to CSV

---

### 3. NodeStatusPanel Component

**Purpose:** Display health and status of all edge nodes

**Props:**
```typescript
interface NodeStatusPanelProps {
  nodes: Node[];
  onBlackoutToggle: (nodeId: string) => void;
}
```

**For each node, display:**
- Node ID (e.g., "sentry-01")
- Status badge (online/offline/blackout)
- Last heartbeat timestamp
- Detection count (last 1 hour)
- Blackout controls (if applicable)

**Status Colors:**
- Online: Green
- Offline: Gray
- Covert: Blue (blackout/covert operations mode)

---

### 4. BlackoutControl Component

**Purpose:** Interface for activating/deactivating blackout mode

**Props:**
```typescript
interface BlackoutControlProps {
  node: Node;
  onActivate: (nodeId: string) => void;
  onDeactivate: (nodeId: string) => void;
}
```

**UI Elements:**
- "Activate Blackout" button (when node online)
- "Resume Transmission" button (when node in blackout)
- Blackout timer (time since activation)
- Queued detection count
- Confirmation dialog before activation

**States:**
- Normal: Show activate button
- Blackout Active: Show timer, queued count, resume button
- Resuming: Show progress indicator

---

### 5. AlertPanel Component

**Purpose:** Highlight high-confidence detections requiring attention

**Props:**
```typescript
interface AlertPanelProps {
  detections: Detection[];
  onAcknowledge: (detectionId: number) => void;
}
```

**Features:**
- Show detections with confidence >0.85
- Visual alert (red border)
- Optional sound notification
- "Acknowledge" button to dismiss
- Auto-dismiss after 30 seconds
- Max 5 alerts shown simultaneously

---

## TypeScript Types

```typescript
// src/lib/types.ts

export interface Detection {
  id: number;
  node_id: string;
  timestamp: string;
  latitude: number;
  longitude: number;
  altitude_m?: number;
  accuracy_m?: number;
  detections: ObjectDetection[];
  detection_count: number;
  inference_time_ms?: number;
  model?: string;
}

export interface ObjectDetection {
  bbox: BoundingBox;
  class: string;
  confidence: number;
  class_id: number;
}

export interface BoundingBox {
  xmin: number;
  ymin: number;
  xmax: number;
  ymax: number;
}

export interface Node {
  id: number;
  node_id: string;
  status: 'online' | 'offline' | 'covert';  // Backend uses 'covert' not 'blackout'
  last_heartbeat?: string;
  created_at: string;
}

export interface BlackoutEvent {
  id: number;
  node_id: number;
  activated_at: string;
  deactivated_at?: string;
  activated_by?: string;
  reason?: string;
  detections_queued: number;
}

export interface WebSocketMessage {
  type: 'detection' | 'node_status' | 'blackout_event';
  data: Detection | Node | BlackoutEvent;
}

export interface Filters {
  objectClass: string[];
  confidenceMin: number;
  timeRange: 'hour' | '6hours' | '24hours' | 'custom';
  nodeIds: string[];
  customTimeStart?: Date;
  customTimeEnd?: Date;
}
```

---

## State Management (Zustand)

**Note:** React Query is the primary source of truth for server state (detections, nodes). Zustand only manages UI state.

```typescript
// src/store/useStore.ts

import { create } from 'zustand';
import { Detection } from '@/lib/types';

interface AppState {
  // UI State only - React Query handles server state
  selectedDetection: Detection | null;
  setSelectedDetection: (detection: Detection | null) => void;

  // WebSocket connection state
  isConnected: boolean;
  setIsConnected: (connected: boolean) => void;
}

export const useStore = create<AppState>((set) => ({
  // UI State
  selectedDetection: null,
  setSelectedDetection: (detection) => set({ selectedDetection: detection }),

  // WebSocket
  isConnected: false,
  setIsConnected: (connected) => set({ isConnected: connected }),
}));
```

**Architecture Note:**
- **React Query** manages server state (detections, nodes) with caching, refetching, and invalidation
- **Zustand** manages UI state (selected detection, connection status)
- **WebSocket** updates trigger React Query cache invalidation for real-time sync

---

## Custom Hooks

### useWebSocket Hook

```typescript
// src/hooks/useWebSocket.ts

import { useEffect, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useStore } from '@/store/useStore';
import { WebSocketMessage } from '@/lib/types';

// Generate unique client ID for WebSocket connection (required by backend)
const CLIENT_ID = crypto.randomUUID();
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8001/ws';
const WS_URL = `${WS_BASE_URL}?client_id=${CLIENT_ID}`;

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttempts = useRef(0);

  const queryClient = useQueryClient();
  const { setIsConnected } = useStore();
  
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    
    const ws = new WebSocket(WS_URL);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      reconnectAttempts.current = 0;
    };
    
    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);

        switch (message.type) {
          case 'detection':
            // New detection received - invalidate detections cache to refetch
            console.log('New detection received:', message.data);
            queryClient.invalidateQueries({ queryKey: ['detections'] });
            break;
          case 'node_status':
            // Node status changed - invalidate nodes cache to refetch
            console.log('Node status updated:', message.data);
            queryClient.invalidateQueries({ queryKey: ['nodes'] });
            break;
          default:
            console.log('Unknown message type:', message.type);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      
      // Exponential backoff reconnection
      const delay = Math.min(1000 * 2 ** reconnectAttempts.current, 30000);
      reconnectAttempts.current += 1;
      
      reconnectTimeoutRef.current = setTimeout(() => {
        console.log(`Reconnecting... (attempt ${reconnectAttempts.current})`);
        connect();
      }, delay);
    };
    
    wsRef.current = ws;
  }, [queryClient, setIsConnected]);
  
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    wsRef.current?.close();
    wsRef.current = null;
  }, []);
  
  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);
  
  return {
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
    reconnect: connect,
  };
}
```

---

### useDetections Hook

```typescript
// src/hooks/useDetections.ts

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Detection } from '@/lib/types';

export function useDetections() {
  return useQuery({
    queryKey: ['detections'],
    queryFn: async () => {
      const response = await api.get<Detection[]>('/api/detections', {
        params: { limit: 1000 }
      });
      return response.data;
    },
    refetchInterval: 30000, // Refetch every 30s as backup to WebSocket
    staleTime: 10000, // Consider data stale after 10s
  });
}
```

**Note:** React Query v5 removed `onSuccess`. Data is now accessed directly via the hook's return value.

---

### useNodes Hook

```typescript
// src/hooks/useNodes.ts

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Node } from '@/lib/types';

export function useNodes() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ['nodes'],
    queryFn: async () => {
      const response = await api.get<Node[]>('/api/nodes');
      return response.data;
    },
    refetchInterval: 10000, // Refetch every 10s
    staleTime: 5000, // Consider data stale after 5s
  });

  const activateBlackout = useMutation({
    mutationFn: async (nodeId: string) => {
      // Backend expects { node_id: string, reason?: string }
      await api.post('/api/blackout/activate', { node_id: nodeId });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['nodes'] });
    },
  });

  const deactivateBlackout = useMutation({
    mutationFn: async (nodeId: string) => {
      // Backend expects { node_id: string }
      await api.post('/api/blackout/deactivate', { node_id: nodeId });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['nodes'] });
    },
  });

  return {
    ...query,
    activateBlackout: activateBlackout.mutate,
    deactivateBlackout: deactivateBlackout.mutate,
  };
}
```

**Important:** Backend blackout endpoints are:
- `POST /api/blackout/activate` (not `/api/nodes/{id}/blackout/activate`)
- `POST /api/blackout/deactivate` (not `/api/nodes/{id}/blackout/deactivate`)

Both take `{ node_id: string }` in the request body.

---

## API Client

```typescript
// src/lib/api.ts

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);
```

---

## Tailwind Configuration (Tactical Theme)

```javascript
// tailwind.config.js

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Tactical color palette
        tactical: {
          bg: '#0a0e1a',
          surface: '#141824',
          border: '#1f2937',
          text: '#e5e7eb',
          textMuted: '#9ca3af',
          primary: '#3b82f6',
          success: '#10b981',
          warning: '#f59e0b',
          danger: '#ef4444',
          info: '#06b6d4',
        },
        // Node status colors
        status: {
          online: '#10b981',
          offline: '#6b7280',
          covert: '#3b82f6',  // Backend uses 'covert' status
        },
        // Confidence colors
        confidence: {
          high: '#ef4444',
          medium: '#f59e0b',
          low: '#fbbf24',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Courier New', 'monospace'],
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
};
```

---

## Main Application Component

```typescript
// src/App.tsx

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TacticalMap } from '@/components/TacticalMap';
import { DetectionList } from '@/components/DetectionList';
import { NodeStatusPanel } from '@/components/NodeStatusPanel';
import { AlertPanel } from '@/components/AlertPanel';
import { ConnectionStatus } from '@/components/ConnectionStatus';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useDetections } from '@/hooks/useDetections';
import { useNodes } from '@/hooks/useNodes';
import { useStore } from '@/store/useStore';

const queryClient = new QueryClient();

function DashboardContent() {
  // WebSocket connection for real-time updates
  useWebSocket();

  // Fetch server state via React Query
  const { data: detections = [], isLoading: detectionsLoading } = useDetections();
  const { data: nodes = [], isLoading: nodesLoading, activateBlackout, deactivateBlackout } = useNodes();

  // UI state from Zustand
  const { selectedDetection, setSelectedDetection, isConnected } = useStore();

  const highConfidenceDetections = detections.filter(
    (d) => d.detections.some((obj) => obj.confidence > 0.85)
  );

  if (detectionsLoading || nodesLoading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-tactical-bg text-tactical-text">
      {/* Header */}
      <header className="bg-tactical-surface border-b border-tactical-border p-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Sentinel - Operator Dashboard</h1>
          <ConnectionStatus isConnected={isConnected} />
        </div>
      </header>
      
      {/* Main Content */}
      <div className="flex h-[calc(100vh-73px)]">
        {/* Left Panel - Map */}
        <div className="flex-1">
          <TacticalMap
            detections={detections}
            nodes={nodes}
            selectedDetection={selectedDetection}
            onDetectionClick={setSelectedDetection}
          />
        </div>
        
        {/* Right Panel - Lists and Controls */}
        <div className="w-[500px] border-l border-tactical-border flex flex-col">
          {/* Alerts */}
          {highConfidenceDetections.length > 0 && (
            <div className="border-b border-tactical-border">
              <AlertPanel
                detections={highConfidenceDetections}
                onAcknowledge={(id) => console.log('Acknowledged:', id)}
              />
            </div>
          )}
          
          {/* Node Status */}
          <div className="border-b border-tactical-border p-4">
            <h2 className="text-lg font-semibold mb-4">Edge Nodes</h2>
            <NodeStatusPanel
              nodes={nodes}
              onBlackoutToggle={(nodeId) => {
                const node = nodes.find((n) => n.node_id === nodeId);
                if (node?.status === 'covert') {  // Backend uses 'covert' status
                  deactivateBlackout(nodeId);
                } else {
                  activateBlackout(nodeId);
                }
              }}
            />
          </div>
          
          {/* Detection List */}
          <div className="flex-1 overflow-hidden">
            <DetectionList
              detections={detections}
              onDetectionClick={setSelectedDetection}
              selectedDetection={selectedDetection}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <DashboardContent />
    </QueryClientProvider>
  );
}
```

---

## Important Setup Notes

### Leaflet CSS Import

**CRITICAL:** Leaflet requires its CSS to be imported in your main entry point:

```typescript
// src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import 'leaflet/dist/leaflet.css';  // REQUIRED for Leaflet map styling

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

### Leaflet Marker Icons Fix (Vite)

Leaflet has a known issue with marker icons in Vite. Add this to your TacticalMap component:

```typescript
import L from 'leaflet';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

// Fix default marker icon paths for Vite
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
});
```

---

## Package Configuration

**package.json:**
```json
{
  "name": "sentinel-dashboard",
  "version": "2.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:e2e": "playwright test",
    "lint": "eslint src --ext ts,tsx",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-leaflet": "^4.2.1",
    "leaflet": "^1.9.4",
    "@tanstack/react-query": "^5.17.0",
    "zustand": "^4.4.7",
    "axios": "^1.6.5",
    "lucide-react": "^0.303.0",
    "date-fns": "^3.0.6",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.48",
    "@types/react-dom": "^18.2.18",
    "@types/leaflet": "^1.9.8",
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.3.3",
    "vite": "^5.0.11",
    "tailwindcss": "^3.4.1",
    "postcss": "^8.4.33",
    "autoprefixer": "^10.4.16",
    "vitest": "^1.2.0",
    "@testing-library/react": "^14.1.2",
    "@testing-library/jest-dom": "^6.2.0",
    "playwright": "^1.40.1",
    "eslint": "^8.56.0"
  }
}
```

---

## Vite Configuration

```typescript
// vite.config.ts

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8001',
        ws: true,
      },
    },
  },
});
```

---

## Testing Strategy

### Unit Tests (Vitest)

```typescript
// tests/components/DetectionList.test.tsx

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DetectionList } from '@/components/DetectionList';

describe('DetectionList', () => {
  it('renders empty state when no detections', () => {
    render(<DetectionList detections={[]} onDetectionClick={() => {}} />);
    expect(screen.getByText(/no detections/i)).toBeInTheDocument();
  });
  
  it('renders detections in table', () => {
    const detections = [
      {
        id: 1,
        node_id: 'sentry-01',
        timestamp: '2025-07-15T14:23:45Z',
        latitude: 70.5,
        longitude: -100.2,
        detections: [{ class: 'person', confidence: 0.89 }],
        detection_count: 1,
      },
    ];
    
    render(<DetectionList detections={detections} onDetectionClick={() => {}} />);
    expect(screen.getByText('sentry-01')).toBeInTheDocument();
    expect(screen.getByText('person')).toBeInTheDocument();
  });
});
```

### E2E Tests (Playwright)

```typescript
// tests/e2e/operator-workflow.spec.ts

import { test, expect } from '@playwright/test';

test.describe('Operator Workflow', () => {
  test('can view detections on map', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Wait for map to load
    await page.waitForSelector('.leaflet-container');
    
    // Should see detection markers
    const markers = await page.locator('.leaflet-marker-icon').count();
    expect(markers).toBeGreaterThan(0);
  });
  
  test('can activate blackout mode', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Find node card
    await page.click('text=sentry-01');
    
    // Click activate blackout
    await page.click('button:has-text("Activate Blackout")');
    
    // Confirm dialog
    await page.click('button:has-text("Confirm")');
    
    // Should see blackout status
    await expect(page.locator('text=BLACKOUT')).toBeVisible();
  });
});
```

---

## Environment Variables

**.env.example:**
```bash
VITE_API_URL=http://localhost:8001
VITE_WS_URL=ws://localhost:8001/ws
```

---

## Specification Updates (Backend Integration)

**Last Updated:** 2025-11-14

This specification has been updated to align with the actual backend implementation (Modules 1-3). Key changes:

### 1. **Node Status Terminology**
- **Changed:** `status: 'online' | 'offline' | 'blackout'`
- **To:** `status: 'online' | 'offline' | 'covert'`
- **Reason:** Backend uses "covert" for blackout mode operations

### 2. **WebSocket Connection**
- **Added:** `client_id` query parameter required by backend
- **Change:** `ws://localhost:8001/ws?client_id={uuid}`
- **Reason:** Backend validates client_id and closes connection without it

### 3. **Blackout API Endpoints**
- **Changed:** `POST /api/nodes/{nodeId}/blackout/activate`
- **To:** `POST /api/blackout/activate` with `{ node_id: string }` body
- **Changed:** `POST /api/nodes/{nodeId}/blackout/deactivate`
- **To:** `POST /api/blackout/deactivate` with `{ node_id: string }` body
- **Reason:** Backend implements global blackout endpoints, not node-specific routes

### 4. **State Management Architecture**
- **Changed:** Zustand stores detections and nodes
- **To:** React Query is source of truth for server state
- **Reason:** Reduces duplication, leverages React Query caching
- **Note:** Zustand now only manages UI state (selected detection, connection status)

### 5. **React Query v5 Compatibility**
- **Removed:** `onSuccess` callback (deprecated in v5)
- **Changed:** Direct data access via hook return values
- **Updated:** `invalidateQueries` syntax to use object form

### 6. **WebSocket Message Handling**
- **Changed:** Direct state updates via `addDetection()`, `updateNode()`
- **To:** Cache invalidation: `queryClient.invalidateQueries()`
- **Reason:** Maintains single source of truth, prevents stale data

### 7. **Leaflet Integration Notes**
- **Added:** CSS import requirement in main.tsx
- **Added:** Marker icon fix for Vite bundler
- **Reason:** Common Leaflet + Vite pitfalls

### Backend API Contract Verified ✅
All TypeScript types now match actual backend schemas:
- `DetectionResponse` includes full detection objects (not just counts)
- `node_id` is string type (not integer) throughout
- WebSocket message format: `{ type: string, data: object }`

---

## Claude Code Implementation Prompts

### Session 1: Project Setup + Base Components

```
Create Module 4 (Operator Dashboard) for Sentinel v2 Arctic surveillance system.

REQUIREMENTS:
- React 18 + TypeScript
- Vite build tool
- Tailwind CSS with tactical dark theme
- Component-driven architecture

STEP 1: Project Setup
1. Create Vite React TypeScript project
2. Install all dependencies from package.json
3. Configure Tailwind with tactical theme colors
4. Set up path aliases (@/ for src/)
5. Create .env.example

STEP 2: TypeScript Types
1. Create src/lib/types.ts with all interfaces
2. Ensure strict type checking

STEP 3: Base UI Components (shadcn/ui)
1. Install shadcn/ui CLI
2. Add components: button, card, badge, table, dialog, alert
3. Customize theme colors for tactical aesthetic

Success criteria:
- Project builds without errors
- Tailwind tactical theme applied
- All base components available
```

### Session 2: State Management + API Integration

```
Continue Module 4 - Add state management and API client.

STEP 4: Zustand Store
1. Create src/store/useStore.ts
2. Implement all state slices (detections, nodes, filters, websocket)
3. Add type-safe actions

STEP 5: API Client
1. Create src/lib/api.ts with axios
2. Add interceptors for logging and error handling
3. Configure base URL from env

STEP 6: Custom Hooks
1. Create useWebSocket hook with reconnection logic
2. Create useDetections hook with React Query
3. Create useNodes hook with mutations
4. Create useFilters hook for filter state

Success criteria:
- State management working
- API client configured
- Custom hooks tested
```

### Session 3: Core Components

```
Continue Module 4 - Build main UI components.

STEP 7: TacticalMap Component
1. Install leaflet and react-leaflet
2. Create TacticalMap component with Arctic center
3. Add DetectionMarker and NodeMarker components
4. Implement click handlers and selection

STEP 8: DetectionList Component
1. Create sortable table component
2. Add filtering controls
3. Implement pagination
4. Add row selection

STEP 9: NodeStatusPanel Component
1. Create node status cards
2. Add status badges with colors
3. Display last heartbeat and detection count

Success criteria:
- Map renders with Arctic center
- Detection list shows data
- Node status displays correctly
```

### Session 4: Advanced Features + Integration

```
Finalize Module 4 - Add blackout controls and real-time features.

STEP 10: BlackoutControl Component
1. Create blackout activation UI
2. Add confirmation dialog
3. Implement timer display
4. Show queued detection count

STEP 11: AlertPanel Component
1. Create high-confidence detection alerts
2. Add visual and audio notifications
3. Implement acknowledge functionality

STEP 12: WebSocket Integration
1. Connect useWebSocket hook to all components
2. Test real-time updates
3. Add connection status indicator

STEP 13: App Integration
1. Create main App.tsx layout
2. Wire all components together
3. Test full operator workflow

Success criteria:
- Blackout mode functional
- Alerts display correctly
- WebSocket updates work
- Full app integrated
```

### Session 5: Testing + Documentation

```
Finalize Module 4 - Add tests and documentation.

STEP 14: Unit Tests
1. Add Vitest configuration
2. Write component tests for:
   - DetectionList
   - NodeStatusPanel
   - BlackoutControl
3. Test custom hooks

STEP 15: E2E Tests
1. Configure Playwright
2. Write operator workflow tests
3. Test WebSocket scenarios

STEP 16: Documentation
1. Create comprehensive README.md
2. Add component documentation
3. Include setup instructions
4. Add deployment guide

Success criteria:
- All unit tests pass
- E2E tests cover main workflows
- README complete
- Deployment guide included
```

---

## Success Criteria

**Must Have:**
- ✅ Tactical dark theme applied
- ✅ Map displays detections and nodes
- ✅ Detection list with filtering
- ✅ Node status panel functional
- ✅ WebSocket real-time updates
- ✅ Blackout control working

**Should Have:**
- ✅ Type-safe throughout
- ✅ Component tests (>70% coverage)
- ✅ E2E tests for main workflows
- ✅ Responsive design
- ✅ Loading states and error handling

**Nice to Have:**
- ✅ Alert notifications
- ✅ Export to CSV functionality
- ✅ Keyboard shortcuts
- ✅ Accessibility (ARIA labels)

---

## Deployment

**Development:**
```bash
npm run dev
```

**Production Build:**
```bash
npm run build
npm run preview
```

**Deploy to Vercel:**
```bash
vercel --prod
```

**Environment Variables (Vercel):**
- `VITE_API_URL`: Backend API URL
- `VITE_WS_URL`: WebSocket URL

---

## Next Steps After Module 4

Once Module 4 is complete:
1. Integration test: Full flow from edge → backend → dashboard
2. Deploy all modules together
3. Create demo video showing operator workflow
4. Document system architecture
5. Prepare for job applications

**End of Module 4 Specification**
