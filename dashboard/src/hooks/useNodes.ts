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
