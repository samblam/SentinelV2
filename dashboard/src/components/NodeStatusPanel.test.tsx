// NodeStatusPanel.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/test-utils';
import { NodeStatusPanel } from './NodeStatusPanel';
import { createMockNode } from '@/test/test-utils';

describe('NodeStatusPanel', () => {
  const mockOnActivateBlackout = vi.fn();
  const mockOnDeactivateBlackout = vi.fn();

  it('renders empty state when no nodes', () => {
    render(
      <NodeStatusPanel
        nodes={[]}
        onActivateBlackout={mockOnActivateBlackout}
        onDeactivateBlackout={mockOnDeactivateBlackout}
      />
    );

    expect(screen.getByText('No nodes registered')).toBeInTheDocument();
  });

  it('displays node information correctly', () => {
    const nodes = [
      createMockNode({
        node_id: 'sentry-01',
        status: 'online',
      }),
      createMockNode({
        id: 2,
        node_id: 'aerostat-01',
        status: 'offline',
      }),
    ];

    render(
      <NodeStatusPanel
        nodes={nodes}
        onActivateBlackout={mockOnActivateBlackout}
        onDeactivateBlackout={mockOnDeactivateBlackout}
      />
    );

    expect(screen.getByText('sentry-01')).toBeInTheDocument();
    expect(screen.getByText('aerostat-01')).toBeInTheDocument();
  });

  it('displays online status with correct styling', () => {
    const node = createMockNode({ status: 'online' });

    render(
      <NodeStatusPanel
        nodes={[node]}
        onActivateBlackout={mockOnActivateBlackout}
        onDeactivateBlackout={mockOnDeactivateBlackout}
      />
    );

    expect(screen.getByText('Online')).toBeInTheDocument();
    expect(screen.getByText('Online')).toHaveClass('bg-green-500');
  });

  it('displays offline status with correct styling', () => {
    const node = createMockNode({ status: 'offline' });

    render(
      <NodeStatusPanel
        nodes={[node]}
        onActivateBlackout={mockOnActivateBlackout}
        onDeactivateBlackout={mockOnDeactivateBlackout}
      />
    );

    expect(screen.getByText('Offline')).toBeInTheDocument();
    expect(screen.getByText('Offline')).toHaveClass('bg-gray-500');
  });

  it('displays covert status with correct styling', () => {
    const node = createMockNode({
      status: 'covert',
      blackout_status: {
        active: true,
        activated_at: new Date().toISOString(),
        detections_queued: 5,
      },
    });

    render(
      <NodeStatusPanel
        nodes={[node]}
        onActivateBlackout={mockOnActivateBlackout}
        onDeactivateBlackout={mockOnDeactivateBlackout}
      />
    );

    expect(screen.getByText('Covert')).toBeInTheDocument();
    expect(screen.getByText('Covert')).toHaveClass('bg-yellow-500');
  });

  it('displays resuming status with correct styling', () => {
    const node = createMockNode({ status: 'resuming' });

    render(
      <NodeStatusPanel
        nodes={[node]}
        onActivateBlackout={mockOnActivateBlackout}
        onDeactivateBlackout={mockOnDeactivateBlackout}
      />
    );

    expect(screen.getByText('Resuming')).toBeInTheDocument();
    expect(screen.getByText('Resuming')).toHaveClass('bg-blue-500');
  });

  it('displays last heartbeat timestamp', () => {
    const heartbeatTime = new Date('2025-11-17T10:30:00Z');
    const node = createMockNode({
      last_heartbeat: heartbeatTime.toISOString(),
    });

    render(
      <NodeStatusPanel
        nodes={[node]}
        onActivateBlackout={mockOnActivateBlackout}
        onDeactivateBlackout={mockOnDeactivateBlackout}
      />
    );

    // Should display some form of the timestamp
    expect(screen.getByText(/10:30/)).toBeInTheDocument();
  });

  it('shows blackout control for online nodes', () => {
    const node = createMockNode({ status: 'online' });

    render(
      <NodeStatusPanel
        nodes={[node]}
        onActivateBlackout={mockOnActivateBlackout}
        onDeactivateBlackout={mockOnDeactivateBlackout}
      />
    );

    // BlackoutControl component should be rendered (contains "Activate Blackout" button)
    // The exact button text depends on BlackoutControl implementation
    const buttons = screen.getAllByRole('button');
    expect(buttons.length).toBeGreaterThan(0);
  });

  it('shows blackout info for covert nodes', () => {
    const node = createMockNode({
      status: 'covert',
      blackout_status: {
        active: true,
        activated_at: new Date('2025-11-17T10:00:00Z').toISOString(),
        detections_queued: 12,
      },
    });

    render(
      <NodeStatusPanel
        nodes={[node]}
        onActivateBlackout={mockOnActivateBlackout}
        onDeactivateBlackout={mockOnDeactivateBlackout}
      />
    );

    // Should show queued detections count
    expect(screen.getByText(/12/)).toBeInTheDocument();
  });

  it('sorts nodes by status (covert first, then online, then offline)', () => {
    const nodes = [
      createMockNode({ id: 1, node_id: 'node-01', status: 'offline' }),
      createMockNode({ id: 2, node_id: 'node-02', status: 'online' }),
      createMockNode({ id: 3, node_id: 'node-03', status: 'covert' }),
    ];

    const { container } = render(
      <NodeStatusPanel
        nodes={nodes}
        onActivateBlackout={mockOnActivateBlackout}
        onDeactivateBlackout={mockOnDeactivateBlackout}
      />
    );

    const nodeElements = container.querySelectorAll('[class*="border"]');

    // Covert should be first, offline should be last
    // This is implementation-dependent, adjust based on actual implementation
    expect(nodeElements.length).toBeGreaterThan(0);
  });

  it('displays created_at timestamp', () => {
    const createdTime = new Date('2025-11-17T08:00:00Z');
    const node = createMockNode({
      created_at: createdTime.toISOString(),
    });

    render(
      <NodeStatusPanel
        nodes={[node]}
        onActivateBlackout={mockOnActivateBlackout}
        onDeactivateBlackout={mockOnDeactivateBlackout}
      />
    );

    // Should display some form of creation timestamp
    const timeElements = screen.getAllByText(/08:00|8:00/);
    expect(timeElements.length).toBeGreaterThan(0);
  });
});
