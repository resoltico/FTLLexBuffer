# Version Management

**Status:** Production-ready
**Architecture:** Single source of truth via importlib.metadata

This document describes FTLLexBuffer's version management system.

---

## How It Works

FTLLexBuffer uses **automatic version synchronization** from package metadata. Version information is defined **once** in `pyproject.toml` and automatically propagates to runtime code.

**Single source of truth:**
```toml
# pyproject.toml
[project]
version = "0.1.0"  # ← ONLY place to edit version
```

**Automatic runtime population:**
```python
# src/ftllexbuffer/__init__.py
from importlib.metadata import version
__version__ = version("ftllexbuffer")  # ← Auto-populated from package metadata
```

**Result:** Impossible for version drift. Change version once in `pyproject.toml`, it propagates everywhere automatically.

---

## Developer Workflow

### Bumping Version (Manual Method)

1. **Edit version in pyproject.toml:**
   ```bash
   vim pyproject.toml  # Change: version = "0.2.0"
   ```

2. **Refresh package metadata:**
   ```bash
   pip install -e .
   ```

3. **Verify version updated:**
   ```bash
   python -c "import ftllexbuffer; print(ftllexbuffer.__version__)"
   # Output: 0.2.0
   ```

4. **Run validation:**
   ```bash
   ./scripts/lint.sh
   ./scripts/test.sh
   ```

5. **Commit and tag:**
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 0.2.0"
   git tag v0.2.0
   git push origin main --tags
   ```

### Automated Release (Recommended)

Use the automation scripts for safer, validated releases:

**Option A: Fully Automated**

```bash
# 1. Bump version automatically
./scripts/bump-version.sh patch  # or: minor, major

# Script will:
# - Update pyproject.toml
# - Refresh package metadata
# - Verify version propagation
# - Display next steps

# 2. Update CHANGELOG.md (as prompted by script)
vim CHANGELOG.md

# 3. Commit changes
git add pyproject.toml CHANGELOG.md
git commit -m "Bump version to 0.2.0"

# 4. Run release validation script
./scripts/release.sh

# Script will:
# - Validate version consistency
# - Check CHANGELOG.md updated
# - Check git working directory is clean
# - Run full test suite
# - Validate git tag format
# - Create git tag v0.2.0
# - Display push commands
```

**Option B: Manual Version Edit**

```bash
# 1. Update version in pyproject.toml
vim pyproject.toml  # Change: version = "0.2.0"

# 2. Refresh metadata
pip install -e .

# 3. Update CHANGELOG.md
vim CHANGELOG.md

# 4. Commit and run release script
git add pyproject.toml CHANGELOG.md
git commit -m "Bump version to 0.2.0"
./scripts/release.sh
```

**Release script options:**
```bash
./scripts/release.sh           # Interactive mode with full validation
./scripts/release.sh --dry-run # Validate only, no git operations
./scripts/release.sh --help    # Show usage information
```

**Advantages of automated release:**
- ✅ Prevents version mismatches
- ✅ Ensures clean git state
- ✅ Validates all tests pass
- ✅ Creates properly formatted tags
- ✅ Reduces manual errors

**IMPORTANT:** Never manually edit `__version__` in `__init__.py` - it auto-updates from metadata.

---

## Architecture

### Why importlib.metadata?

**Industry standard approach used by major Python projects (requests, numpy, etc.):**

| Approach | Single Source | Auto-Sync | Overhead | Standard |
|----------|---------------|-----------|----------|----------|
| **importlib.metadata** | ✅ Yes | ✅ Yes | None (cached) | ✅ Python stdlib |
| Manual duplication | ❌ No | ❌ No | None | ❌ Error-prone |
| Dynamic TOML reading | ✅ Yes | ✅ Yes | ~1ms per import | ⚠️ Non-standard |

**Benefits:**
- **Zero maintenance** after setup - version auto-synced
- **No drift possible** - structurally enforced at language level
- **Fast** - metadata cached by Python, zero I/O overhead
- **Standard** - works with all package managers (pip, poetry, hatch, uv)

**How it works:**
1. `pip install -e .` reads `pyproject.toml` and populates package metadata
2. `importlib.metadata.version("ftllexbuffer")` reads from installed metadata
3. `__version__` automatically set to correct value
4. If package not installed, falls back to `"0.0.0+dev"` (development mode)

### Implementation

**File: `src/ftllexbuffer/__init__.py`** (lines 137-150):
```python
# Version information - Auto-populated from package metadata
# SINGLE SOURCE OF TRUTH: pyproject.toml [project] version
try:
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as _get_version
except ImportError as e:
    # This should never happen on Python 3.13+ (importlib.metadata is stdlib since 3.8)
    raise RuntimeError(
        "importlib.metadata unavailable - Python version too old? " + str(e)
    ) from e

