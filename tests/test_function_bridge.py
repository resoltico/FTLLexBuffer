"""Tests for function call bridge between Python and FTL.

Validates parameter name conversion and function registration.
"""

from __future__ import annotations

from typing import Any

import pytest

from ftllexbuffer.diagnostics import FluentResolutionError
from ftllexbuffer.runtime.function_bridge import FunctionRegistry, FunctionSignature

# ============================================================================
# HELPER FUNCTIONS FOR TESTING
# ============================================================================


def sample_function(value: int, *, minimum_fraction_digits: int = 0) -> str:
    """Sample function with snake_case parameters."""
    return f"{value:.{minimum_fraction_digits}f}"


def simple_function(text: str) -> str:
    """Simple function with single parameter."""
    return text.upper()


def positional_only_function(value: int, /) -> str:
    """Function with positional-only parameter."""
    return str(value * 2)


def mixed_params_function(
    value: int, /, *, use_grouping: bool = False, date_style: str = "short"
) -> str:
    """Function with mixed parameter types."""
    result = str(value)
    if use_grouping:
        result = f"{value:,}"
    return f"{result} ({date_style})"


# ============================================================================
# FUNCTION SIGNATURE TESTS
# ============================================================================


class TestFunctionSignature:
    """Test FunctionSignature dataclass."""

    def test_create_function_signature(self) -> None:
        """Create FunctionSignature with all fields."""
        sig = FunctionSignature(
            python_name="test_func",
            ftl_name="TEST",
            param_mapping={"minimumValue": "minimum_value"},
            callable=lambda x: str(x),
        )

        assert sig.python_name == "test_func"
        assert sig.ftl_name == "TEST"
        assert sig.param_mapping == {"minimumValue": "minimum_value"}

    def test_function_signature_immutable(self) -> None:
        """FunctionSignature is immutable."""
        sig = FunctionSignature(
            python_name="test",
            ftl_name="TEST",
            param_mapping={},
            callable=lambda: "test",
        )

        with pytest.raises(AttributeError):
            sig.python_name = "new_name"  # type: ignore[misc]


# ============================================================================
# FUNCTION REGISTRY BASIC TESTS
# ============================================================================


class TestFunctionRegistryBasic:
    """Test basic FunctionRegistry functionality."""

    def test_create_registry(self) -> None:
        """Create empty function registry."""
        registry = FunctionRegistry()

        assert not registry.has_function("NUMBER")

    def test_register_function_with_default_name(self) -> None:
        """Register function with auto-generated FTL name."""
        registry = FunctionRegistry()

        def number(value: int) -> str:
            return str(value)

        registry.register(number)

        assert registry.has_function("NUMBER")
        assert registry.get_python_name("NUMBER") == "number"

    def test_register_function_with_custom_ftl_name(self) -> None:
        """Register function with custom FTL name."""
        registry = FunctionRegistry()

        registry.register(sample_function, ftl_name="NUM_FORMAT")

        assert registry.has_function("NUM_FORMAT")
        assert not registry.has_function("SAMPLE_FUNCTION")

    def test_register_function_with_custom_param_map(self) -> None:
        """Register function with custom parameter mappings."""
        registry = FunctionRegistry()

        def custom_func(arg1: int, *, special_arg: str = "") -> str:
            return f"{arg1}:{special_arg}"

        registry.register(
            custom_func,
            ftl_name="CUSTOM",
            param_map={"customArg": "special_arg"},
        )

        result = registry.call("CUSTOM", [42], {"customArg": "test"})
        assert result == "42:test"


# ============================================================================
# PARAMETER NAME CONVERSION TESTS
# ============================================================================


class TestParameterNameConversion:
    """Test snake_case <-> camelCase conversion."""

    def test_to_camel_case_single_word(self) -> None:
        """Convert single word (no change)."""
        result = FunctionRegistry._to_camel_case("value")

        assert result == "value"

    def test_to_camel_case_two_words(self) -> None:
        """Convert two_words to twoWords."""
        result = FunctionRegistry._to_camel_case("minimum_value")

        assert result == "minimumValue"

    def test_to_camel_case_multiple_words(self) -> None:
        """Convert multiple_word_name to multipleWordName."""
        result = FunctionRegistry._to_camel_case("minimum_fraction_digits")

        assert result == "minimumFractionDigits"

    def test_to_camel_case_already_camel(self) -> None:
        """Convert camelCase (no underscores) stays same."""
        result = FunctionRegistry._to_camel_case("alreadyCamel")

        assert result == "alreadyCamel"

    def test_to_snake_case_single_word(self) -> None:
        """Convert single word (no change)."""
        result = FunctionRegistry._to_snake_case("value")

        assert result == "value"

    def test_to_snake_case_camel_case(self) -> None:
        """Convert camelCase to camel_case."""
        result = FunctionRegistry._to_snake_case("minimumValue")

        assert result == "minimum_value"

    def test_to_snake_case_multiple_capitals(self) -> None:
        """Convert multipleWords to multiple_words."""
        result = FunctionRegistry._to_snake_case("minimumFractionDigits")

        assert result == "minimum_fraction_digits"

    def test_to_snake_case_already_snake(self) -> None:
        """Convert already_snake stays same."""
        result = FunctionRegistry._to_snake_case("already_snake")

        assert result == "already_snake"


