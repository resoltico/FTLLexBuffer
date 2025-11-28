"""Error path coverage for __init__.py module.

This module tests exception handlers in __init__.py to achieve 100% coverage.
These are edge cases that rarely occur in production but must be tested.
"""

from __future__ import annotations

import sys
from importlib.metadata import PackageNotFoundError
from unittest.mock import MagicMock, patch

import pytest


def test_importlib_metadata_import_error():
    """Test ImportError handling when importlib.metadata is unavailable.

    This tests lines 140-142 in __init__.py.

    Scenario: importlib.metadata fails to import (extremely rare on Python 3.8+)
    Expected: RuntimeError with clear diagnostic message
    """
    import importlib
    import importlib.util

    # Save ALL ftllexbuffer.* modules before manipulation
    saved_modules = {
        name: module
        for name, module in sys.modules.items()
        if name == "ftllexbuffer" or name.startswith("ftllexbuffer.")
    }
    saved_metadata = sys.modules.get("importlib.metadata")

    try:
        # Remove all ftllexbuffer and metadata modules
        modules_to_remove = [*saved_modules.keys(), "importlib.metadata"]
        for module_name in modules_to_remove:
            if module_name in sys.modules:
                del sys.modules[module_name]

        # Create a mock that blocks importlib.metadata
        def import_mock(name, *args, **kwargs):
            if "metadata" in name or (
                len(args) > 3 and args[3] and "metadata" in str(args[3])
            ):
                raise ImportError("Simulated importlib.metadata unavailable")
            # For other imports, use the original loader
            return original_import(name, *args, **kwargs)

        import builtins

        original_import = builtins.__import__

        builtins.__import__ = import_mock

        try:
            # This should trigger the ImportError handler and raise RuntimeError
            importlib.import_module("ftllexbuffer")
            # If we reach here, test failed
            pytest.fail("Expected RuntimeError but import succeeded")
        except RuntimeError as e:
            # Expected error - verify message
            assert "importlib.metadata unavailable" in str(e)
            assert "Python version too old" in str(e)
        finally:
            # Restore original __import__
            builtins.__import__ = original_import

    finally:
        # Complete cleanup: remove ALL ftllexbuffer modules (including any newly created)
        all_ftllexbuffer_modules = [
            name
            for name in sys.modules
            if name == "ftllexbuffer" or name.startswith("ftllexbuffer.")
        ]
        for module_name in all_ftllexbuffer_modules:
            del sys.modules[module_name]

        # Restore ALL original modules
        sys.modules.update(saved_modules)

        # Restore metadata module
        if saved_metadata is not None:
            sys.modules["importlib.metadata"] = saved_metadata


def test_package_not_found_error():
    """Test PackageNotFoundError handling when package is not installed.

    This tests lines 148-151 in __init__.py.

    Scenario: importlib.metadata.version() raises PackageNotFoundError
    Expected: __version__ defaults to '0.0.0+dev'
    """
    # Save ALL ftllexbuffer.* modules before manipulation
    saved_modules = {
        name: module
        for name, module in sys.modules.items()
        if name == "ftllexbuffer" or name.startswith("ftllexbuffer.")
    }

    try:
        # Remove all ftllexbuffer modules to force re-import
        for module_name in list(saved_modules.keys()):
            if module_name in sys.modules:
                del sys.modules[module_name]

        # Mock importlib.metadata.version to raise PackageNotFoundError
        mock_version = MagicMock(side_effect=PackageNotFoundError("ftllexbuffer"))

        with patch("importlib.metadata.version", mock_version):
            # Import should succeed with fallback version
            import ftllexbuffer

            assert ftllexbuffer.__version__ == "0.0.0+dev", (
                "Expected fallback version '0.0.0+dev' when package not found, "
                f"got {ftllexbuffer.__version__!r}"
            )
    finally:
        # Complete cleanup: remove ALL ftllexbuffer modules (including any newly created)
        all_ftllexbuffer_modules = [
            name
            for name in sys.modules
            if name == "ftllexbuffer" or name.startswith("ftllexbuffer.")
        ]
        for module_name in all_ftllexbuffer_modules:
            del sys.modules[module_name]

        # Restore ALL original modules
        sys.modules.update(saved_modules)


def test_package_not_found_hypothesis_strategy():
    """Property-based test: PackageNotFoundError always sets dev version.

    Uses Hypothesis to ensure the fallback version is deterministic
    regardless of package name or error message.
    """
    from hypothesis import given
    from hypothesis import strategies as st

    # Save ALL ftllexbuffer.* modules before manipulation
    saved_modules = {
        name: module
        for name, module in sys.modules.items()
        if name == "ftllexbuffer" or name.startswith("ftllexbuffer.")
    }

    try:

        @given(package_name=st.text(min_size=1, max_size=50))
        def property_test(package_name):
            # Remove all ftllexbuffer modules for each test run
            all_ftllexbuffer_modules = [
                name
                for name in list(sys.modules.keys())
                if name == "ftllexbuffer" or name.startswith("ftllexbuffer.")
            ]
            for module_name in all_ftllexbuffer_modules:
                del sys.modules[module_name]

            # Mock with varying package names
            mock_version = MagicMock(side_effect=PackageNotFoundError(package_name))

            with patch("importlib.metadata.version", mock_version):
                import ftllexbuffer

                # Invariant: dev version is always '0.0.0+dev'
                assert ftllexbuffer.__version__ == "0.0.0+dev"

        # Run property test - Hypothesis provides the argument via @given decorator
        property_test()  # pylint: disable=no-value-for-parameter

    finally:
        # Complete cleanup after all Hypothesis runs
        all_ftllexbuffer_modules = [
            name
            for name in sys.modules
            if name == "ftllexbuffer" or name.startswith("ftllexbuffer.")
        ]
        for module_name in all_ftllexbuffer_modules:
            del sys.modules[module_name]

        # Restore ALL original modules
        sys.modules.update(saved_modules)
