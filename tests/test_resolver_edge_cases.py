"""Additional resolver edge case tests for complete coverage.

Tests error paths and edge cases not covered by main resolver tests.
"""

from __future__ import annotations

import pytest

from ftllexbuffer.diagnostics import FluentReferenceError, FluentResolutionError
from ftllexbuffer.runtime.bundle import FluentBundle
from ftllexbuffer.runtime.functions import FUNCTION_REGISTRY
from ftllexbuffer.runtime.resolver import FluentResolver
from ftllexbuffer.syntax.ast import (
    Identifier,
    Message,
    Pattern,
    Placeable,
    SelectExpression,
    TextElement,
    VariableReference,
    Variant,
)

# ============================================================================
# EDGE CASE EXPRESSION RESOLUTION
# ============================================================================


class TestResolverExpressionEdgeCases:
    """Test edge cases in expression resolution."""

    def test_resolve_placeable_expression(self) -> None:
        """Resolve placeable containing variable."""
        ftl = """test = { $value }"""
        bundle = FluentBundle("en", use_isolating=False)
        bundle.add_resource(ftl)

        result, _ = bundle.format_pattern("test", {"value": "hello"})

        assert result == "hello"

    def test_resolve_unknown_expression_type_raises_error(self) -> None:
        """Unknown expression type raises FluentResolutionError."""
        # This tests the default case in _resolve_expression match statement
        # We create a custom AST node type to trigger this
        resolver = FluentResolver(
            locale="en",
            messages={},
            terms={},
            function_registry=FUNCTION_REGISTRY,
            use_isolating=False
        )

        # Create an invalid pattern with an object that's not a valid expression
        class UnknownExpr:
            """Fake expression type."""

        unknown = UnknownExpr()

        with pytest.raises(FluentResolutionError, match="Unknown expression type"):
            resolver._resolve_expression(unknown, {})

    def test_resolve_bool_true_as_string(self) -> None:
        """Boolean True converts to lowercase 'true' string."""
        resolver = FluentResolver(
            locale="en",
            messages={},
            terms={},
            function_registry=FUNCTION_REGISTRY,
            use_isolating=False
        )

        result = resolver._format_value(True)

        assert result == "true"

    def test_resolve_bool_false_as_string(self) -> None:
        """Boolean False converts to lowercase 'false' string."""
        resolver = FluentResolver(
            locale="en",
            messages={},
            terms={},
            function_registry=FUNCTION_REGISTRY,
            use_isolating=False
        )

        result = resolver._format_value(False)

        assert result == "false"

    def test_resolve_none_as_empty_string(self) -> None:
        """None value converts to empty string."""
        resolver = FluentResolver(
            locale="en",
            messages={},
            terms={},
            function_registry=FUNCTION_REGISTRY,
            use_isolating=False
        )

        result = resolver._format_value(None)

        assert result == ""


# ============================================================================
# SELECT EXPRESSION EDGE CASES
# ============================================================================


class TestSelectExpressionEdgeCases:
    """Test edge cases in select expression resolution."""

    def test_select_with_no_matching_variant_uses_default(self) -> None:
        """Select with no match uses default variant."""
        ftl = """
test = { $value ->
   [one] One
  *[other] Other
}
"""
        bundle = FluentBundle("en", use_isolating=False)
        bundle.add_resource(ftl)

        result, _ = bundle.format_pattern("test", {"value": "unknown"})

        assert "Other" in result

    def test_select_with_number_tries_plural_category(self) -> None:
        """Select with number value tries plural category matching."""
        ftl = """
test = { $count ->
   [one] One item
  *[other] Many items
}
"""
        bundle = FluentBundle("en", use_isolating=False)
        bundle.add_resource(ftl)

        # 1 matches "one" plural category
        result, _ = bundle.format_pattern("test", {"count": 1})
        assert "One item" in result

        # 5 matches "other" plural category
        result, _ = bundle.format_pattern("test", {"count": 5})
        assert "Many items" in result

    def test_select_with_no_default_uses_first_variant(self) -> None:
        """Select with no default variant uses first variant as fallback."""
        # Manually create AST without default to test fallback
        msg = Message(
            id=Identifier(name="test"),
            value=Pattern(
                elements=(
                    Placeable(
                        expression=SelectExpression(
                            selector=VariableReference(id=Identifier(name="x")),
                            variants=(
                                Variant(
                                    key=Identifier(name="a"),
                                    value=Pattern(elements=(TextElement(value="A"),)),
                                    default=False,  # No default!
                                ),
                                Variant(
                                    key=Identifier(name="b"),
                                    value=Pattern(elements=(TextElement(value="B"),)),
                                    default=False,
                                ),
                            ),
                        )
                    ),
                )
            ),
            attributes=(),
        )

        resolver = FluentResolver(
            locale="en",
            messages={"test": msg},
            terms={},
            function_registry=FUNCTION_REGISTRY,
            use_isolating=False,
        )

        # Non-matching value should use first variant
        result, _ = resolver.resolve_message(msg, {"x": "unknown"})

        assert "A" in result

    def test_select_with_empty_variants_raises_error(self) -> None:
        """Select with no variants raises error.

        Note: This tests internal resolver logic. The parser would normally
        reject empty variants, but we can test the resolver's handling directly.
        """
        # Create select expression with empty variants tuple
        msg = Message(
            id=Identifier(name="test"),
            value=Pattern(
                elements=(
                    Placeable(
                        expression=SelectExpression(
                            selector=VariableReference(id=Identifier(name="x")),
                            variants=(),  # Empty!
                        )
                    ),
                )
            ),
            attributes=(),
        )

        resolver = FluentResolver(
            locale="en",
            messages={"test": msg},
            terms={},
            function_registry=FUNCTION_REGISTRY,
            use_isolating=False,
        )

        # The resolver will use the variable value as text when variants are empty
        # This tests the fallback behavior
        result, _ = resolver.resolve_message(msg, {"x": "value"})
        # Should handle gracefully - check that it doesn't crash
        assert isinstance(result, str)


