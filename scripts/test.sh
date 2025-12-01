#!/usr/bin/env bash
# ==============================================================================
# test.sh - Test Suite Runner
# ==============================================================================
#
# PURPOSE:
#   Run the full pytest test suite with coverage reporting and Hypothesis
#   property-based testing. Automatically uses discovered examples from
#   previous fuzzing campaigns (.hypothesis/examples/).
#
# USAGE:
#   ./scripts/test.sh           # Run all tests with coverage
#   ./scripts/test.sh --quick   # Run tests without coverage
#   ./scripts/test.sh --clean   # Clear pytest cache before running
#   ./scripts/test.sh --ci      # CI mode
#
# ==============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Helper for printing headers
print_header() {
    echo ""
    echo -e "${BLUE}=================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=================================================================${NC}"
}

# Check if running in project root
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}[ERROR] Must run from project root directory${NC}"
    exit 1
fi

# Activate virtual environment if available
if [ -z "$VIRTUAL_ENV" ] && [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Parse arguments
QUICK_MODE=false
CI_MODE=false
CLEAN_CACHE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK_MODE=true
            shift
            ;;
        --ci)
            CI_MODE=true
            shift
            ;;
        --clean)
            CLEAN_CACHE=true
            shift
            ;;
        -h|--help)
            head -45 "$0" | grep "^#" | sed 's/^# *//'
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--quick] [--clean] [--ci]"
            exit 1
            ;;
    esac
done

# Check for required tools
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}[ERROR] Required tool 'pytest' not found in PATH${NC}"
    echo "Please install dependencies (e.g., 'pip install -r requirements-dev.txt')"
    exit 1
fi

print_header "TEST SUITE"

# Show Hypothesis database status
if [ -d ".hypothesis/examples" ]; then
    EXAMPLE_COUNT=$(find .hypothesis/examples -type d -mindepth 1 | wc -l | tr -d ' ')
    echo "[INFO] Hypothesis database: $EXAMPLE_COUNT discovered examples"
    echo "[INFO] These edge cases will be replayed during testing"
else
    echo "[INFO] No Hypothesis database found (first run or after clean)"
fi

# Cache cleanup
if [ "$CLEAN_CACHE" = true ]; then
    print_header "CACHE CLEANUP"
    if [ -d ".pytest_cache" ]; then
        echo "[INFO] Clearing pytest cache..."
        rm -rf .pytest_cache
        echo -e "${GREEN}[OK] Cache cleared${NC}"
    else
        echo "[INFO] No pytest cache (fresh state)"
    fi
fi

print_header "RUNNING TESTS"

# Build pytest command
PYTEST_CMD="pytest tests/"

if [ "$QUICK_MODE" = true ]; then
    echo "[MODE] Quick mode - no coverage"
    PYTEST_CMD="$PYTEST_CMD -q"
else
    echo "[MODE] Full mode - with coverage (95% threshold)"
    
    # Dynamic package detection
    # Finds the first directory in src/ to use as the package name
    PACKAGE_NAME=$(find src -mindepth 1 -maxdepth 1 -type d | head -n 1 | xargs basename)
    
    if [ -z "$PACKAGE_NAME" ]; then
        echo -e "${YELLOW}[WARNING] Could not detect package in src/. Running without coverage.${NC}"
    else
        echo "[INFO] Detected package: $PACKAGE_NAME"
        PYTEST_CMD="$PYTEST_CMD --cov=src/$PACKAGE_NAME --cov-report=term-missing --cov-fail-under=95"
    fi
fi

# Add Hypothesis statistics unless in CI mode
if [ "$CI_MODE" = false ]; then
    PYTEST_CMD="$PYTEST_CMD --hypothesis-show-statistics"
fi

echo "[CMD] $PYTEST_CMD"
echo ""

# Run tests and capture output for analysis
PYTEST_OUTPUT_FILE=$(mktemp)
# We use set +e here because we want to capture the exit code manually
set +e
$PYTEST_CMD 2>&1 | tee "$PYTEST_OUTPUT_FILE"
TEST_EXIT_CODE=${PIPESTATUS[0]}
set -e

echo ""
print_header "SUMMARY"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}[PASS] All tests passed!${NC}"

    # Check if new examples were added by Hypothesis during this run
    if [ -d ".hypothesis/examples" ]; then
        # Count examples modified in last 5 minutes (this test run)
        NEW_EXAMPLES=$(find .hypothesis/examples -type f -mmin -5 2>/dev/null | wc -l | tr -d ' ')
        if [ "$NEW_EXAMPLES" -gt 0 ]; then
            echo ""
            echo -e "${BLUE}[INFO] Hypothesis saved $NEW_EXAMPLES new edge cases${NC}"
            echo "[INFO] These will be replayed automatically in future test runs"
        fi
    fi
else
    echo -e "${RED}[FAIL] Tests failed with exit code: $TEST_EXIT_CODE${NC}"
    echo ""

    # Check if this was a Hypothesis failure by analyzing test output
    if grep -q "Falsifying example:" "$PYTEST_OUTPUT_FILE"; then
        echo -e "${RED}============================================${NC}"
        echo -e "${RED}[ALERT] HYPOTHESIS DISCOVERED A BUG${NC}"
        echo -e "${RED}============================================${NC}"
        echo ""
        echo "Hypothesis found a failing input that breaks your code."
        echo "This is a REAL BUG that needs investigation."
        echo ""
        echo "What to do:"
        echo "  1. Look at the 'Falsifying example' in the test output above"
        echo "  2. This example has been saved to .hypothesis/examples/"
        echo "  3. Fix the bug in your code"
        echo "  4. Re-run tests - the example will replay to verify the fix"
        echo "  5. (Optional) Add @example() decorator to test for documentation"
        echo ""
        echo "This failing example will AUTOMATICALLY replay on every"
        echo "future test run until you fix it - permanent regression protection!"
        echo ""
    fi
fi

# Cleanup temporary file
rm -f "$PYTEST_OUTPUT_FILE"

echo ""
echo "Next steps:"
echo "  ./scripts/lint.sh - Check code quality"
echo ""

exit $TEST_EXIT_CODE
