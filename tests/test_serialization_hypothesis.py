"""Hypothesis-based property tests for FTL serialization roundtrip.

Focus on parse → serialize → parse idempotence.
"""

from __future__ import annotations

from hypothesis import assume, given, settings
from hypothesis import strategies as st

from ftllexbuffer import parse_ftl, serialize_ftl
from ftllexbuffer.syntax.ast import Message


class TestSerializationRoundtrip:
    """Property-based tests for serialization idempotence."""

    @given(
        message_id=st.text(
            alphabet=st.characters(
                whitelist_categories=("L", "Nd"),
                blacklist_characters="\n\r\t ",
            ),
            min_size=1,
            max_size=20,
        ).filter(lambda x: x and x[0].isalpha()),
        value=st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ,.!?'-",
            min_size=1,
            max_size=100,
        ).filter(lambda x: x.strip()),
    )
    @settings(max_examples=200)
    def test_simple_message_roundtrip(self, message_id: str, value: str) -> None:
        """Simple messages survive parse → serialize → parse roundtrip."""
        # Create FTL source
        ftl_source = f"{message_id} = {value}"

        # Parse
        resource1 = parse_ftl(ftl_source)
        assert len(resource1.entries) >= 1

        # Serialize
        serialized = serialize_ftl(resource1)

        # Parse again
        resource2 = parse_ftl(serialized)

        # Should have same structure
        assert len(resource2.entries) == len(resource1.entries)

        # First entry should be Message
        entry1 = resource1.entries[0]
        entry2 = resource2.entries[0]

        assert isinstance(entry1, Message)
        assert isinstance(entry2, Message)
        assert entry1.id.name == entry2.id.name

    @given(
        message_id=st.text(
            alphabet=st.characters(whitelist_categories=("L", "Nd")),
            min_size=1,
            max_size=20,
        ).filter(lambda x: x and x[0].isalpha() and "-" not in x),
        attr_name=st.text(
            alphabet=st.characters(whitelist_categories=("L", "Nd")),
            min_size=1,
            max_size=15,
        ).filter(lambda x: x and x[0].isalpha()),
        attr_value=st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ,.!?'-",
            min_size=1,
            max_size=50,
        ).filter(lambda x: x.strip()),
    )
    @settings(max_examples=100)
    def test_message_with_attribute_roundtrip(
        self, message_id: str, attr_name: str, attr_value: str
    ) -> None:
        """Messages with attributes survive roundtrip."""
        assume(message_id != attr_name)  # Distinct names

        ftl_source = f"{message_id} = Value\n    .{attr_name} = {attr_value}"

        # Roundtrip
        resource1 = parse_ftl(ftl_source)
        serialized = serialize_ftl(resource1)
        resource2 = parse_ftl(serialized)

        # Should have same number of entries
        assert len(resource2.entries) == len(resource1.entries)

        # First entry should be Message with attribute
        entry1 = resource1.entries[0]
        entry2 = resource2.entries[0]

        assert isinstance(entry1, Message)
        assert isinstance(entry2, Message)
        assert len(entry1.attributes) == len(entry2.attributes)

    @given(
        message_count=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=50)
    def test_multiple_messages_count_preserved(self, message_count: int) -> None:
        """Roundtrip preserves number of messages."""
        # Generate multiple simple messages
        ftl_lines = [f"msg{i} = Value {i}" for i in range(message_count)]
        ftl_source = "\n".join(ftl_lines)

        # Roundtrip
        resource1 = parse_ftl(ftl_source)
        serialized = serialize_ftl(resource1)
        resource2 = parse_ftl(serialized)

        # Count Message entries
        messages1 = [e for e in resource1.entries if isinstance(e, Message)]
        messages2 = [e for e in resource2.entries if isinstance(e, Message)]

        assert len(messages2) == len(messages1) == message_count

    @given(
        iterations=st.integers(min_value=2, max_value=5),
    )
    @settings(max_examples=20)
    def test_serialization_idempotence(self, iterations: int) -> None:
        """serialize(parse(serialize(parse(...)))) stabilizes after first cycle."""
        ftl_source = "hello = Hello, World!"

        resource = parse_ftl(ftl_source)
        serialized1 = serialize_ftl(resource)

        # Multiple iterations
        current = serialized1
        for _ in range(iterations - 1):
            resource_temp = parse_ftl(current)
            current = serialize_ftl(resource_temp)

        # Should be identical after stabilization
        assert current == serialized1

    @given(
        whitespace_prefix=st.text(
            alphabet=" \t",
            min_size=0,
            max_size=5,
        ),
    )
    @settings(max_examples=50)
    def test_whitespace_normalization(self, whitespace_prefix: str) -> None:
        """Roundtrip may normalize whitespace but preserves structure."""
        # FTL with varying whitespace
        ftl_source = f"{whitespace_prefix}hello = World"

        resource1 = parse_ftl(ftl_source)
        serialized = serialize_ftl(resource1)
        resource2 = parse_ftl(serialized)

        # Structure preserved
        messages1 = [e for e in resource1.entries if isinstance(e, Message)]
        messages2 = [e for e in resource2.entries if isinstance(e, Message)]

        assert len(messages2) == len(messages1)
        if messages1:
            assert messages1[0].id.name == messages2[0].id.name


