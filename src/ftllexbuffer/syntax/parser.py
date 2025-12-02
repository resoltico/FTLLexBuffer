"""Fluent FTL parser using immutable cursor architecture.

Design:
- Immutable cursor prevents infinite loops (no manual guards needed)
- Type-safe by design (no `str | None` patterns)
- Error messages include line:column with source context

Architecture:
- Every parser method takes Cursor (immutable) as input
- Every parser returns Success[ParseResult[T]] | Failure[ParseError]
- No mutation - compiler enforces progress

Module Organization:
This module is intentionally monolithic (>1000 lines).

Rationale:
- High cohesion: All methods parse FTL syntax into AST nodes
- Single dependency: Result monad from ftllexbuffer.result
- Implements complete Fluent 1.0 specification
- Splitting would introduce coupling between parser submodules

See docs/adr/ADR-003-parser-module-organization.md for analysis.
"""

# Pylint suppression: Monolithic parser module by design
# pylint: disable=too-many-lines

from __future__ import annotations

import logging

from ftllexbuffer.result import Failure, Success

from .ast import (
    Annotation,
    Attribute,
    CallArguments,
    Comment,
    FunctionReference,
    Identifier,
    InlineExpression,
    Junk,
    Message,
    MessageReference,
    NamedArgument,
    NumberLiteral,
    Pattern,
    Placeable,
    Resource,
    SelectExpression,
    Span,
    StringLiteral,
    Term,
    TermReference,
    TextElement,
    VariableReference,
    Variant,
)
from .cursor import Cursor, ParseError, ParseResult

# Module-level logger (after imports per PEP 8)
logger = logging.getLogger(__name__)


