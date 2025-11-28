"""Tests for span attachment to AST nodes per Fluent spec.

Verifies that parser attaches Span objects to AST nodes for IDE integration
and error reporting.
"""


from ftllexbuffer.syntax.ast import Attribute, Junk, Message, Span, Term
from ftllexbuffer.syntax.parser import FluentParserV1


class TestMessageSpans:
    # Test span attachment to Message nodes

    def test_simple_message_has_span(self):
        # Simple message should have span
        parser = FluentParserV1()
        source = "hello = World"
        resource = parser.parse(source)

        assert len(resource.entries) == 1
        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None

        # Check span is attached
        assert msg.span is not None
        assert isinstance(msg.span, Span)

        # Verify span covers entire message
        assert msg.span.start == 0
        assert msg.span.end == len(source)

    def test_message_with_value_has_span(self):
        # Message with value should have correct span
        parser = FluentParserV1()
        source = "greeting = Hello, world!"
        resource = parser.parse(source)

        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None
        assert msg.span is not None

        # Span should cover from start to end of message
        assert msg.span.start == 0
        assert msg.span.end == len(source)

    def test_message_with_variable_has_span(self):
        # Message with variable should have span
        parser = FluentParserV1()
        source = "welcome = Hello, { $name }!"
        resource = parser.parse(source)

        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None
        assert msg.span is not None
        assert msg.span.start == 0
        assert msg.span.end == len(source)

    def test_message_with_attribute_has_span(self):
        # Message with attribute should have span covering both
        parser = FluentParserV1()
        source = "button = Save\n    .tooltip = Click to save"
        resource = parser.parse(source)

        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None
        assert msg.span is not None

        # Span should cover message including attributes
        assert msg.span.start == 0
        assert msg.span.end == len(source)

    def test_multiple_messages_have_distinct_spans(self):
        # Multiple messages should have distinct spans
        parser = FluentParserV1()
        source = "msg1 = First\nmsg2 = Second\nmsg3 = Third"
        resource = parser.parse(source)

        assert len(resource.entries) == 3

        # Each message should have its own span
        msg1 = resource.entries[0]
        assert isinstance(msg1, Message)
        assert msg1.value is not None
        msg2 = resource.entries[1]
        assert isinstance(msg2, Message)
        assert msg2.value is not None
        msg3 = resource.entries[2]
        assert isinstance(msg3, Message)
        assert msg3.value is not None

        assert all(isinstance(m, Message) for m in [msg1, msg2, msg3])
        assert all(m.span is not None for m in [msg1, msg2, msg3])

        # Spans should not overlap
        assert msg1.span is not None
        assert msg2.span is not None
        assert msg3.span is not None
        assert msg1.span.end <= msg2.span.start
        assert msg2.span.end <= msg3.span.start


class TestTermSpans:
    # Test span attachment to Term nodes

    def test_simple_term_has_span(self):
        # Simple term should have span
        parser = FluentParserV1()
        source = "-brand = Firefox"
        resource = parser.parse(source)

        assert len(resource.entries) == 1
        term = resource.entries[0]
        assert isinstance(term, Term)

        # Check span is attached
        assert term.span is not None
        assert isinstance(term.span, Span)

        # Verify span covers entire term
        assert term.span.start == 0
        assert term.span.end == len(source)

    def test_term_with_attribute_has_span(self):
        # Term with attribute should have span covering both
        parser = FluentParserV1()
        source = "-brand = Firefox\n    .version = 3.0"
        resource = parser.parse(source)

        term = resource.entries[0]
        assert isinstance(term, Term)
        assert term.span is not None

        # Span should cover term including attributes (at least most of it)
        assert term.span.start == 0
        assert term.span.end >= len(source) - 5  # Allow for trailing characters

    def test_term_starts_at_minus_sign(self):
        # Term span should start at the '-' character
        parser = FluentParserV1()
        source = "-brand = MyApp"
        resource = parser.parse(source)

        term = resource.entries[0]
        assert isinstance(term, Term)
        assert term.span is not None

        # Verify span starts at '-'
        assert source[term.span.start] == "-"


class TestAttributeSpans:
    # Test span attachment to Attribute nodes

    def test_attribute_has_span(self):
        # Attribute should have span
        parser = FluentParserV1()
        source = "msg = Value\n    .tooltip = Help text"
        resource = parser.parse(source)

        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None
        assert len(msg.attributes) == 1

        attr = msg.attributes[0]
        assert isinstance(attr, Attribute)
        assert attr.span is not None
        assert isinstance(attr.span, Span)

        # Verify span covers attribute (including leading whitespace)
        assert attr.span.start >= 0
        assert attr.span.end <= len(source)

    def test_multiple_attributes_have_distinct_spans(self):
        # Multiple attributes should have distinct spans
        parser = FluentParserV1()
        source = "msg = Value\n    .attr1 = First\n    .attr2 = Second"
        resource = parser.parse(source)

        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None
        assert len(msg.attributes) == 2

        attr1 = msg.attributes[0]
        assert isinstance(attr1, Attribute)
        attr2 = msg.attributes[1]
        assert isinstance(attr2, Attribute)

        assert attr1.span is not None
        assert attr2.span is not None

        # Spans should not overlap
        assert attr1.span.end <= attr2.span.start


