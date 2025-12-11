"""Primitive parsing utilities for Fluent FTL parser.

This module provides low-level parsers for identifiers, numbers,
and string literals per the Fluent specification.
"""

from ftllexbuffer.syntax.cursor import Cursor, ParseResult


def parse_identifier(cursor: Cursor) -> ParseResult[str] | None:
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
        return None  # "Expected identifier (must start with letter)"

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
    return ParseResult(identifier, cursor)


def parse_number_value(num_str: str) -> int | float:
    """Parse number string to int or float.


    Args:
        num_str: Number string from parse_number

    Returns:
        int if no decimal point, float otherwise
    """
    return int(num_str) if "." not in num_str else float(num_str)


def parse_number(cursor: Cursor) -> ParseResult[str] | None:
    """Parse number literal: -?[0-9]+(.[0-9]+)?

    Returns the raw string representation. Use parse_number_value()
    to convert to int or float for NumberLiteral construction.

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
        return None  # "Expected number", cursor, expected=["0-9"]

    # Integer part
    while not cursor.is_eof and cursor.current.isdigit():
        cursor = cursor.advance()

    # Optional decimal part
    if not cursor.is_eof and cursor.current == ".":
        cursor = cursor.advance()

        # Must have digit after decimal
        if cursor.is_eof or not cursor.current.isdigit():
            return None  # "Expected digit after decimal point", cursor, expected=["0-9"]

        while not cursor.is_eof and cursor.current.isdigit():
            cursor = cursor.advance()

    # Extract number string
    number_str = Cursor(cursor.source, start_pos).slice_to(cursor.pos)
    return ParseResult(number_str, cursor)


def parse_escape_sequence(cursor: Cursor) -> tuple[str, Cursor] | None:  # noqa: PLR0911
    """Parse escape sequence after backslash in string.

    Helper method extracted from parse_string_literal to reduce complexity.

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
        return None  # "Unexpected EOF in string", cursor

    escape_ch = cursor.current

    if escape_ch == '"':
        return ('"', cursor.advance())
    if escape_ch == "\\":
        return ("\\", cursor.advance())
    if escape_ch == "n":
        return ("\n", cursor.advance())
    if escape_ch == "t":
        return ("\t", cursor.advance())

    if escape_ch == "u":
        # Unicode escape: \uXXXX (4 hex digits)
        cursor = cursor.advance()
        hex_digits = ""
        for _ in range(4):
            if cursor.is_eof or cursor.current not in "0123456789abcdefABCDEF":
                return None  # "Invalid Unicode escape (expected 4 hex digits)", cursor
            hex_digits += cursor.current
            cursor = cursor.advance()

        # Convert to character
        code_point = int(hex_digits, 16)
        return (chr(code_point), cursor)

    if escape_ch == "U":
        # Unicode escape: \UXXXXXX (6 hex digits)
        cursor = cursor.advance()
        hex_digits = ""
        for _ in range(6):
            if cursor.is_eof or cursor.current not in "0123456789abcdefABCDEF":
                return None  # "Invalid Unicode escape (expected 6 hex digits)", cursor
            hex_digits += cursor.current
            cursor = cursor.advance()

        # Convert to character
        code_point = int(hex_digits, 16)
        # Validate Unicode code point range
        if code_point > 0x10FFFF:
            return None  # f"Invalid Unicode code point: U+{hex_digits} (max U+10FFFF)", cursor
        return (chr(code_point), cursor)

    return None  # f"Invalid escape sequence: \\{escape_ch}", cursor


def parse_string_literal(cursor: Cursor) -> ParseResult[str] | None:
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
        return None  # "Expected opening quote", cursor, expected=['"']

    cursor = cursor.advance()  # Skip opening "
    value = ""

    while not cursor.is_eof:
        ch = cursor.current

        if ch == '"':
            # Closing quote - done!
            cursor = cursor.advance()
            return ParseResult(value, cursor)

        if ch == "\\":
            # Escape sequence - use extracted helper
            cursor = cursor.advance()
            escape_result = parse_escape_sequence(cursor)
            if escape_result is None:
                return escape_result

            escaped_char, cursor = escape_result
            value += escaped_char

        else:
            # Regular character
            value += ch
            cursor = cursor.advance()

    # EOF without closing quote
    return None  # "Unterminated string literal", cursor
