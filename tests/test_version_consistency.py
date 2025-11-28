"""Version consistency validation tests.

This module ensures version information remains synchronized across all sources,
enforcing pyproject.toml as the single source of truth.

CRITICAL: Any version mismatch indicates a manual synchronization failure and
must be resolved immediately.
"""

from __future__ import annotations

import re
import tomllib
import warnings
from pathlib import Path

import ftllexbuffer


def test_version_matches_pyproject():
    """CRITICAL: __version__ must match pyproject.toml (single source of truth).

    Architecture: Version auto-populated via importlib.metadata from package metadata.
    pyproject.toml is the ONLY manual edit point for version information.

    This test validates:
    - Package metadata correctly reads from pyproject.toml
    - __version__ successfully auto-populated from metadata
    - No manual version hardcoding in __init__.py

    Failure indicates:
    - Package not installed in editable mode (run: pip install -e .)
    - Metadata extraction failed during package build
    - Manual override in __init__.py (not allowed)

    Resolution:
    - Run: pip install -e .
    - Verify: python -c "import ftllexbuffer; print(ftllexbuffer.__version__)"
    - Check __init__.py has no hardcoded version string
    """
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"

    with pyproject_path.open("rb") as f:
        pyproject_data = tomllib.load(f)
        canonical_version = pyproject_data["project"]["version"]

    assert ftllexbuffer.__version__ == canonical_version, (
        f"\n"
        f"{'=' * 70}\n"
        f"VERSION AUTO-SYNC FAILURE\n"
        f"{'=' * 70}\n"
        f"\n"
        f"Single source of truth:  pyproject.toml = {canonical_version!r}\n"
        f"Auto-populated version:  __version__    = {ftllexbuffer.__version__!r}\n"
        f"\n"
        f"Possible causes:\n"
        f"  1. Package not installed: Run 'pip install -e .'\n"
        f"  2. Stale metadata: Re-run 'pip install -e .'\n"
        f"  3. Manual override in __init__.py (CHECK CODE)\n"
        f"\n"
        f"Expected behavior:\n"
        f"  - Edit version ONLY in pyproject.toml\n"
        f"  - Run 'pip install -e .' to refresh metadata\n"
        f"  - __version__ auto-updates from package metadata\n"
        f"{'=' * 70}\n"
    )


def test_version_is_valid_semver():
    """Version string must follow semantic versioning specification.

    Format: MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]

    Valid examples:
    - 0.1.0
    - 1.0.0
    - 2.3.4-alpha
    - 1.0.0-beta.1
    - 3.2.1+build.123
    - 1.0.0-rc.1+20240101

    Invalid examples:
    - 1.0 (missing PATCH)
    - v1.0.0 (prefix not allowed)
    - 1.0.0.0 (too many parts)
    """
    version = ftllexbuffer.__version__

    # Semantic versioning: MAJOR.MINOR.PATCH with optional prerelease/build
    # Reference: https://semver.org/
    semver_pattern = (
        r"^\d+\.\d+\.\d+"  # MAJOR.MINOR.PATCH (required)
        r"(?:-[a-zA-Z0-9.]+)?"  # -PRERELEASE (optional)
        r"(?:\+[a-zA-Z0-9.]+)?$"  # +BUILD (optional)
    )

    assert re.match(semver_pattern, version), (
        f"\n"
        f"Invalid version format: {version!r}\n"
        f"\n"
        f"Expected semantic versioning: MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]\n"
        f"\n"
        f"Valid examples:\n"
        f"  - 0.1.0 (basic release)\n"
        f"  - 1.0.0-alpha (pre-release)\n"
        f"  - 2.3.4+build.123 (with build metadata)\n"
        f"\n"
        f"See: https://semver.org/\n"
    )


def test_version_not_development_placeholder():
    """Version must not be a development placeholder.

    Development placeholders like '0.0.0+dev' or '0.0.0+unknown' indicate:
    - Package not installed (run: pip install -e .)
    - Version metadata extraction failed
    - Using importlib.metadata without package install

    This test ensures production releases have real version numbers.
    """
    version = ftllexbuffer.__version__

    invalid_placeholders = [
        "0.0.0+dev",
        "0.0.0+unknown",
        "0.0.0.dev0",
        "unknown",
        "dev",
    ]

    assert version not in invalid_placeholders, (
        f"\n"
        f"Development placeholder detected: {version!r}\n"
        f"\n"
        f"Possible causes:\n"
        f"  - Package not installed (run: pip install -e .)\n"
        f"  - Using importlib.metadata without package metadata\n"
        f"  - Version extraction failed during build\n"
        f"\n"
        f"For CI/CD: Ensure package is installed before running tests\n"
    )


