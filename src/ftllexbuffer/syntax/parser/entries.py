"""Entry parsing for Fluent FTL parser.

This module provides parsers for top-level FTL entries including messages,
terms, attributes, and comments.
"""

from ftllexbuffer.enums import CommentType
from ftllexbuffer.syntax.ast import Attribute, Comment, Identifier, Message, Pattern, Span, Term
from ftllexbuffer.syntax.cursor import Cursor, ParseResult
from ftllexbuffer.syntax.parser.primitives import parse_identifier
from ftllexbuffer.syntax.parser.whitespace import skip_blank_inline, skip_multiline_pattern_start


def parse_message_header(cursor: Cursor) -> ParseResult[str] | None:
    """Parse message header: Identifier "="

    Returns identifier string and cursor after '='.
    """
    id_result = parse_identifier(cursor)
    if id_result is None:
        return id_result

    id_parse = id_result
    # Per spec: Message ::= Identifier blank_inline? "=" ...
    cursor = skip_blank_inline(id_parse.cursor)

    if cursor.is_eof or cursor.current != "=":
        return None  # "Expected '=' after message ID", cursor

    cursor = cursor.advance()  # Skip =
    return ParseResult(id_parse.value, cursor)


def parse_message_attributes(cursor: Cursor) -> ParseResult[list[Attribute]] | None:
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
        cursor = cursor.skip_spaces()

        if cursor.is_eof or cursor.current != ".":
            cursor = saved_cursor
            break  # Not an attribute

        # Parse attribute
        attr_result = parse_attribute(saved_cursor)
        if attr_result is None:
            cursor = saved_cursor
            break  # Invalid attribute syntax

        attr_parse = attr_result
        attributes.append(attr_parse.value)
        cursor = attr_parse.cursor

    return ParseResult(attributes, cursor)


def validate_message_content(
    _msg_id: str, pattern: Pattern | None, attributes: list[Attribute]
) -> bool:
    """Validate message has either pattern or attributes.

    Per Fluent spec: Message ::= ID "=" ((Pattern Attribute*) | (Attribute+))

    Args:
        _msg_id: Message identifier (for potential future validation)
        pattern: Message value pattern (may be None)
        attributes: List of message attributes

    Returns:
        True if validation passed, False if validation failed
    """
    has_pattern = pattern is not None and len(pattern.elements) > 0
    has_attributes = len(attributes) > 0

    # Message must have either value or attributes
    return has_pattern or has_attributes


