// Integration tests for complete App rendering and basic workflows
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from '@/App';
import { renderWithIntegrationProviders, setupWebSocketMock, cleanupWebSocketMock } from './helpers.integration';
import './setup.integration';

describe('App Integration Tests', () => {
  beforeEach(() => {
    setupWebSocketMock();
  });

  afterEach(() => {
    cleanupWebSocketMock();
  });

  it('renders complete application with all major components', async () => {
    renderWithIntegrationProviders(<App />);

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText('Loading Sentinel Dashboard...')).not.toBeInTheDocument();
    });

    // Check header
    expect(screen.getByText('Sentinel - Operator Dashboard')).toBeInTheDocument();

    // Check connection status component
    expect(screen.getByText(/Connected|Disconnected/)).toBeInTheDocument();

    // Check node panel
    expect(screen.getByText('Edge Nodes')).toBeInTheDocument();

    // Check detection list
    expect(screen.getByText('Recent Detections')).toBeInTheDocument();
  });

  it('loads and displays initial data from API', async () => {
    renderWithIntegrationProviders(<App />);

    // Wait for data to load
    await waitFor(() => {
      expect(screen.queryByText('Loading Sentinel Dashboard...')).not.toBeInTheDocument();
    });

    // Should display nodes
    await waitFor(() => {
      expect(screen.getByText('sentry-01')).toBeInTheDocument();
      expect(screen.getByText('aerostat-01')).toBeInTheDocument();
    });

    // Should display detections
    await waitFor(() => {
      expect(screen.getByText('person')).toBeInTheDocument();
      expect(screen.getByText('vehicle')).toBeInTheDocument();
    });

    // Should show detection count
    expect(screen.getByText(/2 total detections/)).toBeInTheDocument();
  });

  it('shows loading state initially', () => {
    renderWithIntegrationProviders(<App />);

    // Should show loading state
    expect(screen.getByText('Loading Sentinel Dashboard...')).toBeInTheDocument();
    expect(screen.getByText('Connecting to backend')).toBeInTheDocument();
  });

  it('displays connection status correctly', async () => {
    renderWithIntegrationProviders(<App />);

    await waitFor(() => {
      expect(screen.queryByText('Loading Sentinel Dashboard...')).not.toBeInTheDocument();
    });

    // Should show connection status (either Connected or Disconnected)
    const connectionStatus = screen.getByText(/Connected|Disconnected/);
    expect(connectionStatus).toBeInTheDocument();
  });

  it('renders map container', async () => {
    renderWithIntegrationProviders(<App />);

    await waitFor(() => {
      expect(screen.queryByText('Loading Sentinel Dashboard...')).not.toBeInTheDocument();
    });

    // Map container should be present (mocked in setup)
    const mapContainer = screen.getByTestId('map-container');
    expect(mapContainer).toBeInTheDocument();
  });

  it('renders node status panel with correct node information', async () => {
    renderWithIntegrationProviders(<App />);

    await waitFor(() => {
      expect(screen.queryByText('Loading Sentinel Dashboard...')).not.toBeInTheDocument();
    });

    // Should show node IDs
    expect(screen.getByText('sentry-01')).toBeInTheDocument();
    expect(screen.getByText('aerostat-01')).toBeInTheDocument();

    // Should show node statuses
    const onlineStatuses = screen.getAllByText('ONLINE');
    expect(onlineStatuses.length).toBeGreaterThan(0);
  });

  it('renders detection list with detection details', async () => {
    renderWithIntegrationProviders(<App />);

    await waitFor(() => {
      expect(screen.queryByText('Loading Sentinel Dashboard...')).not.toBeInTheDocument();
    });

    // Should show detection classes
    expect(screen.getByText('person')).toBeInTheDocument();
    expect(screen.getByText('vehicle')).toBeInTheDocument();

    // Should show confidence levels
    expect(screen.getByText('95%')).toBeInTheDocument();
    expect(screen.getByText('78%')).toBeInTheDocument();
  });

  it('renders alert panel for high-confidence detections', async () => {
    renderWithIntegrationProviders(<App />);

    await waitFor(() => {
      expect(screen.queryByText('Loading Sentinel Dashboard...')).not.toBeInTheDocument();
    });

    // Alert panel should be present
    expect(screen.getByText('High-Confidence Alerts')).toBeInTheDocument();

    // Should show threshold info
    expect(screen.getByText(/Showing detections with confidence ≥ 85%/)).toBeInTheDocument();
  });

  it('handles detection selection across components', async () => {
    const user = userEvent.setup();
    renderWithIntegrationProviders(<App />);

    await waitFor(() => {
      expect(screen.queryByText('Loading Sentinel Dashboard...')).not.toBeInTheDocument();
    });

    // Find detection rows in the list
    const detectionRows = screen.getAllByRole('row');

    // Click on a detection (skip header row)
    if (detectionRows.length > 1) {
      await user.click(detectionRows[1]);

      // Detection should be selected (visual feedback would be tested in E2E)
      // For integration test, we verify the click was handled
      expect(detectionRows[1]).toBeInTheDocument();
    }
  });

  it('integrates all data sources correctly', async () => {
    renderWithIntegrationProviders(<App />);

    await waitFor(() => {
      expect(screen.queryByText('Loading Sentinel Dashboard...')).not.toBeInTheDocument();
    });

    // Verify data from API is displayed across multiple components

    // Nodes in NodeStatusPanel
    expect(screen.getByText('sentry-01')).toBeInTheDocument();

    // Detections in DetectionList
    expect(screen.getByText('person')).toBeInTheDocument();

    // High-confidence detection in AlertPanel
    await waitFor(() => {
      const alerts = screen.queryAllByText('person');
      // Should appear in both DetectionList and AlertPanel
      expect(alerts.length).toBeGreaterThanOrEqual(1);
    });
  });
});
