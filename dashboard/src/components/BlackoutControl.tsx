// dashboard/src/components/BlackoutControl.tsx

import { useState, useEffect } from 'react';
import { Node } from '@/lib/types';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, Eye, EyeOff, Timer } from 'lucide-react';

interface BlackoutControlProps {
  node: Node;
  onActivate: (nodeId: string, reason?: string) => Promise<void>;
  onDeactivate: (nodeId: string) => Promise<void>;
}

export function BlackoutControl({ node, onActivate, onDeactivate }: BlackoutControlProps) {
  const [showDialog, setShowDialog] = useState(false);
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [duration, setDuration] = useState('');

  // Calculate duration from activated_at
  useEffect(() => {
    if (node.status === 'covert' && node.blackout_status?.activated_at) {
      const updateDuration = () => {
        const activatedAt = new Date(node.blackout_status!.activated_at!);
        const now = new Date();
        const diffMs = now.getTime() - activatedAt.getTime();
        const diffSec = Math.floor(diffMs / 1000);

        const hours = Math.floor(diffSec / 3600);
        const minutes = Math.floor((diffSec % 3600) / 60);
        const seconds = diffSec % 60;

        if (hours > 0) {
          setDuration(`${hours}h ${minutes}m ${seconds}s`);
        } else if (minutes > 0) {
          setDuration(`${minutes}m ${seconds}s`);
        } else {
          setDuration(`${seconds}s`);
        }
      };

      updateDuration();
      const interval = setInterval(updateDuration, 1000);
      return () => clearInterval(interval);
    } else {
      setDuration('');
    }
  }, [node.status, node.blackout_status?.activated_at]);

  const handleActivate = async () => {
    setLoading(true);
    try {
      await onActivate(node.node_id, reason || undefined);
      setShowDialog(false);
      setReason('');
    } finally {
      setLoading(false);
    }
  };

  const handleDeactivate = async () => {
    setLoading(true);
    try {
      await onDeactivate(node.node_id);
    } finally {
      setLoading(false);
    }
  };

  // In blackout mode (covert status)
  if (node.status === 'covert') {
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="bg-blue-500/10 text-blue-500 border-blue-500/30">
            <EyeOff className="w-3 h-3 mr-1" />
            COVERT OPS
          </Badge>
        </div>

        <div className="space-y-2 text-sm">
          <div className="flex items-center gap-2 text-tactical-textMuted">
            <Timer className="w-4 h-4" />
            <span>Duration: {duration || '0s'}</span>
          </div>

          <div className="flex items-center gap-2 text-tactical-textMuted">
            <Eye className="w-4 h-4" />
            <span>Detections queued: {node.blackout_status?.detections_queued || 0}</span>
          </div>

          {node.blackout_status?.reason && (
            <div className="text-xs text-tactical-textMuted mt-2 p-2 bg-tactical-bg rounded border border-tactical-border">
              <span className="font-semibold">Reason:</span> {node.blackout_status.reason}
            </div>
          )}
        </div>

        <Button
          onClick={handleDeactivate}
          disabled={loading}
          className="w-full"
          variant="outline"
        >
          {loading ? 'Resuming...' : 'Resume Transmission'}
        </Button>
      </div>
    );
  }

  // Resuming state (burst transmission in progress)
  if (node.status === 'resuming') {
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="bg-yellow-500/10 text-yellow-500 border-yellow-500/30 animate-pulse">
            <Eye className="w-3 h-3 mr-1" />
            RESUMING
          </Badge>
        </div>

        <div className="text-sm text-tactical-textMuted">
          <span>Transmitting queued detections...</span>
        </div>
      </div>
    );
  }

  // Normal mode - show activation button
  return (
    <>
      <Button
        onClick={() => setShowDialog(true)}
        disabled={node.status !== 'online' || loading}
        variant="outline"
        className="w-full"
      >
        <EyeOff className="w-4 h-4 mr-2" />
        Activate Blackout
      </Button>

      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-yellow-500" />
              Activate Blackout Mode
            </DialogTitle>
            <DialogDescription>
              Node {node.node_id} will appear offline while continuing covert surveillance.
              All detections will be queued locally until you resume transmission.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">
                Tactical Justification (Optional)
              </label>
              <Textarea
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Reason for activating blackout mode..."
                className="mt-2"
                rows={4}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleActivate} disabled={loading}>
              {loading ? 'Activating...' : 'Activate Blackout'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
