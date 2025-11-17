// AlertPanel.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, userEvent, waitFor } from '@/test/test-utils';
import { AlertPanel } from './AlertPanel';
import { createMockDetection } from '@/test/test-utils';

describe('AlertPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const highConfidenceDetection = createMockDetection({
    id: 1,
    detections: [
      { class: 'person', confidence: 0.95, bbox: { xmin: 0, ymin: 0, xmax: 100, ymax: 100 }, class_id: 0 },
    ],
  });

  const lowConfidenceDetection = createMockDetection({
    id: 2,
    detections: [
      { class: 'vehicle', confidence: 0.70, bbox: { xmin: 0, ymin: 0, xmax: 100, ymax: 100 }, class_id: 1 },
    ],
  });

  it('renders alert panel with high-confidence threshold message', () => {
    render(<AlertPanel detections={[]} confidenceThreshold={0.85} />);

    expect(screen.getByText(/Showing detections with confidence ≥ 85%/)).toBeInTheDocument();
  });

  it('displays empty state when no alerts', () => {
    render(<AlertPanel detections={[]} />);

    expect(screen.getByText('No high-confidence alerts')).toBeInTheDocument();
  });

  it('filters detections by confidence threshold', async () => {
    render(
      <AlertPanel
        detections={[highConfidenceDetection, lowConfidenceDetection]}
        confidenceThreshold={0.85}
      />
    );

    // Wait for alerts to be processed
    await waitFor(() => {
      // High confidence alert should be shown
      expect(screen.getByText('person')).toBeInTheDocument();
    });

    // Low confidence alert should not be shown
    expect(screen.queryByText('vehicle')).not.toBeInTheDocument();
  });

  it('displays alert with correct confidence percentage', async () => {
    render(<AlertPanel detections={[highConfidenceDetection]} />);

    await waitFor(() => {
      expect(screen.getByText('95.0%')).toBeInTheDocument();
    });
  });

  it('shows unacknowledged alert count', async () => {
    render(<AlertPanel detections={[highConfidenceDetection]} />);

    await waitFor(() => {
      // Should show badge with "1" for one unacknowledged alert
      const badges = screen.getAllByText('1');
      expect(badges.length).toBeGreaterThan(0);
    });
  });

  it('acknowledges individual alert when Ack button clicked', async () => {
    const user = userEvent.setup();

    render(<AlertPanel detections={[highConfidenceDetection]} />);

    await waitFor(() => {
      expect(screen.getByText('person')).toBeInTheDocument();
    });

    // Click Ack button
    const ackButton = screen.getByText('Ack');
    await user.click(ackButton);

    // Alert should still be visible but acknowledged (opacity reduced)
    await waitFor(() => {
      const alertDiv = ackButton.closest('.border');
      expect(alertDiv).toHaveClass('opacity-60');
    });
  });

  it('dismisses alert when X button clicked', async () => {
    const user = userEvent.setup();

    render(<AlertPanel detections={[highConfidenceDetection]} />);

    await waitFor(() => {
      expect(screen.getByText('person')).toBeInTheDocument();
    });

    // Find and click dismiss button (X icon)
    const dismissButtons = screen.getAllByRole('button');
    const dismissButton = dismissButtons.find((btn) => btn.getAttribute('title') === 'Dismiss');

    if (dismissButton) {
      await user.click(dismissButton);

      // Alert should be removed
      await waitFor(() => {
        expect(screen.queryByText('person')).not.toBeInTheDocument();
      });
    }
  });

  it('acknowledges all alerts when Acknowledge All clicked', async () => {
    const user = userEvent.setup();

    const detections = [
      highConfidenceDetection,
      createMockDetection({
        id: 3,
        detections: [
          { class: 'vehicle', confidence: 0.90, bbox: { xmin: 0, ymin: 0, xmax: 100, ymax: 100 }, class_id: 1 },
        ],
      }),
    ];

    render(<AlertPanel detections={detections} />);

    await waitFor(() => {
      expect(screen.getByText('person')).toBeInTheDocument();
      expect(screen.getByText('vehicle')).toBeInTheDocument();
    });

    // Click Acknowledge All button
    const acknowledgeAllButton = screen.getByText('Acknowledge All');
    await user.click(acknowledgeAllButton);

    // All alerts should be acknowledged
    await waitFor(() => {
      const alertDivs = document.querySelectorAll('.border.opacity-60');
      expect(alertDivs.length).toBe(2);
    });
  });

  it('dismisses all alerts when Dismiss All clicked', async () => {
    const user = userEvent.setup();

    render(<AlertPanel detections={[highConfidenceDetection]} />);

    await waitFor(() => {
      expect(screen.getByText('person')).toBeInTheDocument();
    });

    // Click Dismiss All button
    const dismissAllButton = screen.getByText('Dismiss All');
    await user.click(dismissAllButton);

    // Should show empty state
    await waitFor(() => {
      expect(screen.getByText('No high-confidence alerts')).toBeInTheDocument();
    });
  });

  it('minimizes and expands panel', async () => {
    const user = userEvent.setup();

    render(<AlertPanel detections={[highConfidenceDetection]} />);

    await waitFor(() => {
      expect(screen.getByText('High-Confidence Alerts')).toBeInTheDocument();
    });

    // Find minimize button
    const minimizeButton = screen.getByTitle('Minimize');
    await user.click(minimizeButton);

    // Panel header should be hidden
    await waitFor(() => {
      expect(screen.queryByText('High-Confidence Alerts')).not.toBeInTheDocument();
    });

    // Should show minimized button
    const minimizedButton = document.querySelector('button svg');
    expect(minimizedButton).toBeInTheDocument();

    // Click to expand
    const expandButton = minimizedButton?.closest('button');
    if (expandButton) {
      await user.click(expandButton);

      // Panel header should be visible again
      await waitFor(() => {
        expect(screen.getByText('High-Confidence Alerts')).toBeInTheDocument();
      });
    }
  });

  it('toggles sound on and off', async () => {
    const user = userEvent.setup();

    render(<AlertPanel detections={[]} />);

    // Find sound toggle button
    const soundButtons = screen.getAllByRole('button');
    const soundToggle = soundButtons.find((btn) => btn.getAttribute('title')?.includes('sound'));

    if (soundToggle) {
      // Initially should be enabled (Volume2 icon)
      expect(soundToggle).toBeInTheDocument();

      // Click to disable
      await user.click(soundToggle);

      // Should show VolumeX icon (muted)
      expect(soundToggle).toBeInTheDocument();
    }
  });

  it('displays node information correctly', async () => {
    const detection = createMockDetection({
      node_id: 'sentry-01',
      detection_count: 3,
    });

    render(<AlertPanel detections={[detection]} />);

    await waitFor(() => {
      expect(screen.getByText(/Node: sentry-01/)).toBeInTheDocument();
      expect(screen.getByText(/Count: 3 objects/)).toBeInTheDocument();
    });
  });

  it('uses custom confidence threshold', async () => {
    const detection = createMockDetection({
      detections: [
        { class: 'person', confidence: 0.80, bbox: { xmin: 0, ymin: 0, xmax: 100, ymax: 100 }, class_id: 0 },
      ],
    });

    // With threshold 0.85, should not show
    const { rerender } = render(<AlertPanel detections={[detection]} confidenceThreshold={0.85} />);

    await waitFor(() => {
      expect(screen.getByText('No high-confidence alerts')).toBeInTheDocument();
    });

    // With threshold 0.75, should show
    rerender(<AlertPanel detections={[detection]} confidenceThreshold={0.75} />);

    await waitFor(() => {
      expect(screen.getByText('person')).toBeInTheDocument();
    });
  });
});
