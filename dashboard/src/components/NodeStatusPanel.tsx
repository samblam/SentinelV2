// src/components/NodeStatusPanel.tsx

import { Server, Circle } from 'lucide-react';
import { Node } from '@/lib/types';
import { cn } from '@/lib/utils';
import { BlackoutControl } from './BlackoutControl';

interface NodeStatusPanelProps {
  nodes: Node[];
  onActivateBlackout?: (nodeId: string, reason?: string) => Promise<void>;
  onDeactivateBlackout?: (nodeId: string) => Promise<void>;
}

export function NodeStatusPanel({ nodes, onActivateBlackout, onDeactivateBlackout }: NodeStatusPanelProps) {
  const getStatusColor = (status: 'online' | 'offline' | 'covert' | 'resuming') => {
    switch (status) {
      case 'online':
        return 'text-status-online';
      case 'offline':
        return 'text-status-offline';
      case 'covert':
        return 'text-status-covert';
      case 'resuming':
        return 'text-yellow-500';
      default:
        return 'text-tactical-textMuted';
    }
  };

  const getStatusBgColor = (status: 'online' | 'offline' | 'covert' | 'resuming') => {
    switch (status) {
      case 'online':
        return 'bg-status-online';
      case 'offline':
        return 'bg-status-offline';
      case 'covert':
        return 'bg-status-covert';
      case 'resuming':
        return 'bg-yellow-500';
      default:
        return 'bg-tactical-textMuted';
    }
  };

  const getStatusLabel = (status: 'online' | 'offline' | 'covert' | 'resuming') => {
    switch (status) {
      case 'online':
        return 'ONLINE';
      case 'offline':
        return 'OFFLINE';
      case 'covert':
        return 'COVERT';
      case 'resuming':
        return 'RESUMING';
      default:
        return 'UNKNOWN';
    }
  };

  if (nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-tactical-textMuted">
        No nodes available
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {nodes.map((node) => (
        <div
          key={node.id}
          className="bg-tactical-surface border border-tactical-border rounded-lg p-3"
        >
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <div className="mt-1">
                <Server className={cn('w-5 h-5', getStatusColor(node.status))} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-mono font-semibold text-sm">
                    {node.node_id}
                  </span>
                  <div className="flex items-center gap-1">
                    <Circle
                      className={cn('w-2 h-2 fill-current', getStatusColor(node.status))}
                    />
                    <span className={cn('text-xs font-medium uppercase', getStatusColor(node.status))}>
                      {getStatusLabel(node.status)}
                    </span>
                  </div>
                </div>
                {node.last_heartbeat && (
                  <div className="text-xs text-tactical-textMuted">
                    Last seen: {new Date(node.last_heartbeat).toLocaleString()}
                  </div>
                )}
              </div>
            </div>

            {/* Blackout Control (Module 5) */}
            {onActivateBlackout && onDeactivateBlackout && (
              <BlackoutControl
                node={node}
                onActivate={onActivateBlackout}
                onDeactivate={onDeactivateBlackout}
              />
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
