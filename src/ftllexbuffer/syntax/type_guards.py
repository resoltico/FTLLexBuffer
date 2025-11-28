"""Type guard functions for AST node type narrowing.

Provides TypeIs-based type guards for mypy to narrow union types safely.
Python 3.13+ with TypeIs support (PEP 742).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeIs

if TYPE_CHECKING:
    from ftllexbuffer.syntax.ast import (
        Comment,
        Junk,
        Message,
        Placeable,
        Term,
        TextElement,
    )

__all__ = [
    "has_value",
    "is_comment",
    "is_junk",
    "is_message",
    "is_placeable",
    "is_term",
    "is_text_element",
]


def is_message(entry: object) -> TypeIs[Message]:
    """Check if entry is a Message node.

    Args:
        entry: AST entry to check

    Returns:
        True if entry is Message, False otherwise

    Example:
        >>> from ftllexbuffer.syntax.ast import Message, Term
        >>> if is_message(entry):
        ...     entry.id.name  # Type-safe: mypy knows entry is Message
    """
    from ftllexbuffer.syntax.ast import Message

    return isinstance(entry, Message)


def is_term(entry: object) -> TypeIs[Term]:
    """Check if entry is a Term node.

    Args:
        entry: AST entry to check

    Returns:
        True if entry is Term, False otherwise
    """
    from ftllexbuffer.syntax.ast import Term

    return isinstance(entry, Term)


def is_comment(entry: object) -> TypeIs[Comment]:
    """Check if entry is a Comment node.

    Args:
        entry: AST entry to check

    Returns:
        True if entry is Comment, False otherwise
    """
    from ftllexbuffer.syntax.ast import Comment

    return isinstance(entry, Comment)


def is_junk(entry: object) -> TypeIs[Junk]:
    """Check if entry is a Junk node.

    Args:
        entry: AST entry to check

    Returns:
        True if entry is Junk, False otherwise
    """
    from ftllexbuffer.syntax.ast import Junk

    return isinstance(entry, Junk)


def is_text_element(element: object) -> TypeIs[TextElement]:
    """Check if pattern element is TextElement.

    Args:
        element: Pattern element to check

    Returns:
        True if element is TextElement, False otherwise

    Example:
        >>> if is_text_element(element):
        ...     element.value  # Type-safe: mypy knows it has .value attribute
    """
    from ftllexbuffer.syntax.ast import TextElement

    return isinstance(element, TextElement)


def is_placeable(element: object) -> TypeIs[Placeable]:
    """Check if pattern element is Placeable.

    Args:
        element: Pattern element to check

    Returns:
        True if element is Placeable, False otherwise

    Example:
        >>> if is_placeable(element):
        ...     element.expression  # Type-safe: mypy knows it has .expression
    """
    from ftllexbuffer.syntax.ast import Placeable

    return isinstance(element, Placeable)


def has_value(msg_or_term: object) -> TypeIs[Message | Term]:
    """Check if message/term has a value pattern (not None).

    Args:
        msg_or_term: Message or Term to check

    Returns:
        True if has non-None value, False otherwise

    Note:
        This narrows Pattern | None to Pattern by checking msg.value is not None.
        After this guard, mypy knows msg.value.elements is safe to access.
    """
    from ftllexbuffer.syntax.ast import Message, Term

    if isinstance(msg_or_term, (Message, Term)):
        return msg_or_term.value is not None
    return False
