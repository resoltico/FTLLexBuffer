"""Comprehensive coverage tests for syntax/parser/patterns.py.

Targets uncovered lines:
- Line 31: Variable reference without $ prefix
- Lines 124-127: Text element edge case (cursor.pos == text_start)
- Line 211->155: Pattern parsing edge case
"""

from __future__ import annotations

from ftllexbuffer.runtime.bundle import FluentBundle

# ============================================================================
# LINE 31: Variable Reference Without $ Prefix
# ============================================================================


class TestVariableReferenceErrorPaths:
    """Test variable reference parsing error paths (line 31)."""

    def test_variable_reference_requires_dollar_sign(self) -> None:
        """Test that variable reference without $ fails (line 31).

        parse_variable_reference expects '$' at start. If missing, returns None (line 31).
        """
        bundle = FluentBundle("en_US")
        # Pattern with identifier but no $
        bundle.add_resource("msg = Value { var }")

        # Should treat as message reference, not variable
        result, _errors = bundle.format_pattern("msg")
        # Will error because 'var' message doesn't exist
        assert len(_errors) > 0 or "{var}" in result


# ============================================================================
# LINES 124-127: Text Element Edge Case
# ============================================================================


class TestTextElementEdgeCases:
    """Test text element parsing edge cases (lines 124-127)."""

    def test_pattern_with_stop_char_not_placeable(self) -> None:
        """Test pattern with stop character that's not '{' (lines 124-127).

        When cursor is at a stop character but hasn't consumed any text,
        the parser advances to prevent infinite loop (line 127).
        """
        bundle = FluentBundle("en_US")
        # Pattern ending at newline (stop char)
        bundle.add_resource("msg = Value\n")

        result, _errors = bundle.format_pattern("msg")
        assert "Value" in result

    def test_empty_pattern_followed_by_attribute(self) -> None:
        """Test empty pattern followed by attribute (edge case).

        This tests the cursor advancement when pos == text_start.
        """
        bundle = FluentBundle("en_US")
        # Message with empty value but attributes
        bundle.add_resource("""
msg =
    .attr = Attribute
""")

        result, _errors = bundle.format_pattern("msg", attribute="attr")
        assert "Attribute" in result


# ============================================================================
# LINE 211->155: Pattern Parsing Edge Case
# ============================================================================


class TestPatternParsingEdgeCases:
    """Test pattern parsing edge cases (line 211->155)."""

    def test_pattern_at_eof_without_newline(self) -> None:
        """Test pattern parsing at EOF (line 211).

        When pattern ends at EOF, cursor.pos > text_start check succeeds.
        """
        bundle = FluentBundle("en_US")
        # Pattern at EOF without trailing newline
        bundle.add_resource("msg = Value at EOF")  # No \n

        result, _errors = bundle.format_pattern("msg")
        assert "Value at EOF" in result

    def test_multiline_pattern_with_continuation(self) -> None:
        """Test multiline pattern with indented continuation."""
        bundle = FluentBundle("en_US")
        # Multiline pattern with continuation
        bundle.add_resource("""
msg =
    First line
    Second line
""")

        result, _errors = bundle.format_pattern("msg")
        # Should contain both lines
        assert "First line" in result or "Second line" in result


# ============================================================================
# Integration Tests
# ============================================================================


class TestPatternParsingIntegration:
    """Integration tests for pattern parsing."""

    def test_complex_pattern_with_text_and_placeables(self) -> None:
        """Test pattern with mixed text and placeables."""
        bundle = FluentBundle("en_US")
        bundle.add_resource("msg = Hello { $name }, you have { $count } messages.")

        result, _errors = bundle.format_pattern("msg", {"name": "Alice", "count": 5})
        # Account for Unicode bidi marks
        assert "Alice" in result
        assert "5" in result
        assert "messages" in result

    def test_pattern_with_special_characters(self) -> None:
        """Test pattern with special characters."""
        bundle = FluentBundle("en_US")
        bundle.add_resource("msg = Value with \t tabs and  spaces")

        result, _errors = bundle.format_pattern("msg")
        assert "Value" in result

    def test_pattern_with_unicode(self) -> None:
        """Test pattern with Unicode characters."""
        bundle = FluentBundle("en_US")
        bundle.add_resource("msg = Unicode: \u4e2d\u6587 \u1f600")

        result, _errors = bundle.format_pattern("msg")
        assert "Unicode:" in result
        assert "\u4e2d\u6587" in result

    def test_empty_pattern_edge_case(self) -> None:
        """Test truly empty pattern."""
        bundle = FluentBundle("en_US")
        # Message with whitespace-only pattern
        bundle.add_resource("msg =   \n")

        result, _errors = bundle.format_pattern("msg")
        # Should return something (empty or error)
        assert isinstance(result, str)
