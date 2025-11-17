// src/App.tsx

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TacticalMap } from '@/components/TacticalMap';
import { DetectionList } from '@/components/DetectionList';
import { NodeStatusPanel } from '@/components/NodeStatusPanel';
import { ConnectionStatus } from '@/components/ConnectionStatus';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useDetections } from '@/hooks/useDetections';
import { useNodes } from '@/hooks/useNodes';
import { useStore } from '@/store/useStore';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    },
  },
});

function DashboardContent() {
  // WebSocket connection for real-time updates
  useWebSocket();

  // Fetch server state via React Query
  const { data: detections = [], isLoading: detectionsLoading } = useDetections();
  const { data: nodes = [], isLoading: nodesLoading, activateBlackout, deactivateBlackout } = useNodes();

  // UI state from Zustand
  const { selectedDetection, setSelectedDetection, isConnected } = useStore();

  if (detectionsLoading || nodesLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-tactical-bg text-tactical-text">
        <div className="text-center">
          <div className="text-xl font-semibold mb-2">Loading Sentinel Dashboard...</div>
          <div className="text-sm text-tactical-textMuted">Connecting to backend</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-tactical-bg text-tactical-text">
      {/* Header */}
      <header className="bg-tactical-surface border-b border-tactical-border p-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Sentinel - Operator Dashboard</h1>
          <ConnectionStatus isConnected={isConnected} />
        </div>
      </header>

      {/* Main Content */}
      <div className="flex h-[calc(100vh-73px)]">
        {/* Left Panel - Map */}
        <div className="flex-1">
          <TacticalMap
            detections={detections}
            nodes={nodes}
            selectedDetection={selectedDetection}
            onDetectionClick={setSelectedDetection}
          />
        </div>

        {/* Right Panel - Lists and Controls */}
        <div className="w-[500px] border-l border-tactical-border flex flex-col">
          {/* Node Status */}
          <div className="border-b border-tactical-border p-4">
            <h2 className="text-lg font-semibold mb-4">Edge Nodes</h2>
            <NodeStatusPanel
              nodes={nodes}
              onActivateBlackout={async (nodeId: string, reason?: string) => {
                activateBlackout(nodeId, reason);
              }}
              onDeactivateBlackout={async (nodeId: string) => {
                deactivateBlackout(nodeId);
              }}
            />
          </div>

          {/* Detection List */}
          <div className="flex-1 overflow-hidden">
            <DetectionList
              detections={detections}
              onDetectionClick={setSelectedDetection}
              selectedDetection={selectedDetection}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <DashboardContent />
    </QueryClientProvider>
  );
}
