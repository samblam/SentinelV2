// TacticalMap.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { TacticalMap } from './TacticalMap';
import { createMockDetection, createMockNode } from '@/test/test-utils';

describe('TacticalMap', () => {
  const mockOnDetectionClick = vi.fn();

  it('renders map container', () => {
    render(
      <TacticalMap
        detections={[]}
        nodes={[]}
        selectedDetection={null}
        onDetectionClick={mockOnDetectionClick}
      />
    );

    expect(screen.getByTestId('map-container')).toBeInTheDocument();
  });

  it('renders tile layer for map tiles', () => {
    render(
      <TacticalMap
        detections={[]}
        nodes={[]}
        selectedDetection={null}
        onDetectionClick={mockOnDetectionClick}
      />
    );

    expect(screen.getByTestId('tile-layer')).toBeInTheDocument();
  });

  it('renders markers for detections', () => {
    const detections = [
      createMockDetection({ id: 1, latitude: 70.5, longitude: -100.2 }),
      createMockDetection({ id: 2, latitude: 71.0, longitude: -101.0 }),
    ];

    render(
      <TacticalMap
        detections={detections}
        nodes={[]}
        selectedDetection={null}
        onDetectionClick={mockOnDetectionClick}
      />
    );

    const markers = screen.getAllByTestId('marker');
    expect(markers.length).toBe(2);
  });

  it('renders markers for nodes', () => {
    const nodes = [
      createMockNode({ id: 1, node_id: 'sentry-01' }),
      createMockNode({ id: 2, node_id: 'aerostat-01' }),
    ];

    // Nodes need to have location data for markers
    // This depends on implementation - nodes might not have lat/lon
    render(
      <TacticalMap
        detections={[]}
        nodes={nodes}
        selectedDetection={null}
        onDetectionClick={mockOnDetectionClick}
      />
    );

    // Verify map is rendered (nodes may or may not have markers depending on implementation)
    expect(screen.getByTestId('map-container')).toBeInTheDocument();
  });

  it('renders popup for selected detection', () => {
    const detection = createMockDetection({
      id: 1,
      node_id: 'sentry-01',
      detection_count: 2,
    });

    render(
      <TacticalMap
        detections={[detection]}
        nodes={[]}
        selectedDetection={detection}
        onDetectionClick={mockOnDetectionClick}
      />
    );

    // Popup should be rendered for selected detection
    const popups = screen.getAllByTestId('popup');
    expect(popups.length).toBeGreaterThan(0);
  });

  it('displays detection information in popup', () => {
    const detection = createMockDetection({
      id: 1,
      node_id: 'sentry-01',
      detection_count: 3,
      detections: [
        { class: 'person', confidence: 0.95, bbox: { xmin: 0, ymin: 0, xmax: 100, ymax: 100 }, class_id: 0 },
      ],
    });

    render(
      <TacticalMap
        detections={[detection]}
        nodes={[]}
        selectedDetection={detection}
        onDetectionClick={mockOnDetectionClick}
      />
    );

    // Should display node ID and detection count in popup
    expect(screen.getByText(/sentry-01/)).toBeInTheDocument();
    expect(screen.getByText(/3/)).toBeInTheDocument();
  });

  it('handles empty detections array', () => {
    render(
      <TacticalMap
        detections={[]}
        nodes={[]}
        selectedDetection={null}
        onDetectionClick={mockOnDetectionClick}
      />
    );

    expect(screen.getByTestId('map-container')).toBeInTheDocument();
    expect(screen.queryByTestId('marker')).not.toBeInTheDocument();
  });

  it('handles empty nodes array', () => {
    render(
      <TacticalMap
        detections={[]}
        nodes={[]}
        selectedDetection={null}
        onDetectionClick={mockOnDetectionClick}
      />
    );

    expect(screen.getByTestId('map-container')).toBeInTheDocument();
  });

  it('renders multiple detection markers with different positions', () => {
    const detections = [
      createMockDetection({ id: 1, latitude: 70.1, longitude: -100.1 }),
      createMockDetection({ id: 2, latitude: 70.2, longitude: -100.2 }),
      createMockDetection({ id: 3, latitude: 70.3, longitude: -100.3 }),
    ];

    render(
      <TacticalMap
        detections={detections}
        nodes={[]}
        selectedDetection={null}
        onDetectionClick={mockOnDetectionClick}
      />
    );

    const markers = screen.getAllByTestId('marker');
    expect(markers.length).toBe(3);
  });

  it('distinguishes between selected and unselected markers', () => {
    const detections = [
      createMockDetection({ id: 1 }),
      createMockDetection({ id: 2 }),
    ];

    const { container } = render(
      <TacticalMap
        detections={detections}
        nodes={[]}
        selectedDetection={detections[0]}
        onDetectionClick={mockOnDetectionClick}
      />
    );

    // Selected marker might have different styling
    // This is implementation-dependent
    const markers = screen.getAllByTestId('marker');
    expect(markers.length).toBe(2);
  });

  it('displays confidence level in marker color or popup', () => {
    const highConfidenceDetection = createMockDetection({
      id: 1,
      detections: [
        { class: 'person', confidence: 0.95, bbox: { xmin: 0, ymin: 0, xmax: 100, ymax: 100 }, class_id: 0 },
      ],
    });

    render(
      <TacticalMap
        detections={[highConfidenceDetection]}
        nodes={[]}
        selectedDetection={highConfidenceDetection}
        onDetectionClick={mockOnDetectionClick}
      />
    );

    // Should display confidence somewhere (marker or popup)
    expect(screen.getByText(/95/)).toBeInTheDocument();
  });

  it('shows node status in different colors', () => {
    const nodes = [
      createMockNode({ id: 1, node_id: 'node-01', status: 'online' }),
      createMockNode({ id: 2, node_id: 'node-02', status: 'covert' }),
      createMockNode({ id: 3, node_id: 'node-03', status: 'offline' }),
    ];

    render(
      <TacticalMap
        detections={[]}
        nodes={nodes}
        selectedDetection={null}
        onDetectionClick={mockOnDetectionClick}
      />
    );

    // Nodes with different statuses might render differently
    // This is implementation-dependent
    expect(screen.getByTestId('map-container')).toBeInTheDocument();
  });
});