def parse_message(cursor: Cursor) -> ParseResult[Message] | None:
    """Parse message with full support for select expressions.

    This replaces parse_simple_message() for complete functionality.

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
    # Import here to avoid circular dependency
    from .patterns import parse_pattern  # noqa: PLC0415

    start_pos = cursor.pos

    # Parse: Identifier "="
    id_result = parse_message_header(cursor)
    if id_result is None:
        return id_result
    id_parse = id_result
    cursor = id_parse.cursor

    # Parse pattern (message value)
    cursor = skip_multiline_pattern_start(cursor)
    pattern_result = parse_pattern(cursor)
    if pattern_result is None:
        return pattern_result
    pattern_parse = pattern_result
    cursor = pattern_parse.cursor

    # Parse: Attribute* (zero or more attributes)
    attributes_result = parse_message_attributes(cursor)
    if attributes_result is None:
        return attributes_result
    attributes_parse = attributes_result
    cursor = attributes_parse.cursor

    # Validate: Per spec, Message must have Pattern OR Attribute
    is_valid = validate_message_content(
        id_parse.value, pattern_parse.value, attributes_parse.value
    )
    if not is_valid:
        return None  # Validation failed

    # Construct Message node
    message = Message(
        id=Identifier(id_parse.value),
        value=pattern_parse.value,
        attributes=tuple(attributes_parse.value),
        span=Span(start=start_pos, end=cursor.pos),
    )

    return ParseResult(message, cursor)


def parse_attribute(cursor: Cursor) -> ParseResult[Attribute] | None:
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
    # Import here to avoid circular dependency
    from .patterns import parse_pattern  # noqa: PLC0415

    # Skip leading whitespace (ONLY spaces per spec, NOT tabs or newlines)
    # Per spec: Attribute ::= line_end blank? "." ...
    # blank can contain spaces but NOT tabs
    cursor = skip_blank_inline(cursor)

    # Check for '.' at start
    if cursor.is_eof or cursor.current != ".":
        return None  # "Expected '.' at start of attribute", cursor, expected=["."]

    cursor = cursor.advance()  # Skip '.'

    # Parse identifier after '.'
    id_result = parse_identifier(cursor)
    if id_result is None:
        return id_result

    id_parse = id_result
    # Per spec: Attribute ::= line_end blank? "." Identifier blank_inline? "=" ...
    cursor = skip_blank_inline(id_parse.cursor)

    # Expect '='
    if cursor.is_eof or cursor.current != "=":
        return None  # "Expected '=' after attribute identifier", cursor, expected=["="]

    cursor = cursor.advance()  # Skip '='
    # After '=', handle multiline pattern start (same as messages)
    # Per spec: Attribute ::= ... blank_inline? "=" blank_inline? Pattern
    # Pattern can start on same line or next line with indentation
    cursor = skip_multiline_pattern_start(cursor)

    # Parse pattern
    pattern_result = parse_pattern(cursor)
    if pattern_result is None:
        return pattern_result

    pattern_parse = pattern_result

    attribute = Attribute(id=Identifier(id_parse.value), value=pattern_parse.value)

    return ParseResult(attribute, pattern_parse.cursor)


def parse_term(cursor: Cursor) -> ParseResult[Term] | None:
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
    # Import here to avoid circular dependency
    from .patterns import parse_pattern  # noqa: PLC0415
    from .whitespace import is_indented_continuation  # noqa: PLC0415

    # Capture start position for span
    start_pos = cursor.pos

    # Expect '-' prefix
    if cursor.is_eof or cursor.current != "-":
        return None  # "Expected '-' at start of term", cursor, expected=["-"]

    cursor = cursor.advance()  # Skip '-'

    # Parse identifier
    id_result = parse_identifier(cursor)
    if id_result is None:
        return id_result

    id_parse = id_result
    # Per spec: Term ::= "-" Identifier blank_inline? "=" ...
    cursor = skip_blank_inline(id_parse.cursor)

    # Expect '='
    if cursor.is_eof or cursor.current != "=":
        return None  # "Expected '=' after term ID", cursor, expected=["="]

    cursor = cursor.advance()  # Skip '='

    # After '=', skip inline whitespace (per spec: blank_inline, space only)
    cursor = skip_blank_inline(cursor)

    # Check for pattern starting on next line (multiline value pattern)
    # Example: -term =\n    value
    if not cursor.is_eof and cursor.current in ("\n", "\r"):  # noqa: SIM102
        # Check if next line is indented (valid multiline pattern)
        if is_indented_continuation(cursor):
            # Multiline pattern - skip newline and leading indentation
            cursor = cursor.advance()
            if not cursor.is_eof and cursor.current == "\n":  # Handle \r\n
                cursor = cursor.advance()
            # Skip leading indentation before parsing
            # parse_pattern will handle continuation lines itself
            cursor = cursor.skip_spaces()
        # Else: Empty pattern - leave cursor at newline, parse_pattern will handle it

    # Parse pattern
    pattern_result = parse_pattern(cursor)
    if pattern_result is None:
        return pattern_result

    pattern_parse = pattern_result
    cursor = pattern_parse.cursor

    # Validate term has non-empty value (FTL spec requirement)
    if not pattern_parse.value.elements:
        return None  # f'Expected term "-{id_parse.value}" to have a value'

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
        cursor = cursor.skip_spaces()

        if cursor.is_eof or cursor.current != ".":
            # Not an attribute, restore cursor and break
            cursor = saved_cursor
            break

        # Parse attribute
        attr_result = parse_attribute(saved_cursor)
        if attr_result is None:
            # Not a valid attribute, restore and break
            cursor = saved_cursor
            break

        attr_parse = attr_result
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

    return ParseResult(term, cursor)


def parse_comment(cursor: Cursor) -> ParseResult[Comment] | None:
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
        return None  # f"Invalid comment: expected 1-3 '#' characters, found {hash_count}"

    # Map hash count to comment type
    comment_type = {
        1: CommentType.COMMENT,
        2: CommentType.GROUP,
        3: CommentType.RESOURCE,
    }.get(hash_count, CommentType.COMMENT)

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

    return ParseResult(comment_node, cursor)
