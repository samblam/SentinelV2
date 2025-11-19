// src/hooks/useWebSocket.ts

import { useEffect, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useStore } from '@/store/useStore';
import type { WebSocketMessage } from '@/lib/types';

// Generate unique client ID for WebSocket connection (required by backend)
const CLIENT_ID = crypto.randomUUID();

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttempts = useRef(0);

  const queryClient = useQueryClient();
  const { setIsConnected } = useStore();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8001/ws';
    const WS_URL = `${WS_BASE_URL}?client_id=${CLIENT_ID}`;

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
