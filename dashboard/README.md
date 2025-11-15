# Sentinel v2 - Operator Dashboard

**Purpose:** Tactical command & control interface for real-time Arctic surveillance operations
**Version:** 2.0.0
**Technology:** React 18 + TypeScript + Vite + Tailwind CSS

---

## Features

### Core Capabilities (MVP)
- **Real-time Detection Monitoring**: Live updates via WebSocket with <1s latency
- **Tactical Map Visualization**: Leaflet-based map centered on Arctic (70°N, -100°W)
- **Node Status Tracking**: Real-time health monitoring of all edge nodes
- **Detection List**: Sortable, filterable table of all detections
- **Blackout Mode Control**: Activate/deactivate covert operations mode
- **Connection Status**: WebSocket connection indicator with auto-reconnection

### Technical Architecture
- **State Management**:
  - React Query v5 for server state (detections, nodes)
  - Zustand for UI state (selected detection, connection status)
- **Real-time Updates**: WebSocket with cache invalidation pattern
- **Styling**: Tailwind CSS with tactical dark theme
- **Type Safety**: Full TypeScript coverage

---

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

Create a `.env` file (or copy from `.env.example`):

```bash
VITE_API_URL=http://localhost:8001
VITE_WS_URL=ws://localhost:8001/ws
```

### 3. Start Development Server

```bash
npm run dev
```

The dashboard will be available at `http://localhost:3000`

### 4. Build for Production

```bash
npm run build
npm run preview
```

---

## Project Structure

```
dashboard/
├── src/
│   ├── components/         # React components
│   ├── hooks/              # Custom React hooks
│   ├── lib/                # Utilities and types
│   ├── store/              # Global state (Zustand)
│   ├── App.tsx             # Main application
│   └── main.tsx            # Entry point
├── package.json
├── vite.config.ts
└── tailwind.config.js
```

---

## Key Implementation Details

### WebSocket Connection

The dashboard connects with a unique `client_id` (required by backend):

```typescript
const WS_URL = `ws://localhost:8001/ws?client_id=${crypto.randomUUID()}`;
```

### Node Status Values

Backend uses `'covert'` (not `'blackout'`) for blackout mode:

```typescript
type NodeStatus = 'online' | 'offline' | 'covert';
```

### Blackout API Endpoints

- **Activate**: `POST /api/blackout/activate` with `{ node_id: string }`
- **Deactivate**: `POST /api/blackout/deactivate` with `{ node_id: string }`

---

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server (port 3000) |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |
| `npm run type-check` | Check TypeScript types |

---

## Troubleshooting

### Map not rendering
Ensure Leaflet CSS is imported in `main.tsx` (already configured).

### WebSocket not connecting
1. Verify backend is running on `http://localhost:8001`
2. Check `.env` file configuration
3. Check browser console for errors

### Build errors
Run type checking first: `npm run type-check`

---

**Last Updated:** 2025-11-14
**Module:** 4 - Operator Dashboard
**Status:** MVP Complete
