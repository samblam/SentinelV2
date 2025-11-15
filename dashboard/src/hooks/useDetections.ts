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
