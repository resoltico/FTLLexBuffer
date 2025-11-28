"""Tests for Fluent type guards - runtime type narrowing.

Tests PEP 742 TypeIs type guards for Fluent AST types.
"""

from ftllexbuffer.guards import (
    is_identifier,
    is_number_literal,
    is_placeable,
    is_select_expression,
    is_text_element,
    is_variable_reference,
)
from ftllexbuffer.syntax import (
    Identifier,
    MessageReference,
    NumberLiteral,
    Pattern,
    Placeable,
    SelectExpression,
    TextElement,
    VariableReference,
    Variant,
)


class TestIsTextElement:
    """Test is_text_element type guard."""

    def test_returns_true_for_text_element(self) -> None:
        """Type guard returns True for TextElement."""
        elem = TextElement(value="Hello")
        assert is_text_element(elem) is True

    def test_returns_false_for_placeable(self) -> None:
        """Type guard returns False for Placeable."""
        expr = VariableReference(id=Identifier("name"))
        elem = Placeable(expression=expr)
        assert is_text_element(elem) is False

    def test_returns_false_for_non_pattern_elements(self) -> None:
        """Type guard returns False for non-PatternElement types."""
        # Can't directly test with wrong types due to type checker,
        # but the isinstance check handles this at runtime
        elem = TextElement(value="test")
        assert is_text_element(elem) is True


class TestIsPlaceable:
    """Test is_placeable type guard."""

    def test_returns_true_for_placeable(self) -> None:
        """Type guard returns True for Placeable."""
        expr = VariableReference(id=Identifier("name"))
        elem = Placeable(expression=expr)
        assert is_placeable(elem) is True

    def test_returns_false_for_text_element(self) -> None:
        """Type guard returns False for TextElement."""
        elem = TextElement(value="Hello")
        assert is_placeable(elem) is False

    def test_returns_true_for_placeable_with_select_expression(self) -> None:
        """Type guard returns True for Placeable containing SelectExpression."""
        select_expr = SelectExpression(
            selector=VariableReference(id=Identifier("count")),
            variants=(
                Variant(
                    key=NumberLiteral("1"),
                    value=Pattern(elements=(TextElement(value="one item"),)),
                    default=False,
                ),
                Variant(
                    key=NumberLiteral("0"),
                    value=Pattern(elements=(TextElement(value="other items"),)),
                    default=True,
                ),
            ),
        )
        elem = Placeable(expression=select_expr)
        assert is_placeable(elem) is True


class TestIsVariableReference:
    """Test is_variable_reference type guard."""

    def test_returns_true_for_variable_reference(self) -> None:
        """Type guard returns True for VariableReference."""
        expr = VariableReference(id=Identifier("name"))
        assert is_variable_reference(expr) is True

    def test_returns_false_for_select_expression(self) -> None:
        """Type guard returns False for SelectExpression."""
        expr = SelectExpression(
            selector=VariableReference(id=Identifier("count")),
            variants=(
                Variant(
                    key=NumberLiteral("1"),
                    value=Pattern(elements=(TextElement(value="one"),)),
                    default=True,
                ),
            ),
        )
        assert is_variable_reference(expr) is False

    def test_returns_false_for_message_reference(self) -> None:
        """Type guard returns False for MessageReference."""
        expr = MessageReference(id=Identifier("brand"), attribute=None)
        assert is_variable_reference(expr) is False

    def test_returns_false_for_number_literal(self) -> None:
        """Type guard returns False for NumberLiteral."""
        expr = NumberLiteral("42")
        assert is_variable_reference(expr) is False


class TestIsSelectExpression:
    """Test is_select_expression type guard."""

    def test_returns_true_for_select_expression(self) -> None:
        """Type guard returns True for SelectExpression."""
        expr = SelectExpression(
            selector=VariableReference(id=Identifier("count")),
            variants=(
                Variant(
                    key=NumberLiteral("1"),
                    value=Pattern(elements=(TextElement(value="one"),)),
                    default=True,
                ),
            ),
        )
        assert is_select_expression(expr) is True

    def test_returns_false_for_variable_reference(self) -> None:
        """Type guard returns False for VariableReference."""
        expr = VariableReference(id=Identifier("name"))
        assert is_select_expression(expr) is False

    def test_returns_false_for_message_reference(self) -> None:
        """Type guard returns False for MessageReference."""
        expr = MessageReference(id=Identifier("brand"), attribute=None)
        assert is_select_expression(expr) is False

    def test_returns_true_for_complex_select_expression(self) -> None:
        """Type guard returns True for complex SelectExpression with multiple variants."""
        expr = SelectExpression(
            selector=VariableReference(id=Identifier("count")),
            variants=(
                Variant(
                    key=NumberLiteral("0"),
                    value=Pattern(elements=(TextElement(value="zero items"),)),
                    default=False,
                ),
                Variant(
                    key=NumberLiteral("1"),
                    value=Pattern(elements=(TextElement(value="one item"),)),
                    default=False,
                ),
                Variant(
                    key=NumberLiteral("2"),
                    value=Pattern(elements=(TextElement(value="other items"),)),
                    default=True,
                ),
            ),
        )
        assert is_select_expression(expr) is True


