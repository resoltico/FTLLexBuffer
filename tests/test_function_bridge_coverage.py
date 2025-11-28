"""Tests for runtime/function_bridge.py to achieve 100% coverage.

Focuses on parameter skip logic for 'self', '/', and '*' (line 106).
"""

from ftllexbuffer.runtime.function_bridge import FunctionRegistry


class TestParameterSkipLogic:
    """Test that special parameter names are skipped (line 106)."""

    def test_register_function_with_self_parameter(self):
        """Test registering an unbound method with 'self' parameter."""
        registry = FunctionRegistry()

        # Create a class with a method containing 'self'
        class TestClass:
            def format_value(self, value: int) -> str:
                return f"Value: {value}"

        # Register the UNBOUND method (from class, not instance)
        # This will have 'self' in signature, triggering line 106
        registry.register(TestClass.format_value, ftl_name="FORMAT")

        # Call with instance as first positional arg
        instance = TestClass()
        result = registry.call("FORMAT", [instance, 42], {})
        assert result == "Value: 42"

        # Verify 'self' was skipped in parameter mapping
        sig = registry._functions["FORMAT"]
        assert "self" not in sig.param_mapping.values()
        assert "value" in sig.param_mapping.values()

    def test_register_function_with_star_separator(self):
        """Test registering function with keyword-only separator '*'."""
        registry = FunctionRegistry()

        # Function with keyword-only parameters (uses * separator)
        def format_kw_only(*, value: int, style: str = "plain") -> str:
            return f"{value} ({style})"

        registry.register(format_kw_only, ftl_name="KW")

        # Call with named arguments (star separator should be skipped)
        result = registry.call("KW", [], {"value": 10, "style": "fancy"})
        assert result == "10 (fancy)"

    def test_register_function_with_positional_only_slash(self):
        """Test registering function with positional-only separator '/'."""
        registry = FunctionRegistry()

        # Function with positional-only parameters
        def format_pos_only(value: int, /) -> str:
            return f"Result: {value}"

        registry.register(format_pos_only, ftl_name="POS")

        # Call should work, skipping '/' in mapping
        result = registry.call("POS", [99], {})
        assert result == "Result: 99"

    def test_register_method_with_self_and_kwargs(self):
        """Test method with self and keyword arguments."""
        registry = FunctionRegistry()

        class Formatter:
            def format_number(self, value: int, *, precision: int = 2) -> str:
                return f"{value:.{precision}f}"

        formatter = Formatter()
        registry.register(formatter.format_number, ftl_name="NUM")

        # self should be skipped, precision should map to precision
        result = registry.call("NUM", [42], {"precision": 1})
        assert result == "42.0"

    def test_all_special_params_are_skipped(self):
        """Verify that self, /, and * are all skipped in parameter mapping."""
        registry = FunctionRegistry()

        class ComplexFormatter:
            def complex_format(
                self, pos: int, /, *, keyword_arg: str = "default"
            ) -> str:
                return f"{pos}: {keyword_arg}"

        formatter = ComplexFormatter()
        registry.register(formatter.complex_format, ftl_name="COMPLEX")

        # Only 'keyword_arg' should be in the mapping, not self, /, or *
        sig = registry._functions["COMPLEX"]
        param_names = set(sig.param_mapping.values())

        # Should include keyword_arg but NOT self, /, or *
        assert "keyword_arg" in param_names
        assert "self" not in param_names
        assert "/" not in param_names
        assert "*" not in param_names
