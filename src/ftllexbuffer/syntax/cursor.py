"""Immutable cursor infrastructure for type-safe parsing.

Implements the immutable cursor pattern for zero-`None` parsing.
Python 3.13+. Zero external dependencies (returns library already in pyproject.toml).

Design Philosophy:
    - Cursor is immutable (frozen dataclass)
    - No `str | None` anywhere - type safety by design
    - EOF is a state (is_eof), not a return value
    - Every advance() returns NEW cursor (prevents infinite loops)
    - Line:column computed on-demand (O(n) only for errors)

Pattern Reference:
    - Rust nom parser combinator library
    - Haskell Parsec
    - F# FParsec
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ["Cursor", "ParseError", "ParseResult"]


@dataclass(frozen=True, slots=True)
class Cursor:
    """Immutable source position tracker.

    Key Design Decisions:
        1. Frozen dataclass - Immutability enforced by Python
        2. Slots - Memory efficiency (important for large files)
        3. Simple position - Just an integer offset
        4. EOF is a property - Not a return value
        5. current raises - No None handling needed!

    Example:
        >>> cursor = Cursor("hello", 0)
        >>> cursor.current  # Type: str (not str | None!)
        'h'
        >>> new_cursor = cursor.advance()
        >>> new_cursor.current
        'e'
        >>> cursor.current  # Original unchanged (immutability)
        'h'
        >>> cursor.is_eof
        False
        >>> eof_cursor = Cursor("hi", 2)
        >>> eof_cursor.is_eof
        True
        >>> eof_cursor.current  # Raises EOFError
        Traceback (most recent call last):
        ...
        EOFError: Unexpected EOF at position 2
    """

    source: str
    pos: int

    @property
    def is_eof(self) -> bool:
        """Check if at end of input.

        Returns:
            True if position >= source length

        Note: This is the preferred way to check for EOF.
              Use this in while loops: `while not cursor.is_eof:`
        """
        return self.pos >= len(self.source)

    @property
    def current(self) -> str:
        """Get current character.

        Returns:
            Current character at position

        Raises:
            EOFError: If at end of input

        Design Note:
            This is the KEY difference from old parser!

            Old parser:
                _peek() -> str | None
                # Every call site needs None check:
                if self._peek() and self._peek() in "abc":  # Verbose!

            New parser:
                cursor.current -> str
                # No None checks needed:
                if cursor.current in "abc":  # Clean!
                # EOF is handled via is_eof property

            Type safety: mypy knows current is ALWAYS str, never None.
        """
        if self.is_eof:
            from ftllexbuffer.diagnostics import ErrorTemplate

            diagnostic = ErrorTemplate.unexpected_eof(self.pos)
            raise EOFError(diagnostic.message)
        return self.source[self.pos]

    def peek(self, offset: int = 0) -> str | None:
        """Peek at character with offset without advancing.

        Args:
            offset: Offset from current position (0 = current, 1 = next)

        Returns:
            Character at position + offset, or None if beyond EOF

        Note:
            Returns None ONLY when peeking beyond EOF.
            Use for lookahead: `if cursor.peek(1) == '=':`

            Unlike old parser's _peek(), this is used for lookahead only.
            For normal character access, use .current property.
        """
        target_pos = self.pos + offset
        if target_pos >= len(self.source):
            return None
        return self.source[target_pos]

    def advance(self, count: int = 1) -> Cursor:
        """Return new cursor advanced by count positions.

        Args:
            count: Number of positions to advance (default: 1)

        Returns:
            New Cursor instance at new position (original unchanged)

        Design Note:
            Immutability prevents infinite loops!

            Old parser (mutable):
                while condition:
                    # If we forget self._advance(), infinite loop!
                    pass

            New parser (immutable):
                while not cursor.is_eof:
                    cursor = cursor.advance()  # Must reassign!
                    # If we forget reassignment, loop exits (cursor unchanged)

            The compiler enforces progress!

        Example:
            >>> cursor = Cursor("hello", 0)
            >>> cursor2 = cursor.advance()
            >>> cursor.pos  # Original unchanged
            0
            >>> cursor2.pos  # New cursor advanced
            1
        """
        new_pos = min(self.pos + count, len(self.source))
        return Cursor(self.source, new_pos)

    def slice_to(self, end_pos: int) -> str:
        """Extract source slice from current position to end_pos.

        Args:
            end_pos: End position (exclusive)

        Returns:
            Source substring from current position to end_pos

        Usage:
            Useful for extracting matched text after parsing:

            >>> cursor = Cursor("hello world", 0)
            >>> # Parse "hello"
            >>> start = cursor.pos
            >>> while not cursor.is_eof and cursor.current != ' ':
            ...     cursor = cursor.advance()
            >>> text = cursor.slice_to(cursor.pos)
            >>> # Wait, that won't work because we need original cursor!

            Better pattern:
            >>> cursor = Cursor("hello world", 0)
            >>> start_pos = cursor.pos
            >>> while not cursor.is_eof and cursor.current != ' ':
            ...     cursor = cursor.advance()
            >>> text = Cursor("hello world", start_pos).slice_to(cursor.pos)

            Or store start cursor:
            >>> cursor = Cursor("hello world", 0)
            >>> start_cursor = cursor
            >>> while not cursor.is_eof and cursor.current != ' ':
            ...     cursor = cursor.advance()
            >>> text = start_cursor.slice_to(cursor.pos)
        """
        return self.source[self.pos : end_pos]

    def compute_line_col(self) -> tuple[int, int]:
        """Compute line and column for current position.

        Returns:
            (line, column) tuple (1-indexed, like text editors)

        Performance:
            O(n) where n = current position
            Only call for error reporting, not during normal parsing!

        Example:
            >>> source = "line1\\nline2\\nline3"
            >>> cursor = Cursor(source, 0)
            >>> cursor.compute_line_col()
            (1, 1)
            >>> cursor = Cursor(source, 6)  # Start of line2
            >>> cursor.compute_line_col()
            (2, 1)
            >>> cursor = Cursor(source, 8)  # Middle of line2
            >>> cursor.compute_line_col()
            (2, 3)
        """
        # Count newlines before current position
        lines_before = self.source[: self.pos].count("\n")
        line = lines_before + 1

        # Find last newline before current position
        last_newline = self.source.rfind("\n", 0, self.pos)
        # Use ternary for simple conditional assignment (Pythonic style)
        col = self.pos - last_newline if last_newline >= 0 else self.pos + 1

        return (line, col)

    @property
    def line_col(self) -> tuple[int, int]:
        """Line and column position as property for cleaner API.

        Property wrapper around compute_line_col() for Pythonic attribute access.
        Consistent with cursor.current, cursor.is_eof (properties).

        Returns:
            Tuple of (line_number, column_number), both 1-indexed

        Note:
            This is an O(n) operation. Cache result if calling multiple times.

        Example:
            >>> cursor = Cursor("hello\nworld", 7)
            >>> line, col = cursor.line_col
            >>> print(f"Position: {line}:{col}")
            Position: 2:2
        """
        return self.compute_line_col()


@dataclass(frozen=True, slots=True)
class ParseResult[T]:
    """Parser result containing parsed value and new cursor position.

    Type Parameters:
        T: The type of the parsed value

    Design:
        - Generic over result type T
        - Frozen for immutability
        - Contains BOTH parsed value AND new cursor
        - Parsers return Result[ParseResult[T], ParseError]

    Pattern:
        Every parser has signature:
            def parse_foo(cursor: Cursor) -> Result[ParseResult[Foo], ParseError]:
                ...
                return Success(ParseResult(parsed_value, new_cursor))

    Example:
        >>> cursor = Cursor("hello", 0)
        >>> # Parse single character
        >>> result = ParseResult('h', cursor.advance())
        >>> result.value
        'h'
        >>> result.cursor.pos
        1
        >>> result.cursor.current
        'e'
    """

    value: T
    cursor: Cursor


@dataclass(frozen=True, slots=True)
class ParseError:
    """Parse error with location and context.

    Design:
        - Stores cursor at error point (for line:column)
        - User-friendly message
        - Expected tokens list (for better errors)
        - Immutable for error chaining

    Example:
        >>> cursor = Cursor("hello", 2)
        >>> error = ParseError("Expected '}'", cursor, expected=['}', ']'])
        >>> error.format_error()
        "1:3: Expected '}' (expected: '}', ']')"
    """

    message: str
    cursor: Cursor
    expected: list[str] = field(default_factory=list)

    def format_error(self) -> str:
        """Format error with line:column.

        Returns:
            Formatted error string with location

        Example:
            >>> cursor = Cursor("hello\\nworld", 7)
            >>> error = ParseError("Expected ']'", cursor)
            >>> error.format_error()
            "2:2: Expected ']'"

            >>> error2 = ParseError("Unexpected", cursor, expected=[']', '}'])
            >>> error2.format_error()
            "2:2: Unexpected (expected: ']', '}')"
        """
        line, col = self.cursor.compute_line_col()
        error_msg = f"{line}:{col}: {self.message}"

        if self.expected:
            expected_str = ", ".join(f"'{e}'" for e in self.expected)
            error_msg += f" (expected: {expected_str})"

        return error_msg

    def format_with_context(self, context_lines: int = 2) -> str:
        """Format error with source context and pointer.

        Shows the problematic line and a caret pointing to the error location.

        Args:
            context_lines: Number of lines to show before/after error

        Returns:
            Multi-line formatted error with context

        Example:
            >>> source = "hello = Hi\\nworld = { $name\\nfoo = Bar"
            >>> cursor = Cursor(source, 26)  # After $name
            >>> error = ParseError("Expected '}'", cursor)
            >>> print(error.format_with_context())
            2:15: Expected '}'
            <BLANKLINE>
               1 | hello = Hi
               2 | world = { $name
                 |                ^
               3 | foo = Bar
        """
        line, col = self.cursor.compute_line_col()
        lines = self.cursor.source.split("\n")

        result_lines = [self.format_error(), ""]

        # Calculate line range to show
        start_line = max(1, line - context_lines)
        end_line = min(len(lines), line + context_lines)

        # Show context lines with line numbers
        for i in range(start_line, end_line + 1):
            line_num_str = f"{i:4} | "
            result_lines.append(line_num_str + lines[i - 1])

            # Add pointer on error line
            if i == line:
                pointer = " " * (len(line_num_str) + col - 1) + "^"
                result_lines.append(pointer)

        return "\n".join(result_lines)
