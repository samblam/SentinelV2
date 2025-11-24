// Integration test setup - Mock API server using MSW
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { afterAll, afterEach, beforeAll } from 'vitest';
import type { Detection, Node } from '@/lib/types';

// Mock data
export const mockDetections: Detection[] = [
  {
    id: 1,
    node_id: 'sentry-01',
    timestamp: '2025-11-19T10:00:00Z',
    latitude: 70.5,
    longitude: -100.2,
    detection_count: 2,
    detections: [
      {
        bbox: { xmin: 100, ymin: 150, xmax: 300, ymax: 400 },
        class: 'person',
        confidence: 0.95,
        class_id: 0,
      },
      {
        bbox: { xmin: 350, ymin: 200, xmax: 500, ymax: 450 },
        class: 'vehicle',
        confidence: 0.88,
        class_id: 2,
      },
    ],
    inference_time_ms: 87.5,
    model: 'yolov5n',
  },
  {
    id: 2,
    node_id: 'aerostat-01',
    timestamp: '2025-11-19T11:00:00Z',
    latitude: 71.0,
    longitude: -101.0,
    detection_count: 1,
    detections: [
      {
        bbox: { xmin: 50, ymin: 60, xmax: 150, ymax: 200 },
        class: 'vehicle',
        confidence: 0.78,
        class_id: 2,
      },
    ],
    inference_time_ms: 92.3,
    model: 'yolov5n',
  },
];

export const mockNodes: Node[] = [
  {
    id: 1,
    node_id: 'sentry-01',
    status: 'online',
    last_heartbeat: '2025-11-19T12:00:00Z',
    created_at: '2025-11-19T08:00:00Z',
  },
  {
    id: 2,
    node_id: 'aerostat-01',
    status: 'online',
    last_heartbeat: '2025-11-19T12:00:00Z',
    created_at: '2025-11-19T08:00:00Z',
  },
];

// API handlers
export const handlers = [
  // Get detections
  http.get('*/api/detections', () => {
    return HttpResponse.json(mockDetections);
  }),

  // Get nodes
  http.get('*/api/nodes', () => {
    return HttpResponse.json(mockNodes);
  }),

  // Activate blackout (node-specific endpoint)
  http.post('*/api/nodes/:nodeId/blackout/activate', async ({ params }) => {
    const { nodeId } = params;
    return HttpResponse.json({
      status: 'activated',
      node_id: nodeId,
      blackout_id: 1,
      activated_at: new Date().toISOString(),
    });
  }),

  // Deactivate blackout (node-specific endpoint)
  http.post('*/api/nodes/:nodeId/blackout/deactivate', async ({ params }) => {
    const { nodeId } = params;
    return HttpResponse.json({
      status: 'deactivated',
      node_id: nodeId,
      blackout_id: 1,
      activated_at: new Date(Date.now() - 3600000).toISOString(),
      deactivated_at: new Date().toISOString(),
      duration_seconds: 3600,
      detections_queued: 0,
      detections_transmitted: 0,
    });
  }),
];

// Setup MSW server
export const server = setupServer(...handlers);

// Establish API mocking before all tests
beforeAll(() => {
  server.listen({ onUnhandledRequest: 'warn' });
});

// Reset handlers after each test
afterEach(() => {
  server.resetHandlers();
});

// Clean up after all tests
afterAll(() => {
  server.close();
});
