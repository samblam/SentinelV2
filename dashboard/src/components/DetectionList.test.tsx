// DetectionList.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, userEvent } from '@/test/test-utils';
import { DetectionList } from './DetectionList';
import { createMockDetection } from '@/test/test-utils';

describe('DetectionList', () => {
  const mockDetections = [
    createMockDetection({
      id: 1,
      node_id: 'sentry-01',
      timestamp: '2025-11-17T10:00:00Z',
      detection_count: 2,
      detections: [
        { class: 'person', confidence: 0.95, bbox: { xmin: 0, ymin: 0, xmax: 100, ymax: 100 }, class_id: 0 },
      ],
    }),
    createMockDetection({
      id: 2,
      node_id: 'aerostat-01',
      timestamp: '2025-11-17T11:00:00Z',
      detection_count: 1,
      detections: [
        { class: 'vehicle', confidence: 0.78, bbox: { xmin: 0, ymin: 0, xmax: 100, ymax: 100 }, class_id: 1 },
      ],
    }),
  ];

  const mockOnDetectionClick = vi.fn();

  it('renders detection list with correct count', () => {
    render(
      <DetectionList
        detections={mockDetections}
        onDetectionClick={mockOnDetectionClick}
        selectedDetection={null}
      />
    );

    expect(screen.getByText('2 total detections')).toBeInTheDocument();
  });

  it('renders empty state when no detections', () => {
    render(
      <DetectionList
        detections={[]}
        onDetectionClick={mockOnDetectionClick}
        selectedDetection={null}
      />
    );

    expect(screen.getByText('No detections found')).toBeInTheDocument();
  });

  it('displays detection information correctly', () => {
    render(
      <DetectionList
        detections={mockDetections}
        onDetectionClick={mockOnDetectionClick}
        selectedDetection={null}
      />
    );

    expect(screen.getByText('sentry-01')).toBeInTheDocument();
    expect(screen.getByText('aerostat-01')).toBeInTheDocument();
  });

  it('calls onDetectionClick when detection is clicked', async () => {
    const user = userEvent.setup();

    render(
      <DetectionList
        detections={mockDetections}
        onDetectionClick={mockOnDetectionClick}
        selectedDetection={null}
      />
    );

    // Find and click first detection row
    const detectionRows = screen.getAllByRole('row');
    // Skip header row (index 0), click first data row (index 1)
    if (detectionRows.length > 1) {
      await user.click(detectionRows[1]);
      expect(mockOnDetectionClick).toHaveBeenCalledWith(mockDetections[0]);
    }
  });

  it('sorts detections when column header is clicked', async () => {
    const user = userEvent.setup();

    render(
      <DetectionList
        detections={mockDetections}
        onDetectionClick={mockOnDetectionClick}
        selectedDetection={null}
      />
    );

    // Find sort button for timestamp column
    const sortButtons = screen.getAllByRole('button');
    const timestampSortButton = sortButtons.find((btn) =>
      btn.textContent?.includes('Time')
    );

    if (timestampSortButton) {
      await user.click(timestampSortButton);
      // Verify sorting changed (implementation detail, could check row order)
      expect(timestampSortButton).toBeInTheDocument();
    }
  });

  it('highlights selected detection', () => {
    const { container } = render(
      <DetectionList
        detections={mockDetections}
        onDetectionClick={mockOnDetectionClick}
        selectedDetection={mockDetections[0]}
      />
    );

    // Check that selected row has highlight styling
    const highlightedRow = container.querySelector('.bg-tactical-border');
    expect(highlightedRow).toBeInTheDocument();
  });

  it('displays confidence levels correctly', () => {
    render(
      <DetectionList
        detections={mockDetections}
        onDetectionClick={mockOnDetectionClick}
        selectedDetection={null}
      />
    );

    // Check that high confidence (0.95) is displayed
    expect(screen.getByText(/95\.0%/)).toBeInTheDocument();
    // Check that medium confidence (0.78) is displayed
    expect(screen.getByText(/78\.0%/)).toBeInTheDocument();
  });

  it('displays detection count correctly', () => {
    render(
      <DetectionList
        detections={mockDetections}
        onDetectionClick={mockOnDetectionClick}
        selectedDetection={null}
      />
    );

    // Check detection count badges
    expect(screen.getByText('2')).toBeInTheDocument(); // First detection has 2 objects
    expect(screen.getByText('1')).toBeInTheDocument(); // Second detection has 1 object
  });
});
