#!/usr/bin/env bash
# Release automation script for FTLLexBuffer
#
# This script automates the release process by:
# 1. Validating version consistency across all sources
# 2. Running comprehensive test suite
# 3. Creating git tag with proper naming
# 4. Providing push commands for release
#
# Usage:
#   ./scripts/release.sh           # Interactive mode with validation
#   ./scripts/release.sh --help    # Show usage information
#   ./scripts/release.sh --dry-run # Validate only, no git operations

set -euo pipefail

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Script configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Parse command line arguments
DRY_RUN=false
SKIP_TESTS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            cat <<EOF
Release Automation Script for FTLLexBuffer

Usage: ./scripts/release.sh [OPTIONS]

OPTIONS:
    --help, -h       Show this help message
    --dry-run        Validate only, no git operations
    --skip-tests     Skip test suite (not recommended)

WORKFLOW:
    1. Validates version in pyproject.toml matches __version__
    2. Checks git working directory is clean
    3. Runs full test suite (unless --skip-tests)
    4. Creates git tag: v{VERSION}
    5. Displays push commands

REQUIREMENTS:
    - pip install -e . must have been run
    - All changes must be committed
    - Tests must pass

EXAMPLE:
    # Recommended workflow (automated version bump)
    ./scripts/bump-version.sh patch  # Updates pyproject.toml + runs pip install -e .
    vim CHANGELOG.md                 # Document changes
    git add pyproject.toml CHANGELOG.md
    git commit -m "Bump version to 0.2.0"
    ./scripts/release.sh

    # Manual workflow (if version already updated)
    pip install -e .                 # Refresh package metadata
    ./scripts/release.sh

    # Validation only (no git tag)
    ./scripts/release.sh --dry-run
EOF
            exit 0
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        *)
            echo -e "${RED}[ERROR] Unknown option: $1${NC}"
            echo "Run './scripts/release.sh --help' for usage information"
            exit 1
            ;;
    esac
done

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $*"
}

# Check if running from project root or scripts directory
cd "$PROJECT_ROOT"

echo "=========================================="
echo "FTLLexBuffer Release Automation"
echo "=========================================="
echo ""

# Check required dependencies
log_info "Checking required dependencies..."

if ! command -v python &> /dev/null; then
    log_error "Python not found in PATH"
    exit 1
fi

if ! command -v curl &> /dev/null; then
    log_warn "curl not found in PATH"
    log_warn "PyPI availability check will be skipped"
fi

log_success "Required dependencies available"

# Check if in virtual environment (informational only)
if [[ -z "$VIRTUAL_ENV" ]]; then
    log_warn "No virtual environment detected"
    log_warn "Consider running: python -m venv .venv && source .venv/bin/activate"
    log_warn "Proceeding with system Python..."
    echo ""
fi

# Step 1: Extract version from pyproject.toml
log_info "Extracting version from pyproject.toml..."

if ! command -v python &> /dev/null; then
    log_error "Python not found in PATH"
    exit 1
fi

# Check Python version (FTLLexBuffer requires Python 3.13+)
log_info "Validating Python version..."
PYTHON_VERSION=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')

if ! python -c 'import sys; sys.exit(0 if sys.version_info >= (3, 13) else 1)' 2>/dev/null; then
    log_error "Python $PYTHON_VERSION detected. FTLLexBuffer requires Python 3.13+"
    log_warn "Current Python: $PYTHON_VERSION"
    log_warn "Required: 3.13 or newer"
    exit 1
fi

log_success "Python version valid: $PYTHON_VERSION"

PYPROJECT_VERSION=$(python <<EOF
import sys
import tomllib
from pathlib import Path

try:
    with open('pyproject.toml', 'rb') as f:
        data = tomllib.load(f)
        print(data['project']['version'])
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    exit(1)
EOF
)

if [[ -z "$PYPROJECT_VERSION" ]]; then
    log_error "Failed to extract version from pyproject.toml"
    exit 1
fi

