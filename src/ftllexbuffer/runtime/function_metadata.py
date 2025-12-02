"""Metadata system for built-in Fluent functions.

This module provides explicit metadata for built-in functions, replacing
magic tuples with declarative configuration.

Architecture:
    - FunctionMetadata: Dataclass with explicit properties
    - BUILTIN_FUNCTIONS: Centralized registry of built-in function metadata
    - Helper functions for type-safe queries

Design Goals:
    - Explicit over implicit (no magic tuples)
    - Self-validating (import-time checks)
    - Type-safe (mypy --strict compliant)
    - Future-proof (easy to extend)

Python 3.13+. Zero external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class FunctionMetadata:
    """Metadata for a built-in Fluent function.

    Attributes:
        python_name: Python function name (snake_case)
        ftl_name: FTL function name (UPPERCASE)
        requires_locale: Whether function needs bundle locale injected
        category: Function category for documentation

    Example:
        >>> NUMBER_META = FunctionMetadata(
        ...     python_name="number_format",
        ...     ftl_name="NUMBER",
        ...     requires_locale=True,
        ...     category="formatting",
        ... )
    """

    python_name: str
    ftl_name: str
    requires_locale: bool
    category: Literal["formatting", "text", "custom"] = "formatting"


# Centralized metadata registry for built-in functions
# This is the SINGLE SOURCE OF TRUTH for which functions need locale injection
BUILTIN_FUNCTIONS: dict[str, FunctionMetadata] = {
    "NUMBER": FunctionMetadata(
        python_name="number_format",
        ftl_name="NUMBER",
        requires_locale=True,
        category="formatting",
    ),
    "DATETIME": FunctionMetadata(
        python_name="datetime_format",
        ftl_name="DATETIME",
        requires_locale=True,
        category="formatting",
    ),
    "CURRENCY": FunctionMetadata(
        python_name="currency_format",
        ftl_name="CURRENCY",
        requires_locale=True,
        category="formatting",
    ),
}


def requires_locale_injection(func_name: str) -> bool:
    """Check if function requires locale injection (type-safe).

    This is the proper way to check if a function needs locale injection,
    replacing the old magic tuple approach.

    Args:
        func_name: FTL function name (e.g., "NUMBER", "CURRENCY")

    Returns:
        True if function requires locale injection, False otherwise

    Example:
        >>> requires_locale_injection("NUMBER")
        True
        >>> requires_locale_injection("CUSTOM")
        False
    """
    metadata = BUILTIN_FUNCTIONS.get(func_name)
    return metadata.requires_locale if metadata else False


def is_builtin_function(func_name: str) -> bool:
    """Check if function is a built-in Fluent function.

    Args:
        func_name: FTL function name

    Returns:
        True if function is built-in, False otherwise

    Example:
        >>> is_builtin_function("NUMBER")
        True
        >>> is_builtin_function("CUSTOM")
        False
    """
    return func_name in BUILTIN_FUNCTIONS


def get_python_name(ftl_name: str) -> str | None:
    """Get Python function name for FTL function name.

    Args:
        ftl_name: FTL function name (e.g., "NUMBER")

    Returns:
        Python function name (e.g., "number_format") or None if not found

    Example:
        >>> get_python_name("NUMBER")
        'number_format'
        >>> get_python_name("CUSTOM")
        None
    """
    metadata = BUILTIN_FUNCTIONS.get(ftl_name)
    return metadata.python_name if metadata else None


def should_inject_locale(func_name: str, function_registry: Any) -> bool:
    """Check if locale should be injected for this function call.

    This is the CORRECT way to check locale injection, handling both
    built-in functions and custom functions with the same name.

    Args:
        func_name: FTL function name (e.g., "NUMBER", "CURRENCY")
        function_registry: FunctionRegistry instance to check

    Returns:
        True if locale should be injected, False otherwise

    Logic:
        1. Check if function name is a built-in that needs locale
        2. Check if function in registry is the actual built-in (not custom replacement)
        3. Only inject if BOTH conditions are true

    Example:
        >>> # Built-in NUMBER function
        >>> should_inject_locale("NUMBER", bundle._function_registry)
        True

        >>> # Custom CURRENCY function (same name, different function)
        >>> bundle.add_function("CURRENCY", my_custom_currency)
        >>> should_inject_locale("CURRENCY", bundle._function_registry)
        False
    """
    # Import here to avoid circular dependency
    from ftllexbuffer.runtime.functions import FUNCTION_REGISTRY

    # Check if it's a built-in function that requires locale
    if not requires_locale_injection(func_name):
        return False

    # Check if the function in the registry is the original built-in
    # If a custom function was registered with the same name, it will be different
    if not function_registry.has_function(func_name):
        return False

    # Get the Python function name for this FTL function
    python_name = get_python_name(func_name)
    if python_name is None:
        return False

    # Compare: is the function in the bundle's registry the same as the global built-in?
    try:
        # Get function signatures from both registries
        # pylint: disable=protected-access  # Need to compare callables to detect custom functions
        bundle_func = function_registry._functions.get(func_name)
        global_func = FUNCTION_REGISTRY._functions.get(func_name)

        if bundle_func is None or global_func is None:
            return False

        # If the callable is the same, it's the built-in; if different, it's custom
        return bundle_func.callable is global_func.callable
    except (AttributeError, KeyError):
        # If we can't compare, be conservative and don't inject
        return False
