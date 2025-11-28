"""Fluent exception hierarchy with structured diagnostics.

Integrates with diagnostic codes for Rust/Elm-inspired error messages.
All exceptions store Diagnostic objects for rich error information.

Python 3.13+. Zero external dependencies.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .codes import Diagnostic


class FluentError(Exception):
    """Base exception for all Fluent errors.

    Attributes:
        diagnostic: Structured diagnostic information (optional)
    """

    def __init__(self, message: str | Diagnostic) -> None:
        """Initialize FluentError.

        Args:
            message: Error message string OR Diagnostic object
        """
        # Import at runtime to avoid circular dependency
        from .codes import Diagnostic

        if isinstance(message, Diagnostic):
            self.diagnostic: Diagnostic | None = message
            super().__init__(message.format_error())
        else:
            self.diagnostic = None
            super().__init__(message)


class FluentSyntaxError(FluentError):
    """FTL syntax error during parsing.

    Parser continues after syntax errors (robustness principle).
    Errors become Junk entries in AST.
    """


class FluentReferenceError(FluentError):
    """Unknown message or term reference.

    Raised when resolving a message that references non-existent ID.
    Fallback: return message ID as string.
    """


class FluentResolutionError(FluentError):
    """Runtime error during message resolution.

    Examples:
    - Division by zero in expression
    - Type mismatch
    - Invalid function arguments

    Fallback: return partial result up to error point.
    """


class FluentCyclicReferenceError(FluentReferenceError):
    """Cyclic reference detected (message references itself).

    Example:
        hello = { hello }  ← Infinite loop!

    Fallback: return message ID.
    """
