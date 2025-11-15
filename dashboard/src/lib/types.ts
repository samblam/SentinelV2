// src/lib/types.ts

export interface Detection {
  id: number;
  node_id: string;
  timestamp: string;
  latitude: number;
  longitude: number;
  altitude_m?: number;
  accuracy_m?: number;
  detections: ObjectDetection[];
  detection_count: number;
  inference_time_ms?: number;
  model?: string;
}

export interface ObjectDetection {
  bbox: BoundingBox;
  class: string;
  confidence: number;
  class_id: number;
}

export interface BoundingBox {
  xmin: number;
  ymin: number;
  xmax: number;
  ymax: number;
}

export interface Node {
  id: number;
  node_id: string;
  status: 'online' | 'offline' | 'covert';  // Backend uses 'covert' not 'blackout'
  last_heartbeat?: string;
  created_at: string;
}

export interface BlackoutEvent {
  id: number;
  node_id: number;
  activated_at: string;
  deactivated_at?: string;
  activated_by?: string;
  reason?: string;
  detections_queued: number;
}

export interface WebSocketMessage {
  type: 'detection' | 'node_status' | 'blackout_event';
  data: Detection | Node | BlackoutEvent;
}

export interface Filters {
  objectClass: string[];
  confidenceMin: number;
  timeRange: 'hour' | '6hours' | '24hours' | 'custom';
  nodeIds: string[];
  customTimeStart?: Date;
  customTimeEnd?: Date;
}
