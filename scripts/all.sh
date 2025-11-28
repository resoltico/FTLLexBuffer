#!/usr/bin/env bash
# ==============================================================================
# all.sh - Run Complete Quality Pipeline
# ==============================================================================
#
# PURPOSE:
#   Execute all quality scripts in the correct order. Use this for full
#   validation before commits or releases.
#
# USAGE:
#   ./scripts/all.sh       # Run lint + test
#   ./scripts/all.sh --ci  # CI mode (no prompts)
#
# EXECUTION ORDER:
#   1. lint.sh - Code quality checks
#   2. test.sh - Run test suite
#
# ==============================================================================

set -e

# Check if running in project root
if [ ! -f "pyproject.toml" ]; then
    echo "[ERROR] Must run from project root directory"
    exit 1
fi

# Parse arguments
CI_MODE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --ci)
            CI_MODE="--ci"
            shift
            ;;
        -h|--help)
            head -20 "$0" | grep "^#" | sed 's/^# *//'
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--ci]"
            exit 1
            ;;
    esac
done

echo "========================================="
echo "FTLLexBuffer Quality Pipeline"
echo "========================================="
echo ""
echo "Execution order:"
echo "  1. lint.sh - Code quality"
echo "  2. test.sh - Test suite"
echo ""

# Step 1: Lint
echo "========================================="
echo "STEP 1/2: LINT"
echo "========================================="
./scripts/lint.sh $CI_MODE

# Step 2: Test
echo ""
echo "========================================="
echo "STEP 2/2: TEST"
echo "========================================="
./scripts/test.sh $CI_MODE

echo ""
echo "========================================="
echo "[PASS] All quality checks passed!"
echo "========================================="