log_success "pyproject.toml version: $PYPROJECT_VERSION"

# Step 2: Extract runtime __version__
log_info "Extracting runtime __version__..."

RUNTIME_VERSION=$(python -c "import ftllexbuffer; print(ftllexbuffer.__version__)" 2>&1)
exit_code=$?

if [[ $exit_code -ne 0 ]]; then
    log_error "Failed to import ftllexbuffer"
    echo "$RUNTIME_VERSION"
    log_warn "Run 'pip install -e .' to install package in editable mode"
    exit 1
fi

log_success "Runtime __version__: $RUNTIME_VERSION"

# Step 3: Check for development placeholder FIRST
log_info "Checking for development placeholder..."

if [[ "$RUNTIME_VERSION" == "0.0.0+dev" ]] || [[ "$RUNTIME_VERSION" == "0.0.0+unknown" ]]; then
    log_error "Version is development placeholder: $RUNTIME_VERSION"
    log_warn "Update version in pyproject.toml and run 'pip install -e .'"
    exit 1
fi

log_success "Not a development placeholder"

# Step 4: Validate version consistency
log_info "Validating version consistency..."

if [[ "$PYPROJECT_VERSION" != "$RUNTIME_VERSION" ]]; then
    log_error "Version mismatch detected!"
    echo ""
    echo "  pyproject.toml:  $PYPROJECT_VERSION"
    echo "  __version__:     $RUNTIME_VERSION"
    echo ""
    log_warn "Solution: Run 'pip install -e .' to refresh package metadata"
    exit 1
fi

log_success "Version consistency validated: $PYPROJECT_VERSION"

# Step 5: Validate semantic versioning format
log_info "Validating semantic versioning format..."

# Improved regex: prevents trailing separators like "0.1.0-" or "0.1.0+"
# Pre-release: one or more alphanumeric identifiers separated by dots
# Build metadata: one or more alphanumeric identifiers separated by dots
if ! echo "$RUNTIME_VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*)?(\+[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*)?$'; then
    log_error "Invalid semantic version format: $RUNTIME_VERSION"
    log_warn "Expected: MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]"
    log_warn "Examples: 0.1.0, 1.0.0-alpha.1, 2.3.4+build.123"
    exit 1
fi

log_success "Semantic versioning format valid"

# Step 6: Check git working directory status
log_info "Checking git working directory..."

if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    log_error "Git working directory is not clean"
    echo ""
    git status --short
    echo ""
    log_warn "Commit or stash changes before creating release"
    exit 1
fi

log_success "Git working directory is clean"

# Step 7: Validate CHANGELOG.md has been updated
log_info "Validating CHANGELOG.md documents this version..."

if [[ ! -f "CHANGELOG.md" ]]; then
    log_error "CHANGELOG.md not found"
    log_warn "Create CHANGELOG.md and document version $RUNTIME_VERSION before release"
    exit 1
fi

# Escape regex metacharacters in version for safe pattern matching
# Version strings like "0.1.0+build" contain '.', '+' which are regex metacharacters
# Must escape for both grep (ERE) and sed (BRE)
RUNTIME_VERSION_ESCAPED=$(printf '%s\n' "$RUNTIME_VERSION" | sed 's/[.+]/\\&/g')

# Check if version is documented in CHANGELOG.md headers only (tightened regex)
# Accepts formats at start of line: ## [0.1.0] or ## 0.1.0
if ! grep -qE "^## (\[$RUNTIME_VERSION_ESCAPED\]|$RUNTIME_VERSION_ESCAPED)" CHANGELOG.md; then
    log_error "CHANGELOG.md does not document version $RUNTIME_VERSION"
    echo ""
    log_warn "Add a changelog entry before creating release:"
    echo ""
    echo "  ## [$RUNTIME_VERSION] - $(date +%Y-%m-%d)"
    echo ""
    echo "  ### Added"
    echo "  - Feature descriptions..."
    echo ""
    echo "  ### Fixed"
    echo "  - Bug fix descriptions..."
    echo ""
    exit 1