class FluentParserV1:
    """Fluent FTL parser using immutable cursor pattern."""

    def parse(self, source: str) -> Resource:
        """Parse FTL source into AST Resource.

        Parses complete FTL file into messages, terms, and comments.
        Continues parsing after errors (robustness principle).

        Args:
            source: FTL file content

        Returns:
            Resource with list of entries (Message, Term, or Junk)

        Raises:
            FluentSyntaxError: Only on critical parse failures
        """
        cursor = Cursor(source, 0)
        entries: list[Message | Term | Junk | Comment] = []

        # Parse entries until EOF
        while not cursor.is_eof:
            # Per spec: blank_block ::= (blank_inline? line_end)+
            # Between resource entries, skip blank (spaces and newlines, NOT tabs)
            cursor = self._skip_blank(cursor)

            if cursor.is_eof:
                break

            # Parse comments (per Fluent spec: #, ##, ###)
            if cursor.current == "#":
                comment_result = self._parse_comment(cursor)
                if isinstance(comment_result, Success):
                    comment_parse = comment_result.unwrap()
                    entries.append(comment_parse.value)
                    cursor = comment_parse.cursor
                    continue
                # If comment parsing fails, skip the line
                while not cursor.is_eof and cursor.current not in ("\n", "\r"):
                    cursor = cursor.advance()
                if not cursor.is_eof:
                    cursor = cursor.advance()
                continue

            # Try to parse term (starts with '-')
            if cursor.current == "-":
                term_result = self._parse_term(cursor)

                if isinstance(term_result, Success):
                    term_parse = term_result.unwrap()
                    entries.append(term_parse.value)
                    cursor = term_parse.cursor
                    continue

            # Try to parse message
            message_result = self._parse_message(cursor)

            if isinstance(message_result, Success):
                message_parse = message_result.unwrap()
                entries.append(message_parse.value)
                cursor = message_parse.cursor
            else:
                # Parse error - create Junk entry and continue (robustness principle)
                error = message_result.failure()

                # Structured logging for production observability
                # Only logs at DEBUG level to avoid performance impact
                if logger.isEnabledFor(logging.DEBUG):
                    line, col = error.cursor.line_col
                    logger.debug(
                        "parse_error_created_junk",
                        extra={
                            "message": error.message,
                            "line": line,
                            "column": col,
                            "position": error.cursor.pos,
                            "expected": error.expected,
                            "found": error.cursor.current if not error.cursor.is_eof else "<EOF>",
                        },
                    )

                junk_start = cursor.pos

                # Per FTL spec: Junk ::= junk_line (junk_line - "#" - "-" - [a-zA-Z])*
                # Consume multiple lines until we hit a valid entry start
                cursor = self._consume_junk_lines(cursor)

                # Create Junk entry with all consumed problematic content
                junk_content = cursor.source[junk_start : cursor.pos]
                junk_span = Span(start=junk_start, end=cursor.pos)

                # Create annotation from parse error
                annotation = Annotation(
                    code="E0099",  # Generic parse error code
                    message=error.message,
                    span=Span(start=error.cursor.pos, end=error.cursor.pos),
                )

                entries.append(
                    Junk(content=junk_content, annotations=(annotation,), span=junk_span)
                )

        return Resource(entries=tuple(entries))

    # ===== Core Parser Methods (Session 2) =====

    def _consume_junk_lines(self, cursor: Cursor) -> Cursor:
        """Consume junk lines per FTL spec until valid entry start.

        Per Fluent EBNF:
            Junk ::= junk_line (junk_line - "#" - "-" - [a-zA-Z])*
            junk_line ::= /[^\n]*/ ("\u000A" | EOF)

        This means:
        1. First junk line: consume to end of line
        2. Subsequent lines: continue UNTIL hitting a line that starts with:
           - "#" (comment)
           - "-" (term)
           - [a-zA-Z] (message identifier)

        Args:
            cursor: Current position in source (at start of junk content)

        Returns:
            New cursor position after all junk lines consumed
        """
        # Skip first line to end
        while not cursor.is_eof and cursor.current not in ("\n", "\r"):
            cursor = cursor.advance()

        # Skip the newline
        if not cursor.is_eof and cursor.current in ("\n", "\r"):
            cursor = cursor.advance()
            if not cursor.is_eof and cursor.current == "\n":  # Handle CRLF
                cursor = cursor.advance()

        # Continue consuming lines UNTIL we hit a valid entry start
        while not cursor.is_eof:
            # Save position at start of line
            saved_cursor = cursor

            # Skip leading spaces on THIS line only (not newlines)
            while not cursor.is_eof and cursor.current == " ":
                cursor = cursor.advance()

            if cursor.is_eof:
                break

            # Check for valid entry start characters
            # Per spec: Junk stops at #, -, or [a-zA-Z]
            if cursor.current in ("#", "-") or cursor.current.isalpha():
                # Found valid entry start - restore to line start and stop
                cursor = saved_cursor
                break

            # This line doesn't start a valid entry - consume it as junk
            # Skip to end of line
            while not cursor.is_eof and cursor.current not in ("\n", "\r"):
                cursor = cursor.advance()

            # Skip the newline
            if not cursor.is_eof and cursor.current in ("\n", "\r"):
                cursor = cursor.advance()
                if not cursor.is_eof and cursor.current == "\n":  # Handle CRLF
                    cursor = cursor.advance()

        return cursor

    def _parse_identifier(self, cursor: Cursor) -> Success[ParseResult[str]] | Failure[ParseError]:
        """Parse identifier: [a-zA-Z][a-zA-Z0-9_-]*

        Fluent identifiers start with a letter and continue with letters,
        digits, hyphens, or underscores.

        Examples:
            hello → "hello"
            brand-name → "brand-name"
            file_name → "file_name"

        Args:
            cursor: Current position in source

        Returns:
            Success(ParseResult(identifier, new_cursor)) on success
            Failure(ParseError(...)) if not an identifier
        """
        # Check first character is alpha
        if cursor.is_eof or not cursor.current.isalpha():
            return Failure(
                ParseError(
                    "Expected identifier (must start with letter)", cursor, expected=["a-z", "A-Z"]
                )
            )

        # Save start position
        start_pos = cursor.pos
        cursor = cursor.advance()  # Skip first character

        # Continue with alphanumeric, -, _
        while not cursor.is_eof:
            ch = cursor.current
            if ch.isalnum() or ch in ("-", "_"):
                cursor = cursor.advance()
            else:
                break

        # Extract identifier
        identifier = Cursor(cursor.source, start_pos).slice_to(cursor.pos)
        return Success(ParseResult(identifier, cursor))

    def _parse_number(self, cursor: Cursor) -> Success[ParseResult[str]] | Failure[ParseError]:
        """Parse number literal: -?[0-9]+(.[0-9]+)?

        Numbers are stored as strings to preserve precision (like Decimal).

        Examples:
            42 → "42"
            -3.14 → "-3.14"
            0.001 → "0.001"

        Args:
            cursor: Current position in source

        Returns:
            Success(ParseResult(number_str, new_cursor)) on success
            Failure(ParseError(...)) if not a number
        """
        start_pos = cursor.pos

        # Optional minus sign
        if not cursor.is_eof and cursor.current == "-":
            cursor = cursor.advance()

        # Must have at least one digit
        if cursor.is_eof or not cursor.current.isdigit():
            return Failure(ParseError("Expected number", cursor, expected=["0-9"]))

        # Integer part
        while not cursor.is_eof and cursor.current.isdigit():
            cursor = cursor.advance()

        # Optional decimal part
        if not cursor.is_eof and cursor.current == ".":
            cursor = cursor.advance()

            # Must have digit after decimal
            if cursor.is_eof or not cursor.current.isdigit():
                return Failure(
                    ParseError("Expected digit after decimal point", cursor, expected=["0-9"])
                )

            while not cursor.is_eof and cursor.current.isdigit():
                cursor = cursor.advance()

        # Extract number string
        number_str = Cursor(cursor.source, start_pos).slice_to(cursor.pos)
        return Success(ParseResult(number_str, cursor))

    def _skip_blank_inline(self, cursor: Cursor) -> Cursor:
        """Skip inline whitespace (ONLY space U+0020, per FTL spec).

        Per Fluent EBNF specification:
            blank_inline ::= "\u0020"+

        This is stricter than _skip_blank() - it ONLY accepts space (U+0020),
        NOT tabs or newlines.

        Used in contexts where spec requires blank_inline:
        - Between tokens on same line (identifier = value)
        - Inside call arguments and select expressions
        - Before/after operators (=, ->, :)

        Args:
            cursor: Current position in source

        Returns:
            New cursor at first non-space character (or EOF)

        Design:
            Immutable cursor ensures termination (same proof as _skip_blank).
        """
        while not cursor.is_eof and cursor.current == " ":
            cursor = cursor.advance()  # Always makes progress
        return cursor

    def _skip_blank(self, cursor: Cursor) -> Cursor:
        """Skip blank (spaces and line endings, per FTL spec).

        Per Fluent EBNF specification:
            blank ::= (blank_inline | line_end)+
            blank_inline ::= "\u0020"+
            line_end ::= "\u000D\u000A" | "\u000A" | EOF

        This accepts spaces and newlines, but NOT tabs.

        Used in contexts where spec requires blank:
        - Between entries in resource
        - Inside select expression variant lists
        - Before/after patterns with line breaks

        Args:
            cursor: Current position in source

        Returns:
            New cursor at first non-blank character (or EOF)

        Design:
            Immutable cursor ensures termination.
        """
        while not cursor.is_eof and cursor.current in (" ", "\n", "\r"):
            cursor = cursor.advance()  # Always makes progress
        return cursor


    def _is_indented_continuation(self, cursor: Cursor) -> bool:
        """Check if the next line is an indented pattern continuation.

        According to FTL spec:
        - Continuation lines must start with at least one space (U+0020)
        - Lines starting with [, *, or . are NOT pattern continuations
          (they indicate variants, default variants, or attributes)

        Args:
            cursor: Current position (should be at newline character)

        Returns:
            True if next line is an indented continuation, False otherwise
        """
        if cursor.is_eof or cursor.current not in ("\n", "\r"):
            return False

        # Skip the newline(s)
        next_cursor = cursor.advance()
        if not next_cursor.is_eof and next_cursor.current == "\n":
            next_cursor = next_cursor.advance()  # Handle \r\n

        # Check if next line starts with space (U+0020 only, NOT tab)
        if next_cursor.is_eof or next_cursor.current != " ":
            return False

        # Skip leading spaces to find first non-space character
        while not next_cursor.is_eof and next_cursor.current == " ":
            next_cursor = next_cursor.advance()

        # If line starts with special chars, it's not a pattern continuation
        return not (not next_cursor.is_eof and next_cursor.current in ("[", "*", "."))

    def _parse_escape_sequence(  # noqa: PLR0911
        self, cursor: Cursor
    ) -> Success[tuple[str, Cursor]] | Failure[ParseError]:
        """Parse escape sequence after backslash in string.

        Helper method extracted from _parse_string_literal to reduce complexity.

        Supported escape sequences:
            \\" → "
            \\\\ → \\
            \\n → newline
            \\t → tab
            \\uXXXX → Unicode character (4 hex digits)
            \\UXXXXXX → Unicode character (6 hex digits)

        Note: PLR0911 (too many returns) is acceptable for parser grammar methods.
        Each return represents a successfully parsed grammar alternative.

        Args:
            cursor: Position AFTER the backslash

        Returns:
            Success((escaped_char, new_cursor)) on success
            Failure(ParseError(...)) on invalid escape
        """
        if cursor.is_eof:
            return Failure(ParseError("Unexpected EOF in string", cursor))

        escape_ch = cursor.current

        if escape_ch == '"':
            return Success(('"', cursor.advance()))
        if escape_ch == "\\":
            return Success(("\\", cursor.advance()))
        if escape_ch == "n":
            return Success(("\n", cursor.advance()))
        if escape_ch == "t":
            return Success(("\t", cursor.advance()))

        if escape_ch == "u":
            # Unicode escape: \uXXXX (4 hex digits)
            cursor = cursor.advance()
            hex_digits = ""
            for _ in range(4):
                if cursor.is_eof or cursor.current not in "0123456789abcdefABCDEF":
                    return Failure(
                        ParseError("Invalid Unicode escape (expected 4 hex digits)", cursor)
                    )
                hex_digits += cursor.current
                cursor = cursor.advance()

            # Convert to character
            code_point = int(hex_digits, 16)
            return Success((chr(code_point), cursor))

        if escape_ch == "U":
            # Unicode escape: \UXXXXXX (6 hex digits)
            cursor = cursor.advance()
            hex_digits = ""
            for _ in range(6):
                if cursor.is_eof or cursor.current not in "0123456789abcdefABCDEF":
                    return Failure(
                        ParseError("Invalid Unicode escape (expected 6 hex digits)", cursor)
                    )
                hex_digits += cursor.current
                cursor = cursor.advance()

            # Convert to character
            code_point = int(hex_digits, 16)
            # Validate Unicode code point range
            if code_point > 0x10FFFF:
                return Failure(
                    ParseError(f"Invalid Unicode code point: U+{hex_digits} (max U+10FFFF)", cursor)
                )
            return Success((chr(code_point), cursor))

        return Failure(ParseError(f"Invalid escape sequence: \\{escape_ch}", cursor))

    def _parse_string_literal(
        self, cursor: Cursor
    ) -> Success[ParseResult[str]] | Failure[ParseError]:
        """Parse string literal: "text"

        Supports escape sequences:
            \\" → "
            \\\\ → \\
            \\n → newline
            \\t → tab
            \\uXXXX → Unicode character (4 hex digits)
            \\UXXXXXX → Unicode character (6 hex digits)

        Examples:
            "hello" → "hello"
            "with \\"quotes\\"" → 'with "quotes"'
            "unicode: \\u00E4" → "unicode: ä"
            "emoji: \\U01F600" → Unicode emoji character

        Args:
            cursor: Current position in source

        Returns:
            Success(ParseResult(string_value, new_cursor)) on success
            Failure(ParseError(...)) if invalid string
        """
        # Expect opening quote
        if cursor.is_eof or cursor.current != '"':
            return Failure(ParseError("Expected opening quote", cursor, expected=['"']))

        cursor = cursor.advance()  # Skip opening "
        value = ""

        while not cursor.is_eof:
            ch = cursor.current

            if ch == '"':
                # Closing quote - done!
                cursor = cursor.advance()
                return Success(ParseResult(value, cursor))

            if ch == "\\":
                # Escape sequence - use extracted helper
                cursor = cursor.advance()
                escape_result = self._parse_escape_sequence(cursor)
                if isinstance(escape_result, Failure):
                    return escape_result

                escaped_char, cursor = escape_result.unwrap()
                value += escaped_char

            else:
                # Regular character
                value += ch
                cursor = cursor.advance()

        # EOF without closing quote
        return Failure(ParseError("Unterminated string literal", cursor))

    # ===== Pattern & Message Methods (Session 3) =====

    def _parse_variable_reference(
        self, cursor: Cursor
    ) -> Success[ParseResult[VariableReference]] | Failure[ParseError]:
        """Parse variable reference: $variable

        Variables start with $ followed by an identifier.

        Examples:
            $name → VariableReference(Identifier("name"))
            $count → VariableReference(Identifier("count"))

        Args:
            cursor: Current position in source

        Returns:
            Success(ParseResult(VariableReference, new_cursor)) on success
            Failure(ParseError(...)) if not a variable reference
        """
        # Expect $
        if cursor.is_eof or cursor.current != "$":
            return Failure(
                ParseError("Expected variable reference (starts with $)", cursor, expected=["$"])
            )

        cursor = cursor.advance()  # Skip $

        # Parse identifier
        result = self._parse_identifier(cursor)
        if isinstance(result, Failure):
            return result

        parse_result = result.unwrap()
        var_ref = VariableReference(id=Identifier(parse_result.value))
        return Success(ParseResult(var_ref, parse_result.cursor))

    def _parse_simple_pattern(
        self, cursor: Cursor
    ) -> Success[ParseResult[Pattern]] | Failure[ParseError]:
        """Parse simple pattern (text with optional placeables).

        Handles:
        - Plain text
        - All placeable types: {$var}, {-term}, {NUMBER(...)}, {"string"}, {42}
        - Select expressions: {$x -> [a] A *[b] B}

        Stops at: newline, EOF, or dot (attribute marker)
        Also stops at variant delimiters: }, [, *

        Examples:
            "Hello"  → Pattern([TextElement("Hello")])
            "Hi {$name}"  → Pattern([TextElement("Hi "), Placeable(VariableReference("name"))])
            "{-term} text"  → Pattern([Placeable(TermReference("term")), TextElement(" text")])

        Args:
            cursor: Current position in source

        Returns:
            Success(ParseResult(Pattern, new_cursor)) on success
            Failure(ParseError(...)) on parse error
        """
        elements: list[TextElement | Placeable] = []

        while not cursor.is_eof:
            ch = cursor.current

            # Stop conditions
            # Also stop at } [ * for variant patterns inside select expressions
            if ch in ("\n", "\r", ".", "}", "[", "*"):
                break

            # Placeable: {expression}  # noqa: ERA001
            if ch == "{":
                cursor = cursor.advance()  # Skip {

                # Use full placeable parser which handles all expression types
                # (variables, terms, functions, strings, numbers, select expressions)
                placeable_result = self._parse_placeable(cursor)
                if isinstance(placeable_result, Failure):
                    return placeable_result

                placeable_parse = placeable_result.unwrap()
                cursor = placeable_parse.cursor
                elements.append(placeable_parse.value)

            else:
                # Parse text until { or stop condition
                text_start = cursor.pos
                while not cursor.is_eof:
                    ch = cursor.current
                    # Stop at: placeable start, line end, or special pattern markers
                    # Note: '.' removed - only stops attributes at line start, not mid-pattern
                    if ch in ("{", "\n", "\r", "}", "[", "*"):
                        break
                    cursor = cursor.advance()

                if cursor.pos > text_start:
                    text = Cursor(cursor.source, text_start).slice_to(cursor.pos)
                    elements.append(TextElement(value=text))
                elif cursor.pos == text_start:
                    # Prevent infinite loop: advance cursor when no text consumed
                    # This happens when current char is a stop char but not '{'
                    cursor = cursor.advance()

        pattern = Pattern(elements=tuple(elements))
        return Success(ParseResult(pattern, cursor))

    # ===== Select Expression Methods (Session 4) =====

    def _parse_variant_key(
        self, cursor: Cursor
    ) -> Success[ParseResult[Identifier | NumberLiteral]] | Failure[ParseError]:
        """Parse variant key (identifier or number).

        Helper method extracted from _parse_variant to reduce complexity.

        Args:
            cursor: Current position in source

        Returns:
            Success(ParseResult(Identifier | NumberLiteral, cursor)) on success
            Failure(ParseError(...)) on parse error
        """
        # Try number first
        if not cursor.is_eof and (cursor.current.isdigit() or cursor.current == "-"):
            num_result = self._parse_number(cursor)
            if isinstance(num_result, Success):
                num_parse = num_result.unwrap()
                return Success(ParseResult(NumberLiteral(value=num_parse.value), num_parse.cursor))

            # Failed to parse as number, try identifier
            id_result = self._parse_identifier(cursor)
            if isinstance(id_result, Failure):
                # Both failed - return parse error
                return Failure(ParseError("Expected variant key (identifier or number)", cursor))

            id_parse = id_result.unwrap()
            return Success(ParseResult(Identifier(id_parse.value), id_parse.cursor))

        # Parse as identifier
        id_result = self._parse_identifier(cursor)
        if isinstance(id_result, Failure):
            return id_result

        id_parse = id_result.unwrap()
        return Success(ParseResult(Identifier(id_parse.value), id_parse.cursor))

    def _parse_variant(self, cursor: Cursor) -> Success[ParseResult[Variant]] | Failure[ParseError]:
        """Parse variant: [key] pattern or *[key] pattern

        Variants are the cases in a select expression.

        Examples:
            [zero] no items
            *[other] many items

        Args:
            cursor: Current position in source

        Returns:
            Success(ParseResult(Variant, new_cursor)) on success
            Failure(ParseError(...)) on parse error
        """
        # Capture start position for span
        start_pos = cursor.pos

        # Check for default marker *
        is_default = False
        if not cursor.is_eof and cursor.current == "*":
            is_default = True
            cursor = cursor.advance()

        # Expect [
        if cursor.is_eof or cursor.current != "[":
            return Failure(ParseError("Expected '[' at start of variant", cursor))

        cursor = cursor.advance()  # Skip [

        # Parse variant key (identifier or number) using extracted helper
        # Per spec: VariantKey ::= "[" blank? (NumberLiteral | Identifier) blank? "]"
        cursor = self._skip_blank_inline(cursor)
        key_result = self._parse_variant_key(cursor)
        if isinstance(key_result, Failure):
            return key_result

        key_parse = key_result.unwrap()
        variant_key = key_parse.value
        cursor = self._skip_blank_inline(key_parse.cursor)

        # Expect ]
        if cursor.is_eof or cursor.current != "]":
            return Failure(ParseError("Expected ']' after variant key", cursor))

        cursor = cursor.advance()  # Skip ]
        # After ], before pattern: blank_inline (same line) or newline+indent
        cursor = self._skip_blank_inline(cursor)

        # Parse pattern (on same line or next line with indent)
        # Simplified: parse until newline that's not indented
        pattern_result = self._parse_simple_pattern(cursor)
        if isinstance(pattern_result, Failure):
            return pattern_result

        pattern_parse = pattern_result.unwrap()

        # Create span from start to current position
        span = Span(start=start_pos, end=pattern_parse.cursor.pos)

        # Don't skip trailing whitespace - let select expression parser handle it
        variant = Variant(key=variant_key, value=pattern_parse.value, default=is_default, span=span)
        return Success(ParseResult(variant, pattern_parse.cursor))

    def _parse_select_expression(
        self, cursor: Cursor, selector: InlineExpression, start_pos: int
    ) -> Success[ParseResult[SelectExpression]] | Failure[ParseError]:
        """Parse select expression after seeing selector and ->

        Format: {$var -> [key1] value1 *[key2] value2}

        The selector has already been parsed.

        Example:
            After parsing {$count and seeing ->, we parse:
            [zero] {$count} items
            [one] {$count} item
            *[other] {$count} items
            }

        Args:
            cursor: Current position (should be after ->)
            selector: The selector expression (e.g., VariableReference($count))
            start_pos: Start position of the selector (for span tracking)

        Returns:
            Success(ParseResult(SelectExpression, new_cursor)) on success
            Failure(ParseError(...)) on parse error
        """
        # Per spec: SelectExpression ::= InlineExpression blank? "->" blank_inline? variant_list
        # After ->, we need blank_inline before variant list starts (could be on next line)
        # variant_list allows line_end, so use _skip_blank to handle newlines
        cursor = self._skip_blank(cursor)

        # Parse variants
        variants: list[Variant] = []

        while not cursor.is_eof:
            # Within variant_list, allow blank (spaces and newlines)
            cursor = self._skip_blank(cursor)

            # Check for end of select }
            if cursor.current == "}":
                break

            # Parse variant
            variant_result = self._parse_variant(cursor)
            if isinstance(variant_result, Failure):
                return variant_result

            variant_parse = variant_result.unwrap()
            variants.append(variant_parse.value)
            cursor = variant_parse.cursor

        if not variants:
            return Failure(ParseError("Select expression must have at least one variant", cursor))

        # Validate exactly one default variant (FTL spec requirement)
        default_count = sum(1 for v in variants if v.default)
        if default_count == 0:
            return Failure(
                ParseError(
                    "Select expression must have exactly one default variant (marked with *)",
                    cursor,
                )
            )
        if default_count > 1:
            return Failure(
                ParseError(
                    "Select expression must have exactly one default variant, found multiple",
                    cursor,
                )
            )

        # Create span from selector start to end of last variant
        span = Span(start=start_pos, end=cursor.pos)

        select_expr = SelectExpression(selector=selector, variants=tuple(variants), span=span)
        return Success(ParseResult(select_expr, cursor))

    def _parse_argument_expression(  # noqa: PLR0911
        self, cursor: Cursor
    ) -> Success[ParseResult[InlineExpression]] | Failure[ParseError]:
        """Parse a single argument expression (variable, string, number, or identifier).

        Helper method extracted from _parse_call_arguments to reduce complexity.

        Args:
            cursor: Current position in source

        Returns:
            Success(ParseResult(InlineExpression, cursor)) on success
            Failure(ParseError(...)) on parse error
        """
        if cursor.current == "$":
            var_result = self._parse_variable_reference(cursor)
            if isinstance(var_result, Failure):
                return var_result
            var_parse = var_result.unwrap()
            return Success(ParseResult(var_parse.value, var_parse.cursor))

        if cursor.current == '"':
            str_result = self._parse_string_literal(cursor)
            if isinstance(str_result, Failure):
                return str_result
            str_parse = str_result.unwrap()
            return Success(ParseResult(StringLiteral(value=str_parse.value), str_parse.cursor))

        if cursor.current.isdigit() or cursor.current == "-":
            num_result = self._parse_number(cursor)
            if isinstance(num_result, Failure):
                return num_result
            num_parse = num_result.unwrap()
            return Success(ParseResult(NumberLiteral(value=num_parse.value), num_parse.cursor))

        if cursor.current.isalpha():
            id_result = self._parse_identifier(cursor)
            if isinstance(id_result, Failure):
                return id_result
            id_parse = id_result.unwrap()
            return Success(
                ParseResult(MessageReference(id=Identifier(id_parse.value)), id_parse.cursor)
            )

        return Failure(
            ParseError(
                "Expected argument expression (variable, string, number, or identifier)",
                cursor,
            )
        )

    def _parse_call_arguments(  # noqa: PLR0911
        self, cursor: Cursor
    ) -> Success[ParseResult[CallArguments]] | Failure[ParseError]:
        """Parse function call arguments: (pos1, pos2, name1: val1, name2: val2)

        Arguments consist of positional arguments followed by named arguments.
        Positional arguments must come before named arguments.
        Named argument names must be unique.

        Examples:
            ($value) → CallArguments(positional=[$value], named=[])
            ($value, minimumFractionDigits: 2) → CallArguments with both types

        Args:
            cursor: Position AFTER the opening '('

        Returns:
            Success(ParseResult(CallArguments, cursor_after_))) on success
            Failure(ParseError(...)) on parse error
        """
        # Per spec: CallArguments ::= blank? "(" blank? argument_list blank? ")"
        cursor = self._skip_blank_inline(cursor)

        positional: list[InlineExpression] = []
        named: list[NamedArgument] = []
        seen_named_arg_names: set[str] = set()
        seen_named = False  # Track if we've seen any named args

        # Parse comma-separated arguments
        while not cursor.is_eof:
            cursor = self._skip_blank_inline(cursor)

            # Check for end of arguments
            if cursor.current == ")":
                break

            # Parse the argument expression using extracted helper
            arg_result = self._parse_argument_expression(cursor)
            if isinstance(arg_result, Failure):
                return arg_result

            arg_parse = arg_result.unwrap()
            arg_expr = arg_parse.value
            cursor = self._skip_blank_inline(arg_parse.cursor)

            # Check if this is a named argument (followed by :)
            if not cursor.is_eof and cursor.current == ":":
                # This is a named argument
                cursor = cursor.advance()  # Skip :
                cursor = self._skip_blank_inline(cursor)

                # The argument expression must be an identifier (MessageReference)
                if not isinstance(arg_expr, MessageReference):
                    return Failure(
                        ParseError("Named argument name must be an identifier", cursor)
                    )

                arg_name = arg_expr.id.name

                # Check for duplicate named argument names
                if arg_name in seen_named_arg_names:
                    return Failure(
                        ParseError(f"Duplicate named argument: '{arg_name}'", cursor)
                    )
                seen_named_arg_names.add(arg_name)

                # Parse the value (must be inline expression)
                if cursor.is_eof:
                    return Failure(ParseError("Expected value after ':'", cursor))

                # Parse value expression using extracted helper
                value_result = self._parse_argument_expression(cursor)
                if isinstance(value_result, Failure):
                    return value_result

                value_parse = value_result.unwrap()
                value_expr = value_parse.value
                cursor = value_parse.cursor

                # Per FTL spec: NamedArgument ::= Identifier ":" (StringLiteral | NumberLiteral)
                # Named argument values MUST be literals, NOT references or variables
                if not isinstance(value_expr, (StringLiteral, NumberLiteral)):
                    # Enhanced error message with explanation and workaround
                    error_msg = (
                        f"Named argument '{arg_name}' requires a literal value "
                        f"(string or number), not a variable or reference.\n\n"
                        f"FTL Specification Restriction:\n"
                        f"  The Fluent spec restricts named arguments to literals\n"
                        f"  for static analysis by translation tools.\n\n"
                        f"Workaround - Use Select Expression:\n"
                        f"  Instead of: {{ FUNCTION($val, {arg_name}: $variable) }}\n"
                        f"  Use this:   {{ $variable ->\n"
                        f'                 [opt1] {{ FUNCTION($val, {arg_name}: "opt1") }}\n'
                        f'                 [opt2] {{ FUNCTION($val, {arg_name}: "opt2") }}\n'
                        f"                *[other] {{ $val }}\n"
                        f"              }}\n\n"
                        f"See: https://projectfluent.org/fluent/guide/selectors.html"
                    )
                    return Failure(ParseError(error_msg, cursor))

                named.append(NamedArgument(name=Identifier(arg_name), value=value_expr))
                seen_named = True

            else:
                # This is a positional argument
                if seen_named:
                    return Failure(
                        ParseError("Positional arguments must come before named arguments", cursor)
                    )
                positional.append(arg_expr)

            cursor = self._skip_blank_inline(cursor)

            # Check for comma (optional before closing paren)
            if not cursor.is_eof and cursor.current == ",":
                cursor = cursor.advance()  # Skip comma
                cursor = self._skip_blank_inline(cursor)

        call_args = CallArguments(positional=tuple(positional), named=tuple(named))
        return Success(ParseResult(call_args, cursor))

    def _parse_function_reference(
        self, cursor: Cursor
    ) -> Success[ParseResult[FunctionReference]] | Failure[ParseError]:
        """Parse function reference: FUNCTION(args)

        Function names must be uppercase identifiers.

        Examples:
            NUMBER($value)
            NUMBER($value, minimumFractionDigits: 2)
            DATETIME($date, dateStyle: "full")

        Args:
            cursor: Position at start of function name

        Returns:
            Success(ParseResult(FunctionReference, cursor_after_))) on success
            Failure(ParseError(...)) on parse error
        """
        # Parse function name (must be uppercase identifier)
        id_result = self._parse_identifier(cursor)
        if isinstance(id_result, Failure):
            return id_result

        id_parse = id_result.unwrap()
        func_name = id_parse.value

        # Validate function name is uppercase
        if not func_name.isupper():
            return Failure(
                ParseError(f"Function name must be uppercase: '{func_name}'", id_parse.cursor)
            )

        # Per spec: FunctionReference uses blank? before "("
        cursor = self._skip_blank_inline(id_parse.cursor)

        # Expect opening parenthesis
        if cursor.is_eof or cursor.current != "(":
            return Failure(ParseError("Expected '(' after function name", cursor))

        cursor = cursor.advance()  # Skip (

        # Parse arguments
        args_result = self._parse_call_arguments(cursor)
        if isinstance(args_result, Failure):
            return args_result

        args_parse = args_result.unwrap()
        cursor = self._skip_blank_inline(args_parse.cursor)

        # Expect closing parenthesis
        if cursor.is_eof or cursor.current != ")":
            return Failure(ParseError("Expected ')' after function arguments", cursor))

        cursor = cursor.advance()  # Skip )

        func_ref = FunctionReference(id=Identifier(func_name), arguments=args_parse.value)
        return Success(ParseResult(func_ref, cursor))

    def _parse_inline_expression(  # noqa: PLR0911, PLR0915  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        self, cursor: Cursor
    ) -> Success[ParseResult[
            VariableReference
            | StringLiteral
            | NumberLiteral
            | FunctionReference
            | MessageReference
            | TermReference
        ]] | Failure[ParseError,]:
        """Parse inline expression (variable, string, number, function, message, or term reference).

        Helper method extracted to reduce complexity in _parse_placeable.

        Handles:
        - Variable references: $var
        - String literals: "text"
        - Number literals: 42
        - Function calls: NUMBER(args)
        - Message references: identifier
        - Term references: -term-id

        Args:
            cursor: Current position in source

        Returns:
            Success(ParseResult(expression, cursor)) on success
            Failure(ParseError(...)) on parse error
        """
        if not cursor.is_eof and cursor.current == "$":
            # Parse variable reference
            var_result = self._parse_variable_reference(cursor)
            if isinstance(var_result, Failure):
                return var_result
            var_parse = var_result.unwrap()
            return Success(ParseResult(var_parse.value, var_parse.cursor))

        if not cursor.is_eof and cursor.current == '"':
            # Parse string literal
            str_result = self._parse_string_literal(cursor)
            if isinstance(str_result, Failure):
                return str_result
            str_parse = str_result.unwrap()
            return Success(ParseResult(StringLiteral(value=str_parse.value), str_parse.cursor))

        if not cursor.is_eof and cursor.current == "-":
            # Could be negative number or term reference
            # Peek ahead to distinguish: -123 is number, -brand is term
            next_cursor = cursor.advance()
            if not next_cursor.is_eof and next_cursor.current.isalpha():
                # It's a term reference: -brand
                term_result = self._parse_term_reference(cursor)
                if isinstance(term_result, Failure):
                    return term_result
                term_parse = term_result.unwrap()
                return Success(ParseResult(term_parse.value, term_parse.cursor))
            # It's a negative number: -123
            num_result = self._parse_number(cursor)
            if isinstance(num_result, Failure):
                return num_result
            num_parse = num_result.unwrap()
            return Success(ParseResult(NumberLiteral(value=num_parse.value), num_parse.cursor))

        if not cursor.is_eof and cursor.current.isdigit():
            # Parse number literal
            num_result = self._parse_number(cursor)
            if isinstance(num_result, Failure):
                return num_result
            num_parse = num_result.unwrap()
            return Success(ParseResult(NumberLiteral(value=num_parse.value), num_parse.cursor))

        if not cursor.is_eof and cursor.current.isupper():
            # Might be a function call (uppercase identifier followed by '(')
            # Peek ahead to check for opening parenthesis
            id_result = self._parse_identifier(cursor)
            if isinstance(id_result, Failure):
                return id_result

            id_parse = id_result.unwrap()
            func_name = id_parse.value

            # Check if uppercase and followed by '('
            cursor_after_id = self._skip_blank_inline(id_parse.cursor)
            is_function_call = (
                func_name.isupper()
                and not cursor_after_id.is_eof
                and cursor_after_id.current == "("
            )
            if is_function_call:
                # It's a function call! Parse it fully
                func_result = self._parse_function_reference(cursor)
                if isinstance(func_result, Failure):
                    return func_result
                func_parse = func_result.unwrap()
                return Success(ParseResult(func_parse.value, func_parse.cursor))

            # Not a function - must be a message reference (lowercase or no parens)
            # Check for optional attribute access (.attribute)
            cursor_after_id = id_parse.cursor
            attribute: Identifier | None = None

            if not cursor_after_id.is_eof and cursor_after_id.current == ".":
                cursor_after_id = cursor_after_id.advance()  # Skip '.'

                attr_id_result = self._parse_identifier(cursor_after_id)
                if isinstance(attr_id_result, Failure):
                    return attr_id_result

                attr_id_parse = attr_id_result.unwrap()
                attribute = Identifier(attr_id_parse.value)
                cursor_after_id = attr_id_parse.cursor

            return Success(
                ParseResult(
                    MessageReference(id=Identifier(func_name), attribute=attribute),
                    cursor_after_id,
                )
            )

        # Try parsing as lowercase message reference (msg or msg.attr)
        if not cursor.is_eof and (cursor.current.islower() or cursor.current == "_"):
            id_result = self._parse_identifier(cursor)
            if isinstance(id_result, Failure):
                return id_result

            id_parse = id_result.unwrap()
            msg_name = id_parse.value
            cursor_after_id = id_parse.cursor
            msg_attribute: Identifier | None = None

            # Check for optional attribute access (.attribute)
            if not cursor_after_id.is_eof and cursor_after_id.current == ".":
                cursor_after_id = cursor_after_id.advance()  # Skip '.'

                attr_id_result = self._parse_identifier(cursor_after_id)
                if isinstance(attr_id_result, Failure):
                    return attr_id_result

                attr_id_parse = attr_id_result.unwrap()
                msg_attribute = Identifier(attr_id_parse.value)
                cursor_after_id = attr_id_parse.cursor

            return Success(
                ParseResult(
                    MessageReference(id=Identifier(msg_name), attribute=msg_attribute),
                    cursor_after_id,
                )
            )

        return Failure(
            ParseError(
                'Expected variable ($var), string (""), number, or function call',
                cursor,
            )
        )

    def _parse_placeable(
        self, cursor: Cursor
    ) -> Success[ParseResult[Placeable]] | Failure[ParseError]:
        """Parse placeable expression: {$var}, {"\n"}, {$var -> [key] value}, or {FUNC()}.

        Parser combinator helper that reduces nesting in _parse_pattern().

        Handles:
        - Variable references: {$var}
        - String literals: {"\n"}
        - Number literals: {42}
        - Select expressions: {$var -> [one] item *[other] items}
        - Function calls: {NUMBER($value, minimumFractionDigits: 2)}

        Args:
            cursor: Position AFTER the opening '{'

        Returns:
            Success(ParseResult(Placeable, cursor_after_})) on success
            Failure(ParseError(...)) on parse error

        Example:
            cursor at: "$var}"  → parses to Placeable(VariableReference("var"))
            cursor at: "\"\n\"}" → parses to Placeable(StringLiteral("\n"))
            cursor at: "$n -> [one] 1 *[other] N}" → parses to Placeable(SelectExpression(...))
            cursor at: "NUMBER($val)}" → parses to Placeable(FunctionReference(...))
        """
        # Per spec: inline_placeable ::= "{" blank? (SelectExpression | InlineExpression) blank? "}"
        cursor = self._skip_blank_inline(cursor)

        # Capture start position before parsing expression (for select expression span)
        expr_start_pos = cursor.pos

        # Parse the inline expression using extracted helper
        expr_result = self._parse_inline_expression(cursor)
        if isinstance(expr_result, Failure):
            return expr_result

        expr_parse = expr_result.unwrap()
        expression = expr_parse.value
        parse_result_cursor = expr_parse.cursor

        cursor = self._skip_blank_inline(parse_result_cursor)

        # Check for select expression (->)
        # Per FTL 1.0 spec: SelectExpression ::= InlineExpression blank? "->" ...
        # Valid selectors (any InlineExpression):
        #   - VariableReference: { $var -> ... }
        #   - StringLiteral: { "foo" -> ... }
        #   - NumberLiteral: { 42 -> ... }
        #   - FunctionReference: { NUMBER($x) -> ... }
        #   - MessageReference: { msg -> ... } or { msg.attr -> ... }
        #   - TermReference: { -term -> ... } or { -term.attr -> ... }
        is_valid_selector = isinstance(
            expression,
            (
                VariableReference,
                StringLiteral,
                NumberLiteral,
                FunctionReference,
                MessageReference,
                TermReference,
            ),
        )

        if is_valid_selector and not cursor.is_eof and cursor.current == "-":
            # Peek ahead for ->
            next_cursor = cursor.advance()
            if not next_cursor.is_eof and next_cursor.current == ">":
                # It's a select expression!
                cursor = next_cursor.advance()  # Skip ->

                select_result = self._parse_select_expression(
                    cursor, expression, expr_start_pos
                )
                if isinstance(select_result, Failure):
                    return select_result

                select_parse = select_result.unwrap()
                cursor = self._skip_blank_inline(select_parse.cursor)

                # Expect }
                if cursor.is_eof or cursor.current != "}":
                    return Failure(ParseError("Expected '}' after select expression", cursor))

                cursor = cursor.advance()  # Skip }
                return Success(ParseResult(Placeable(expression=select_parse.value), cursor))

        # Just a simple inline expression {$var}, {"\n"}, or {42}
        # Expect }
        if cursor.is_eof or cursor.current != "}":
            return Failure(ParseError("Expected '}'", cursor))

        cursor = cursor.advance()  # Skip }
        return Success(ParseResult(Placeable(expression=expression), cursor))

    def _parse_pattern(self, cursor: Cursor) -> Success[ParseResult[Pattern]] | Failure[ParseError]:
        """Parse full pattern with support for select expressions.

        This replaces _parse_simple_pattern() for complete functionality.

        Handles:
        - Plain text
        - Variable references {$var}
        - Select expressions {$var -> [key] value}

        Args:
            cursor: Current position in source

        Returns:
            Success(ParseResult(Pattern, new_cursor)) on success
            Failure(ParseError(...)) on parse error
        """
        elements: list[TextElement | Placeable] = []

        while not cursor.is_eof:
            ch = cursor.current

            # Stop conditions - but check for indented continuations first
            if ch in ("\n", "\r"):
                if self._is_indented_continuation(cursor):
                    # Skip newline and consume indentation
                    cursor = cursor.advance()
                    if not cursor.is_eof and cursor.current == "\n":
                        cursor = cursor.advance()  # Handle \r\n
                    # Skip leading spaces (continuation indent)
                    while not cursor.is_eof and cursor.current == " ":
                        cursor = cursor.advance()
                    # Add a space to represent the line break in the pattern value
                    if elements and not isinstance(elements[-1], Placeable):
                        # Append space to previous text element
                        last_elem = elements[-1]
                        elements[-1] = TextElement(value=last_elem.value + " ")
                    else:
                        # Add new text element with space
                        elements.append(TextElement(value=" "))
                    continue  # Continue parsing on next line
                break  # Not a continuation, stop parsing pattern

            # Note: '.' is removed from stop conditions here.
            # Per Fluent spec, '.' only starts an attribute when it appears at the
            # beginning of a NEW LINE (after newline + optional indentation).
            # A '.' on the same line as '=' is valid text content.
            # Attributes are detected in message/term parsing after pattern completes.

            # Placeable: {$var} or {$var -> ...}
            if ch == "{":
                cursor = cursor.advance()  # Skip {

                # Use helper method to parse placeable (reduces nesting!)
                placeable_result = self._parse_placeable(cursor)
                if isinstance(placeable_result, Failure):
                    return placeable_result

                placeable_parse = placeable_result.unwrap()
                elements.append(placeable_parse.value)
                cursor = placeable_parse.cursor

            else:
                # Parse text until { or stop condition
                text_start = cursor.pos
                while not cursor.is_eof:
                    ch = cursor.current
                    # Stop at: placeable start, line end, or special pattern markers
                    # Note: '.' removed - only stops attributes at line start, not mid-pattern
                    if ch in ("{", "\n", "\r", "}", "[", "*"):
                        break
                    cursor = cursor.advance()

                if cursor.pos > text_start:
                    text = Cursor(cursor.source, text_start).slice_to(cursor.pos)
                    elements.append(TextElement(value=text))
                elif cursor.pos == text_start:
                    # Prevent infinite loop: advance cursor when no text consumed
                    # This happens when current char is a stop char but not '{'
                    cursor = cursor.advance()

        pattern = Pattern(elements=tuple(elements))
        return Success(ParseResult(pattern, cursor))

    def _parse_message(self, cursor: Cursor) -> Success[ParseResult[Message]] | Failure[ParseError]:
        """Parse message with full support for select expressions.

        This replaces _parse_simple_message() for complete functionality.

        Examples:
            "hello = World"
            "welcome = Hello, {$name}!"
            "count = {$num -> [one] item *[other] items}"

        Args:
            cursor: Current position in source

        Returns:
            Success(ParseResult(Message, new_cursor)) on success
            Failure(ParseError(...)) on parse error
        """
        start_pos = cursor.pos

        # Parse: Identifier "="
        id_result = self._parse_message_header(cursor)
        if isinstance(id_result, Failure):
            return id_result
        id_parse = id_result.unwrap()
        cursor = id_parse.cursor

        # Parse pattern (message value)
        cursor = self._skip_multiline_pattern_start(cursor)
        pattern_result = self._parse_pattern(cursor)
        if isinstance(pattern_result, Failure):
            return pattern_result
        pattern_parse = pattern_result.unwrap()
        cursor = pattern_parse.cursor

        # Parse: Attribute* (zero or more attributes)
        attributes_result = self._parse_message_attributes(cursor)
        if isinstance(attributes_result, Failure):
            return attributes_result
        attributes_parse = attributes_result.unwrap()
        cursor = attributes_parse.cursor

        # Validate: Per spec, Message must have Pattern OR Attribute
        validation_result = self._validate_message_content(
            id_parse.value, pattern_parse.value, attributes_parse.value
        )
        if isinstance(validation_result, Failure):
            return validation_result

        # Construct Message node
        message = Message(
            id=Identifier(id_parse.value),
            value=pattern_parse.value,
            attributes=tuple(attributes_parse.value),
            span=Span(start=start_pos, end=cursor.pos),
        )

        return Success(ParseResult(message, cursor))

    def _parse_message_header(
        self, cursor: Cursor
    ) -> Success[ParseResult[str]] | Failure[ParseError]:
        """Parse message header: Identifier "="

        Returns identifier string and cursor after '='.
        """
        id_result = self._parse_identifier(cursor)
        if isinstance(id_result, Failure):
            return id_result

        id_parse = id_result.unwrap()
        # Per spec: Message ::= Identifier blank_inline? "=" ...
        cursor = self._skip_blank_inline(id_parse.cursor)

        if cursor.is_eof or cursor.current != "=":
            return Failure(ParseError("Expected '=' after message ID", cursor))

        cursor = cursor.advance()  # Skip =
        return Success(ParseResult(id_parse.value, cursor))

    def _skip_multiline_pattern_start(self, cursor: Cursor) -> Cursor:
        """Skip whitespace and handle multiline pattern start.

        Per spec: Pattern can start on same line or next line (if indented).
            Message ::= Identifier blank_inline? "=" blank_inline? Pattern
            Attribute ::= ... blank_inline? "=" blank_inline? Pattern
            blank_inline ::= "\u0020"+  (ONLY space, NOT tabs)

        This method handles:
        1. Inline patterns: "key = value" (skip spaces on same line)
        2. Multiline patterns: "key =\n    value" (skip newline + leading spaces)
        """
        # Skip inline whitespace (ONLY spaces per spec, NOT tabs)
        cursor = self._skip_blank_inline(cursor)

        # Check for pattern starting on next line
        if not cursor.is_eof and cursor.current in ("\n", "\r"):  # noqa: SIM102
            if self._is_indented_continuation(cursor):
                # Multiline pattern - skip newline and leading indentation
                cursor = cursor.advance()
                if not cursor.is_eof and cursor.current == "\n":  # Handle \r\n (CRLF)
                    cursor = cursor.advance()
                # Skip leading indentation (ONLY spaces per spec)
                cursor = self._skip_blank_inline(cursor)

        return cursor

    def _parse_message_attributes(
        self, cursor: Cursor
    ) -> Success[ParseResult[list[Attribute]]] | Failure[ParseError]:
        """Parse zero or more message attributes.

        Attributes must appear on new lines starting with '.'.
        """
        attributes: list[Attribute] = []

        while not cursor.is_eof:
            # Advance to next line
            if cursor.current in ("\n", "\r"):
                cursor = cursor.advance()
                if not cursor.is_eof and cursor.current == "\n":  # Handle \r\n
                    cursor = cursor.advance()
            else:
                break  # No newline, done with attributes

            # Check if line starts with '.' (attribute marker)
            # Per spec: Attribute ::= line_end blank? "." ...
            # blank allows spaces and newlines, but NOT tabs
            saved_cursor = cursor
            # Skip leading spaces on this line (NOT tabs per spec)
            while not cursor.is_eof and cursor.current == " ":
                cursor = cursor.advance()

            if cursor.is_eof or cursor.current != ".":
                cursor = saved_cursor
                break  # Not an attribute

            # Parse attribute
            attr_result = self._parse_attribute(saved_cursor)
            if isinstance(attr_result, Failure):
                cursor = saved_cursor
                break  # Invalid attribute syntax

            attr_parse = attr_result.unwrap()
            attributes.append(attr_parse.value)
            cursor = attr_parse.cursor

        return Success(ParseResult(attributes, cursor))

    def _validate_message_content(
        self, msg_id: str, pattern: Pattern | None, attributes: list[Attribute]
    ) -> Success[None] | Failure[ParseError]:
        """Validate message has either pattern or attributes.

        Per Fluent spec: Message ::= ID "=" ((Pattern Attribute*) | (Attribute+))
        """
        has_pattern = pattern is not None and len(pattern.elements) > 0
        has_attributes = len(attributes) > 0

        if not has_pattern and not has_attributes:
            # Create dummy cursor for error reporting (position doesn't matter here)
            return Failure(
                ParseError(
                    f'Message "{msg_id}" must have either a value or at least one attribute',
                    Cursor("", 0),
                )
            )

        return Success(None)

    def _parse_attribute(
        self, cursor: Cursor
    ) -> Success[ParseResult[Attribute]] | Failure[ParseError]:
        """Parse message attribute (.attribute = pattern).

        FTL syntax:
            button = Save
                .tooltip = Click to save changes
                .aria-label = Save button

        Attributes are indented and start with a dot followed by an identifier.

        Args:
            cursor: Current position in source (should be at start of line with '.')

        Returns:
            Success(ParseResult(Attribute, new_cursor)) on success
            Failure(ParseError(...)) on parse error
        """
        # Capture start position for span
        start_pos = cursor.pos

        # Skip leading whitespace (ONLY spaces per spec, NOT tabs or newlines)
        # Per spec: Attribute ::= line_end blank? "." ...
        # blank can contain spaces but NOT tabs
        cursor = self._skip_blank_inline(cursor)

        # Check for '.' at start
        if cursor.is_eof or cursor.current != ".":
            return Failure(ParseError("Expected '.' at start of attribute", cursor, expected=["."]))

        cursor = cursor.advance()  # Skip '.'

        # Parse identifier after '.'
        id_result = self._parse_identifier(cursor)
        if isinstance(id_result, Failure):
            return id_result

        id_parse = id_result.unwrap()
        # Per spec: Attribute ::= line_end blank? "." Identifier blank_inline? "=" ...
        cursor = self._skip_blank_inline(id_parse.cursor)

        # Expect '='
        if cursor.is_eof or cursor.current != "=":
            return Failure(
                ParseError("Expected '=' after attribute identifier", cursor, expected=["="])
            )

        cursor = cursor.advance()  # Skip '='
        # After '=', handle multiline pattern start (same as messages)
        # Per spec: Attribute ::= ... blank_inline? "=" blank_inline? Pattern
        # Pattern can start on same line or next line with indentation
        cursor = self._skip_multiline_pattern_start(cursor)

        # Parse pattern
        pattern_result = self._parse_pattern(cursor)
        if isinstance(pattern_result, Failure):
            return pattern_result

        pattern_parse = pattern_result.unwrap()

        # Create span from start to current position
        span = Span(start=start_pos, end=pattern_parse.cursor.pos)

        attribute = Attribute(id=Identifier(id_parse.value), value=pattern_parse.value, span=span)

        return Success(ParseResult(attribute, pattern_parse.cursor))

    def _parse_term(  # pylint: disable=too-many-branches
        self, cursor: Cursor
    ) -> Success[ParseResult[Term]] | Failure[ParseError]:
        """Parse term definition (-term-id = pattern).

        FTL syntax:
            -brand = Firefox
            -brand-version = 3.0
                .tooltip = Current version

        Terms are private definitions prefixed with '-' and can have attributes.

        Args:
            cursor: Current position in source (should be at '-')

        Returns:
            Success(ParseResult(Term, new_cursor)) on success
            Failure(ParseError(...)) on parse error
        """
        # Capture start position for span
        start_pos = cursor.pos

        # Expect '-' prefix
        if cursor.is_eof or cursor.current != "-":
            return Failure(ParseError("Expected '-' at start of term", cursor, expected=["-"]))

        cursor = cursor.advance()  # Skip '-'

        # Parse identifier
        id_result = self._parse_identifier(cursor)
        if isinstance(id_result, Failure):
            return id_result

        id_parse = id_result.unwrap()
        # Per spec: Term ::= "-" Identifier blank_inline? "=" ...
        cursor = self._skip_blank_inline(id_parse.cursor)

        # Expect '='
        if cursor.is_eof or cursor.current != "=":
            return Failure(ParseError("Expected '=' after term ID", cursor, expected=["="]))

        cursor = cursor.advance()  # Skip '='

        # After '=', skip inline whitespace (per spec: blank_inline, space only)
        cursor = self._skip_blank_inline(cursor)

        # Check for pattern starting on next line (multiline value pattern)
        # Example: -term =\n    value
        if not cursor.is_eof and cursor.current in ("\n", "\r"):  # noqa: SIM102
            # Check if next line is indented (valid multiline pattern)
            if self._is_indented_continuation(cursor):
                # Multiline pattern - skip newline and leading indentation
                cursor = cursor.advance()
                if not cursor.is_eof and cursor.current == "\n":  # Handle \r\n
                    cursor = cursor.advance()
                # Skip leading indentation before parsing
                # _parse_pattern will handle continuation lines itself
                while not cursor.is_eof and cursor.current == " ":
                    cursor = cursor.advance()
            # Else: Empty pattern - leave cursor at newline, _parse_pattern will handle it

        # Parse pattern
        pattern_result = self._parse_pattern(cursor)
        if isinstance(pattern_result, Failure):
            return pattern_result

        pattern_parse = pattern_result.unwrap()
        cursor = pattern_parse.cursor

        # Validate term has non-empty value (FTL spec requirement)
        if not pattern_parse.value.elements:
            return Failure(
                ParseError(
                    f'Expected term "-{id_parse.value}" to have a value',
                    cursor,
                )
            )

        # Parse attributes (reuse attribute parsing logic)
        attributes: list[Attribute] = []
        while not cursor.is_eof:
            # Skip to next line
            if cursor.current in ("\n", "\r"):
                cursor = cursor.advance()
                if not cursor.is_eof and cursor.current == "\n":  # Handle \r\n
                    cursor = cursor.advance()
            else:
                # No newline, done with attributes
                break

            # Check if next line starts with whitespace followed by '.'
            # Per spec: Attribute ::= line_end blank? "." ...
            # blank can contain spaces, but NOT tabs
            saved_cursor = cursor
            while not cursor.is_eof and cursor.current == " ":
                cursor = cursor.advance()

            if cursor.is_eof or cursor.current != ".":
                # Not an attribute, restore cursor and break
                cursor = saved_cursor
                break

            # Parse attribute
            attr_result = self._parse_attribute(saved_cursor)
            if isinstance(attr_result, Failure):
                # Not a valid attribute, restore and break
                cursor = saved_cursor
                break

            attr_parse = attr_result.unwrap()
            attributes.append(attr_parse.value)
            cursor = attr_parse.cursor

        # Create span from start to current position
        span = Span(start=start_pos, end=cursor.pos)

        term = Term(
            id=Identifier(id_parse.value),
            value=pattern_parse.value,
            attributes=tuple(attributes),
            span=span,
        )

        return Success(ParseResult(term, cursor))

    def _parse_term_reference(
        self, cursor: Cursor
    ) -> Success[ParseResult[TermReference]] | Failure[ParseError]:
        """Parse term reference in inline expression (-term-id or -term.attr).

        FTL syntax:
            { -brand }
            { -brand.short }
            { -brand(case: "nominative") }

        Term references can have optional attribute access and arguments.

        Args:
            cursor: Current position (should be at '-')

        Returns:
            Success(ParseResult(TermReference, new_cursor)) on success
            Failure(ParseError(...)) on parse error
        """
        # Expect '-' prefix
        if cursor.is_eof or cursor.current != "-":
            return Failure(
                ParseError("Expected '-' at start of term reference", cursor, expected=["-"])
            )

        cursor = cursor.advance()  # Skip '-'

        # Parse identifier
        id_result = self._parse_identifier(cursor)
        if isinstance(id_result, Failure):
            return id_result

        id_parse = id_result.unwrap()
        cursor = id_parse.cursor

        # Check for optional attribute access (.attribute)
        attribute: Identifier | None = None
        if not cursor.is_eof and cursor.current == ".":
            cursor = cursor.advance()  # Skip '.'

            attr_id_result = self._parse_identifier(cursor)
            if isinstance(attr_id_result, Failure):
                return attr_id_result

            attr_id_parse = attr_id_result.unwrap()
            attribute = Identifier(attr_id_parse.value)
            cursor = attr_id_parse.cursor

        # Check for optional arguments (case: "nominative")
        # Per spec: TermReference uses blank? before "("
        cursor = self._skip_blank_inline(cursor)

        arguments: CallArguments | None = None
        if not cursor.is_eof and cursor.current == "(":
            # Parse call arguments (reuse function argument parsing)
            cursor = cursor.advance()  # Skip '('
            args_result = self._parse_call_arguments(cursor)
            if isinstance(args_result, Failure):
                return args_result

            args_parse = args_result.unwrap()
            cursor = self._skip_blank_inline(args_parse.cursor)

            # Expect closing parenthesis
            if cursor.is_eof or cursor.current != ")":
                return Failure(ParseError("Expected ')' after term arguments", cursor))

            cursor = cursor.advance()  # Skip ')'
            arguments = args_parse.value

        term_ref = TermReference(
            id=Identifier(id_parse.value), attribute=attribute, arguments=arguments
        )

        return Success(ParseResult(term_ref, cursor))

    def _parse_comment(self, cursor: Cursor) -> Success[ParseResult[Comment]] | Failure[ParseError]:
        """Parse comment line per Fluent spec.

        Per spec, comments come in three types:
        - # (single-line comment)
        - ## (group comment)
        - ### (resource comment)

        Adjacent comment lines of the same type are joined during AST construction.

        EBNF:
            CommentLine ::= ("###" | "##" | "#") ("\u0020" comment_char*)? line_end

        Args:
            cursor: Current parse position (must be at '#')

        Returns:
            Success with Comment node or Failure with ParseError
        """
        start_pos = cursor.pos

        # Determine comment type by counting '#' characters
        hash_count = 0
        temp_cursor = cursor
        while not temp_cursor.is_eof and temp_cursor.current == "#":
            hash_count += 1
            temp_cursor = temp_cursor.advance()

        # Validate comment type (1, 2, or 3 hashes)
        if hash_count > 3:
            return Failure(
                ParseError(
                    f"Invalid comment: expected 1-3 '#' characters, found {hash_count}",
                    cursor,
                )
            )

        # Map hash count to comment type
        comment_type = {1: "comment", 2: "group", 3: "resource"}.get(hash_count, "comment")

        # Advance cursor past the '#' characters
        cursor = temp_cursor

        # Per spec: optional space after '#'
        if not cursor.is_eof and cursor.current == " ":
            cursor = cursor.advance()

        # Collect comment content (everything until line end)
        content_start = cursor.pos
        while not cursor.is_eof and cursor.current not in ("\n", "\r"):
            cursor = cursor.advance()

        # Extract comment text
        content = cursor.source[content_start : cursor.pos]

        # Advance past line ending
        if not cursor.is_eof:
            if cursor.current == "\r":
                cursor = cursor.advance()
                # Handle CRLF
                if not cursor.is_eof and cursor.current == "\n":
                    cursor = cursor.advance()
            elif cursor.current == "\n":
                cursor = cursor.advance()

        # Create Comment node with span
        comment_node = Comment(
            content=content,
            type=comment_type,
            span=Span(start=start_pos, end=cursor.pos),
        )

        return Success(ParseResult(comment_node, cursor))
