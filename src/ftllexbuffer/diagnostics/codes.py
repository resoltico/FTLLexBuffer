"""Diagnostic codes and data structures.

Defines error codes, source spans, and diagnostic messages.
Python 3.13+. Zero external dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DiagnosticCode(Enum):
    """Error codes with unique identifiers.

    Organized by category:
        1000-1999: Reference errors (missing messages, terms, variables)
        2000-2999: Resolution errors (runtime evaluation failures)
        3000-3999: Syntax errors (parser failures)
    """

    # Reference errors (1000-1999)
    MESSAGE_NOT_FOUND = 1001
    ATTRIBUTE_NOT_FOUND = 1002
    TERM_NOT_FOUND = 1003
    TERM_ATTRIBUTE_NOT_FOUND = 1004
    VARIABLE_NOT_PROVIDED = 1005
    MESSAGE_NO_VALUE = 1006

    # Resolution errors (2000-2999)
    CYCLIC_REFERENCE = 2001
    NO_VARIANTS = 2002
    FUNCTION_NOT_FOUND = 2003
    FUNCTION_FAILED = 2004
    UNKNOWN_EXPRESSION = 2005

    # Syntax errors (3000-3999)
    UNEXPECTED_EOF = 3001
    INVALID_CHARACTER = 3002
    EXPECTED_TOKEN = 3003


@dataclass(frozen=True, slots=True)
class SourceSpan:
    """Source code location for error reporting.

    Attributes:
        start: Starting byte offset
        end: Ending byte offset (exclusive)
        line: Line number (1-indexed)
        column: Column number (1-indexed)
    """

    start: int
    end: int
    line: int
    column: int


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """Structured diagnostic message.

    Inspired by Rust compiler diagnostics. Provides rich error information
    for both humans and tools (IDEs, LSP servers).

    Attributes:
        code: Unique error code
        message: Human-readable error description
        span: Source location (None for non-syntax errors)
        hint: Suggestion for fixing the error
        help_url: Documentation URL for this error
    """

    code: DiagnosticCode
    message: str
    span: SourceSpan | None = None
    hint: str | None = None
    help_url: str | None = None

    def format_error(self) -> str:
        """Format diagnostic like Rust compiler.

        Example output:
            error[MESSAGE_NOT_FOUND]: Message 'hello' not found
              --> line 5, column 10
              = help: Check that the message is defined in the loaded resources
              = note: see https://projectfluent.org/fluent/guide/messages.html

        Returns:
            Formatted error message
        """
        parts = [f"error[{self.code.name}]: {self.message}"]

        if self.span:
            parts.append(f"  --> line {self.span.line}, column {self.span.column}")

        if self.hint:
            parts.append(f"  = help: {self.hint}")

        if self.help_url:
            parts.append(f"  = note: see {self.help_url}")

        return "\n".join(parts)
