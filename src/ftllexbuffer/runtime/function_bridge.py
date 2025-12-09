"""Function call bridge between Python and FTL calling conventions.

Provides a bidirectional mapping layer:
    - Python: snake_case parameters (PEP 8)
    - FTL: camelCase parameters (JavaScript/ICU heritage)

This allows Python functions to use Pythonic APIs while maintaining
compatibility with FTL syntax in .ftl files.

Architecture:
    - FunctionRegistry: Manages function registration and calling
    - Auto-generates parameter mappings from function signatures
    - Converts FTL camelCase args → Python snake_case args at call time

Example:
    # Python function (snake_case):
    def number_format(value, *, minimum_fraction_digits=0):
        ...

    # FTL file (camelCase):
    price = { $amount NUMBER(minimumFractionDigits: 2) }

    # Bridge automatically converts: minimumFractionDigits → minimum_fraction_digits

Python 3.13+. Zero external dependencies.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from inspect import signature
from typing import Any

from ftllexbuffer.diagnostics import ErrorTemplate, FluentResolutionError

# Type alias for Fluent-compatible functions
FluentFunction = Callable[..., str]


@dataclass(frozen=True, slots=True)
class FunctionSignature:
    """Function metadata with calling convention mappings.

    Attributes:
        python_name: Function name in Python (snake_case)
        ftl_name: Function name in FTL files (UPPERCASE)
        param_mapping: Maps FTL camelCase params → Python snake_case params
        callable: The actual Python function
    """

    python_name: str
    ftl_name: str
    param_mapping: dict[str, str]
    callable: FluentFunction


class FunctionRegistry:
    """Manages Python ↔ FTL function calling convention bridge.

    Provides automatic parameter name conversion:
        - FTL uses camelCase (minimumFractionDigits)
        - Python uses snake_case (minimum_fraction_digits)

    The registry handles the conversion transparently.

    Supports dict-like introspection:
        - list_functions(): List all registered function names
        - get_function_info(name): Get function metadata
        - __iter__: Iterate over function names
        - __len__: Count registered functions
        - __contains__: Check if function exists (supports 'in' operator)

    Example:
        >>> registry = FunctionRegistry()
        >>> registry.register(my_func, ftl_name="CUSTOM")
        >>> "CUSTOM" in registry
        True
        >>> len(registry)
        1
        >>> for name in registry:
        ...     print(name)
        CUSTOM
    """

    def __init__(self) -> None:
        """Initialize empty function registry."""
        self._functions: dict[str, FunctionSignature] = {}

    def register(
        self,
        func: FluentFunction,
        *,
        ftl_name: str | None = None,
        param_map: dict[str, str] | None = None,
    ) -> None:
        """Register Python function for FTL use.

        Args:
            func: Python function to register
            ftl_name: Function name in FTL (default: func.__name__.upper())
            param_map: Custom parameter mappings (overrides auto-generation)

        Example:
            >>> def number_format(value, *, minimum_fraction_digits=0):
            ...     return str(value)
            >>> registry = FunctionRegistry()
            >>> registry.register(number_format, ftl_name="NUMBER")
            >>> # FTL: { $x NUMBER(minimumFractionDigits: 2) }
            >>> # Python: number_format(x, minimum_fraction_digits=2)
        """
        # Default FTL name: UPPERCASE version of function name
        if ftl_name is None:
            ftl_name = func.__name__.upper()

        # Auto-generate parameter mappings from function signature
        sig = signature(func)
        auto_map = {}

        for param_name in sig.parameters:
            # Skip 'self' and positional-only markers
            if param_name in ("self", "/", "*"):
                continue

            # Convert Python snake_case → FTL camelCase
            camel_case = self._to_camel_case(param_name)
            auto_map[camel_case] = param_name

        # Merge custom mappings with auto-generated ones
        # Custom mappings override auto-generated ones
        final_map = {**auto_map, **(param_map or {})}

        # Store function signature
        self._functions[ftl_name] = FunctionSignature(
            python_name=func.__name__,
            ftl_name=ftl_name,
            param_mapping=final_map,
            callable=func,
        )

    def call(
        self,
        ftl_name: str,
        positional: list[Any],
        named: dict[str, Any],
    ) -> str:
        """Call Python function with FTL arguments.

        Converts FTL camelCase parameters to Python snake_case parameters.

        Args:
            ftl_name: Function name from FTL (e.g., "NUMBER")
            positional: Positional arguments
            named: Named arguments from FTL (camelCase)

        Returns:
            Function result (always string for Fluent functions)

        Raises:
            FluentReferenceError: If function not found
            FluentResolutionError: If function execution fails
        """
        # Check if function exists
        if ftl_name not in self._functions:
            raise FluentResolutionError(ErrorTemplate.function_not_found(ftl_name))

        func_sig = self._functions[ftl_name]

        # Convert FTL camelCase args → Python snake_case args
        python_kwargs = {}
        for ftl_param, value in named.items():
            # Look up Python parameter name
            python_param = func_sig.param_mapping.get(ftl_param, ftl_param)
            python_kwargs[python_param] = value

        # Call Python function
        try:
            return func_sig.callable(*positional, **python_kwargs)
        except Exception as e:
            raise FluentResolutionError(ErrorTemplate.function_failed(ftl_name, str(e))) from e

    def has_function(self, ftl_name: str) -> bool:
        """Check if function is registered.

        Args:
            ftl_name: Function name from FTL

        Returns:
            True if function is registered
        """
        return ftl_name in self._functions

    def get_python_name(self, ftl_name: str) -> str | None:
        """Get Python function name for FTL function.

        Args:
            ftl_name: Function name from FTL

        Returns:
            Python function name, or None if not found
        """
        sig = self._functions.get(ftl_name)
        return sig.python_name if sig else None

    def list_functions(self) -> list[str]:
        """List all registered function names (FTL names).

        Returns:
            List of FTL function names (e.g., ["NUMBER", "DATETIME", "CURRENCY"])

        Example:
            >>> registry = FunctionRegistry()
            >>> registry.register(lambda x: str(x), ftl_name="CUSTOM")
            >>> registry.list_functions()
            ['CUSTOM']
        """
        return list(self._functions.keys())

    def get_function_info(self, ftl_name: str) -> FunctionSignature | None:
        """Get function metadata by FTL name.

        Args:
            ftl_name: Function name from FTL (e.g., "NUMBER")

        Returns:
            FunctionSignature with metadata, or None if not found

        Example:
            >>> registry = FunctionRegistry()
            >>> def my_func(value, *, min_digits=0): return str(value)
            >>> registry.register(my_func, ftl_name="MYFUNC")
            >>> info = registry.get_function_info("MYFUNC")
            >>> info.python_name
            'my_func'
            >>> info.ftl_name
            'MYFUNC'
        """
        return self._functions.get(ftl_name)

    def __iter__(self) -> Iterator[str]:
        """Iterate over FTL function names.

        Returns:
            Iterator over FTL function names

        Example:
            >>> registry = FunctionRegistry()
            >>> registry.register(lambda x: str(x), ftl_name="FUNC1")
            >>> registry.register(lambda x: str(x), ftl_name="FUNC2")
            >>> for name in registry:
            ...     print(name)
            FUNC1
            FUNC2
        """
        return iter(self._functions)

    def __len__(self) -> int:
        """Count of registered functions.

        Returns:
            Number of registered functions

        Example:
            >>> registry = FunctionRegistry()
            >>> len(registry)
            0
            >>> registry.register(lambda x: str(x), ftl_name="FUNC")
            >>> len(registry)
            1
        """
        return len(self._functions)

    def __contains__(self, ftl_name: str) -> bool:
        """Check if function is registered using 'in' operator.

        Args:
            ftl_name: Function name from FTL

        Returns:
            True if function is registered

        Example:
            >>> registry = FunctionRegistry()
            >>> registry.register(lambda x: str(x), ftl_name="CUSTOM")
            >>> "CUSTOM" in registry
            True
            >>> "MISSING" in registry
            False
        """
        return ftl_name in self._functions

    def __repr__(self) -> str:
        """Return string representation for debugging.

        v0.9.0: Added for better REPL and debugging experience.

        Returns:
            String representation showing registered functions

        Example:
            >>> registry = FunctionRegistry()
            >>> repr(registry)
            'FunctionRegistry(functions=0)'
        """
        return f"FunctionRegistry(functions={len(self._functions)})"

    def copy(self) -> FunctionRegistry:
        """Create a shallow copy of this registry.

        Returns:
            New FunctionRegistry instance with the same functions.

        Note:
            This creates a shallow copy - the FunctionSignature objects
            are shared, but modifications to the registry (adding/removing
            functions) won't affect the original.
        """
        new_registry = FunctionRegistry()
        new_registry._functions = self._functions.copy()  # pylint: disable=protected-access
        return new_registry

    @staticmethod
    def _to_camel_case(snake_case: str) -> str:
        """Convert Python snake_case to FTL camelCase.

        Args:
            snake_case: Python parameter name (e.g., "minimum_fraction_digits")

        Returns:
            FTL parameter name (e.g., "minimumFractionDigits")

        Examples:
            >>> FunctionRegistry._to_camel_case("minimum_fraction_digits")
            'minimumFractionDigits'
            >>> FunctionRegistry._to_camel_case("use_grouping")
            'useGrouping'
            >>> FunctionRegistry._to_camel_case("value")
            'value'
        """
        # Split on underscores
        components = snake_case.split("_")

        # First component stays lowercase, rest are capitalized
        return components[0] + "".join(comp.capitalize() for comp in components[1:])

    @staticmethod
    def _to_snake_case(camel_case: str) -> str:
        """Convert FTL camelCase to Python snake_case.

        Args:
            camel_case: FTL parameter name (e.g., "minimumFractionDigits")

        Returns:
            Python parameter name (e.g., "minimum_fraction_digits")

        Examples:
            >>> FunctionRegistry._to_snake_case("minimumFractionDigits")
            'minimum_fraction_digits'
            >>> FunctionRegistry._to_snake_case("useGrouping")
            'use_grouping'
            >>> FunctionRegistry._to_snake_case("value")
            'value'
        """
        # Insert underscore before uppercase letters
        return re.sub(r"(?<!^)(?=[A-Z])", "_", camel_case).lower()