fi

log_success "CHANGELOG.md documents version $RUNTIME_VERSION"

# Step 7b: Validate CHANGELOG.md format for this version
log_info "Validating CHANGELOG.md format..."

# Check for date format (YYYY-MM-DD) in the version header
# This is more robust than trying to extract entire sections
if grep -qE "^## (\[$RUNTIME_VERSION_ESCAPED\]|$RUNTIME_VERSION_ESCAPED)[[:space:]]*-[[:space:]]*[0-9]{4}-[0-9]{2}-[0-9]{2}" CHANGELOG.md; then
    log_success "CHANGELOG.md format valid (date present)"
else
    log_warn "CHANGELOG.md entry for $RUNTIME_VERSION missing date in format YYYY-MM-DD"
    log_warn "Expected format: ## [$RUNTIME_VERSION] - $(date +%Y-%m-%d)"
    log_warn "This is informational - release can continue"
fi

# Check for standard sections (informational only)
# Extract lines between this version header and the next version header
# Using awk for more robust section extraction
CHANGELOG_SECTION=$(awk "/^## (\[$RUNTIME_VERSION_ESCAPED\]|$RUNTIME_VERSION_ESCAPED)/,/^## (\[[0-9]|\[Unreleased|[0-9])/" CHANGELOG.md)

if [[ -n "$CHANGELOG_SECTION" ]] && echo "$CHANGELOG_SECTION" | grep -qE "^### (Added|Changed|Fixed|Removed|Deprecated|Security)"; then
    log_success "CHANGELOG.md has structured sections (Added/Changed/Fixed/Removed/etc.)"
else
    log_warn "CHANGELOG.md missing standard sections (Added/Changed/Fixed/Removed)"
    log_warn "Consider using Keep a Changelog format: https://keepachangelog.com/"
    log_warn "This is informational - release can continue"
fi

# Step 7c: Check if version already exists on PyPI (early check to fail fast)
log_info "Checking if version $RUNTIME_VERSION exists on PyPI..."

# Only check if curl is available
if command -v curl &> /dev/null; then
    # Use curl to check PyPI JSON API with timeout
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "https://pypi.org/pypi/ftllexbuffer/$RUNTIME_VERSION/json" 2>/dev/null || echo "000")

    if [[ "$HTTP_CODE" == "200" ]]; then
        log_error "Version $RUNTIME_VERSION already exists on PyPI"
        log_warn "PyPI does not allow re-uploading the same version"
        log_warn "Bump to a new version before releasing"
        exit 1
    elif [[ "$HTTP_CODE" == "404" ]]; then
        log_success "Version $RUNTIME_VERSION not found on PyPI (ready to publish)"
    elif [[ "$HTTP_CODE" == "000" ]]; then
        log_warn "Could not check PyPI (network error or timeout)"
        log_warn "Proceeding with release - GitHub Actions will validate before publish"
    else
        log_warn "Unexpected HTTP code from PyPI: $HTTP_CODE"
        log_warn "Proceeding with release - GitHub Actions will validate before publish"
    fi
else
    log_warn "curl not available - skipping PyPI availability check"
    log_warn "GitHub Actions will validate version before publish"
fi

# Step 8: Validate git tag format
TAG_NAME="v$RUNTIME_VERSION"
log_info "Validating git tag format..."