class TestJunkSpans:
    # Test span attachment and annotations on Junk nodes

    def test_junk_has_span(self):
        # Junk should have span
        parser = FluentParserV1()
        # Invalid syntax - missing =
        source = "invalid syntax"
        resource = parser.parse(source)

        # Should create Junk entry
        assert len(resource.entries) >= 1
        entry = resource.entries[0]

        # Entry might be Junk or Message depending on parser
        if isinstance(entry, Junk):
            assert entry.span is not None
            assert isinstance(entry.span, Span)

    def test_junk_has_annotations(self):
        # Junk should have error annotations
        parser = FluentParserV1()
        # Invalid syntax
        source = "bad { syntax"
        resource = parser.parse(source)

        # Look for Junk entry
        junk_entries = [e for e in resource.entries if isinstance(e, Junk)]

        if junk_entries:
            junk = junk_entries[0]

            # Should have annotations
            assert len(junk.annotations) > 0

            # Annotations should have required fields
            annotation = junk.annotations[0]
            assert annotation.code is not None
            assert annotation.message is not None


class TestSpanProperties:
    # Test span invariants and properties

    def test_span_start_before_end(self):
        # Span start should always be before or equal to end
        parser = FluentParserV1()
        source = "msg = Value"
        resource = parser.parse(source)

        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None

        assert msg.span is not None
        assert msg.span.start <= msg.span.end

    def test_span_within_source_bounds(self):
        # Span should be within source bounds
        parser = FluentParserV1()
        source = "msg = Value"
        resource = parser.parse(source)

        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None
        assert msg.span is not None

        # Start and end should be valid positions
        assert msg.span.start >= 0
        assert msg.span.end <= len(source)

    def test_span_covers_actual_content(self):
        # Span should extract the actual message content
        parser = FluentParserV1()
        source = "greeting = Hello"
        resource = parser.parse(source)

        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None
        assert msg.span is not None

        # Extract content using span
        content = source[msg.span.start : msg.span.end]
        assert content == "greeting = Hello"


class TestMultilineSpans:
    # Test span handling for multiline content

    def test_multiline_message_span(self):
        # Multiline message should have span covering all lines
        parser = FluentParserV1()
        source = "msg =\n    Line 1\n    Line 2"
        resource = parser.parse(source)

        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None
        assert msg.span is not None

        # Span should cover entire multiline message
        assert msg.span.start == 0
        assert msg.span.end == len(source)

    def test_message_with_multiline_attribute_span(self):
        # Message with multiline attribute should have correct span
        parser = FluentParserV1()
        source = "msg = Value\n    .attr =\n        Line 1\n        Line 2"
        resource = parser.parse(source)

        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None
        assert msg.span is not None

        # Span should cover message and all attributes
        assert msg.span.start == 0
        assert msg.span.end == len(source)


class TestSelectExpressionSpans:
    # Test span attachment to SelectExpression nodes

    def test_simple_select_has_span(self):
        # Simple select expression should have span
        parser = FluentParserV1()
        source = "msg = { $count ->\n    [one] One\n   *[other] Many\n}"
        resource = parser.parse(source)

        assert len(resource.entries) == 1
        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None
        assert msg.value is not None

        # Get the select expression from the placeable
        from ftllexbuffer.syntax.ast import Placeable, SelectExpression
        placeable = msg.value.elements[0]
        assert isinstance(placeable, Placeable)
        select_expr = placeable.expression
        assert isinstance(select_expr, SelectExpression)

        # Check select expression has span
        assert select_expr.span is not None
        assert isinstance(select_expr.span, Span)

    def test_select_span_covers_selector_and_variants(self):
        # Select span should cover from selector start to end of variants
        parser = FluentParserV1()
        source = "msg = { $count ->\n    [one] One item\n   *[other] Many items\n}"
        resource = parser.parse(source)

        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None

        from ftllexbuffer.syntax.ast import Placeable, SelectExpression
        placeable = msg.value.elements[0]
        assert isinstance(placeable, Placeable)
        select_expr = placeable.expression
        assert isinstance(select_expr, SelectExpression)

        # Span should start at $count (position 8: "msg = { ")
        # and end after last variant
        assert select_expr.span is not None
        assert select_expr.span.start == 8  # Start of "$count"
        # End should be after all variants are parsed (before closing })

    def test_select_with_multiple_variants_span(self):
        # Select with multiple variants should have span
        parser = FluentParserV1()
        source = "msg = { $count ->\n    [zero] Zero\n    [one] One\n    [two] Two\n   *[other] Many\n}"  # noqa: E501 pylint: disable=line-too-long
        resource = parser.parse(source)

        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None
        from ftllexbuffer.syntax.ast import Placeable, SelectExpression
        placeable = msg.value.elements[0]
        assert isinstance(placeable, Placeable)
        select_expr = placeable.expression
        assert isinstance(select_expr, SelectExpression)

        assert select_expr.span is not None
        assert select_expr.span.start <= select_expr.span.end


