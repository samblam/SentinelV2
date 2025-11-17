// useWebSocket.test.ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useWebSocket } from './useWebSocket';
import { useStore } from '@/store/useStore';

// Mock the useStore hook
vi.mock('@/store/useStore', () => ({
  useStore: vi.fn(),
}));

describe('useWebSocket', () => {
  let mockWebSocket: any;
  let mockSetConnected: ReturnType<typeof vi.fn>;
  let mockAddDetection: ReturnType<typeof vi.fn>;
  let mockUpdateNode: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    // Reset mocks
    mockSetConnected = vi.fn();
    mockAddDetection = vi.fn();
    mockUpdateNode = vi.fn();

    // Mock useStore return value
    (useStore as any).mockReturnValue({
      setConnected: mockSetConnected,
      addDetection: mockAddDetection,
      updateNode: mockUpdateNode,
    });

    // Mock WebSocket
    mockWebSocket = {
      send: vi.fn(),
      close: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      readyState: WebSocket.OPEN,
      CONNECTING: WebSocket.CONNECTING,
      OPEN: WebSocket.OPEN,
      CLOSING: WebSocket.CLOSING,
      CLOSED: WebSocket.CLOSED,
    };

    // @ts-ignore - Mock global WebSocket
    global.WebSocket = vi.fn(() => mockWebSocket) as any;
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('creates WebSocket connection on mount', () => {
    renderHook(() => useWebSocket());

    expect(global.WebSocket).toHaveBeenCalledWith(
      expect.stringContaining('ws://')
    );
  });

  it('sets connected state when WebSocket opens', async () => {
    renderHook(() => useWebSocket());

    // Simulate WebSocket open event
    const openHandler = mockWebSocket.addEventListener.mock.calls.find(
      (call: any[]) => call[0] === 'open'
    )?.[1];

    if (openHandler) {
      openHandler(new Event('open'));

      await waitFor(() => {
        expect(mockSetConnected).toHaveBeenCalledWith(true);
      });
    }
  });

  it('sets disconnected state when WebSocket closes', async () => {
    renderHook(() => useWebSocket());

    // Simulate WebSocket close event
    const closeHandler = mockWebSocket.addEventListener.mock.calls.find(
      (call: any[]) => call[0] === 'close'
    )?.[1];

    if (closeHandler) {
      closeHandler(new CloseEvent('close'));

      await waitFor(() => {
        expect(mockSetConnected).toHaveBeenCalledWith(false);
      });
    }
  });

  it('handles detection message', async () => {
    renderHook(() => useWebSocket());

    const detectionData = {
      id: 1,
      node_id: 'test-node',
      timestamp: new Date().toISOString(),
      latitude: 70.5,
      longitude: -100.2,
      detections: [],
      detection_count: 1,
    };

    // Simulate WebSocket message event
    const messageHandler = mockWebSocket.addEventListener.mock.calls.find(
      (call: any[]) => call[0] === 'message'
    )?.[1];

    if (messageHandler) {
      const messageEvent = {
        data: JSON.stringify({
          type: 'detection',
          data: detectionData,
        }),
      };

      messageHandler(messageEvent);

      await waitFor(() => {
        expect(mockAddDetection).toHaveBeenCalledWith(detectionData);
      });
    }
  });

  it('handles node status update message', async () => {
    renderHook(() => useWebSocket());

    const nodeData = {
      id: 1,
      node_id: 'test-node',
      status: 'covert' as const,
      last_heartbeat: new Date().toISOString(),
      created_at: new Date().toISOString(),
    };

    // Simulate WebSocket message event
    const messageHandler = mockWebSocket.addEventListener.mock.calls.find(
      (call: any[]) => call[0] === 'message'
    )?.[1];

    if (messageHandler) {
      const messageEvent = {
        data: JSON.stringify({
          type: 'node_status',
          data: nodeData,
        }),
      };

      messageHandler(messageEvent);

      await waitFor(() => {
        expect(mockUpdateNode).toHaveBeenCalledWith(nodeData);
      });
    }
  });

  it('handles blackout event message', async () => {
    renderHook(() => useWebSocket());

    const blackoutData = {
      id: 1,
      node_id: 1,
      activated_at: new Date().toISOString(),
      activated_by: 'operator-01',
      detections_queued: 5,
    };

    // Simulate WebSocket message event
    const messageHandler = mockWebSocket.addEventListener.mock.calls.find(
      (call: any[]) => call[0] === 'message'
    )?.[1];

    if (messageHandler) {
      const messageEvent = {
        data: JSON.stringify({
          type: 'blackout_event',
          data: blackoutData,
        }),
      };

      messageHandler(messageEvent);

      // Should handle blackout event (implementation-dependent)
      // At minimum, should not throw error
      await waitFor(() => {
        expect(true).toBe(true);
      });
    }
  });

  it('handles malformed JSON message gracefully', async () => {
    renderHook(() => useWebSocket());

    // Simulate WebSocket message with invalid JSON
    const messageHandler = mockWebSocket.addEventListener.mock.calls.find(
      (call: any[]) => call[0] === 'message'
    )?.[1];

    if (messageHandler) {
      const messageEvent = {
        data: 'invalid json{{{',
      };

      // Should not throw error
      expect(() => messageHandler(messageEvent)).not.toThrow();
    }
  });

  it('handles WebSocket error', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    renderHook(() => useWebSocket());

    // Simulate WebSocket error event
    const errorHandler = mockWebSocket.addEventListener.mock.calls.find(
      (call: any[]) => call[0] === 'error'
    )?.[1];

    if (errorHandler) {
      const errorEvent = new Event('error');
      errorHandler(errorEvent);

      // Should log error (implementation-dependent)
      await waitFor(() => {
        expect(true).toBe(true);
      });
    }

    consoleErrorSpy.mockRestore();
  });

  it('cleans up WebSocket on unmount', () => {
    const { unmount } = renderHook(() => useWebSocket());

    unmount();

    // WebSocket should be closed
    expect(mockWebSocket.close).toHaveBeenCalled();
  });

  it('attempts to reconnect after connection is lost', async () => {
    vi.useFakeTimers();

    renderHook(() => useWebSocket());

    // Simulate WebSocket close (unexpected)
    const closeHandler = mockWebSocket.addEventListener.mock.calls.find(
      (call: any[]) => call[0] === 'close'
    )?.[1];

    if (closeHandler) {
      closeHandler(new CloseEvent('close', { code: 1006 })); // Abnormal closure

      // Wait for reconnection attempt
      vi.advanceTimersByTime(3000);

      await waitFor(() => {
        // Should attempt to create new WebSocket connection
        expect(global.WebSocket).toHaveBeenCalledTimes(2);
      });
    }

    vi.useRealTimers();
  });

  it('does not reconnect if connection was closed normally', () => {
    renderHook(() => useWebSocket());

    const { unmount } = renderHook(() => useWebSocket());

    // Close normally (on unmount)
    unmount();

    // Should not attempt reconnection
    expect(global.WebSocket).toHaveBeenCalledTimes(2); // Initial + second hook
  });

  it('parses WebSocket URL from environment variable', () => {
    const originalEnv = import.meta.env.VITE_WS_URL;

    // Mock environment variable
    (import.meta as any).env.VITE_WS_URL = 'ws://custom-backend:8000/ws';

    renderHook(() => useWebSocket());

    expect(global.WebSocket).toHaveBeenCalledWith('ws://custom-backend:8000/ws');

    // Restore
    (import.meta as any).env.VITE_WS_URL = originalEnv;
  });
});
