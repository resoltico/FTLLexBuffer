"""Property-based tests for system invariants.

Uses Hypothesis to test properties that must always hold, regardless of input.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from ftllexbuffer import FluentBundle
from ftllexbuffer.diagnostics import (
    FluentCyclicReferenceError,
    FluentReferenceError,
    FluentSyntaxError,
)
from ftllexbuffer.runtime import FunctionRegistry, select_plural_category

from .strategies import (
    camel_case_identifiers,
    ftl_identifiers,
    ftl_numbers,
    ftl_simple_messages,
    snake_case_identifiers,
)


class TestFunctionBridgeProperties:
    """Function bridge must maintain bijection between snake_case and camelCase."""

    @given(snake_case_identifiers())
    @settings(max_examples=100)
    def test_snake_to_camel_roundtrip(self, snake_case: str) -> None:
        """snake_case → camelCase → snake_case preserves original."""
        camel = FunctionRegistry._to_camel_case(snake_case)
        snake2 = FunctionRegistry._to_snake_case(camel)
        assert snake_case == snake2

    @given(camel_case_identifiers())
    @settings(max_examples=100)
    def test_camel_to_snake_is_lowercase(self, camel_case: str) -> None:
        """camelCase → snake_case produces lowercase with underscores."""
        snake = FunctionRegistry._to_snake_case(camel_case)
        assert snake.islower() or "_" in snake
        assert all(c.isalnum() or c == "_" for c in snake)


class TestPluralRulesProperties:
    """Plural rules must follow CLDR specification."""

    @given(st.integers(min_value=0, max_value=100000))
    @settings(max_examples=200)
    def test_latvian_plural_categories_complete(self, n: int) -> None:
        """Every number maps to a valid Latvian category."""
        category = select_plural_category(n, "lv_LV")
        assert category in ["zero", "one", "other"]

    @given(st.integers(min_value=0, max_value=100000))
    @settings(max_examples=200)
    def test_english_plural_categories(self, n: int) -> None:
        """English has only one/other, and one means exactly 1."""
        category = select_plural_category(n, "en_US")
        assert category in ["one", "other"]
        assert (category == "one") == (n == 1)

    @given(st.integers(min_value=0, max_value=100000))
    @settings(max_examples=100)
    def test_german_plural_same_as_english(self, n: int) -> None:
        """German and English have identical plural rules."""
        de_cat = select_plural_category(n, "de_DE")
        en_cat = select_plural_category(n, "en_US")
        assert de_cat == en_cat


class TestParserProperties:
    """Parser must handle any input gracefully."""

    @given(ftl_simple_messages())
    @settings(max_examples=50)
    def test_parser_accepts_valid_simple_messages(self, ftl_source: str) -> None:
        """Parser successfully parses valid simple messages.

        If this raises an exception, Hypothesis will find the minimal failing
        example - that's exactly what we want (reveals bugs or invalid strategy).
        """
        bundle = FluentBundle("en-US")
        bundle.add_resource(ftl_source)
        # If parser can't handle "valid" input, test should fail

    @given(st.text(max_size=100))
    @settings(max_examples=50)
    def test_parser_never_crashes(self, random_text: str) -> None:
        """Parser handles ANY input gracefully (no crashes).

        Fuzzing test: Parser should handle random text without crashing.
        Expected exceptions (graceful degradation) are caught.
        Unexpected exceptions (bugs) will fail the test.
        """
        bundle = FluentBundle("en-US")
        try:
            bundle.add_resource(random_text)
            # Should either parse successfully or raise expected error
        except (FluentSyntaxError, FluentReferenceError, FluentCyclicReferenceError):
            # Expected: Invalid syntax, missing references, circular deps
            # What matters: Parser recovered gracefully (no crash)
            pass


class TestResolverProperties:
    """Resolver must be deterministic and never crash."""

    @given(ftl_simple_messages())
    @settings(max_examples=30)
    def test_resolver_is_deterministic(self, message: str) -> None:
        """Same message always produces same output."""
        bundle = FluentBundle("en-US")
        bundle.add_resource(message)

        # Extract message ID
        if " = " in message:
            msg_id = message.split(" = ")[0].strip()

            # Format twice with same args
            result1 = bundle.format_pattern(msg_id, {})
            result2 = bundle.format_pattern(msg_id, {})
            assert result1 == result2


class TestIdentifierProperties:
    """FTL identifiers must follow naming rules."""

    @given(ftl_identifiers())
    @settings(max_examples=100)
    def test_identifiers_start_with_letter(self, identifier: str) -> None:
        """Generated identifiers always start with a letter."""
        assert identifier[0].islower()

    @given(ftl_identifiers())
    @settings(max_examples=100)
    def test_identifiers_valid_characters(self, identifier: str) -> None:
        """Generated identifiers only contain valid characters."""
        assert all(c.isalnum() or c in "-_" for c in identifier)


class TestNumberProperties:
    """Number formatting must be consistent."""

    @given(ftl_numbers())
    @settings(max_examples=50)
    def test_number_format_returns_string(self, number: int | float) -> None:
        """Number formatting always returns a string."""
        from ftllexbuffer.runtime.functions import number_format

        result = number_format(number)
        assert isinstance(result, str)
        assert len(result) > 0
