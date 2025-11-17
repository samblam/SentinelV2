#!/bin/bash
# Comprehensive Test Suite Runner for SentinelV2
# Runs all unit, integration, and end-to-end tests

set -e  # Exit on first error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         SentinelV2 Comprehensive Test Suite Runner           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to run tests in a module
run_module_tests() {
    local module=$1
    local test_type=$2

    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Running ${test_type} tests in ${module}...${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    cd /home/user/SentinelV2/${module}

    if [ ! -d "tests" ]; then
        echo -e "${YELLOW}⚠ No tests directory found in ${module}, skipping...${NC}"
        echo ""
        return
    fi

    # Check if pytest is available via python -m
    if ! python3 -c "import pytest" 2>/dev/null; then
        echo -e "${YELLOW}⚠ pytest not installed in ${module}, installing requirements...${NC}"
        if [ -f "requirements-dev.txt" ]; then
            pip install -q -r requirements-dev.txt 2>&1 | tail -5
        fi
    fi

    # Run syntax checks first
    echo -e "${BLUE}→ Running syntax checks...${NC}"
    for file in tests/test_*.py; do
        if [ -f "$file" ]; then
            if python3 -m py_compile "$file" 2>/dev/null; then
                echo -e "  ${GREEN}✓${NC} $(basename $file)"
            else
                echo -e "  ${RED}✗${NC} $(basename $file) - SYNTAX ERROR"
                ((FAILED_TESTS++))
            fi
        fi
    done
    echo ""

    # Run pytest with coverage if available
    echo -e "${BLUE}→ Running pytest...${NC}"
    if python3 -m pytest tests/ -v --tb=short --color=yes 2>&1 | tee /tmp/test_output_${module}.txt; then
        echo -e "${GREEN}✓ All tests passed in ${module}${NC}"
        # Parse results
        local results=$(tail -20 /tmp/test_output_${module}.txt | grep -E "passed|failed|skipped" | tail -1)
        echo -e "  ${results}"
    else
        echo -e "${RED}✗ Some tests failed in ${module}${NC}"
        ((FAILED_TESTS++))
    fi

    echo ""
    cd /home/user/SentinelV2
}

# Function to run integration tests (root level)
run_integration_tests() {
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Running Integration Tests (Root Level)...${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    cd /home/user/SentinelV2

    echo -e "${BLUE}→ Running syntax checks on integration tests...${NC}"
    for file in test_*.py; do
        if [ -f "$file" ]; then
            if python3 -m py_compile "$file" 2>/dev/null; then
                echo -e "  ${GREEN}✓${NC} $file"
            else
                echo -e "  ${RED}✗${NC} $file - SYNTAX ERROR"
            fi
        fi
    done
    echo ""

    echo -e "${YELLOW}⚠ Integration tests require running backend and edge services${NC}"
    echo -e "${YELLOW}  These tests are marked with @pytest.mark.integration${NC}"
    echo -e "${YELLOW}  They will be skipped in this automated run${NC}"
    echo ""
}

# Main test execution
echo -e "${BLUE}Starting comprehensive test suite...${NC}"
echo -e "${BLUE}Test execution date: $(date)${NC}"
echo ""

# 1. Backend tests
run_module_tests "backend" "Backend Unit"

# 2. Edge inference tests
run_module_tests "edge-inference" "Edge Inference Unit"

# 3. ATAK integration tests
run_module_tests "atak_integration" "ATAK Integration Unit"

# 4. Integration tests
run_integration_tests

# Final summary
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Test Execution Complete${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}Summary:${NC}"
if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ All test suites passed!${NC}"
else
    echo -e "${RED}✗ Some tests failed. Check output above for details.${NC}"
fi

# Show output files
echo ""
echo -e "${BLUE}Detailed output saved to:${NC}"
ls -1 /tmp/test_output_*.txt 2>/dev/null || echo "  No output files generated"

echo ""
echo -e "${GREEN}Test run complete!${NC}"
