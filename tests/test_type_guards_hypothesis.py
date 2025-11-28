"""Hypothesis-based property tests for type guard functions.

Targets 78% → 100% coverage gap in src/ftllexbuffer/syntax/type_guards.py.
Focuses on missing coverage for is_comment, is_junk, and has_value edge cases.

Missing lines (22% gap):
- Lines 74-76: is_comment with Comment nodes
- Lines 88-90: is_junk with Junk nodes
- Line 146: has_value returning False for non-Message/Term objects

This file adds ~12 property tests to kill ~25 mutations and achieve 100% coverage
on type_guards.py.

Target: Kill type guard mutations in:
- isinstance() checks
- Type narrowing logic
- Boolean return values
- Guard completeness (exactly one guard matches per node)

Phase: 3.2 (Type Guards Hypothesis Tests)
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from ftllexbuffer.syntax.type_guards import (
    has_value,
    is_comment,
    is_junk,
    is_message,
    is_placeable,
    is_term,
    is_text_element,
)
from tests.strategies import any_ast_entry, any_ast_pattern_element

# ============================================================================
# GUARD COMPLETENESS TESTS
# ============================================================================


class TestTypeGuardCompleteness:
    """Property tests for type guard completeness.

    INVARIANT: Exactly one entry guard should match each AST entry.
    Targets mutations in isinstance() checks.
    """

    @given(any_ast_entry())
    @settings(max_examples=200)
    def test_exactly_one_entry_guard_matches(self, entry):
        """PROPERTY: Exactly one entry guard matches each AST entry.

        Kills: isinstance() mutations (Message → Term, etc.)
        """
        # mypy: list of type guards with different narrowing types
        # Using list for iteration, each guard has different TypeIs signature
        entry_guards: list = [is_message, is_term, is_comment, is_junk]
        matches = sum(1 for guard in entry_guards if guard(entry))

        assert matches == 1, (
            f"Expected exactly 1 guard to match {type(entry).__name__}, "
            f"but {matches} matched"
        )

    @given(any_ast_pattern_element())
    @settings(max_examples=200)
    def test_exactly_one_element_guard_matches(self, element):
        """PROPERTY: Exactly one element guard matches each pattern element.

        Kills: isinstance() mutations for TextElement/Placeable.
        """
        # mypy: list of type guards with different narrowing types
        # Using list for iteration, each guard has different TypeIs signature
        element_guards: list = [is_text_element, is_placeable]
        matches = sum(1 for guard in element_guards if guard(element))

        assert matches == 1, (
            f"Expected exactly 1 guard to match {type(element).__name__}, "
            f"but {matches} matched"
        )

    @given(any_ast_entry())
    @settings(max_examples=100)
    def test_message_and_term_mutually_exclusive(self, entry):
        """PROPERTY: Entry cannot be both Message and Term.

        Kills: Boolean operator mutations (and → or).
        """
        # At most one can be true (mypy: distinct types can't overlap)
        assert not (is_message(entry) and is_term(entry)), (  # type: ignore[unreachable]
            "Entry cannot be both Message and Term"
        )

    @given(any_ast_entry())
    @settings(max_examples=100)
    def test_comment_and_junk_mutually_exclusive(self, entry):
        """PROPERTY: Entry cannot be both Comment and Junk.

        Kills: Boolean operator mutations.
        """
        # mypy: distinct types can't overlap
        assert not (is_comment(entry) and is_junk(entry)), (  # type: ignore[unreachable]
            "Entry cannot be both Comment and Junk"
        )


# ============================================================================
# GUARD ROBUSTNESS TESTS
# ============================================================================


class TestTypeGuardRobustness:
    """Property tests for type guard robustness.

    INVARIANT: Guards should handle any Python object without crashing.
    Targets error handling and edge cases.
    """

    @given(
        st.one_of(
            st.none(),
            st.integers(),
            st.floats(),
            st.text(),
            st.booleans(),
            st.lists(st.integers()),
            st.dictionaries(st.text(), st.integers()),
            any_ast_entry(),
        )
    )
    @settings(max_examples=300)
    def test_entry_guards_never_crash_on_any_object(self, obj):
        """ROBUSTNESS: Entry guards handle ANY Python object.

        Kills: Unexpected exception mutations, missing type checks.
        Targets line 146: has_value False branch.
        """
        # mypy: list of type guards with different narrowing types
        # Using list for iteration, each guard has different TypeIs signature
        entry_guards: list = [is_message, is_term, is_comment, is_junk, has_value]

        for guard in entry_guards:
            # Should always return bool, never raise
            result = guard(obj)
            assert isinstance(result, bool), (
                f"Guard {guard.__name__} should return bool, got {type(result)}"
            )

    @given(
        st.one_of(
            st.none(),
            st.integers(),
            st.text(),
            st.lists(st.text()),
            any_ast_pattern_element(),
        )
    )
    @settings(max_examples=200)
    def test_element_guards_never_crash_on_any_object(self, obj):
        """ROBUSTNESS: Element guards handle ANY Python object.

        Kills: Unexpected exception mutations in is_text_element/is_placeable.
        """
        # mypy: list of type guards with different narrowing types
        # Using list for iteration, each guard has different TypeIs signature
        element_guards: list = [is_text_element, is_placeable]

        for guard in element_guards:
            result = guard(obj)
            assert isinstance(result, bool), (
                f"Guard {guard.__name__} should return bool, got {type(result)}"
            )


# ============================================================================
# HAS_VALUE SPECIFIC TESTS
# ============================================================================


class TestHasValueGuard:
    """Property tests for has_value guard.

    Special focus on the False branch (line 146) which needs coverage.
    """

    @given(
        st.one_of(
            st.none(),
            st.integers(),
            st.text(),
            st.from_type(type).map(lambda _: object()),  # Random objects
        )
    )
    @settings(max_examples=150)
    def test_has_value_false_for_non_message_term(self, obj):
        """COVERAGE: has_value returns False for non-Message/Term objects.

        Specifically targets line 146: return False
        """
        result = has_value(obj)
        assert result is False, f"has_value should be False for {type(obj)}"

    @given(any_ast_entry())
    @settings(max_examples=150)
    def test_has_value_implies_not_none_value(self, entry):
        """PROPERTY: If has_value is True, then entry.value is not None.

        Kills: value is None check mutations.
        """
        if has_value(entry):
            # After type guard, we know it's Message or Term
            assert hasattr(entry, "value"), "Entry should have 'value' attribute"
            assert entry.value is not None, "value should not be None when has_value is True"

    @given(any_ast_entry())
    @settings(max_examples=100)
    def test_has_value_consistency_with_isinstance(self, entry):
        """PROPERTY: has_value is True iff entry is Message/Term with non-None value.

        Kills: isinstance check mutations, value None check mutations.
        """
        is_msg_or_term = is_message(entry) or is_term(entry)

        if is_msg_or_term:
            # Should have value attribute
            assert hasattr(entry, "value")
            # has_value should match whether value is not None
            expected = entry.value is not None
            assert has_value(entry) == expected
        else:
            # Not Message or Term, so has_value should be False
            assert has_value(entry) is False


# ============================================================================
# TYPE NARROWING VERIFICATION
# ============================================================================


class TestTypeNarrowing:
    """Property tests verifying type narrowing works correctly.

    These tests verify that after a guard returns True, the object
    has the expected attributes (proving type narrowing worked).
    """

    @given(any_ast_entry())
    @settings(max_examples=100)
    def test_is_message_implies_id_attribute(self, entry):
        """PROPERTY: is_message guards mean object has .id attribute.

        Kills: Return value mutations (True → False).
        """
        if is_message(entry):
            assert hasattr(entry, "id"), "Message should have id attribute"
            assert hasattr(entry, "value"), "Message should have value attribute"
            assert hasattr(entry, "attributes"), "Message should have attributes"

    @given(any_ast_entry())
    @settings(max_examples=100)
    def test_is_term_implies_id_attribute(self, entry):
        """PROPERTY: is_term guards mean object has .id attribute.

        Kills: Return value mutations.
        """
        if is_term(entry):
            assert hasattr(entry, "id"), "Term should have id attribute"
            assert hasattr(entry, "value"), "Term should have value attribute"

    @given(any_ast_entry())
    @settings(max_examples=100)
    def test_is_comment_implies_content_attribute(self, entry):
        """PROPERTY: is_comment guards mean object has .content attribute.

        Specifically targets lines 74-76: is_comment implementation.
        """
        if is_comment(entry):
            assert hasattr(entry, "content"), "Comment should have content attribute"

    @given(any_ast_entry())
    @settings(max_examples=100)
    def test_is_junk_implies_content_attribute(self, entry):
        """PROPERTY: is_junk guards mean object has .content attribute.

        Specifically targets lines 88-90: is_junk implementation.
        """
        if is_junk(entry):
            assert hasattr(entry, "content"), "Junk should have content attribute"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