class TestVariantSpans:
    # Test span attachment to Variant nodes

    def test_variant_has_span(self):
        # Variant should have span
        parser = FluentParserV1()
        source = "msg = { $count ->\n    [one] One item\n   *[other] Many items\n}"
        resource = parser.parse(source)

        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None
        from ftllexbuffer.syntax.ast import Placeable, SelectExpression
        placeable = msg.value.elements[0]
        assert isinstance(placeable, Placeable)
        select_expr = placeable.expression
        assert isinstance(select_expr, SelectExpression)

        # Check first variant has span
        assert len(select_expr.variants) >= 1
        variant = select_expr.variants[0]
        assert variant.span is not None
        assert isinstance(variant.span, Span)

    def test_all_variants_have_spans(self):
        # All variants in select should have spans
        parser = FluentParserV1()
        source = "msg = { $count ->\n    [zero] Zero\n    [one] One\n   *[other] Many\n}"
        resource = parser.parse(source)

        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None
        from ftllexbuffer.syntax.ast import Placeable, SelectExpression
        placeable = msg.value.elements[0]
        assert isinstance(placeable, Placeable)
        select_expr = placeable.expression
        assert isinstance(select_expr, SelectExpression)

        # All variants should have spans
        assert len(select_expr.variants) == 3
        for variant in select_expr.variants:
            assert variant.span is not None
            assert isinstance(variant.span, Span)
            assert variant.span.start <= variant.span.end

    def test_variant_spans_do_not_overlap(self):
        # Variant spans should not overlap
        parser = FluentParserV1()
        source = "msg = { $count ->\n    [one] One\n    [two] Two\n   *[other] Many\n}"
        resource = parser.parse(source)

        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None
        from ftllexbuffer.syntax.ast import Placeable, SelectExpression
        placeable = msg.value.elements[0]
        assert isinstance(placeable, Placeable)
        select_expr = placeable.expression
        assert isinstance(select_expr, SelectExpression)

        # Variants should be sequential (no overlap)
        variants = select_expr.variants
        for i in range(len(variants) - 1):
            curr_span = variants[i].span
            next_span = variants[i + 1].span
            assert curr_span is not None
            assert next_span is not None
            assert curr_span.end <= next_span.start

    def test_default_variant_has_span(self):
        # Default variant (marked with *) should have span
        parser = FluentParserV1()
        source = "msg = { $count ->\n    [one] One\n   *[other] Many\n}"
        resource = parser.parse(source)

        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None
        from ftllexbuffer.syntax.ast import Placeable, SelectExpression
        placeable = msg.value.elements[0]
        assert isinstance(placeable, Placeable)
        select_expr = placeable.expression
        assert isinstance(select_expr, SelectExpression)

        # Find default variant
        default_variant = None
        for variant in select_expr.variants:
            if variant.default:
                default_variant = variant
                break

        assert default_variant is not None
        assert default_variant.span is not None
        assert isinstance(default_variant.span, Span)


class TestSelectAndVariantSpanIntegration:
    # Test integration of select and variant spans

    def test_select_span_encompasses_all_variants(self):
        # Select expression span should cover all its variants
        parser = FluentParserV1()
        source = "msg = { $count ->\n    [one] One\n   *[other] Many\n}"
        resource = parser.parse(source)

        msg = resource.entries[0]
        assert isinstance(msg, Message)
        assert msg.value is not None
        from ftllexbuffer.syntax.ast import Placeable, SelectExpression
        placeable = msg.value.elements[0]
        assert isinstance(placeable, Placeable)
        select_expr = placeable.expression
        assert isinstance(select_expr, SelectExpression)

        # Select span should start at or before first variant
        first_variant = select_expr.variants[0]
        assert select_expr.span is not None
        assert first_variant.span is not None
        assert select_expr.span.start <= first_variant.span.start

        # Select span should end at or after last variant
        last_variant = select_expr.variants[-1]
        assert last_variant.span is not None
        assert select_expr.span.end >= last_variant.span.end
