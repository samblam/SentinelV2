// Integration test helpers
import { render, type RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { type ReactElement, type ReactNode } from 'react';
import type { Detection, Node } from '@/lib/types';
import { vi } from 'vitest';

// Create a fresh QueryClient for each test
export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false, // Disable retries in tests
        gcTime: 0, // Disable caching
      },
      mutations: {
        retry: false,
      },
    },
  });
}

// Wrapper with all providers
interface IntegrationWrapperProps {
  children: ReactNode;
  queryClient?: QueryClient;
}

function IntegrationWrapper({ children, queryClient }: IntegrationWrapperProps) {
  const client = queryClient || createTestQueryClient();

  return (
    <QueryClientProvider client={client}>
      {children}
    </QueryClientProvider>
  );
}

// Render with all providers
export function renderWithIntegrationProviders(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'> & { queryClient?: QueryClient }
) {
  const { queryClient, ...renderOptions } = options || {};

  return render(ui, {
    wrapper: ({ children }) => (
      <IntegrationWrapper queryClient={queryClient}>
        {children}
      </IntegrationWrapper>
    ),
    ...renderOptions,
  });
}

// Mock WebSocket class for integration tests
export class MockWebSocket {
  static instances: MockWebSocket[] = [];
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  url: string;
  readyState: number = MockWebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);

    // Simulate connection opening
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 10);
  }

  send(_data: string) {
    // Mock send - do nothing
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close'));
    }
  }

  // Helper to simulate receiving a message
  static simulateMessage(message: any) {
    MockWebSocket.instances.forEach((ws) => {
      if (ws.readyState === MockWebSocket.OPEN && ws.onmessage) {
        ws.onmessage(
          new MessageEvent('message', {
            data: JSON.stringify(message),
          })
        );
      }
    });
  }

  // Helper to clear all instances
  static clearInstances() {
    MockWebSocket.instances = [];
  }
}

// Setup global WebSocket mock
export function setupWebSocketMock() {
  vi.stubGlobal('WebSocket', MockWebSocket);
}

// Cleanup WebSocket mock
export function cleanupWebSocketMock() {
  MockWebSocket.clearInstances();
  vi.unstubAllGlobals();
}

// Helper to create mock detection
export function createMockDetection(overrides?: Partial<Detection>): Detection {
  return {
    id: 1,
    node_id: 'test-node',
    timestamp: new Date().toISOString(),
    latitude: 70.0,
    longitude: -100.0,
    detection_count: 1,
    detections: [
      {
        bbox: { xmin: 0, ymin: 0, xmax: 100, ymax: 100 },
        class: 'person',
        confidence: 0.9,
        class_id: 0,
      },
    ],
    inference_time_ms: 50.0,
    model: 'yolov5n',
    ...overrides,
  };
}

// Helper to create mock node
export function createMockNode(overrides?: Partial<Node>): Node {
  return {
    id: 1,
    node_id: 'test-node',
    status: 'online',
    last_heartbeat: new Date().toISOString(),
    created_at: new Date().toISOString(),
    ...overrides,
  };
}

// Wait for async updates
export const waitForAsync = () =>
  new Promise((resolve) => setTimeout(resolve, 0));

// Wait for multiple ticks
export const waitForTicks = (ticks: number = 1) =>
  new Promise((resolve) => setTimeout(resolve, ticks * 10));
