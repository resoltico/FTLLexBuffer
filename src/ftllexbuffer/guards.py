"""Type guard functions for Fluent AST nodes.

Provides standalone TypeIs functions for runtime type narrowing.
These wrap the .guard() static methods on AST node classes.

NOTE: This module uses runtime imports to avoid circular dependencies.
Guards are imported by syntax modules, so we can't import syntax at module level.
This is an intentional architectural decision for dependency management.

PEP 742 TypeIs support (Python 3.13+).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeIs

if TYPE_CHECKING:
    from .syntax import (
        Identifier,
        NumberLiteral,
        Placeable,
        SelectExpression,
        TextElement,
        VariableReference,
    )


def is_text_element(elem: object) -> TypeIs[TextElement]:
    """Type guard for TextElement.

    Args:
        elem: Object to check

    Returns:
        True if elem is TextElement, narrowing type for mypy
    """
    from .syntax import TextElement

    return TextElement.guard(elem)


def is_placeable(elem: object) -> TypeIs[Placeable]:
    """Type guard for Placeable.

    Args:
        elem: Object to check

    Returns:
        True if elem is Placeable, narrowing type for mypy
    """
    from .syntax import Placeable

    return Placeable.guard(elem)


def is_variable_reference(expr: object) -> TypeIs[VariableReference]:
    """Type guard for VariableReference.

    Args:
        expr: Object to check

    Returns:
        True if expr is VariableReference, narrowing type for mypy
    """
    from .syntax import VariableReference

    return VariableReference.guard(expr)


def is_select_expression(expr: object) -> TypeIs[SelectExpression]:
    """Type guard for SelectExpression.

    Args:
        expr: Object to check

    Returns:
        True if expr is SelectExpression, narrowing type for mypy
    """
    from .syntax import SelectExpression

    return SelectExpression.guard(expr)


def is_identifier(key: object) -> TypeIs[Identifier]:
    """Type guard for Identifier.

    Args:
        key: Object to check

    Returns:
        True if key is Identifier, narrowing type for mypy
    """
    from .syntax import Identifier

    return Identifier.guard(key)


def is_number_literal(key: object) -> TypeIs[NumberLiteral]:
    """Type guard for NumberLiteral.

    Args:
        key: Object to check

    Returns:
        True if key is NumberLiteral, narrowing type for mypy
    """
    from .syntax import NumberLiteral

    return NumberLiteral.guard(key)


__all__ = [
    "is_identifier",
    "is_number_literal",
    "is_placeable",
    "is_select_expression",
    "is_text_element",
    "is_variable_reference",
]
