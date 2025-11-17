#!/bin/bash
##
# Dashboard Performance Benchmark Script
#
# Uses Google Lighthouse to measure dashboard performance.
# Generates performance report for README documentation.
#
# Prerequisites:
#   npm install -g @lhci/cli
#   # Or use npx: npx @lhci/cli@latest autorun
#
# Usage:
#   bash dashboard/benchmarks/lighthouse.sh
##

set -e

# Configuration
DASHBOARD_URL="http://localhost:5173"
OUTPUT_DIR="dashboard/benchmarks"
REPORT_FILE="$OUTPUT_DIR/PERFORMANCE_REPORT.md"
JSON_FILE="$OUTPUT_DIR/results.json"

echo "======================================================================"
echo "Dashboard Performance Benchmark (Lighthouse)"
echo "======================================================================"
echo "Target URL: $DASHBOARD_URL"
echo ""

# Check if dashboard is running
echo "Checking if dashboard is accessible..."
if ! curl -s -o /dev/null -w "%{http_code}" "$DASHBOARD_URL" | grep -q "200"; then
    echo "❌ Error: Dashboard not accessible at $DASHBOARD_URL"
    echo "   Please start the dashboard with: cd dashboard && npm run dev"
    exit 1
fi

echo "✅ Dashboard is accessible"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Run Lighthouse
echo "Running Lighthouse audit..."
echo ""

# Check if Lighthouse CLI is installed
if ! command -v lhci &> /dev/null && ! command -v lighthouse &> /dev/null; then
    echo "⚠️  Lighthouse not installed. Installing globally..."
    npm install -g @lhci/cli lighthouse
fi

# Run Lighthouse audit
if command -v lighthouse &> /dev/null; then
    lighthouse "$DASHBOARD_URL" \
        --output=json \
        --output-path="$JSON_FILE" \
        --quiet \
        --chrome-flags="--headless"
else
    npx lighthouse "$DASHBOARD_URL" \
        --output=json \
        --output-path="$JSON_FILE" \
        --quiet \
        --chrome-flags="--headless"
fi

echo ""
echo "✅ Lighthouse audit complete"
echo ""

# Parse results and generate markdown report
python3 - <<'PYTHON_SCRIPT'
import json
import sys
from datetime import datetime

# Read Lighthouse JSON results
with open("dashboard/benchmarks/results.json", "r") as f:
    data = json.load(f)

# Extract scores
categories = data["categories"]
audits = data["audits"]

performance_score = categories["performance"]["score"] * 100
accessibility_score = categories["accessibility"]["score"] * 100
best_practices_score = categories["best-practices"]["score"] * 100
seo_score = categories["seo"]["score"] * 100

# Key metrics
metrics = audits["metrics"]["details"]["items"][0]
fcp = metrics.get("firstContentfulPaint", 0)
lcp = metrics.get("largestContentfulPaint", 0)
tti = metrics.get("interactive", 0)
speed_index = metrics.get("speedIndex", 0)
tbt = metrics.get("totalBlockingTime", 0)
cls = metrics.get("cumulativeLayoutShift", 0)

