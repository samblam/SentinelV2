// dashboard/src/components/AlertPanel.tsx

import { useState, useEffect, useMemo } from 'react';
import { AlertTriangle, Bell, BellOff, X, Volume2, VolumeX } from 'lucide-react';
import { Detection } from '@/lib/types';
import { cn } from '@/lib/utils';

interface AlertPanelProps {
  detections: Detection[];
  confidenceThreshold?: number;
}

interface Alert {
  id: string;
  detection: Detection;
  acknowledged: boolean;
  timestamp: Date;
}

export function AlertPanel({ detections, confidenceThreshold = 0.85 }: AlertPanelProps) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [panelVisible, setPanelVisible] = useState(true);
  const [lastAlertSound, setLastAlertSound] = useState<number>(0);

  // Filter high-confidence detections
  const highConfidenceDetections = useMemo(() => {
    return detections.filter((detection) => {
      const maxConfidence = Math.max(
        ...detection.detections.map((d) => d.confidence),
        0
      );
      return maxConfidence >= confidenceThreshold;
    });
  }, [detections, confidenceThreshold]);

  // Create alerts from new high-confidence detections
  useEffect(() => {
    const existingIds = new Set(alerts.map((a) => `${a.detection.id}`));

    const newAlerts = highConfidenceDetections
      .filter((detection) => !existingIds.has(`${detection.id}`))
      .map((detection) => ({
        id: `${detection.id}-${detection.timestamp}`,
        detection,
        acknowledged: false,
        timestamp: new Date(),
      }));

    if (newAlerts.length > 0) {
      setAlerts((prev) => [...newAlerts, ...prev].slice(0, 50)); // Keep max 50 alerts

      // Play sound for new alerts (with debounce)
      const now = Date.now();
      if (soundEnabled && now - lastAlertSound > 2000) {
        playAlertSound();
        setLastAlertSound(now);
      }
    }
  }, [highConfidenceDetections, alerts, soundEnabled, lastAlertSound]);

  const playAlertSound = () => {
    // Create a simple beep sound using Web Audio API
    try {
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);

      oscillator.frequency.value = 800;
      oscillator.type = 'sine';

      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.5);
    } catch (error) {
      console.warn('Failed to play alert sound:', error);
    }
  };

  const acknowledgeAlert = (alertId: string) => {
    setAlerts((prev) =>
      prev.map((alert) =>
        alert.id === alertId ? { ...alert, acknowledged: true } : alert
      )
    );
  };

  const dismissAlert = (alertId: string) => {
    setAlerts((prev) => prev.filter((alert) => alert.id !== alertId));
  };

  const acknowledgeAll = () => {
    setAlerts((prev) => prev.map((alert) => ({ ...alert, acknowledged: true })));
  };

  const dismissAll = () => {
    setAlerts([]);
  };

  const unacknowledgedCount = alerts.filter((a) => !a.acknowledged).length;

  if (!panelVisible) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <button
          onClick={() => setPanelVisible(true)}
          className={cn(
            'bg-tactical-surface border border-tactical-border rounded-lg px-4 py-3',
            'shadow-lg hover:bg-tactical-bg transition-colors',
            unacknowledgedCount > 0 && 'border-red-500'
          )}
        >
          <div className="flex items-center gap-2">
            <Bell className={cn('h-5 w-5', unacknowledgedCount > 0 && 'text-red-500')} />
            {unacknowledgedCount > 0 && (
              <span className="bg-red-500 text-white text-xs font-bold rounded-full px-2 py-0.5">
                {unacknowledgedCount}
              </span>
            )}
          </div>
        </button>
      </div>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 w-96 bg-tactical-surface border border-tactical-border rounded-lg shadow-2xl z-50 max-h-[600px] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-tactical-border">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-yellow-500" />
          <h3 className="font-semibold">High-Confidence Alerts</h3>
          {unacknowledgedCount > 0 && (
            <span className="bg-red-500 text-white text-xs font-bold rounded-full px-2 py-0.5">
              {unacknowledgedCount}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {/* Sound toggle */}
          <button
            onClick={() => setSoundEnabled(!soundEnabled)}
            className="p-1 hover:bg-tactical-bg rounded transition-colors"
            title={soundEnabled ? 'Disable sound' : 'Enable sound'}
          >
            {soundEnabled ? (
              <Volume2 className="h-4 w-4" />
            ) : (
              <VolumeX className="h-4 w-4 text-tactical-textMuted" />
            )}
          </button>

          {/* Minimize */}
          <button
            onClick={() => setPanelVisible(false)}
            className="p-1 hover:bg-tactical-bg rounded transition-colors"
            title="Minimize"
          >
            <BellOff className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Alert threshold info */}
      <div className="px-4 py-2 bg-tactical-bg border-b border-tactical-border text-xs text-tactical-textMuted">
        Showing detections with confidence ≥ {(confidenceThreshold * 100).toFixed(0)}%
      </div>

      {/* Alerts list */}
      <div className="flex-1 overflow-y-auto">
        {alerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 text-tactical-textMuted">
            <Bell className="h-8 w-8 mb-2 opacity-50" />
            <p className="text-sm">No high-confidence alerts</p>
          </div>
        ) : (
          <div className="p-2 space-y-2">
            {alerts.map((alert) => {
              const maxConfidence = Math.max(
                ...alert.detection.detections.map((d) => d.confidence),
                0
              );
              const detectedClasses = Array.from(
                new Set(alert.detection.detections.map((d) => d.class))
              ).join(', ');

              return (
                <div
                  key={alert.id}
                  className={cn(
                    'border rounded-lg p-3 transition-all',
                    alert.acknowledged
                      ? 'border-tactical-border bg-tactical-bg opacity-60'
                      : 'border-yellow-500 bg-yellow-500/10'
                  )}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      {/* Detection info */}
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-semibold truncate">
                          {detectedClasses}
                        </span>
                        <span
                          className={cn(
                            'text-xs font-bold px-2 py-0.5 rounded',
                            maxConfidence >= 0.95
                              ? 'bg-green-500 text-white'
                              : maxConfidence >= 0.85
                              ? 'bg-yellow-500 text-black'
                              : 'bg-orange-500 text-white'
                          )}
                        >
                          {(maxConfidence * 100).toFixed(1)}%
                        </span>
                      </div>

                      {/* Node and timestamp */}
                      <div className="text-xs text-tactical-textMuted space-y-0.5">
                        <div>Node: {alert.detection.node_id}</div>
                        <div>
                          {new Date(alert.detection.timestamp).toLocaleTimeString()}
                        </div>
                        <div>
                          Count: {alert.detection.detection_count} object
                          {alert.detection.detection_count !== 1 ? 's' : ''}
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col gap-1">
                      {!alert.acknowledged && (
                        <button
                          onClick={() => acknowledgeAlert(alert.id)}
                          className="text-xs px-2 py-1 bg-tactical-border hover:bg-tactical-bg rounded transition-colors whitespace-nowrap"
                        >
                          Ack
                        </button>
                      )}
                      <button
                        onClick={() => dismissAlert(alert.id)}
                        className="p-1 hover:bg-tactical-bg rounded transition-colors"
                        title="Dismiss"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Footer actions */}
      {alerts.length > 0 && (
        <div className="p-3 border-t border-tactical-border flex gap-2">
          <button
            onClick={acknowledgeAll}
            disabled={unacknowledgedCount === 0}
            className={cn(
              'flex-1 text-xs px-3 py-2 rounded transition-colors',
              unacknowledgedCount > 0
                ? 'bg-tactical-border hover:bg-tactical-bg'
                : 'bg-tactical-bg text-tactical-textMuted cursor-not-allowed'
            )}
          >
            Acknowledge All
          </button>
          <button
            onClick={dismissAll}
            className="flex-1 text-xs px-3 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded transition-colors"
          >
            Dismiss All
          </button>
        </div>
      )}
    </div>
  );
}
