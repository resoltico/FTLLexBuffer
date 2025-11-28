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
#   ./scripts/lint.sh           # Run all linters
#   ./scripts/lint.sh --fix     # Auto-fix issues where possible
#   ./scripts/lint.sh --ci      # CI mode (strict, no auto-fix)
#
# OUTPUTS:
#   - Ruff results (fast linting and formatting)
#   - Mypy results (type checking)
#   - Pylint results (comprehensive analysis)
#
# QUALITY STANDARDS:
#   Production code (src/): Strict (10/10 pylint, mypy --strict)
#   Test code (tests/):     Pragmatic (9/10 pylint, relaxed mypy)
#
# ECOSYSTEM:
#   1. lint.sh - Code quality (THIS SCRIPT - run first)
#   2. test.sh - Correctness
#
# CI/CD:
#   GitHub Actions runs: ruff check, mypy, pylint
#   Must pass before merge to main
#
# ==============================================================================

set -e

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
AUTO_FIX=false
CI_MODE=false

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
        -h|--help)
            head -40 "$0" | grep "^#" | sed 's/^# *//'
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--fix] [--ci]"
            exit 1
            ;;
    esac
done

echo "========================================="
echo "FTLLexBuffer Code Quality Checks"
echo "========================================="
echo ""
echo "Standards:"
echo "  Production (src/): mypy --strict, pylint 10/10"
echo "  Tests (tests/):    mypy relaxed, pylint 9/10"
echo ""

# Track if any linter fails
FAILED=false

echo "========================================="
echo "CACHE CLEANUP"
echo "========================================="
# Clear caches for fresh results
for cache_dir in .pylint.d .mypy_cache .ruff_cache; do
    if [ -d "$cache_dir" ]; then
        echo "[INFO] Clearing $cache_dir..."
        rm -rf "$cache_dir"
    fi
done
echo "[OK] Caches cleared"
echo ""

echo "========================================="
echo "RUFF (Fast linting)"
echo "========================================="
if [ "$AUTO_FIX" = true ] && [ "$CI_MODE" = false ]; then
    echo "[MODE] Auto-fix enabled"
    ruff check --fix src/ tests/ || FAILED=true
else
    ruff check src/ tests/ || FAILED=true
fi
echo ""

echo "========================================="
echo "MYPY - Production Code (strict)"
echo "========================================="
echo "[CONFIG] pyproject.toml [tool.mypy] strict=true"
mypy src/ || FAILED=true
echo ""

echo "========================================="
echo "MYPY - Test Code (relaxed)"
echo "========================================="
echo "[CONFIG] tests/mypy.ini strict=false"
(cd tests && mypy .) || FAILED=true
echo ""

echo "========================================="
echo "PYLINT - Production Code"
echo "========================================="
echo "[CONFIG] pyproject.toml [tool.pylint]"
pylint src/ || FAILED=true
echo ""

echo "========================================="
echo "PYLINT - Test Code"
echo "========================================="
echo "[CONFIG] tests/.pylintrc"
(cd tests && pylint .) || FAILED=true
echo ""

echo "========================================="
if [ "$FAILED" = true ]; then
    echo "[FAIL] Some checks failed"
    echo ""
    echo "Fix issues and re-run: ./scripts/lint.sh"
    echo "Auto-fix where possible: ./scripts/lint.sh --fix"
    exit 1
else
    echo "[PASS] All checks passed"
    echo ""
    echo "Next steps:"
    echo "  ./scripts/test.sh - Run test suite"
    echo "  ./scripts/all.sh  - Run complete pipeline (lint + test)"
fi
echo "========================================="
