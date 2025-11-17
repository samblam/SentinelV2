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
      const nodes = response.data;

      // Fetch blackout status for each node in covert mode (Module 5)
      const nodesWithStatus = await Promise.all(
        nodes.map(async (node) => {
          if (node.status === 'covert') {
            try {
              const statusResponse = await api.get(`/api/nodes/${node.node_id}/blackout/status`);
              return {
                ...node,
                blackout_status: statusResponse.data,
              };
            } catch (error) {
              console.error(`Failed to fetch blackout status for ${node.node_id}:`, error);
              return node;
            }
          }
          return node;
        })
      );

      return nodesWithStatus;
    },
    refetchInterval: 5000, // Refetch every 5s for live updates
    staleTime: 2000, // Consider data stale after 2s
  });

  const activateBlackout = useMutation({
    mutationFn: async ({ nodeId, reason }: { nodeId: string; reason?: string }) => {
      // Use node-specific endpoint (Module 5)
      await api.post(`/api/nodes/${nodeId}/blackout/activate`, { reason });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['nodes'] });
    },
  });

  const deactivateBlackout = useMutation({
    mutationFn: async (nodeId: string) => {
      // Use node-specific endpoint (Module 5)
      await api.post(`/api/nodes/${nodeId}/blackout/deactivate`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['nodes'] });
    },
  });

  return {
    ...query,
    activateBlackout: (nodeId: string, reason?: string) =>
      activateBlackout.mutate({ nodeId, reason }),
    deactivateBlackout: deactivateBlackout.mutate,
  };
}
