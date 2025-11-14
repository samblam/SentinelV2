// src/components/DetectionList.tsx

import { useState, useMemo } from 'react';
import { ArrowUpDown, MapPin } from 'lucide-react';
import { Detection } from '@/lib/types';
import { cn } from '@/lib/utils';

interface DetectionListProps {
  detections: Detection[];
  onDetectionClick: (detection: Detection) => void;
  selectedDetection?: Detection | null;
}

type SortField = 'timestamp' | 'node_id' | 'confidence' | 'count';
type SortOrder = 'asc' | 'desc';

export function DetectionList({
  detections,
  onDetectionClick,
  selectedDetection,
}: DetectionListProps) {
  const [sortField, setSortField] = useState<SortField>('timestamp');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  const sortedDetections = useMemo(() => {
    const sorted = [...detections].sort((a, b) => {
      let aValue: any;
      let bValue: any;

      switch (sortField) {
        case 'timestamp':
          aValue = new Date(a.timestamp).getTime();
          bValue = new Date(b.timestamp).getTime();
          break;
        case 'node_id':
          aValue = a.node_id;
          bValue = b.node_id;
          break;
        case 'confidence':
          aValue = Math.max(...a.detections.map((d) => d.confidence));
          bValue = Math.max(...b.detections.map((d) => d.confidence));
          break;
        case 'count':
          aValue = a.detection_count;
          bValue = b.detection_count;
          break;
        default:
          return 0;
      }

      if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    return sorted;
  }, [detections, sortField, sortOrder]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence > 0.85) return 'text-confidence-high';
    if (confidence > 0.7) return 'text-confidence-medium';
    return 'text-confidence-low';
  };

  if (detections.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-tactical-textMuted">
        No detections found
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-tactical-border">
        <h2 className="text-lg font-semibold">Recent Detections</h2>
        <p className="text-sm text-tactical-textMuted mt-1">
          {detections.length} total detections
        </p>
      </div>

      <div className="flex-1 overflow-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-tactical-surface border-b border-tactical-border">
            <tr>
              <th
                className="px-4 py-3 text-left cursor-pointer hover:bg-tactical-bg"
                onClick={() => handleSort('timestamp')}
              >
                <div className="flex items-center gap-2">
                  Time
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th
                className="px-4 py-3 text-left cursor-pointer hover:bg-tactical-bg"
                onClick={() => handleSort('node_id')}
              >
                <div className="flex items-center gap-2">
                  Node
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="px-4 py-3 text-left">Objects</th>
              <th
                className="px-4 py-3 text-left cursor-pointer hover:bg-tactical-bg"
                onClick={() => handleSort('confidence')}
              >
                <div className="flex items-center gap-2">
                  Confidence
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="px-4 py-3 text-center">Actions</th>
            </tr>
          </thead>
          <tbody>
            {sortedDetections.map((detection) => {
              const maxConfidence = Math.max(
                ...detection.detections.map((d) => d.confidence)
              );
              const isSelected = selectedDetection?.id === detection.id;

              return (
                <tr
                  key={detection.id}
                  className={cn(
                    'border-b border-tactical-border hover:bg-tactical-surface cursor-pointer transition-colors',
                    isSelected && 'bg-tactical-primary/10'
                  )}
                  onClick={() => onDetectionClick(detection)}
                >
                  <td className="px-4 py-3 text-tactical-textMuted">
                    {new Date(detection.timestamp).toLocaleTimeString()}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs">
                    {detection.node_id}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-col gap-1">
                      {detection.detections.slice(0, 2).map((obj, idx) => (
                        <div key={idx} className="text-xs">
                          {obj.class}
                        </div>
                      ))}
                      {detection.detections.length > 2 && (
                        <div className="text-xs text-tactical-textMuted">
                          +{detection.detections.length - 2} more
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={cn('font-semibold', getConfidenceColor(maxConfidence))}>
                      {(maxConfidence * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <button
                      className="p-1 hover:bg-tactical-bg rounded"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDetectionClick(detection);
                      }}
                    >
                      <MapPin className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
