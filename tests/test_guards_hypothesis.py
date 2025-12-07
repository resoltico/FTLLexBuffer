"""Hypothesis property-based tests for AST type guards.

Tests type guard correctness, type narrowing properties, and robustness.
Complements test_fluent_guards.py with property-based testing.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from ftllexbuffer import FluentParserV1
from ftllexbuffer.guards import (
    is_identifier,
    is_number_literal,
    is_placeable,
    is_select_expression,
    is_text_element,
    is_variable_reference,
)
from ftllexbuffer.syntax.ast import (
    Identifier,
    Message,
    NumberLiteral,
    Placeable,
    SelectExpression,
    TextElement,
    VariableReference,
)

# ============================================================================
# HYPOTHESIS STRATEGIES
# ============================================================================


# Strategy for text content (excluding FTL syntax characters and whitespace-only)
text_content = st.text(
    alphabet=st.characters(
        blacklist_categories=["Cc"],
        blacklist_characters=["{", "}", "[", "]", "$", "-", "*", "."],
    ),
    min_size=1,
).filter(lambda s: s.strip())

# Strategy for variable names - use st.from_regex per hypothesis.md
variable_names = st.from_regex(r"[a-z]+", fullmatch=True)

# Strategy for message IDs - use st.from_regex per hypothesis.md
message_ids = st.from_regex(r"[a-z]+", fullmatch=True)

# Strategy for numbers - remove arbitrary bounds
numbers = st.integers()


# ============================================================================
# PROPERTY TESTS - TEXT ELEMENT GUARD
# ============================================================================


class TestTextElementGuard:
    """Test is_text_element() type guard properties."""

    @given(text=text_content)
    @settings(max_examples=200)
    def test_text_element_recognized(self, text: str) -> None:
        """PROPERTY: TextElement instances return True."""
        parser = FluentParserV1()
        ftl_source = f"msg = {text}"

        resource = parser.parse(ftl_source)
        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None

        element = msg.value.elements[0]
        assert isinstance(element, TextElement)

        # Guard should return True
        assert is_text_element(element)

    @given(var_name=variable_names)
    @settings(max_examples=200)
    def test_placeable_not_text_element(self, var_name: str) -> None:
        """PROPERTY: Placeable instances return False."""
        parser = FluentParserV1()
        ftl_source = f"msg = {{ ${var_name} }}"

        resource = parser.parse(ftl_source)
        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None

        element = msg.value.elements[0]
        assert isinstance(element, Placeable)

        # Guard should return False
        assert not is_text_element(element)  # type: ignore[unreachable]

    @given(value=st.one_of(st.integers(), st.text(), st.booleans(), st.none()))
    @settings(max_examples=100)
    def test_non_ast_objects_return_false(self, value) -> None:
        """PROPERTY: Non-AST objects always return False."""
        assert not is_text_element(value)


# ============================================================================
# PROPERTY TESTS - PLACEABLE GUARD
# ============================================================================


class TestPlaceableGuard:
    """Test is_placeable() type guard properties."""

    @given(var_name=variable_names)
    @settings(max_examples=200)
    def test_placeable_recognized(self, var_name: str) -> None:
        """PROPERTY: Placeable instances return True."""
        parser = FluentParserV1()
        ftl_source = f"msg = {{ ${var_name} }}"

        resource = parser.parse(ftl_source)
        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None

        element = msg.value.elements[0]
        assert isinstance(element, Placeable)

        # Guard should return True
        assert is_placeable(element)

    @given(text=text_content)
    @settings(max_examples=200)
    def test_text_element_not_placeable(self, text: str) -> None:
        """PROPERTY: TextElement instances return False."""
        parser = FluentParserV1()
        ftl_source = f"msg = {text}"

        resource = parser.parse(ftl_source)
        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None

        element = msg.value.elements[0]
        assert isinstance(element, TextElement)

        # Guard should return False
        assert not is_placeable(element)  # type: ignore[unreachable]

    @given(value=st.one_of(st.integers(), st.text(), st.booleans(), st.none()))
    @settings(max_examples=100)
    def test_non_ast_objects_return_false(self, value) -> None:
        """PROPERTY: Non-AST objects always return False."""
        assert not is_placeable(value)


# ============================================================================
# PROPERTY TESTS - VARIABLE REFERENCE GUARD
# ============================================================================


class TestVariableReferenceGuard:
    """Test is_variable_reference() type guard properties."""

    @given(var_name=variable_names)
    @settings(max_examples=200)
    def test_variable_reference_recognized(self, var_name: str) -> None:
        """PROPERTY: VariableReference instances return True."""
        parser = FluentParserV1()
        ftl_source = f"msg = {{ ${var_name} }}"

        resource = parser.parse(ftl_source)
        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None

        placeable = msg.value.elements[0]
        assert isinstance(placeable, Placeable)

        expr = placeable.expression
        assert isinstance(expr, VariableReference)

        # Guard should return True
        assert is_variable_reference(expr)

    @given(var_name=variable_names)
    @settings(max_examples=100)
    def test_select_expression_not_variable_reference(self, var_name: str) -> None:
        """PROPERTY: SelectExpression instances return False."""
        parser = FluentParserV1()
        ftl_source = f"""msg = {{ ${var_name} ->
    [one] One
   *[other] Other
}}"""

        resource = parser.parse(ftl_source)
        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None

        placeable = msg.value.elements[0]
        assert isinstance(placeable, Placeable)

        expr = placeable.expression
        assert isinstance(expr, SelectExpression)

        # Guard should return False
        assert not is_variable_reference(expr)  # type: ignore[unreachable]

    @given(value=st.one_of(st.integers(), st.text(), st.booleans(), st.none()))
    @settings(max_examples=100)
    def test_non_ast_objects_return_false(self, value) -> None:
        """PROPERTY: Non-AST objects always return False."""
        assert not is_variable_reference(value)


# ============================================================================
# PROPERTY TESTS - SELECT EXPRESSION GUARD
# ============================================================================


class TestSelectExpressionGuard:
    """Test is_select_expression() type guard properties."""

    @given(var_name=variable_names)
    @settings(max_examples=200)
    def test_select_expression_recognized(self, var_name: str) -> None:
        """PROPERTY: SelectExpression instances return True."""
        parser = FluentParserV1()
        ftl_source = f"""msg = {{ ${var_name} ->
    [one] One
   *[other] Other
}}"""

        resource = parser.parse(ftl_source)
        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None

        placeable = msg.value.elements[0]
        assert isinstance(placeable, Placeable)

        expr = placeable.expression
        assert isinstance(expr, SelectExpression)

        # Guard should return True
        assert is_select_expression(expr)

    @given(var_name=variable_names)
    @settings(max_examples=200)
    def test_variable_reference_not_select_expression(self, var_name: str) -> None:
        """PROPERTY: VariableReference instances return False."""
        parser = FluentParserV1()
        ftl_source = f"msg = {{ ${var_name} }}"

        resource = parser.parse(ftl_source)
        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None

        placeable = msg.value.elements[0]
        assert isinstance(placeable, Placeable)

        expr = placeable.expression
        assert isinstance(expr, VariableReference)

        # Guard should return False
        assert not is_select_expression(expr)  # type: ignore[unreachable]

    @given(value=st.one_of(st.integers(), st.text(), st.booleans(), st.none()))
    @settings(max_examples=100)
    def test_non_ast_objects_return_false(self, value) -> None:
        """PROPERTY: Non-AST objects always return False."""
        assert not is_select_expression(value)


# ============================================================================
# PROPERTY TESTS - IDENTIFIER GUARD
# ============================================================================


class TestIdentifierGuard:
    """Test is_identifier() type guard properties."""

    @given(msg_id=message_ids)
    @settings(max_examples=200)
    def test_identifier_recognized(self, msg_id: str) -> None:
        """PROPERTY: Identifier instances return True."""
        parser = FluentParserV1()
        ftl_source = f"{msg_id} = Hello"

        resource = parser.parse(ftl_source)
        msg = resource.entries[0]
        assert isinstance(msg, Message)

        identifier = msg.id
        assert isinstance(identifier, Identifier)

        # Guard should return True
        assert is_identifier(identifier)

    @given(number=numbers)
    @settings(max_examples=100)
    def test_number_literal_not_identifier(self, number: int) -> None:
        """PROPERTY: NumberLiteral instances return False."""
        number_lit = NumberLiteral(value=str(number))

        # Guard should return False
        assert not is_identifier(number_lit)  # type: ignore[unreachable]

    @given(value=st.one_of(st.integers(), st.text(), st.booleans(), st.none()))
    @settings(max_examples=100)
    def test_non_ast_objects_return_false(self, value) -> None:
        """PROPERTY: Non-AST objects always return False."""
        assert not is_identifier(value)


# ============================================================================
# PROPERTY TESTS - NUMBER LITERAL GUARD
# ============================================================================


class TestNumberLiteralGuard:
    """Test is_number_literal() type guard properties."""

    @given(number=numbers)
    @settings(max_examples=200)
    def test_number_literal_recognized(self, number: int) -> None:
        """PROPERTY: NumberLiteral instances return True."""
        number_lit = NumberLiteral(value=str(number))

        # Guard should return True
        assert is_number_literal(number_lit)

    @given(msg_id=message_ids)
    @settings(max_examples=100)
    def test_identifier_not_number_literal(self, msg_id: str) -> None:
        """PROPERTY: Identifier instances return False."""
        identifier = Identifier(name=msg_id)

        # Guard should return False
        assert not is_number_literal(identifier)  # type: ignore[unreachable]

    @given(value=st.one_of(st.integers(), st.text(), st.booleans(), st.none()))
    @settings(max_examples=100)
    def test_non_ast_objects_return_false(self, value) -> None:
        """PROPERTY: Non-AST objects always return False."""
        assert not is_number_literal(value)


# ============================================================================
# PROPERTY TESTS - GUARD CONSISTENCY
# ============================================================================


class TestGuardConsistency:
    """Test consistency between different guards."""

    @given(var_name=variable_names)
    @settings(max_examples=100)
    def test_guards_mutually_exclusive(self, var_name: str) -> None:
        """PROPERTY: AST nodes match exactly one guard."""
        parser = FluentParserV1()
        ftl_source = f"msg = Text {{ ${var_name} }}"

        resource = parser.parse(ftl_source)
        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None

        # Check each element matches exactly one guard
        for element in msg.value.elements:
            guards_true = [
                is_text_element(element),
                is_placeable(element),
            ]
            # Exactly one should be True
            assert sum(guards_true) == 1

    @given(var_name=variable_names)
    @settings(max_examples=100)
    def test_expression_guards_mutually_exclusive(self, var_name: str) -> None:
        """PROPERTY: Expression nodes match exactly one expression guard."""
        parser = FluentParserV1()
        ftl_source = f"msg = {{ ${var_name} }}"

        resource = parser.parse(ftl_source)
        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None

        placeable = msg.value.elements[0]
        assert isinstance(placeable, Placeable)
        expr = placeable.expression

        # Check expression matches exactly one guard
        guards_true = [
            is_variable_reference(expr),
            is_select_expression(expr),
        ]
        # Exactly one should be True
        assert sum(guards_true) == 1


# ============================================================================
# PROPERTY TESTS - IDEMPOTENCE
# ============================================================================


class TestGuardIdempotence:
    """Test idempotent guard operations."""

    @given(var_name=variable_names)
    @settings(max_examples=100)
    def test_is_variable_reference_idempotent(self, var_name: str) -> None:
        """PROPERTY: Multiple guard calls return same result."""
        parser = FluentParserV1()
        ftl_source = f"msg = {{ ${var_name} }}"

        resource = parser.parse(ftl_source)
        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None

        placeable = msg.value.elements[0]
        expr = placeable.expression  # type: ignore[union-attr]

        result1 = is_variable_reference(expr)
        result2 = is_variable_reference(expr)
        result3 = is_variable_reference(expr)

        assert result1 == result2 == result3

    @given(text=text_content)
    @settings(max_examples=100)
    def test_is_text_element_idempotent(self, text: str) -> None:
        """PROPERTY: Multiple guard calls return same result."""
        parser = FluentParserV1()
        ftl_source = f"msg = {text}"

        resource = parser.parse(ftl_source)
        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None

        element = msg.value.elements[0]

        result1 = is_text_element(element)
        result2 = is_text_element(element)
        result3 = is_text_element(element)

        assert result1 == result2 == result3

    @given(number=numbers)
    @settings(max_examples=100)
    def test_is_number_literal_idempotent(self, number: int) -> None:
        """PROPERTY: Multiple guard calls return same result."""
        number_lit = NumberLiteral(value=str(number))

        result1 = is_number_literal(number_lit)
        result2 = is_number_literal(number_lit)
        result3 = is_number_literal(number_lit)

        assert result1 == result2 == result3


# ============================================================================
# PROPERTY TESTS - TYPE NARROWING
# ============================================================================


class TestTypeNarrowing:
    """Test type narrowing behavior of guards."""

    @given(var_name=variable_names)
    @settings(max_examples=100)
    def test_variable_reference_narrows_type(self, var_name: str) -> None:
        """PROPERTY: After guard check, can access VariableReference attributes."""
        parser = FluentParserV1()
        ftl_source = f"msg = {{ ${var_name} }}"

        resource = parser.parse(ftl_source)
        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None

        placeable = msg.value.elements[0]
        expr = placeable.expression  # type: ignore[union-attr]

        if is_variable_reference(expr):
            # Type narrowing should allow accessing .id attribute
            assert expr.id.name == var_name

    @given(msg_id=message_ids)
    @settings(max_examples=100)
    def test_identifier_narrows_type(self, msg_id: str) -> None:
        """PROPERTY: After guard check, can access Identifier attributes."""
        parser = FluentParserV1()
        ftl_source = f"{msg_id} = Hello"

        resource = parser.parse(ftl_source)
        msg = resource.entries[0]
        assert isinstance(msg, Message)

        identifier = msg.id

        if is_identifier(identifier):
            # Type narrowing should allow accessing .name attribute
            assert identifier.name == msg_id
