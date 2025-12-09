"""Enumerations for FTLLexBuffer type-safe constants.

v0.9.0: Replaces magic strings with proper enums for type safety and IDE support.

Python 3.13+.
"""

from __future__ import annotations

from enum import Enum


class CommentType(Enum):
    """Type of FTL comment.

    v0.9.0: Replaces str literals in Comment.type.
    """

    COMMENT = "comment"
    """Standalone comment: # This is a comment"""

    GROUP = "group"
    """Group comment: ## Group Title"""

    RESOURCE = "resource"
    """Resource comment: ### Resource Description"""

    def __str__(self) -> str:
        """Return enum value for serialization."""
        return self.value


class VariableContext(Enum):
    """Context where a variable reference appears.

    v0.9.0: Replaces str literals in VariableInfo.context.
    """

    PATTERN = "pattern"
    """Variable in message pattern: msg = Hello { $name }"""

    SELECTOR = "selector"
    """Variable in select expression selector: { $count -> }"""

    VARIANT = "variant"
    """Variable in select variant: [one] { $count } item"""

    FUNCTION_ARG = "function_arg"
    """Variable in function argument: { NUMBER($value) }"""

    def __str__(self) -> str:
        """Return enum value for serialization."""
        return self.value


class ReferenceKind(Enum):
    """Kind of reference (message or term).

    v0.9.0: Replaces str literals in ReferenceInfo.kind.
    """

    MESSAGE = "message"
    """Reference to a message: { message-id }"""

    TERM = "term"
    """Reference to a term: { -term-id }"""

    def __str__(self) -> str:
        """Return enum value for serialization."""
        return self.value


__all__ = [
    "CommentType",
    "ReferenceKind",
    "VariableContext",
]
