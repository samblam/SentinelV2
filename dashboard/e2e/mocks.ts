export const mockDetections = [
  {
    id: 'd1',
    timestamp: new Date().toISOString(),
    class_name: 'person',
    confidence: 0.95,
    bbox: [100, 100, 200, 200],
    source_node: 'node-001',
    image_url: '/mock-image.jpg'
  },
  {
    id: 'd2',
    timestamp: new Date(Date.now() - 60000).toISOString(),
    class_name: 'vehicle',
    confidence: 0.88,
    bbox: [300, 300, 400, 400],
    source_node: 'node-002',
    image_url: '/mock-image.jpg'
  }
];

export const mockNodes = [
  {
    node_id: 'node-001',
    status: 'online',
    last_seen: new Date().toISOString(),
    location: { lat: 40.7128, lng: -74.0060 },
    config: { mode: 'active' }
  },
  {
    node_id: 'node-002',
    status: 'covert',
    last_seen: new Date().toISOString(),
    location: { lat: 40.7580, lng: -73.9855 },
    config: { mode: 'covert' }
  }
];