# Ensure tag follows v{MAJOR}.{MINOR}.{PATCH} format
if [[ ! "$TAG_NAME" =~ ^v[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?(\+[a-zA-Z0-9.]+)?$ ]]; then
    log_error "Invalid tag format: $TAG_NAME"
    log_warn "Tag must match: v{MAJOR}.{MINOR}.{PATCH}[-PRERELEASE][+BUILD]"
    log_warn "Examples: v0.1.0, v1.0.0-alpha, v2.3.4+build.123"
    exit 1
fi

log_success "Git tag format valid: $TAG_NAME"

# Step 9: Check if tag already exists
log_info "Checking if tag $TAG_NAME already exists..."

if git rev-parse "$TAG_NAME" >/dev/null 2>&1; then
    log_error "Git tag $TAG_NAME already exists"
    log_warn "Delete with: git tag -d $TAG_NAME"
    exit 1
fi

log_success "Tag $TAG_NAME does not exist"

# Step 10: Run test suite
if [[ "$SKIP_TESTS" == "false" ]]; then
    log_info "Running test suite (this may take a minute)..."
    echo ""

    if ! "$SCRIPT_DIR/all.sh" --ci; then
        log_error "Test suite failed"
        log_warn "Fix errors before creating release"
        exit 1
    fi

    echo ""
    log_success "All tests passed"
else
    log_warn "Skipping test suite (--skip-tests flag)"
fi

# Step 11: Create git tag (unless --dry-run)
echo ""
echo "=========================================="
echo "Release Summary"
echo "=========================================="
echo "Version:  $RUNTIME_VERSION"
echo "Tag name: $TAG_NAME"
echo ""

if [[ "$DRY_RUN" == "true" ]]; then
    log_info "Dry run mode - no git operations performed"
    echo ""
    echo "To create release tag, run:"
    echo "  git tag $TAG_NAME"
    echo "  git push origin main --tags"
    exit 0
fi

# Interactive confirmation
read -p "Create release tag $TAG_NAME? [y/N] " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_warn "Release cancelled by user"
    exit 0
fi

# Create tag
log_info "Creating git tag $TAG_NAME..."

if ! git tag -a "$TAG_NAME" -m "Release version $RUNTIME_VERSION"; then
    log_error "Failed to create git tag"
    exit 1
fi

log_success "Git tag $TAG_NAME created successfully"

# Display next steps
echo ""
echo "=========================================="
echo "Next Steps"
echo "=========================================="
echo ""

# Extract repository URL from git config
# This works for standard GitHub URLs (HTTPS and SSH) but may not handle:
# - Non-standard GitHub Enterprise URLs with custom domains
# - Repositories with multiple remotes (only checks 'origin')
# - Unusual SSH configurations
# If extraction fails, fallback to hardcoded repository URL
REPO_URL=$(git config --get remote.origin.url 2>/dev/null || echo "")
if [[ -n "$REPO_URL" ]]; then
    # Convert SSH URLs to HTTPS and extract owner/repo
    # Handles: git@github.com:owner/repo.git → https://github.com/owner/repo
    # Handles: https://github.com/owner/repo.git → https://github.com/owner/repo
    REPO_PATH=$(echo "$REPO_URL" | sed -E 's#^(https?://|git@)##' | sed -E 's#:#/#' | sed 's#\.git$##' | sed 's#github\.com/##')
    GITHUB_BASE="https://github.com/$REPO_PATH"
else
    # Fallback to hardcoded if git config fails
    GITHUB_BASE="https://github.com/resoltico/ftllexbuffer"
    log_warn "Could not extract repository URL from git config, using fallback"
fi

echo "1. Push tag to remote:"
echo "   ${GREEN}git push origin main --tags${NC}"
echo ""
echo "2. Create GitHub Release to trigger automatic PyPI publishing:"
echo "   ${GREEN}$GITHUB_BASE/releases/new?tag=$TAG_NAME${NC}"
echo ""
echo "   IMPORTANT: Only creating a GitHub Release triggers the publish workflow."
echo "   Pushing the tag alone will NOT publish to PyPI."
echo ""
echo "   Steps for GitHub Release:"
echo "   - Select tag: $TAG_NAME"
echo "   - Release title: $TAG_NAME"
echo "   - Description: Copy from CHANGELOG.md"
echo "   - Click 'Publish release'"
echo ""
echo "3. Monitor workflow at:"
echo "   $GITHUB_BASE/actions"
echo ""
echo "4. Verify publication at:"
echo "   https://pypi.org/project/ftllexbuffer/"
echo ""

log_success "Release preparation complete!"
