// src/components/TacticalMap.tsx

import { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import L from 'leaflet';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';
import { Detection, Node } from '@/lib/types';

// Fix default marker icon paths for Vite
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
});

// Custom icons for different confidence levels
const createDetectionIcon = (confidence: number) => {
  let color = '#fbbf24'; // low - yellow
  if (confidence > 0.85) {
    color = '#ef4444'; // high - red
  } else if (confidence > 0.7) {
    color = '#f59e0b'; // medium - orange
  }

  return L.divIcon({
    className: 'custom-detection-marker',
    html: `<div style="background-color: ${color}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white;"></div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });
};

// Custom icons for node status
const createNodeIcon = (status: 'online' | 'offline' | 'covert') => {
  let color = '#6b7280'; // offline - gray
  if (status === 'online') {
    color = '#10b981'; // online - green
  } else if (status === 'covert') {
    color = '#3b82f6'; // covert - blue
  }

  return L.divIcon({
    className: 'custom-node-marker',
    html: `<div style="background-color: ${color}; width: 16px; height: 16px; border-radius: 4px; border: 2px solid white;"></div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  });
};

interface TacticalMapProps {
  detections: Detection[];
  nodes: Node[];
  onDetectionClick?: (detection: Detection) => void;
  onNodeClick?: (node: Node) => void;
  selectedDetection?: Detection | null;
}

export function TacticalMap({
  detections,
  nodes,
  onDetectionClick,
  onNodeClick,
  selectedDetection,
}: TacticalMapProps) {
  useEffect(() => {
    console.log('TacticalMap rendered with', detections.length, 'detections and', nodes.length, 'nodes');
  }, [detections.length, nodes.length]);

  // Arctic center: 70°N, -100°W
  const arcticCenter: [number, number] = [70, -100];

  return (
    <div className="h-full w-full">
      <MapContainer
        center={arcticCenter}
        zoom={4}
        className="h-full w-full"
        style={{ background: '#0a0e1a' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Detection markers */}
        {detections.map((detection) => {
          const maxConfidence = Math.max(
            ...detection.detections.map((d) => d.confidence)
          );

          return (
            <Marker
              key={detection.id}
              position={[detection.latitude, detection.longitude]}
              icon={createDetectionIcon(maxConfidence)}
              eventHandlers={{
                click: () => onDetectionClick?.(detection),
              }}
            >
              <Popup>
                <div className="text-sm">
                  <div className="font-semibold mb-1">Detection #{detection.id}</div>
                  <div className="text-xs text-gray-600">
                    <div>Node: {detection.node_id}</div>
                    <div>Time: {new Date(detection.timestamp).toLocaleString()}</div>
                    <div>Objects: {detection.detection_count}</div>
                    <div className="mt-1">
                      {detection.detections.map((obj, idx) => (
                        <div key={idx}>
                          {obj.class}: {(obj.confidence * 100).toFixed(1)}%
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </Popup>
              {selectedDetection?.id === detection.id && (
                <Circle
                  center={[detection.latitude, detection.longitude]}
                  radius={50000}
                  pathOptions={{ color: '#3b82f6', fillOpacity: 0.1 }}
                />
              )}
            </Marker>
          );
        })}

        {/* Node markers */}
        {nodes.map((node) => (
          <Marker
            key={node.id}
            position={[70 + node.id * 0.5, -100 + node.id * 0.5]} // Placeholder positions
            icon={createNodeIcon(node.status)}
            eventHandlers={{
              click: () => onNodeClick?.(node),
            }}
          >
            <Popup>
              <div className="text-sm">
                <div className="font-semibold mb-1">{node.node_id}</div>
                <div className="text-xs text-gray-600">
                  <div>Status: {node.status}</div>
                  {node.last_heartbeat && (
                    <div>Last seen: {new Date(node.last_heartbeat).toLocaleString()}</div>
                  )}
                </div>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
