"""Tests for runtime/resolver.py to achieve 100% coverage.

Focuses on TextElement branch, Placeable case, and boolean formatting.
"""

from ftllexbuffer.runtime.bundle import FluentBundle


class TestResolverPatternElements:
    """Test pattern element resolution (line 114->111)."""

    def test_resolve_pattern_with_text_element(self):
        """Test TextElement branch in _resolve_pattern (line 112-113)."""
        bundle = FluentBundle("en", use_isolating=False)

        # Simple message with plain text (TextElement)
        bundle.add_resource("hello = Hello, World!")

        result, _ = bundle.format_pattern("hello")
        assert result == "Hello, World!"

    def test_resolve_pattern_with_placeable(self):
        """Test Placeable branch in _resolve_pattern (line 114->111)."""
        bundle = FluentBundle("en", use_isolating=False)

        # Message with placeable (variable reference)
        bundle.add_resource("greeting = Hello, { $name }!")

        result, _ = bundle.format_pattern("greeting", {"name": "Alice"})
        assert result == "Hello, Alice!"

    def test_resolve_pattern_mixed_text_and_placeables(self):
        """Test pattern with both TextElement and Placeable."""
        bundle = FluentBundle("en", use_isolating=False)

        # Message with multiple elements
        bundle.add_resource("welcome = Welcome, { $firstName } { $lastName }!")

        result, _ = bundle.format_pattern(
            "welcome", {"firstName": "John", "lastName": "Doe"}
        )
        assert result == "Welcome, John Doe!"


class TestResolverPlaceableExpression:
    """Test Placeable case in _resolve_expression (line 149)."""

    def test_nested_placeable_expression(self):
        """Test nested Placeable in expression (line 149)."""
        bundle = FluentBundle("en", use_isolating=False)

        # Create message with nested placeables using select expression
        bundle.add_resource(
            """
count-message = { $count ->
    [1] One item
   *[other] { $count } items
}
"""
        )

        # The select expression contains placeables
        result, _ = bundle.format_pattern("count-message", {"count": 5})
        assert "5 items" in result

    def test_placeable_with_function_call(self):
        """Test Placeable containing function reference."""
        bundle = FluentBundle("en", use_isolating=False)

        # Message with NUMBER function (placeable with function ref)
        bundle.add_resource("price = Price: { NUMBER($amount) }")

        result, _ = bundle.format_pattern("price", {"amount": 42.5})
        assert "42" in result or "43" in result  # Depending on rounding


class TestResolverBooleanFormatting:
    """Test boolean formatting in _format_value (line 275)."""

    def test_format_value_boolean_true(self):
        """Test formatting boolean True value (line 275 - true branch)."""
        bundle = FluentBundle("en", use_isolating=False)

        # Custom function that returns boolean
        def BOOL_CHECK(value: int) -> bool:
            return value > 0

        bundle.add_function("BOOL_CHECK", BOOL_CHECK)

        # Message using boolean function
        bundle.add_resource("is-positive = Value is positive: { BOOL_CHECK($num) }")

        result, _ = bundle.format_pattern("is-positive", {"num": 5})
        assert "true" in result.lower()

    def test_format_value_boolean_false(self):
        """Test formatting boolean False value (line 275 - false branch)."""
        bundle = FluentBundle("en", use_isolating=False)

        # Custom function that returns boolean
        def IS_NEGATIVE(value: int) -> bool:
            return value < 0

        bundle.add_function("IS_NEGATIVE", IS_NEGATIVE)

        bundle.add_resource("check = Negative: { IS_NEGATIVE($num) }")

        result, _ = bundle.format_pattern("check", {"num": 5})
        assert "false" in result.lower()

    def test_format_value_none(self):
        """Test formatting None value."""
        bundle = FluentBundle("en", use_isolating=False)

        # Custom function that returns None
        def RETURNS_NONE() -> None:
            return None

        bundle.add_function("RETURNS_NONE", RETURNS_NONE)

        bundle.add_resource("empty = Value: { RETURNS_NONE() }")

        result, _ = bundle.format_pattern("empty")
        # None should format to empty string
        assert result == "Value: "


class TestResolverDeepCoverage:
    """Additional tests for hard-to-reach branches."""

    def test_placeable_in_select_variant(self):
        """Test Placeable case (line 149) with select expression variant."""
        bundle = FluentBundle("en", use_isolating=False)

        # Select expression with placeable in variant
        bundle.add_resource(
            """
item-count = { $count ->
    [0] No items
    [1] { $count } item
   *[other] { $count } items
}
"""
        )

        # This should resolve select, then placeable within variant
        result, _ = bundle.format_pattern("item-count", {"count": 1})
        assert "1 item" in result

    def test_deeply_nested_pattern_elements(self):
        """Test complex pattern with multiple element types."""
        bundle = FluentBundle("en", use_isolating=False)

        # Pattern with text, placeable, text, placeable
        bundle.add_resource(
            "complex = Start { $a } middle { $b } end"
        )

        result, _ = bundle.format_pattern("complex", {"a": "A", "b": "B"})
        assert result == "Start A middle B end"

    def test_boolean_from_python_variable(self):
        """Test boolean value passed as variable (line 275)."""
        bundle = FluentBundle("en", use_isolating=False)

        # Direct variable reference (not function call)
        bundle.add_resource("status = Active: { $isActive }")

        # Pass boolean True as variable
        result, _ = bundle.format_pattern("status", {"isActive": True})
        # Should call _format_value with boolean True
        assert "true" in result.lower() or "True" in result
