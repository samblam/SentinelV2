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
