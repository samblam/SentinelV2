// Test utilities for React component testing
import { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Detection, Node, ObjectDetection } from '@/lib/types';

// Create a new QueryClient for each test
export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
      },
    },
  });
}

// Custom render function with providers
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  queryClient?: QueryClient;
}

export function renderWithProviders(
  ui: ReactElement,
  options?: CustomRenderOptions
) {
  const { queryClient = createTestQueryClient(), ...renderOptions } = options || {};

  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions });
}

// Mock data factories
export function createMockDetection(overrides?: Partial<Detection>): Detection {
  const mockObjectDetection: ObjectDetection = {
    bbox: { xmin: 100, ymin: 150, xmax: 300, ymax: 400 },
    class: 'person',
    confidence: 0.89,
    class_id: 0,
  };

  return {
    id: 1,
    node_id: 'test-node-01',
    timestamp: new Date().toISOString(),
    latitude: 70.5234,
    longitude: -100.8765,
    altitude_m: 45.2,
    accuracy_m: 10.0,
    detections: [mockObjectDetection],
    detection_count: 1,
    inference_time_ms: 87.3,
    model: 'yolov5n',
    ...overrides,
  };
}

export function createMockNode(overrides?: Partial<Node>): Node {
  return {
    id: 1,
    node_id: 'test-node-01',
    status: 'online',
    last_heartbeat: new Date().toISOString(),
    created_at: new Date().toISOString(),
    ...overrides,
  };
}

export function createMockWebSocket() {
  return {
    send: vi.fn(),
    close: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    readyState: WebSocket.OPEN,
  };
}

// Export everything from @testing-library/react
export * from '@testing-library/react';
export { default as userEvent } from '@testing-library/user-event';