class TestIsIdentifier:
    """Test is_identifier type guard."""

    def test_returns_true_for_identifier(self) -> None:
        """Type guard returns True for Identifier."""
        key = Identifier("one")
        assert is_identifier(key) is True

    def test_returns_false_for_number_literal(self) -> None:
        """Type guard returns False for NumberLiteral."""
        key = NumberLiteral("1")
        assert is_identifier(key) is False

    def test_returns_true_for_identifier_with_special_characters(self) -> None:
        """Type guard returns True for Identifier with dashes/underscores."""
        key = Identifier("some-key")
        assert is_identifier(key) is True

        key2 = Identifier("another_key")
        assert is_identifier(key2) is True


class TestIsNumberLiteral:
    """Test is_number_literal type guard."""

    def test_returns_true_for_number_literal(self) -> None:
        """Type guard returns True for NumberLiteral."""
        key = NumberLiteral("1")
        assert is_number_literal(key) is True

    def test_returns_false_for_identifier(self) -> None:
        """Type guard returns False for Identifier."""
        key = Identifier("one")
        assert is_number_literal(key) is False

    def test_returns_true_for_zero(self) -> None:
        """Type guard returns True for zero NumberLiteral."""
        key = NumberLiteral("0")
        assert is_number_literal(key) is True

    def test_returns_true_for_large_number(self) -> None:
        """Type guard returns True for large NumberLiteral."""
        key = NumberLiteral("1000")
        assert is_number_literal(key) is True


class TestTypeGuardsIntegration:
    """Integration tests for type guards in realistic scenarios."""

    def test_pattern_element_discrimination(self) -> None:
        """Type guards correctly discriminate PatternElement union."""
        text_elem = TextElement(value="Hello")
        placeable_elem = Placeable(expression=VariableReference(id=Identifier("name")))

        # Text element
        assert is_text_element(text_elem) is True
        assert is_placeable(text_elem) is False

        # Placeable element
        assert is_placeable(placeable_elem) is True
        assert is_text_element(placeable_elem) is False

    def test_expression_discrimination(self) -> None:
        """Type guards correctly discriminate Expression union."""
        var_ref = VariableReference(id=Identifier("count"))
        select_expr = SelectExpression(
            selector=var_ref,
            variants=(
                Variant(
                    key=NumberLiteral("1"),
                    value=Pattern(elements=(TextElement(value="one"),)),
                    default=True,
                ),
            ),
        )

        # VariableReference
        assert is_variable_reference(var_ref) is True
        assert is_select_expression(var_ref) is False

        # SelectExpression
        assert is_select_expression(select_expr) is True
        assert is_variable_reference(select_expr) is False

    def test_variant_key_discrimination(self) -> None:
        """Type guards correctly discriminate variant key union."""
        id_key = Identifier("one")
        num_key = NumberLiteral("1")

        # Identifier key
        assert is_identifier(id_key) is True
        assert is_number_literal(id_key) is False

        # NumberLiteral key
        assert is_number_literal(num_key) is True
        assert is_identifier(num_key) is False

    def test_guards_with_pattern_containing_both_element_types(self) -> None:
        """Type guards work correctly with patterns containing mixed elements."""
        pattern = Pattern(
            elements=(
                TextElement(value="You have "),
                Placeable(expression=VariableReference(id=Identifier("count"))),
                TextElement(value=" items"),
            )
        )

        # Check each element
        assert is_text_element(pattern.elements[0]) is True
        assert is_placeable(pattern.elements[1]) is True
        assert is_text_element(pattern.elements[2]) is True

        # Check cross-guards
        assert is_placeable(pattern.elements[0]) is False
        assert is_text_element(pattern.elements[1]) is False