# ============================================================================
# FUNCTION CALLING TESTS
# ============================================================================


class TestFunctionCalling:
    """Test calling registered functions."""

    def test_call_function_with_positional_args(self) -> None:
        """Call function with only positional arguments."""
        registry = FunctionRegistry()
        registry.register(simple_function, ftl_name="UPPER")

        result = registry.call("UPPER", ["hello"], {})

        assert result == "HELLO"

    def test_call_function_with_named_args(self) -> None:
        """Call function with named arguments."""
        registry = FunctionRegistry()
        registry.register(sample_function, ftl_name="FORMAT")

        # FTL: FORMAT($value, minimumFractionDigits: 2)
        result = registry.call("FORMAT", [42], {"minimumFractionDigits": 2})

        assert result == "42.00"

    def test_call_function_with_mixed_args(self) -> None:
        """Call function with both positional and named arguments."""
        registry = FunctionRegistry()
        registry.register(mixed_params_function, ftl_name="MIX")

        result = registry.call("MIX", [1000], {"useGrouping": True, "dateStyle": "long"})

        assert "1,000" in result
        assert "long" in result

    def test_call_function_auto_converts_camel_to_snake(self) -> None:
        """Function call auto-converts FTL camelCase to Python snake_case."""
        registry = FunctionRegistry()

        def test_func(*, minimum_value: int = 0, maximum_value: int = 100) -> str:
            return f"{minimum_value}-{maximum_value}"

        registry.register(test_func, ftl_name="RANGE")

        # FTL uses camelCase: minimumValue, maximumValue
        result = registry.call("RANGE", [], {"minimumValue": 5, "maximumValue": 50})

        assert result == "5-50"

    def test_call_nonexistent_function_raises_error(self) -> None:
        """Calling non-existent function raises FluentResolutionError."""
        registry = FunctionRegistry()

        with pytest.raises(FluentResolutionError, match="Function 'NONEXISTENT' not found"):
            registry.call("NONEXISTENT", [], {})

    def test_call_function_that_raises_exception(self) -> None:
        """Function that raises exception is wrapped in FluentResolutionError."""
        registry = FunctionRegistry()

        def failing_func(_value: int) -> str:
            msg = "Something went wrong"
            raise ValueError(msg)

        registry.register(failing_func, ftl_name="FAIL")

        with pytest.raises(FluentResolutionError, match="Function 'FAIL' failed"):
            registry.call("FAIL", [42], {})


# ============================================================================
# AUTO-GENERATION PARAMETER MAPPING TESTS
# ============================================================================


class TestAutoParameterMapping:
    """Test automatic parameter mapping generation."""

    def test_auto_map_snake_case_params(self) -> None:
        """Auto-generate mappings for snake_case parameters."""
        registry = FunctionRegistry()

        def func(*, minimum_value: int = 0, maximum_value: int = 100) -> str:
            return f"{minimum_value}:{maximum_value}"

        registry.register(func, ftl_name="FUNC")

        # Should auto-map: minimumValue -> minimum_value, maximumValue -> maximum_value
        result = registry.call("FUNC", [], {"minimumValue": 1, "maximumValue": 10})
        assert result == "1:10"

    def test_auto_map_skips_self_parameter(self) -> None:
        """Auto-mapping skips 'self' parameter."""

        class TestClass:
            def method(self, value: int) -> str:
                return str(value)

        registry = FunctionRegistry()
        obj = TestClass()
        registry.register(obj.method, ftl_name="METHOD")

        result = registry.call("METHOD", [42], {})
        assert result == "42"

    def test_auto_map_with_positional_only_marker(self) -> None:
        """Auto-mapping skips positional-only marker '/'."""
        registry = FunctionRegistry()

        registry.register(positional_only_function, ftl_name="POS")

        result = registry.call("POS", [21], {})
        assert result == "42"

    def test_custom_param_map_overrides_auto_map(self) -> None:
        """Custom parameter mapping overrides auto-generated mapping."""
        registry = FunctionRegistry()

        def func(*, minimum_value: int = 0) -> str:
            return str(minimum_value)

        # Auto would create: minimumValue -> minimum_value
        # Custom override: minVal -> minimum_value
        registry.register(
            func,
            ftl_name="FUNC",
            param_map={"minVal": "minimum_value"},
        )

        result = registry.call("FUNC", [], {"minVal": 42})
        assert result == "42"


# ============================================================================
# REGISTRY QUERY TESTS
# ============================================================================