try:
    __version__ = _get_version("ftllexbuffer")
except PackageNotFoundError:
    # Development mode: package not installed yet
    # Run: pip install -e .
    __version__ = "0.0.0+dev"
```

**Fallback behavior:**
- **Production:** Version read from package metadata (standard path)
- **Development (no install):** `"0.0.0+dev"` placeholder (triggers CI failure)
- **Python < 3.8:** Raises `RuntimeError` (shouldn't happen on Python 3.13+ project)

---

## Validation

### Automated Tests

**File: `tests/test_version_consistency.py`**

Comprehensive validation of version management:

1. **`test_version_matches_pyproject()`** [CRITICAL]
   - Ensures `__version__` matches `pyproject.toml`
   - Fails if package not installed or metadata stale
   - Detects manual override attempts

2. **`test_version_is_valid_semver()`** [CRITICAL]
   - Validates semantic versioning: `MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]`
   - Rejects invalid formats: `1.0`, `v1.0.0`, `1.0.0.0`

3. **`test_version_not_development_placeholder()`** [CRITICAL]
   - Ensures production releases have real version numbers
   - Rejects `0.0.0+dev`, `0.0.0+unknown` in CI

4. **`test_version_in_api_docs_matches()`** [INFORMATIONAL]
   - Warns if API.md doesn't reference current version
   - Informational only - doesn't fail builds

5. **`test_changelog_has_current_version()`** [INFORMATIONAL] ✨ NEW
   - Warns if CHANGELOG.md doesn't document current version
   - Helps ensure release notes are updated
   - Skips development versions (0.0.0+dev)

6. **`test_version_components_are_integers()`** [CRITICAL]
   - Validates MAJOR, MINOR, PATCH are non-negative integers
   - Ensures version parsing works across tools

7. **`test_version_increment_logic()`** [DOCUMENTATION]
   - Documents next version numbers for reference
   - Always passes - informational only

### Publishing Workflow Validation

**File: `.github/workflows/publish.yml`** validates version metadata before publishing:

```yaml
- name: Validate version metadata
  run: |
    echo "Validating version auto-sync from pyproject.toml..."
    RUNTIME_VERSION=$(python -c "import ftllexbuffer; print(ftllexbuffer.__version__)")
    echo "Runtime version (__version__): $RUNTIME_VERSION"

    # Ensure version is not a fallback placeholder
    if [[ "$RUNTIME_VERSION" == "0.0.0+dev" ]] || [[ "$RUNTIME_VERSION" == "0.0.0+unknown" ]]; then
      echo "[FAIL] Version is fallback placeholder. Package metadata not populated."
      echo "Expected: Version from pyproject.toml via importlib.metadata"
      exit 1
    fi

    echo "[OK] Version metadata successfully auto-populated: $RUNTIME_VERSION"
```

**Execution:** Validates version is correctly populated before publishing to PyPI.

---

## Semantic Versioning

FTLLexBuffer follows [Semantic Versioning 2.0.0](https://semver.org/):

**Format:** `MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]`

**Increment rules:**
- **PATCH (0.1.X):** Bug fixes, no API changes
- **MINOR (0.X.0):** New features, backward-compatible
- **MAJOR (X.0.0):** Breaking changes

**Examples:**
- `0.1.0` - Initial release
- `0.1.1` - Bug fix release
- `0.2.0` - New feature (backward-compatible)
- `1.0.0` - First stable release
- `1.0.0-alpha` - Pre-release version
- `1.0.0+build.123` - Build metadata

**Pre-1.0.0 status:** FTLLexBuffer is currently `0.1.0` (development), indicating API may change before `1.0.0` stable release.

---

## Troubleshooting

### Issue: `__version__` shows `"0.0.0+dev"`

**Cause:** Package not installed or metadata stale

**Solution:**
```bash
pip install -e .
python -c "import ftllexbuffer; print(ftllexbuffer.__version__)"
# Should now show: 0.1.0 (or current version)
```

### Issue: Test fails with "Version mismatch"

**Symptom:** `test_version_matches_pyproject()` fails

**Cause:** Metadata out of sync with `pyproject.toml`

**Solution:**
```bash
# Re-install package to refresh metadata
pip install -e .

# Verify version matches
python -c "import ftllexbuffer; print(ftllexbuffer.__version__)"
```

### Issue: CI fails with "Version is fallback placeholder"

**Cause:** GitHub Actions runner doesn't have package installed

**Solution:** Ensure CI workflow includes:
```yaml
- name: Install dependencies
  run: |
    pip install -e .  # ← Must install package before running tests
