#!/usr/bin/env bash
# ==============================================================================
# test.sh - FTLLexBuffer Test Suite Runner
# ==============================================================================
#
# PURPOSE:
#   Run the full pytest test suite with coverage reporting and Hypothesis
#   property-based testing. Automatically uses discovered examples from
#   previous fuzzing campaigns (.hypothesis/examples/).
#
# USAGE:
#   ./scripts/test.sh           # Run all tests with coverage
#   ./scripts/test.sh --quick   # Run tests without coverage (faster)
#   ./scripts/test.sh --ci      # CI mode (no interactive output)
#
# OUTPUTS:
#   - Test results to stdout
#   - Coverage report (95% threshold enforced)
#   - Hypothesis statistics (example counts, shrink attempts)
#
# DATA CONSUMED:
#   - .hypothesis/examples/ - Replays edge cases discovered during testing
#
# DATA PRODUCED:
#   - .hypothesis/examples/ - Adds any new failures discovered
#   - Coverage data for CI reporting
#
# ECOSYSTEM:
#   1. lint.sh - Code quality (run first)
#   2. test.sh - Correctness (this script)
#
# CI/CD:
#   GitHub Actions runs this via: pytest tests/ --cov=...
#   This script provides identical behavior for local development.
#
# ==============================================================================

set -e  # Exit on error

# Check if running in project root
if [ ! -f "pyproject.toml" ]; then
    echo "[ERROR] Must run from project root directory"
    exit 1
fi

# Activate virtual environment if available
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Parse arguments
QUICK_MODE=false
CI_MODE=false
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
        -h|--help)
            head -45 "$0" | grep "^#" | sed 's/^# *//'
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--quick] [--ci]"
            exit 1
            ;;
    esac
done

echo "========================================="
echo "FTLLexBuffer Test Suite"
echo "========================================="
echo ""

# Show Hypothesis database status
if [ -d ".hypothesis/examples" ]; then
    EXAMPLE_COUNT=$(find .hypothesis/examples -type d -mindepth 1 | wc -l | tr -d ' ')
    echo "[INFO] Hypothesis database: $EXAMPLE_COUNT discovered examples"
    echo "[INFO] These edge cases will be replayed during testing"
else
    echo "[INFO] No Hypothesis database found (first run or after clean)"
fi
echo ""

echo "========================================="
echo "CACHE CLEANUP"
echo "========================================="
# Clear pytest cache for fresh test runs
if [ -d ".pytest_cache" ]; then
    echo "[INFO] Clearing pytest cache..."
    rm -rf .pytest_cache
    echo "[OK] Cache cleared"
else
    echo "[INFO] No pytest cache (fresh state)"
fi
echo ""

echo "========================================="
echo "RUNNING TESTS"
echo "========================================="

# Build pytest command
PYTEST_CMD="pytest tests/"

if [ "$QUICK_MODE" = true ]; then
    echo "[MODE] Quick mode - no coverage"
    PYTEST_CMD="$PYTEST_CMD -q"
else
    echo "[MODE] Full mode - with coverage (95% threshold)"
    PYTEST_CMD="$PYTEST_CMD --cov=src/ftllexbuffer --cov-report=term-missing --cov-fail-under=95"
fi

# Add Hypothesis statistics unless in CI mode
if [ "$CI_MODE" = false ]; then
    PYTEST_CMD="$PYTEST_CMD --hypothesis-show-statistics"
fi

echo "[CMD] $PYTEST_CMD"
echo ""

# Run tests and capture output for analysis
PYTEST_OUTPUT_FILE=$(mktemp)
$PYTEST_CMD 2>&1 | tee "$PYTEST_OUTPUT_FILE"
TEST_EXIT_CODE=${PIPESTATUS[0]}

echo ""
echo "========================================="
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "[PASS] All tests passed!"

    # Check if new examples were added by Hypothesis during this run
    if [ -d ".hypothesis/examples" ]; then
        # Count examples modified in last 5 minutes (this test run)
        NEW_EXAMPLES=$(find .hypothesis/examples -type f -mmin -5 2>/dev/null | wc -l | tr -d ' ')
        if [ "$NEW_EXAMPLES" -gt 0 ]; then
            echo ""
            echo "[INFO] Hypothesis saved $NEW_EXAMPLES new edge cases"
            echo "[INFO] These will be replayed automatically in future test runs"
        fi
    fi
else
    echo "[FAIL] Tests failed with exit code: $TEST_EXIT_CODE"
    echo ""

    # Check if this was a Hypothesis failure by analyzing test output
    if grep -q "Falsifying example:" "$PYTEST_OUTPUT_FILE"; then
        echo "============================================"
        echo "[ALERT] HYPOTHESIS DISCOVERED A BUG"
        echo "============================================"
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

echo "========================================="
echo ""
echo "Next steps:"
echo "  ./scripts/lint.sh - Check code quality"
echo "  ./scripts/all.sh  - Run complete pipeline (lint + test)"
echo ""

exit $TEST_EXIT_CODE