def test_version_in_api_docs_matches():
    """API documentation should reference correct version (informational).

    This test is informational - it's acceptable for docs to lag behind
    code version during development, but they should match for releases.
    """
    # Check if API.md exists and references version
    api_md_path = Path(__file__).parent.parent / "API.md"

    if not api_md_path.exists():
        # API.md not present, skip test
        return

    api_content = api_md_path.read_text(encoding="utf-8")
    version = ftllexbuffer.__version__

    # This is informational - don't fail if version not mentioned
    # (docs may use generic examples or not reference version at all)
    if version in api_content:
        # Version found in docs - good!
        pass
    else:
        # Version not in docs - informational warning only
        warnings.warn(
            f"API.md does not reference version {version}. "
            f"Consider updating documentation for release.",
            stacklevel=2,
        )


def test_changelog_has_current_version():
    """CHANGELOG.md should document current version (informational).

    This test warns if CHANGELOG.md doesn't mention the current version.
    It's acceptable for development versions to not be documented yet,
    but release versions should have CHANGELOG entries.

    This is an informational test - warns but doesn't fail.
    """
    version = ftllexbuffer.__version__

    # Skip for development placeholders
    if "+dev" in version or "+unknown" in version:
        return

    # Check if CHANGELOG.md exists
    changelog_path = Path(__file__).parent.parent / "CHANGELOG.md"
    if not changelog_path.exists():
        warnings.warn(
            "CHANGELOG.md not found. Consider creating one to track version history.",
            stacklevel=2,
        )
        return

    # Check if current version is documented
    changelog_content = changelog_path.read_text(encoding="utf-8")

    # Look for version in various formats:
    # - ## [0.1.0] - 2024-01-01
    # - ## 0.1.0
    # - Version 0.1.0
    # - v0.1.0
    version_patterns = [
        f"## [{version}]",  # Markdown heading with link
        f"## {version}",  # Markdown heading
        f"Version {version}",  # Prose mention
        f"v{version}",  # Git tag style
        version,  # Plain version
    ]

    version_documented = any(pattern in changelog_content for pattern in version_patterns)

    if not version_documented:
        warnings.warn(
            f"CHANGELOG.md doesn't mention version {version}. "
            f"Consider documenting changes for this release before tagging.",
            stacklevel=2,
        )


def test_version_components_are_integers():
    """Version MAJOR.MINOR.PATCH components must be non-negative integers.

    This validates that version parsing will work correctly across tools.
    """
    version = ftllexbuffer.__version__

    # Extract base version (before - or +)
    base_version = version.split("-")[0].split("+")[0]
    parts = base_version.split(".")

    assert len(parts) == 3, (
        f"Version must have exactly 3 components (MAJOR.MINOR.PATCH), "
        f"got {len(parts)}: {version!r}"
    )

    major, minor, patch = parts

    # Validate each component is a non-negative integer
    for component_name, component_value in [
        ("MAJOR", major),
        ("MINOR", minor),
        ("PATCH", patch),
    ]:
        assert component_value.isdigit(), (
            f"{component_name} version component must be integer, "
            f"got {component_value!r} in {version!r}"
        )

        assert int(component_value) >= 0, (
            f"{component_name} version component must be non-negative, "
            f"got {component_value} in {version!r}"
        )


def test_version_increment_logic():
    """Document version increment rules for reference.

    This test doesn't validate anything - it documents the expected
    version increment behavior per semantic versioning.
    """
    version = ftllexbuffer.__version__
    base = version.split("-")[0].split("+")[0]
    major, minor, patch = map(int, base.split("."))

    # Document what the next versions would be
    next_patch = f"{major}.{minor}.{int(patch) + 1}"
    next_minor = f"{major}.{int(minor) + 1}.0"
    next_major = f"{int(major) + 1}.0.0"

    # This is purely informational
    print(f"\nCurrent version: {version}")
    print(f"Next patch release (bug fixes): {next_patch}")
    print(f"Next minor release (new features): {next_minor}")
    print(f"Next major release (breaking changes): {next_major}")

    # Always passes - this is documentation, not validation
    assert True
