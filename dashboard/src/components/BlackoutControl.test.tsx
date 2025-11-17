// BlackoutControl.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, userEvent, waitFor } from '@/test/test-utils';
import { BlackoutControl } from './BlackoutControl';
import { createMockNode } from '@/test/test-utils';

describe('BlackoutControl', () => {
  const mockOnActivate = vi.fn();
  const mockOnDeactivate = vi.fn();

  it('shows activate button for online nodes', () => {
    const node = createMockNode({ status: 'online' });

    render(
      <BlackoutControl
        node={node}
        onActivate={mockOnActivate}
        onDeactivate={mockOnDeactivate}
      />
    );

    expect(screen.getByText('Activate Blackout')).toBeInTheDocument();
  });

  it('opens dialog when activate button clicked', async () => {
    const user = userEvent.setup();
    const node = createMockNode({ status: 'online' });

    render(
      <BlackoutControl
        node={node}
        onActivate={mockOnActivate}
        onDeactivate={mockOnDeactivate}
      />
    );

    const activateButton = screen.getByText('Activate Blackout');
    await user.click(activateButton);

    // Dialog should open with title
    await waitFor(() => {
      expect(screen.getByText(/Activate Blackout Mode/)).toBeInTheDocument();
    });
  });

  it('allows entering reason in dialog', async () => {
    const user = userEvent.setup();
    const node = createMockNode({ status: 'online' });

    render(
      <BlackoutControl
        node={node}
        onActivate={mockOnActivate}
        onDeactivate={mockOnDeactivate}
      />
    );

    // Open dialog
    await user.click(screen.getByText('Activate Blackout'));

    // Find reason textarea
    await waitFor(() => {
      const textarea = screen.getByRole('textbox');
      expect(textarea).toBeInTheDocument();
    });

    const textarea = screen.getByRole('textbox');
    await user.type(textarea, 'Suspected adversary activity');

    expect(textarea).toHaveValue('Suspected adversary activity');
  });

  it('calls onActivate when confirm button clicked', async () => {
    const user = userEvent.setup();
    const node = createMockNode({ status: 'online', node_id: 'sentry-01' });

    mockOnActivate.mockResolvedValue(undefined);

    render(
      <BlackoutControl
        node={node}
        onActivate={mockOnActivate}
        onDeactivate={mockOnDeactivate}
      />
    );

    // Open dialog
    await user.click(screen.getByText('Activate Blackout'));

    // Enter reason
    await waitFor(() => {
      const textarea = screen.getByRole('textbox');
      user.type(textarea, 'Testing');
    });

    // Find and click confirm button
    const confirmButton = screen.getByText('Activate');
    await user.click(confirmButton);

    await waitFor(() => {
      expect(mockOnActivate).toHaveBeenCalledWith('sentry-01', expect.any(String));
    });
  });

  it('shows deactivate button for covert nodes', () => {
    const node = createMockNode({
      status: 'covert',
      blackout_status: {
        active: true,
        activated_at: new Date().toISOString(),
        detections_queued: 5,
      },
    });

    render(
      <BlackoutControl
        node={node}
        onActivate={mockOnActivate}
        onDeactivate={mockOnDeactivate}
      />
    );

    expect(screen.getByText('Resume Transmission')).toBeInTheDocument();
  });

  it('displays blackout duration for covert nodes', () => {
    const activatedTime = new Date(Date.now() - 120000); // 2 minutes ago
    const node = createMockNode({
      status: 'covert',
      blackout_status: {
        active: true,
        activated_at: activatedTime.toISOString(),
        detections_queued: 5,
      },
    });

    render(
      <BlackoutControl
        node={node}
        onActivate={mockOnActivate}
        onDeactivate={mockOnDeactivate}
      />
    );

    // Should show duration (e.g., "2m 0s")
    expect(screen.getByText(/2m/)).toBeInTheDocument();
  });

  it('displays queued detections count for covert nodes', () => {
    const node = createMockNode({
      status: 'covert',
      blackout_status: {
        active: true,
        activated_at: new Date().toISOString(),
        detections_queued: 12,
      },
    });

    render(
      <BlackoutControl
        node={node}
        onActivate={mockOnActivate}
        onDeactivate={mockOnDeactivate}
      />
    );

    expect(screen.getByText(/12 queued/i)).toBeInTheDocument();
  });

  it('calls onDeactivate when resume button clicked', async () => {
    const user = userEvent.setup();
    const node = createMockNode({
      status: 'covert',
      node_id: 'sentry-01',
      blackout_status: {
        active: true,
        activated_at: new Date().toISOString(),
        detections_queued: 5,
      },
    });

    mockOnDeactivate.mockResolvedValue(undefined);

    render(
      <BlackoutControl
        node={node}
        onActivate={mockOnActivate}
        onDeactivate={mockOnDeactivate}
      />
    );

    const resumeButton = screen.getByText('Resume Transmission');
    await user.click(resumeButton);

    await waitFor(() => {
      expect(mockOnDeactivate).toHaveBeenCalledWith('sentry-01');
    });
  });

  it('shows loading state during activation', async () => {
    const user = userEvent.setup();
    const node = createMockNode({ status: 'online' });

    // Make onActivate take some time
    mockOnActivate.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 100)));

    render(
      <BlackoutControl
        node={node}
        onActivate={mockOnActivate}
        onDeactivate={mockOnDeactivate}
      />
    );

    // Open dialog and activate
    await user.click(screen.getByText('Activate Blackout'));
    await waitFor(() => screen.getByText('Activate'));

    const activateButton = screen.getByText('Activate');
    await user.click(activateButton);

    // Button should be disabled during loading
    expect(activateButton).toBeDisabled();
  });

  it('shows loading state during deactivation', async () => {
    const user = userEvent.setup();
    const node = createMockNode({
      status: 'covert',
      blackout_status: {
        active: true,
        activated_at: new Date().toISOString(),
      },
    });

    mockOnDeactivate.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 100)));

    render(
      <BlackoutControl
        node={node}
        onActivate={mockOnActivate}
        onDeactivate={mockOnDeactivate}
      />
    );

    const resumeButton = screen.getByText('Resume Transmission');
    await user.click(resumeButton);

    // Button should be disabled during loading
    await waitFor(() => {
      expect(resumeButton).toBeDisabled();
    });
  });

  it('hides activate button for offline nodes', () => {
    const node = createMockNode({ status: 'offline' });

    render(
      <BlackoutControl
        node={node}
        onActivate={mockOnActivate}
        onDeactivate={mockOnDeactivate}
      />
    );

    // Should not show activate button for offline nodes
    expect(screen.queryByText('Activate Blackout')).not.toBeInTheDocument();
  });

  it('displays warning icon for covert status', () => {
    const node = createMockNode({
      status: 'covert',
      blackout_status: {
        active: true,
        activated_at: new Date().toISOString(),
      },
    });

    const { container } = render(
      <BlackoutControl
        node={node}
        onActivate={mockOnActivate}
        onDeactivate={mockOnDeactivate}
      />
    );

    // Check for AlertTriangle or EyeOff icon (depends on implementation)
    const icons = container.querySelectorAll('svg');
    expect(icons.length).toBeGreaterThan(0);
  });
});
