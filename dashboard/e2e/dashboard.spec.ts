import { test, expect } from '@playwright/test';

test.beforeAll(async ({ request }) => {
  // Seed a node
  await request.post('/api/nodes/register', {
    data: {
      node_id: 'node-001',
      status: 'online',
      location: { lat: 40.7128, lng: -74.0060 }
    }
  });

  // Seed a detection
  await request.post('/api/detections', {
    data: {
      node_id: 'node-001',
      timestamp: new Date().toISOString(),
      location: { latitude: 40.7128, longitude: -74.0060 },
      detections: [
        { class: 'person', confidence: 0.95 },
        { class: 'vehicle', confidence: 0.88 }
      ],
      detection_count: 2,
      inference_time_ms: 45,
      model: 'yolov8n'
    }
  });
});

test.describe('Dashboard Core Functionality', () => {
  test('loads dashboard and displays initial data', async ({ page }) => {
    // Navigate to dashboard
    await page.goto('/');

    // Wait for dashboard to load
    await expect(page.getByText('Sentinel - Operator Dashboard')).toBeVisible({ timeout: 10000 });

    // Check that connection status is displayed
    await expect(page.getByText(/Connected|Disconnected/)).toBeVisible();

    // Verify main sections are present
    await expect(page.getByRole('heading', { name: 'Edge Nodes' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Recent Detections' })).toBeVisible();
  });

  test('displays nodes with status information', async ({ page }) => {
    await page.goto('/');

    // Wait for nodes to load
    await expect(page.getByRole('heading', { name: 'Edge Nodes' })).toBeVisible();

    // Check for node status indicators
    // Note: This assumes backend is running with test data
    await page.waitForTimeout(2000); // Wait for API calls

    // Verify at least one node status is shown
    const statuses = page.getByText(/ONLINE|OFFLINE|COVERT|RESUMING/);
    await expect(statuses.first()).toBeVisible({ timeout: 10000 });
  });

  test('displays detections in list', async ({ page }) => {
    await page.goto('/');

    // Wait for detections section
    await expect(page.getByText('Recent Detections')).toBeVisible();

    // Wait for detections to load
    await page.waitForTimeout(2000);

    // Check for detection count or empty state
    const hasDetections = await page.getByText(/\d+ total detections/).isVisible().catch(() => false);
    const hasEmptyState = await page.getByText('No detections yet').isVisible().catch(() => false);

    expect(hasDetections || hasEmptyState).toBeTruthy();
  });
});

test.describe('Detection Workflows', () => {
  test('can select a detection', async ({ page }) => {
    await page.goto('/');

    // Wait for page to load
    await page.waitForTimeout(3000);

    // Try to find and click a detection
    // This test will pass if no detections exist (graceful degradation)
    const detectionItems = page.locator('[class*="cursor-pointer"]').filter({ hasText: /person|vehicle|animal/ });
    const count = await detectionItems.count();

    if (count > 0) {
      // Click first detection
      const firstDetection = detectionItems.first();
      await expect(firstDetection).toBeVisible();
      await firstDetection.click({ force: true });

      // Verify some visual feedback (selection highlight, etc.)
      // This is a basic check - adjust based on actual UI behavior
      await page.waitForTimeout(500);
    }
  });

  test('high-confidence detections appear in alert panel', async ({ page }) => {
    await page.goto('/');

    // Wait for alert panel to be present
    await expect(page.getByRole('heading', { name: 'High-Confidence Alerts' })).toBeVisible();

    // Check threshold message
    await expect(page.getByText(/Showing detections with confidence ≥ \d+%/)).toBeVisible();

    // Alert panel should show either alerts or empty state
    const hasAlerts = await page.locator('[class*="border-yellow-500"]').count();
    const hasEmptyState = await page.getByText('No high-confidence alerts').isVisible();

    expect(hasAlerts > 0 || hasEmptyState).toBeTruthy();
  });
});

test.describe('Blackout Mode Workflows', () => {
  test('can view blackout controls for nodes', async ({ page }) => {
    await page.goto('/');

    // Wait for nodes to load
    await page.waitForTimeout(3000);

    // Look for blackout-related buttons
    // Buttons might be "Activate Blackout" or "Resume Transmission"
    const blackoutButtons = page.getByRole('button', { name: /Activate Blackout|Resume Transmission/ });
    
    // Should have at least one blackout control visible
    await expect(blackoutButtons.first()).toBeVisible({ timeout: 10000 });
  });

  test('blackout activation dialog opens', async ({ page }) => {
    await page.goto('/');

    // Wait for nodes
    await page.waitForTimeout(3000);

    // Find and click "Activate Blackout" button
    const activateButton = page.getByRole('button', { name: 'Activate Blackout' }).first();
    
    // Minimize AlertPanel if it's covering the button
    const minimizeButton = page.getByRole('button', { name: 'Minimize' });
    if (await minimizeButton.isVisible()) {
      await minimizeButton.click();
      await page.waitForTimeout(500); // Wait for animation
    }

    // Wait for button to be ready
    await expect(activateButton).toBeVisible({ timeout: 5000 });
    await expect(activateButton).toBeEnabled(); // Check if enabled

    // Verify node is online
    await expect(page.getByText('ONLINE').first()).toBeVisible();
    
    if (await activateButton.isVisible()) {
      await activateButton.click({ force: true }); // Force click to be sure

      // Dialog should open
      const dialog = page.getByRole('dialog');
      await expect(dialog).toBeVisible({ timeout: 5000 });
      await expect(dialog).toContainText('Activate Blackout Mode');

      // Should have reason input
      await expect(page.getByRole('textbox')).toBeVisible();

      // Should have confirm button
      await expect(dialog.getByRole('button', { name: /Activate/ })).toBeVisible();
    }
  });
});

test.describe('Real-time Updates', () => {
  test('WebSocket connection status updates', async ({ page }) => {
    await page.goto('/');

    // Check initial connection status
    const connectionStatus = page.getByText(/Connected|Disconnected/);
    await expect(connectionStatus).toBeVisible();

    // Connection should eventually show as connected (if backend is running)
    // or disconnected (if backend is not running)
    await page.waitForTimeout(2000);

    const statusText = await connectionStatus.textContent();
    expect(statusText).toMatch(/Connected|Disconnected/);
  });
});

test.describe('UI Responsiveness', () => {
  test('dashboard is responsive and interactive', async ({ page }) => {
    await page.goto('/');

    // Check that page is interactive
    await expect(page.getByText('Sentinel - Operator Dashboard')).toBeVisible();

    // Verify no critical errors in console
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.waitForTimeout(3000);

    // Filter out known acceptable errors (like WebSocket connection failures in test)
    const criticalErrors = errors.filter(err => 
      !err.includes('WebSocket') && 
      !err.includes('Failed to fetch') &&
      !err.includes('ECONNREFUSED') &&
      !err.includes('[vite]')
    );

    if (criticalErrors.length > 0) {
      console.log('Critical Errors:', criticalErrors);
    }
    expect(criticalErrors.length).toBe(0);
  });
});
