# Dashboard E2E Tests

End-to-end tests for the Sentinel Dashboard using Playwright.

## Running E2E Tests

### Prerequisites

- Backend server running on `http://localhost:8001`
- Dashboard dev server will start automatically

### Commands

```bash
# Run all E2E tests (headless)
npm run test:e2e

# Run E2E tests with UI mode (interactive)
npm run test:e2e:ui

# Run E2E tests in headed mode (see browser)
npm run test:e2e:headed

# Debug E2E tests
npm run test:e2e:debug
```

## Test Coverage

### Dashboard Core Functionality

- ✅ Dashboard loads and displays initial data
- ✅ Nodes display with status information
- ✅ Detections display in list
- ✅ Connection status updates

### Detection Workflows

- ✅ Detection selection
- ✅ High-confidence alerts in alert panel
- ✅ Detection details display

### Blackout Mode Workflows

- ✅ Blackout controls visible for nodes
- ✅ Blackout activation dialog opens
- ✅ Blackout mode activation/deactivation

### Real-time Updates

- ✅ WebSocket connection status
- ✅ Live detection updates (when backend is running)

### UI Responsiveness

- ✅ Dashboard is interactive
- ✅ No critical console errors

## Test Strategy

These E2E tests are designed to:

1. **Work with or without backend** - Tests gracefully handle missing data
2. **Test real user workflows** - Simulate actual user interactions
3. **Catch integration issues** - Verify components work together
4. **Provide visual feedback** - Screenshots/videos on failure

## Notes

- Tests automatically start the dev server (`npm run dev`)
- Tests run in Chromium by default
- Failed tests capture screenshots and videos
- Tests are resilient to backend availability