```

---

## Tools

### Version Bump Script

**File: `scripts/bump-version.sh`**

Automates version bumping to eliminate manual errors.

**Features:**
- Validates current version format
- Calculates new version (major/minor/patch)
- Updates pyproject.toml automatically
- Refreshes package metadata
- Verifies version propagation to __version__
- Provides clear next-step instructions

**Usage:**

```bash
./scripts/bump-version.sh patch  # 0.1.0 -> 0.1.1 (bug fixes)
./scripts/bump-version.sh minor  # 0.1.0 -> 0.2.0 (new features)
./scripts/bump-version.sh major  # 0.1.0 -> 1.0.0 (breaking changes)
```

**Benefits:**
- Eliminates typos in version strings
- Ensures metadata refresh not forgotten
- Validates semantic versioning rules
- Interactive confirmation before changes

### Changelog Extraction Script

**File: `scripts/extract-changelog.sh`**

Extracts changelog section for a specific version from CHANGELOG.md.

**Features:**
- Automatically detects current package version
- Supports multiple changelog formats
- Output suitable for piping or copying
- Provides GitHub release URL

**Usage:**

```bash
# Extract for current version
./scripts/extract-changelog.sh

# Extract for specific version
./scripts/extract-changelog.sh 0.2.0

# Copy to clipboard (macOS)
./scripts/extract-changelog.sh 0.2.0 | pbcopy

# Save to file
./scripts/extract-changelog.sh 0.2.0 > release-notes.md
```

**Benefits:**
- No manual copying from CHANGELOG.md
- Consistent formatting
- Eliminates copy-paste errors
- Speeds up GitHub release creation

### Release Automation Script

**File: `scripts/release.sh`**

Comprehensive release validation script that creates git tags.

**Features:**
- ✅ Validates version in pyproject.toml matches runtime __version__
- ✅ Validates CHANGELOG.md documents the version
- ✅ Checks git working directory is clean (no uncommitted changes)
- ✅ Validates semantic versioning format
- ✅ Validates git tag format (v{VERSION})
- ✅ Runs full test suite before tagging
- ✅ Creates properly named git tags (v{VERSION})
- ✅ Interactive confirmation before creating tags
- ✅ Displays push commands for GitHub

**Usage:**

```bash
# Standard release workflow
./scripts/release.sh

# Validation only (dry-run mode)
./scripts/release.sh --dry-run

# Skip tests (not recommended)
./scripts/release.sh --skip-tests

# Show help
./scripts/release.sh --help
```

**Example output:**
```
==========================================
FTLLexBuffer Release Automation
==========================================

[INFO] Extracting version from pyproject.toml...
[OK] pyproject.toml version: 0.2.0
[INFO] Extracting runtime __version__...
[OK] Runtime __version__: 0.2.0
[INFO] Validating version consistency...
[OK] Version consistency validated: 0.2.0
[INFO] Validating semantic versioning format...
[OK] Semantic versioning format valid
[INFO] Checking git working directory...
[OK] Git working directory is clean
[INFO] Checking if tag v0.2.0 already exists...
[OK] Tag v0.2.0 does not exist
[INFO] Running test suite (this may take a minute)...
[OK] All tests passed

==========================================
Release Summary
==========================================
Version:  0.2.0
Tag name: v0.2.0

Create release tag v0.2.0? [y/N] y
[OK] Git tag v0.2.0 created successfully

==========================================
Next Steps
==========================================

1. Push tag to remote:
   git push origin main --tags

2. Verify tag on GitHub:
   https://github.com/resoltico/FTLLexBuffer/releases/tag/v0.2.0
```

---

## Best Practices

### DO

✅ **Edit version ONLY in pyproject.toml** - Single source of truth
✅ **Run `pip install -e .` after version change** - Refresh metadata
✅ **Use semantic versioning** - MAJOR.MINOR.PATCH format
✅ **Tag releases in git** - `git tag v0.2.0`
✅ **Update CHANGELOG.md** - Document changes per release

### DON'T

❌ **Never edit `__version__` in `__init__.py`** - Auto-populated from metadata
❌ **Don't skip `pip install -e .`** - Metadata won't update
❌ **Don't use non-semver formats** - Breaks tooling
❌ **Don't duplicate version in multiple files** - Causes drift
❌ **Don't commit without testing** - Run `./scripts/lint.sh` and `./scripts/test.sh` first

---

## Related Documentation

- [CONTRIBUTING.md](CONTRIBUTING.md) - Developer workflow and release process
- [CHANGELOG.md](CHANGELOG.md) - Version history and release notes
- [pyproject.toml](pyproject.toml) - Package metadata (VERSION SOURCE OF TRUTH)
- [Semantic Versioning](https://semver.org/) - Official semver specification
- [PEP 621](https://peps.python.org/pep-0621/) - Python project metadata standard

---

**Key Principle:** Version management is a systems design problem. By using `importlib.metadata`, version drift becomes structurally impossible rather than merely policy-forbidden.