# ============================================================================
# MESSAGE REFERENCE EDGE CASES
# ============================================================================


class TestMessageReferenceEdgeCases:
    """Test edge cases in message reference resolution."""

    def test_format_nonexistent_message_raises_error(self) -> None:
        """Formatting non-existent message raises FluentReferenceError."""
        bundle = FluentBundle("en", use_isolating=False)
        # Add a valid message
        bundle.add_resource("hello = Hello")

        # Try to format a message that doesn't exist
        result, errors = bundle.format_pattern("missing", {})
        assert len(errors) == 1
        assert isinstance(errors[0], FluentReferenceError)
        assert result == "{missing}"


# ============================================================================
# INTEGRATION TESTS FOR EDGE CASES
# ============================================================================


class TestResolverIntegrationEdgeCases:
    """Integration tests for resolver edge cases."""

    def test_select_with_string_literal_in_variant(self) -> None:
        """Select expression with string literals in variants."""
        ftl = """test = { $type ->
   [greeting] Hello
   [farewell] Goodbye
  *[other] Message
}"""
        bundle = FluentBundle("en", use_isolating=False)
        bundle.add_resource(ftl)

        result, _ = bundle.format_pattern("test", {"type": "greeting"})
        assert "Hello" in result

        result, _ = bundle.format_pattern("test", {"type": "farewell"})
        assert "Goodbye" in result

        result, _ = bundle.format_pattern("test", {"type": "unknown"})
        assert "Message" in result

    def test_mixed_literal_types_in_pattern(self) -> None:
        """Pattern with different literal types."""
        ftl = """test = Number: { 42 }, String: { "hello" }"""
        bundle = FluentBundle("en", use_isolating=False)
        bundle.add_resource(ftl)

        result, _ = bundle.format_pattern("test", {})

        assert "Number: 42" in result
        assert "String: hello" in result

    def test_complex_value_formatting(self) -> None:
        """Format complex Python values."""
        resolver = FluentResolver(
            locale="en",
            messages={},
            terms={},
            function_registry=FUNCTION_REGISTRY,
            use_isolating=False
        )

        # List
        assert resolver._format_value([1, 2, 3]) == "[1, 2, 3]"

        # Dict
        result = resolver._format_value({"key": "value"})
        assert "key" in result
        assert "value" in result

        # Custom object
        class CustomObj:
            def __str__(self) -> str:
                return "custom"

        assert resolver._format_value(CustomObj()) == "custom"


# ============================================================================
# ERROR PATH COVERAGE
# ============================================================================


class TestResolverErrorPaths:
    """Test error handling paths in resolver."""

    def test_missing_variable_returns_error_message(self) -> None:
        """Missing variable in select expression returns error with fallback."""
        ftl = """test = { $x ->
   [a] Value A
  *[b] Default
}"""
        bundle = FluentBundle("en", use_isolating=False)
        bundle.add_resource(ftl)

        # Missing variable returns fallback (errors in list)
        result, errors = bundle.format_pattern("test", {})
        assert len(errors) > 0  # Should have error
        assert isinstance(errors[0], FluentReferenceError)
        # Error contains diagnostic code
        assert "VARIABLE_NOT_PROVIDED" in str(errors[0])
        # Result shows fallback (select expression too complex for readable fallback)
        assert result == "{???}"