class TestSerializationProperties:
    """Universal properties of serialization."""

    @given(
        ftl_text=st.text(
            alphabet=st.characters(min_codepoint=32, max_codepoint=126),
            min_size=1,
            max_size=200,
        ),
    )
    @settings(max_examples=100)
    def test_serialize_never_crashes(self, ftl_text: str) -> None:
        """serialize_ftl never raises on any parsed resource."""
        # Parse (may produce junk)
        resource = parse_ftl(ftl_text)

        # Serialize should never crash - it's a pure function
        result = serialize_ftl(resource)
        assert isinstance(result, str)

    @given(
        message_id=st.text(
            alphabet=st.characters(whitelist_categories=("L",)),
            min_size=1,
            max_size=20,
        ).filter(lambda x: x and x[0].isalpha()),
    )
    @settings(max_examples=100)
    def test_roundtrip_preserves_message_ids(self, message_id: str) -> None:
        """Message IDs are preserved through roundtrip."""
        ftl_source = f"{message_id} = Value"

        resource1 = parse_ftl(ftl_source)
        serialized = serialize_ftl(resource1)
        resource2 = parse_ftl(serialized)

        messages1 = [e for e in resource1.entries if isinstance(e, Message)]
        messages2 = [e for e in resource2.entries if isinstance(e, Message)]

        if messages1 and messages2:
            assert messages1[0].id.name == messages2[0].id.name == message_id

    def test_empty_resource_roundtrip(self) -> None:
        """Empty resources survive roundtrip."""
        ftl_source = ""

        resource1 = parse_ftl(ftl_source)
        serialized = serialize_ftl(resource1)
        resource2 = parse_ftl(serialized)

        # Both should be empty
        assert len(resource1.entries) == 0
        assert len(resource2.entries) == 0

    def test_whitespace_only_resource_roundtrip(self) -> None:
        """Whitespace-only resources survive roundtrip."""
        ftl_source = "   \n\n   \n"

        resource1 = parse_ftl(ftl_source)
        serialized = serialize_ftl(resource1)
        resource2 = parse_ftl(serialized)

        # Should have no messages
        messages1 = [e for e in resource1.entries if isinstance(e, Message)]
        messages2 = [e for e in resource2.entries if isinstance(e, Message)]

        assert len(messages1) == 0
        assert len(messages2) == 0


class TestSerializationEdgeCases:
    """Edge cases for serialization."""

    @given(
        unicode_value=st.text(
            alphabet=st.characters(
                min_codepoint=0x0080,  # Non-ASCII
                max_codepoint=0x00FF,  # Latin-1 Supplement
            ),
            min_size=1,
            max_size=20,
        ).filter(lambda x: "\n" not in x),
    )
    @settings(max_examples=100)
    def test_unicode_content_roundtrip(self, unicode_value: str) -> None:
        """Unicode content survives roundtrip."""
        ftl_source = f"msg = {unicode_value}"

        resource1 = parse_ftl(ftl_source)
        serialized = serialize_ftl(resource1)
        resource2 = parse_ftl(serialized)

        # Should have messages
        messages1 = [e for e in resource1.entries if isinstance(e, Message)]
        messages2 = [e for e in resource2.entries if isinstance(e, Message)]

        assert len(messages2) == len(messages1)

    @given(
        line_count=st.integers(min_value=1, max_value=20),
    )
    @settings(max_examples=50)
    def test_multiline_pattern_roundtrip(self, line_count: int) -> None:
        """Multiline patterns survive roundtrip."""
        # Create multiline FTL
        lines = ["msg ="]
        lines.extend([f"    Line {i}" for i in range(line_count)])
        ftl_source = "\n".join(lines)

        resource1 = parse_ftl(ftl_source)
        serialized = serialize_ftl(resource1)
        resource2 = parse_ftl(serialized)

        # Should have same message count
        messages1 = [e for e in resource1.entries if isinstance(e, Message)]
        messages2 = [e for e in resource2.entries if isinstance(e, Message)]

        assert len(messages2) == len(messages1)