class TestRegistryQueries:
    """Test registry query methods."""

    def test_has_function_returns_true_when_registered(self) -> None:
        """has_function returns True for registered function."""
        registry = FunctionRegistry()
        registry.register(simple_function, ftl_name="UPPER")

        assert registry.has_function("UPPER")

    def test_has_function_returns_false_when_not_registered(self) -> None:
        """has_function returns False for unregistered function."""
        registry = FunctionRegistry()

        assert not registry.has_function("UNKNOWN")

    def test_get_python_name_returns_name_when_registered(self) -> None:
        """get_python_name returns Python function name."""
        registry = FunctionRegistry()
        registry.register(simple_function, ftl_name="UPPER")

        python_name = registry.get_python_name("UPPER")

        assert python_name == "simple_function"

    def test_get_python_name_returns_none_when_not_registered(self) -> None:
        """get_python_name returns None for unregistered function."""
        registry = FunctionRegistry()

        python_name = registry.get_python_name("UNKNOWN")

        assert python_name is None


# ============================================================================
# EDGE CASES AND INTEGRATION TESTS
# ============================================================================


class TestFunctionBridgeEdgeCases:
    """Test edge cases and corner scenarios."""

    def test_register_multiple_functions(self) -> None:
        """Register multiple functions in same registry."""
        registry = FunctionRegistry()

        def func1(x: int) -> str:
            return str(x)

        def func2(x: int) -> str:
            return str(x * 2)

        registry.register(func1, ftl_name="F1")
        registry.register(func2, ftl_name="F2")

        assert registry.has_function("F1")
        assert registry.has_function("F2")
        assert registry.call("F1", [5], {}) == "5"
        assert registry.call("F2", [5], {}) == "10"

    def test_overwrite_registered_function(self) -> None:
        """Registering same FTL name twice overwrites previous."""
        registry = FunctionRegistry()

        def func1(_x: int) -> str:
            return "first"

        def func2(_x: int) -> str:
            return "second"

        registry.register(func1, ftl_name="FUNC")
        registry.register(func2, ftl_name="FUNC")

        result = registry.call("FUNC", [1], {})
        assert result == "second"

    def test_empty_parameter_name(self) -> None:
        """Handle empty parameter names gracefully."""
        result = FunctionRegistry._to_camel_case("")
        assert result == ""

        result = FunctionRegistry._to_snake_case("")
        assert result == ""

    def test_parameter_with_numbers(self) -> None:
        """Handle parameter names with numbers."""
        result = FunctionRegistry._to_camel_case("param_123_test")
        assert result == "param123Test"

        result = FunctionRegistry._to_snake_case("param123Test")
        assert result == "param123_test"

    def test_call_with_unmapped_parameter(self) -> None:
        """Call with parameter not in mapping passes through unchanged."""
        registry = FunctionRegistry()

        def func(**kwargs: Any) -> str:
            return str(kwargs.get("unknownParam", "default"))

        registry.register(func, ftl_name="FUNC")

        # unknownParam not in auto-mapping, but should pass through
        result = registry.call("FUNC", [], {"unknownParam": "custom"})
        assert result == "custom"


# ============================================================================
# REAL-WORLD USAGE TESTS
# ============================================================================


class TestRealWorldUsage:
    """Test realistic usage scenarios."""

    def test_number_formatting_function(self) -> None:
        """Test NUMBER-like function with real parameters."""
        registry = FunctionRegistry()

        def number_format(
            value: float,
            *,
            minimum_fraction_digits: int = 0,  # noqa: ARG001
            maximum_fraction_digits: int = 3,
            use_grouping: bool = False,
        ) -> str:
            formatted = f"{value:.{maximum_fraction_digits}f}"
            if use_grouping:
                # Simple grouping simulation
                parts = formatted.split(".")
                parts[0] = f"{int(parts[0]):,}"
                formatted = ".".join(parts)
            return formatted

        registry.register(number_format, ftl_name="NUMBER")

        # FTL: { NUMBER($price, minimumFractionDigits: 2, useGrouping: true) }
        result = registry.call(
            "NUMBER",
            [1234.5],
            {"minimumFractionDigits": 2, "useGrouping": True},
        )

        assert "1,234" in result

    def test_datetime_formatting_function(self) -> None:
        """Test DATETIME-like function with style parameters."""
        registry = FunctionRegistry()

        def datetime_format(
            value: str, *, date_style: str = "short", time_style: str = "short"
        ) -> str:
            return f"{value} ({date_style}/{time_style})"

        registry.register(datetime_format, ftl_name="DATETIME")

        # FTL: { DATETIME($date, dateStyle: "long", timeStyle: "medium") }
        result = registry.call(
            "DATETIME",
            ["2024-01-15"],
            {"dateStyle": "long", "timeStyle": "medium"},
        )

        assert result == "2024-01-15 (long/medium)"
