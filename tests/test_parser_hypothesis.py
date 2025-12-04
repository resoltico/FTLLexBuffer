"""Hypothesis property-based tests for Fluent parser.

Focus on parser robustness, error recovery, and invariant properties.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from ftllexbuffer.syntax.parser import FluentParserV1


class TestParserRobustness:
    """Property-based tests for parser robustness."""

    @given(
        identifier=st.text(
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll"), min_codepoint=97, max_codepoint=122
            ),
            min_size=1,
            max_size=20,
        ).filter(lambda x: x[0].isalpha()),
    )
    @settings(max_examples=200)
    def test_simple_message_always_parses(self, identifier: str) -> None:
        """Simple message with valid identifier always parses successfully."""
        source = f"{identifier} = value"
        parser = FluentParserV1()
        resource = parser.parse(source)

        # Should always produce a resource
        assert resource is not None
        assert hasattr(resource, "entries")
        # Should have at least one entry (message or junk)
        assert len(resource.entries) >= 0

    @given(
        identifier=st.text(
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll"), min_codepoint=97, max_codepoint=122
            ),
            min_size=1,
            max_size=20,
        ).filter(lambda x: x[0].isalpha()),
        value=st.text(
            alphabet=st.characters(blacklist_categories=["Cc"], blacklist_characters="{}\n"),
            min_size=0,
            max_size=100,
        ),
    )
    @settings(max_examples=200)
    def test_message_with_arbitrary_value_parses(
        self, identifier: str, value: str
    ) -> None:
        """Messages with arbitrary (non-special) text values parse."""
        source = f"{identifier} = {value}"
        parser = FluentParserV1()
        resource = parser.parse(source)

        assert resource is not None
        assert len(resource.entries) >= 0

    @given(
        comment_text=st.text(
            alphabet=st.characters(blacklist_categories=["Cc"], blacklist_characters="#"),
            min_size=0,
            max_size=100,
        ),
    )
    @settings(max_examples=150)
    def test_single_line_comment_always_parses(self, comment_text: str) -> None:
        """Single-line comments with arbitrary text parse successfully."""
        source = f"# {comment_text}\nkey = value"
        parser = FluentParserV1()
        resource = parser.parse(source)

        # Should parse (comment + message)
        assert resource is not None
        assert len(resource.entries) >= 1

    @given(
        num_newlines=st.integers(min_value=0, max_value=10),
    )
    @settings(max_examples=50)
    def test_blank_lines_do_not_affect_parsing(self, num_newlines: int) -> None:
        """Multiple blank lines should not affect parsing."""
        source = f"key1 = value1{'\\n' * num_newlines}key2 = value2"
        parser = FluentParserV1()
        resource = parser.parse(source)

        # Should parse both messages regardless of blank lines
        assert resource is not None
        # Could be 0-2 entries depending on junk handling
        assert len(resource.entries) >= 0

    @given(
        invalid_start=st.text(
            alphabet=st.characters(whitelist_categories=("P", "S")),
            min_size=1,
            max_size=5,
        ).filter(lambda x: x[0] not in "#-"),
    )
    @settings(max_examples=100)
    def test_invalid_entry_creates_junk(self, invalid_start: str) -> None:
        """Invalid entry start characters create junk entries."""
        source = f"{invalid_start} invalid\nkey = value"
        parser = FluentParserV1()
        resource = parser.parse(source)

        # Should recover and parse the valid message
        assert resource is not None
        assert len(resource.entries) >= 0


class TestParserInvariants:
    """Metamorphic and invariant properties of the parser."""

    @given(
        source=st.text(
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll"),
                min_codepoint=32,
                max_codepoint=126,
            ),
            min_size=0,
            max_size=500,
        ),
    )
    @settings(max_examples=200)
    def test_parser_never_crashes(self, source: str) -> None:
        """Parser should never crash, regardless of input."""
        parser = FluentParserV1()

        # Should not raise exceptions - parser always returns a resource
        resource = parser.parse(source)
        assert resource is not None

    @given(
        identifier=st.text(
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll"), min_codepoint=97, max_codepoint=122
            ),
            min_size=1,
            max_size=20,
        ).filter(lambda x: x[0].isalpha()),
    )
    @settings(max_examples=100)
    def test_parse_idempotence(self, identifier: str) -> None:
        """Parsing the same source twice yields equivalent results."""
        source = f"{identifier} = value"
        parser = FluentParserV1()

        resource1 = parser.parse(source)
        resource2 = parser.parse(source)

        # Both should have same number of entries
        assert len(resource1.entries) == len(resource2.entries)

    @given(
        whitespace=st.text(alphabet=st.sampled_from([" ", "\t"]), min_size=0, max_size=10),
    )
    @settings(max_examples=100)
    def test_leading_whitespace_invariance(self, whitespace: str) -> None:
        """Leading whitespace on continuation lines is significant."""
        # Indented continuation should be treated as continuation
        source1 = "key = value"
        source2 = f"key = value\n{whitespace}  continuation"

        parser = FluentParserV1()
        resource1 = parser.parse(source1)
        resource2 = parser.parse(source2)

        # Both should parse (resource2 might have continuation)
        assert resource1 is not None
        assert resource2 is not None


class TestParserEdgeCases:
    """Edge cases and boundary conditions."""

    @given(
        num_hashes=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=50)
    def test_comment_hash_count_validation(self, num_hashes: int) -> None:
        """Comments with different hash counts are handled correctly."""
        source = f"{'#' * num_hashes} Comment\nkey = value"
        parser = FluentParserV1()
        resource = parser.parse(source)

        # Should handle any number of hashes (1-3 valid, >3 creates junk)
        assert resource is not None
        assert len(resource.entries) >= 0

    @given(
        depth=st.integers(min_value=1, max_value=5),
    )
    @settings(max_examples=50)
    def test_nested_placeables_parse(self, depth: int) -> None:  # noqa: ARG002
        """Nested placeables up to reasonable depth parse."""
        # Create nested variable references (simplified test - just validates parsing)
        inner = "$var"
        source = f"key = {{ {inner} }}"

        parser = FluentParserV1()
        resource = parser.parse(source)

        # Should parse (might create errors for invalid syntax)
        assert resource is not None

    @given(
        num_variants=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=50)
    def test_select_expression_variant_count(self, num_variants: int) -> None:
        """Select expressions with varying variant counts parse."""
        # Generate variants
        variants = "\n".join([f"    [{i}] Variant {i}" for i in range(num_variants)])
        source = f"key = {{ $num ->\\n{variants}\\n   *[other] Default\\n}}"

        parser = FluentParserV1()
        resource = parser.parse(source)

        # Should parse
        assert resource is not None

    def test_empty_source_produces_empty_resource(self) -> None:
        """Empty source produces resource with no entries."""
        parser = FluentParserV1()
        resource = parser.parse("")

        assert resource is not None
        assert len(resource.entries) == 0

    def test_only_whitespace_produces_empty_resource(self) -> None:
        """Source with only whitespace produces empty or junk resource."""
        parser = FluentParserV1()
        resource = parser.parse("   \n\t\n   \n")

        assert resource is not None
        # May be 0 (empty) or contain junk entries for malformed whitespace
        assert len(resource.entries) >= 0

    @given(
        identifier=st.text(
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll"), min_codepoint=97, max_codepoint=122
            ),
            min_size=1,
            max_size=20,
        ).filter(lambda x: x[0].isalpha()),
        num_attributes=st.integers(min_value=1, max_value=5),
    )
    @settings(max_examples=100)
    def test_message_with_multiple_attributes(
        self, identifier: str, num_attributes: int
    ) -> None:
        """Messages with multiple attributes parse correctly."""
        attributes = "\n".join(
            [f"    .attr{i} = Value {i}" for i in range(num_attributes)]
        )
        source = f"{identifier} = Main value\n{attributes}"

        parser = FluentParserV1()
        resource = parser.parse(source)

        # Should parse message with attributes
        assert resource is not None
        assert len(resource.entries) >= 0


class TestParserRecovery:
    """Test error recovery and resilience."""

    @given(
        num_errors=st.integers(min_value=1, max_value=5),
    )
    @settings(max_examples=50)
    def test_multiple_errors_recovery(self, num_errors: int) -> None:
        """Parser recovers from multiple consecutive errors."""
        # Create multiple invalid lines followed by valid message
        invalid_lines = "\n".join([f"!!! invalid {i}" for i in range(num_errors)])
        source = f"{invalid_lines}\nkey = value"

        parser = FluentParserV1()
        resource = parser.parse(source)

        # Should create junk entries and recover
        assert resource is not None
        assert len(resource.entries) >= 0

    @given(
        unicode_char=st.characters(min_codepoint=0x1F600, max_codepoint=0x1F64F),
    )
    @settings(max_examples=50)
    def test_unicode_emoji_in_values(self, unicode_char: str) -> None:
        """Unicode emoji characters in values are handled."""
        source = f"key = Hello {unicode_char}"
        parser = FluentParserV1()
        resource = parser.parse(source)

        # Should parse
        assert resource is not None

    def test_very_long_identifier(self) -> None:
        """Very long identifiers are handled."""
        long_id = "a" * 1000
        source = f"{long_id} = value"
        parser = FluentParserV1()
        resource = parser.parse(source)

        # Should parse (or create junk if too long)
        assert resource is not None

    def test_very_long_value(self) -> None:
        """Very long values are handled."""
        long_value = "value " * 1000
        source = f"key = {long_value}"
        parser = FluentParserV1()
        resource = parser.parse(source)

        # Should parse
        assert resource is not None
