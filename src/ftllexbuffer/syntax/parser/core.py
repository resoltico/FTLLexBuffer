"""Core Fluent FTL parser implementation.

This module provides the main FluentParserV1 class that orchestrates
parsing of FTL source files into AST structures.
"""

from ftllexbuffer.syntax.ast import Annotation, Comment, Junk, Message, Resource, Span, Term
from ftllexbuffer.syntax.cursor import Cursor
from ftllexbuffer.syntax.parser.entries import parse_comment, parse_message, parse_term
from ftllexbuffer.syntax.parser.whitespace import skip_blank


class FluentParserV1:
    """Fluent FTL parser using immutable cursor pattern.

    Design:
    - Immutable cursor prevents infinite loops (no manual guards needed)
    - Type-safe by design (no custom Result monad)
    - Error messages include line:column with source context

    Architecture:
    - Every parser method takes Cursor (immutable) as input
    - Every parser returns ParseResult[T] | None (None indicates parse failure)
    - No mutation - compiler enforces progress
    """

    __slots__ = ()

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
            cursor = skip_blank(cursor)

            if cursor.is_eof:
                break

            # Parse comments (per Fluent spec: #, ##, ###)
            if cursor.current == "#":
                comment_result = parse_comment(cursor)
                if comment_result is not None:
                    comment_parse = comment_result
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
                term_result = parse_term(cursor)

                if term_result is not None:
                    term_parse = term_result
                    entries.append(term_parse.value)
                    cursor = term_parse.cursor
                    continue

            # Try to parse message
            message_result = parse_message(cursor)

            if message_result is not None:
                message_parse = message_result
                entries.append(message_parse.value)
                cursor = message_parse.cursor
            else:
                # Parse error - create Junk entry and continue (robustness principle)
                # Junk creation still preserves robustness
                junk_start = cursor.pos

                # Per FTL spec: Junk ::= junk_line (junk_line - "#" - "-" - [a-zA-Z])*
                # Consume multiple lines until we hit a valid entry start
                cursor = self._consume_junk_lines(cursor)

                # Create Junk entry with all consumed problematic content
                junk_content = cursor.source[junk_start : cursor.pos]
                junk_span = Span(start=junk_start, end=cursor.pos)

                annotation = Annotation(
                    code="E0099",  # Generic parse error code
                    message="Parse error",
                    span=Span(start=junk_start, end=junk_start),
                )

                entries.append(
                    Junk(content=junk_content, annotations=(annotation,), span=junk_span)
                )

        return Resource(entries=tuple(entries))

    def _consume_junk_lines(self, cursor: Cursor) -> Cursor:
        """Consume junk lines per FTL spec until valid entry start.

        Per Fluent EBNF:
            Junk ::= junk_line (junk_line - "#" - "-" - [a-zA-Z])*
            junk_line ::= /[^\n]*/ ("\u000a" | EOF)

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
            cursor = cursor.skip_spaces()

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
