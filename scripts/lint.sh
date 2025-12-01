#!/usr/bin/env bash
# ==============================================================================
# lint.sh - Code Quality Checks
# ==============================================================================
#
# PURPOSE:
#   Run all code quality tools (ruff, mypy, pylint) on production and test
#   code. This is the first step in the quality pipeline - run before testing.
#
# USAGE:
#   ./scripts/lint.sh           # Run all linters (incremental)
#   ./scripts/lint.sh --fix     # Auto-fix issues where possible
#   ./scripts/lint.sh --clean   # Clear caches before running
#   ./scripts/lint.sh --ci      # CI mode (no auto-fix, strict failure)
#
# ==============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
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

# Activate virtual environment if available (and not already active)
if [ -z "$VIRTUAL_ENV" ] && [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Parse arguments
AUTO_FIX=false
CI_MODE=false
CLEAN_CACHE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            AUTO_FIX=true
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
            head -40 "$0" | grep "^#" | sed 's/^# *//'
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--fix] [--clean] [--ci]"
            exit 1
            ;;
    esac
done

# Check for required tools
MISSING_TOOLS=false
for tool in ruff mypy pylint; do
    if ! command -v $tool &> /dev/null; then
        echo -e "${RED}[ERROR] Required tool '$tool' not found in PATH${NC}"
        MISSING_TOOLS=true
    fi
done

if [ "$MISSING_TOOLS" = true ]; then
    echo "Please install dependencies (e.g., 'pip install -r requirements-dev.txt')"
    exit 1
fi

print_header "CODE QUALITY CHECKS"

# Track if any linter fails
FAILED=false

# Cache cleanup
if [ "$CLEAN_CACHE" = true ]; then
    print_header "CACHE CLEANUP"
    # Clean root caches and test caches
    for cache_dir in .pylint.d .mypy_cache .ruff_cache tests/.mypy_cache tests/.pylint.d; do
        if [ -d "$cache_dir" ]; then
            echo "[INFO] Clearing $cache_dir..."
            rm -rf "$cache_dir"
        fi
    done
    echo -e "${GREEN}[OK] Caches cleared${NC}"
fi

# RUFF
print_header "RUFF. Config in pyproject.toml"
if [ "$AUTO_FIX" = true ] && [ "$CI_MODE" = false ]; then
    echo "[MODE] Auto-fix enabled"
    ruff check --fix src/ tests/ || FAILED=true
else
    ruff check src/ tests/ || FAILED=true
fi

# MYPY - PRODUCTION
print_header "MYPY - PRODUCTION CODE. Config in pyproject.toml [tool.mypy]"
mypy src/ || FAILED=true

# MYPY - TESTS
print_header "MYPY - TEST CODE. Config in tests/mypy.ini"
# Run from root, pointing to config
mypy --config-file tests/mypy.ini tests/ || FAILED=true

# PYLINT - PRODUCTION
print_header "PYLINT - PRODUCTION CODE. Config in pyproject.toml [tool.pylint]"
pylint src/ || FAILED=true

# PYLINT - TESTS
print_header "PYLINT - TEST CODE. Config in tests/.pylintrc"
# Run from root, pointing to config
pylint --rcfile tests/.pylintrc tests/ || FAILED=true

print_header "SUMMARY"
if [ "$FAILED" = true ]; then
    echo -e "${RED}[FAIL] Some checks failed${NC}"
    echo ""
    echo "Fix issues and re-run: ./scripts/lint.sh"
    echo "Auto-fix where possible: ./scripts/lint.sh --fix"
    exit 1
else
    echo -e "${GREEN}[PASS] All checks passed${NC}"
    echo ""
    echo "Next steps:"
    echo "  ./scripts/test.sh - Run test suite"
fi