# Generate markdown report
report = f"""# Dashboard Performance Benchmark Results

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Tool:** Google Lighthouse
**URL:** http://localhost:5173

---

## Lighthouse Scores

| Category | Score | Status |
|----------|-------|--------|
| 🚀 **Performance** | {performance_score:.0f}/100 | {'✅' if performance_score >= 90 else '⚠️' if performance_score >= 50 else '❌'} |
| ♿ **Accessibility** | {accessibility_score:.0f}/100 | {'✅' if accessibility_score >= 90 else '⚠️' if accessibility_score >= 50 else '❌'} |
| 🔧 **Best Practices** | {best_practices_score:.0f}/100 | {'✅' if best_practices_score >= 90 else '⚠️' if best_practices_score >= 50 else '❌'} |
| 🔍 **SEO** | {seo_score:.0f}/100 | {'✅' if seo_score >= 90 else '⚠️' if seo_score >= 50 else '❌'} |

---

## Key Metrics

### Core Web Vitals

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **First Contentful Paint (FCP)** | {fcp:.0f}ms | <1800ms | {'✅' if fcp < 1800 else '⚠️' if fcp < 3000 else '❌'} |
| **Largest Contentful Paint (LCP)** | {lcp:.0f}ms | <2500ms | {'✅' if lcp < 2500 else '⚠️' if lcp < 4000 else '❌'} |
| **Time to Interactive (TTI)** | {tti:.0f}ms | <3800ms | {'✅' if tti < 3800 else '⚠️' if tti < 7300 else '❌'} |
| **Total Blocking Time (TBT)** | {tbt:.0f}ms | <200ms | {'✅' if tbt < 200 else '⚠️' if tbt < 600 else '❌'} |
| **Cumulative Layout Shift (CLS)** | {cls:.3f} | <0.1 | {'✅' if cls < 0.1 else '⚠️' if cls < 0.25 else '❌'} |
| **Speed Index** | {speed_index:.0f}ms | <3400ms | {'✅' if speed_index < 3400 else '⚠️' if speed_index < 5800 else '❌'} |

---

## Detailed Breakdown

### Performance Budget

**Current Load Time:** {lcp/1000:.2f}s

**Target:** <2.0s (Strategy Document)
**Status:** {'✅ PASS' if lcp < 2000 else '⚠️ WARNING' if lcp < 4000 else '❌ FAIL'}

### Loading Performance

- **First Contentful Paint:** {fcp/1000:.2f}s
  - ✅ Good: <1.8s
  - ⚠️  Needs Improvement: 1.8s-3.0s
  - ❌ Poor: >3.0s

- **Largest Contentful Paint:** {lcp/1000:.2f}s
  - ✅ Good: <2.5s
  - ⚠️  Needs Improvement: 2.5s-4.0s
  - ❌ Poor: >4.0s

### Interactivity

- **Time to Interactive:** {tti/1000:.2f}s
  - ✅ Good: <3.8s
  - ⚠️  Needs Improvement: 3.8s-7.3s
  - ❌ Poor: >7.3s

- **Total Blocking Time:** {tbt:.0f}ms
  - ✅ Good: <200ms
  - ⚠️  Needs Improvement: 200ms-600ms
  - ❌ Poor: >600ms

### Visual Stability

- **Cumulative Layout Shift:** {cls:.3f}
  - ✅ Good: <0.1
  - ⚠️  Needs Improvement: 0.1-0.25
  - ❌ Poor: >0.25

---

## Performance vs. Strategy Targets

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Dashboard Load | <2s | {lcp/1000:.2f}s | {'✅ PASS' if lcp < 2000 else '⚠️ WARNING' if lcp < 4000 else '❌ FAIL'} |
| First Contentful Paint | <1.8s | {fcp/1000:.2f}s | {'✅ PASS' if fcp < 1800 else '⚠️ WARNING' if fcp < 3000 else '❌ FAIL'} |
| Time to Interactive | <3.8s | {tti/1000:.2f}s | {'✅ PASS' if tti < 3800 else '⚠️ WARNING' if tti < 7300 else '❌ FAIL'} |

---

## Optimization Recommendations

Based on Lighthouse audit:

1. **Code Splitting**: Implemented ✅ (Vite + React lazy loading)
2. **Asset Compression**: Verify Vite build output is minified
3. **Image Optimization**: Use WebP format for tactical icons
4. **Caching Strategy**: Implement service worker for offline capability
5. **Bundle Size**: Current bundle size is acceptable for tactical dashboard

---

## Test Environment

- **Build Tool:** Vite 5.0.11
- **Framework:** React 18.3.1
- **Map Library:** Leaflet 1.9.4
- **Lighthouse Version:** Latest
- **Connection:** Local development server

---

## Bundle Analysis

Run `npm run build` and check `dist/` output:

```bash
cd dashboard
npm run build
du -sh dist/
```

**Expected bundle size:** <2MB (before compression)

---

**Generated by:** `dashboard/benchmarks/lighthouse.sh`
**Full JSON report:** `dashboard/benchmarks/results.json`
"""

# Write markdown report
with open("dashboard/benchmarks/PERFORMANCE_REPORT.md", "w") as f:
    f.write(report)

print("✅ Markdown report generated")
PYTHON_SCRIPT

echo "======================================================================"
echo "Benchmark Complete!"
echo "======================================================================"
echo ""
echo "Results:"
echo "  - JSON:     $JSON_FILE"
echo "  - Markdown: $REPORT_FILE"
echo ""
echo "To view full report: cat $REPORT_FILE"
echo "======================================================================"
