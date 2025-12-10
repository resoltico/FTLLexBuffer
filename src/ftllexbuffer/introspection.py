"""Variable introspection for FTL messages using Python 3.13 type system.

This module provides best-in-class introspection capabilities for analyzing
FTL message patterns and extracting metadata about variable usage, function calls,
and message references.

Key features:
- Type-safe results using Python 3.13's TypeIs for runtime narrowing
- Zero-allocation frozen dataclasses with slots for metadata
- Pattern matching for elegant AST traversal
- Comprehensive variable, function, and reference extraction

Python 3.13+.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .enums import ReferenceKind, VariableContext
from .syntax.ast import (
    FunctionReference,
    Message,
    MessageReference,
    Pattern,
    Placeable,
    SelectExpression,
    Term,
    TermReference,
    TextElement,
    VariableReference,
    Variant,
)
from .syntax.visitor import ASTVisitor

if TYPE_CHECKING:
    from .syntax.ast import Expression, InlineExpression, PatternElement


# ==============================================================================
# INTROSPECTION METADATA (Frozen Dataclasses with Slots)
# ==============================================================================


@dataclass(frozen=True, slots=True)
class VariableInfo:
    """Immutable metadata about a variable reference in a message.


    Uses Python 3.13's frozen dataclass with slots for zero-allocation storage.
    """

    name: str
    """Variable name (without $ prefix)."""

    context: VariableContext
    """Context where variable appears."""


@dataclass(frozen=True, slots=True)
class FunctionCallInfo:
    """Immutable metadata about a function call in a message."""

    name: str
    """Function name (e.g., 'NUMBER', 'DATETIME')."""

    positional_args: tuple[str, ...]
    """Positional argument variable names."""

    named_args: frozenset[str]
    """Named argument keys."""


@dataclass(frozen=True, slots=True)
class ReferenceInfo:
    """Immutable metadata about message/term references.

    """

    id: str
    """Referenced message or term ID."""

    kind: ReferenceKind
    """Reference type."""

    attribute: str | None
    """Attribute name if accessing an attribute."""


@dataclass(frozen=True, slots=True)
class MessageIntrospection:
    """Complete introspection result for a message.

    This is the primary result type returned by the introspection API.
    All fields are immutable and use slots for optimal memory usage.
    """

    message_id: str
    """Message identifier."""

    variables: frozenset[VariableInfo]
    """All variables referenced in the message."""

    functions: frozenset[FunctionCallInfo]
    """All function calls in the message."""

    references: frozenset[ReferenceInfo]
    """All message/term references."""

    has_selectors: bool
    """Whether message uses select expressions."""

    def get_variable_names(self) -> frozenset[str]:
        """Get set of variable names (for backward compatibility).

        Returns:
            Frozen set of variable names without $ prefix.
        """
        return frozenset(var.name for var in self.variables)

    def requires_variable(self, name: str) -> bool:
        """Check if message requires a specific variable.

        Args:
            name: Variable name (without $ prefix)

        Returns:
            True if variable is used in the message
        """
        return any(var.name == name for var in self.variables)

    def get_function_names(self) -> frozenset[str]:
        """Get set of function names used in the message.

        Returns:
            Frozen set of function names (e.g., {'NUMBER', 'DATETIME'})
        """
        return frozenset(func.name for func in self.functions)


# ==============================================================================
# AST VISITOR FOR VARIABLE EXTRACTION
# ==============================================================================


class IntrospectionVisitor(ASTVisitor):
    """AST visitor that extracts variables, functions, and references from messages.

    Uses Python 3.13's pattern matching for elegant AST traversal and TypeIs
    for type-safe runtime narrowing.

    Note on Traversal (v0.8.0):
        This visitor intentionally overrides pattern traversal instead of calling
        super().visit_Pattern(). The FTL specification's Pattern structure is stable
        (elements only), and our introspection logic requires specific handling
        of each element type. Calling super() would invoke generic_visit() which
        is a no-op for this visitor pattern.
    """

    def __init__(self) -> None:
        """Initialize visitor with empty result sets."""
        super().__init__()
        self.variables: set[VariableInfo] = set()
        self.functions: set[FunctionCallInfo] = set()
        self.references: set[ReferenceInfo] = set()
        self.has_selectors: bool = False
        self._context: VariableContext = VariableContext.PATTERN

    def visit_Pattern(self, node: Pattern) -> None:
        """Visit pattern and extract variables from all elements.

        Note: Intentionally does NOT call super().visit_Pattern(node) as this
        visitor implements custom traversal logic. The Pattern node structure
        is stable per FTL specification (only has 'elements' children).
        """
        for element in node.elements:
            self._visit_pattern_element(element)

    def _visit_pattern_element(self, element: "PatternElement") -> None:
        """Visit a pattern element (TextElement or Placeable)."""
        match element:
            case TextElement():
                pass  # No variables in text
            case Placeable(expression=expr):
                self._visit_expression(expr)

    def _visit_expression(self, expr: "Expression | InlineExpression") -> None:
        """Visit an expression and extract metadata using pattern matching."""
        # Use Python 3.13 TypeIs for type-safe narrowing via static .guard() methods
        if VariableReference.guard(expr):
            self.variables.add(VariableInfo(name=expr.id.name, context=self._context))

        elif FunctionReference.guard(expr):
            self._extract_function_call(expr)

        elif MessageReference.guard(expr):
            attr_name = expr.attribute.name if expr.attribute else None
            self.references.add(
                ReferenceInfo(id=expr.id.name, kind=ReferenceKind.MESSAGE, attribute=attr_name)
            )

        elif TermReference.guard(expr):
            attr_name = expr.attribute.name if expr.attribute else None
            self.references.add(
                ReferenceInfo(id=expr.id.name, kind=ReferenceKind.TERM, attribute=attr_name)
            )

        elif SelectExpression.guard(expr):
            self.has_selectors = True
            # Visit selector
            old_context = self._context
            self._context = VariableContext.SELECTOR
            self._visit_expression(expr.selector)
            self._context = old_context

            # Visit variants
            for variant in expr.variants:
                self._visit_variant(variant)

    def _extract_function_call(self, func: FunctionReference) -> None:
        """Extract function call information including arguments."""
        positional: list[str] = []
        named: set[str] = set()

        if func.arguments:
            # Extract positional arguments (must be VariableReferences)
            for pos_arg in func.arguments.positional:
                if VariableReference.guard(pos_arg):
                    positional.append(pos_arg.id.name)
                    # Also track as variable usage
                    self.variables.add(
                        VariableInfo(name=pos_arg.id.name, context=VariableContext.FUNCTION_ARG)
                    )

            # Extract named argument keys
            for named_arg in func.arguments.named:
                named.add(named_arg.name.name)
                # Extract variable from value if it's a VariableReference
                if VariableReference.guard(named_arg.value):
                    var_info = VariableInfo(
                        name=named_arg.value.id.name, context=VariableContext.FUNCTION_ARG
                    )
                    self.variables.add(var_info)

        func_info = FunctionCallInfo(
            name=func.id.name, positional_args=tuple(positional), named_args=frozenset(named)
        )
        self.functions.add(func_info)

    def _visit_variant(self, variant: Variant) -> None:
        """Visit a select variant and extract variables from its pattern."""
        old_context = self._context
        self._context = VariableContext.VARIANT
        self.visit_Pattern(variant.value)
        self._context = old_context


# ==============================================================================
# PUBLIC API
# ==============================================================================


def introspect_message(message: Message) -> MessageIntrospection:
    """Introspect a message and extract all metadata.

    This is the primary entry point for message introspection.

    Args:
        message: Message AST node to introspect

    Returns:
        Complete introspection result with variables, functions, and references

    Example:
        >>> from ftllexbuffer import FluentParserV1
        >>> parser = FluentParserV1()
        >>> resource = parser.parse("greeting = Hello, { $name }!")
        >>> msg = resource.entries[0]
        >>> info = introspect_message(msg)
        >>> print(info.get_variable_names())
        frozenset({'name'})
    """
    if not isinstance(message, (Message, Term)):
        msg = f"Expected Message or Term, got {type(message).__name__}"  # type: ignore[unreachable]
        raise TypeError(msg)

    visitor = IntrospectionVisitor()

    # Visit message value pattern
    if message.value:
        visitor.visit_Pattern(message.value)

    # Visit attribute patterns
    for attr in message.attributes:
        visitor.visit_Pattern(attr.value)

    return MessageIntrospection(
        message_id=message.id.name,
        variables=frozenset(visitor.variables),
        functions=frozenset(visitor.functions),
        references=frozenset(visitor.references),
        has_selectors=visitor.has_selectors,
    )


def extract_variables(message: Message) -> frozenset[str]:
    """Extract variable names from a message (simplified API).

    This is a convenience function for the most common use case.

    Args:
        message: Message AST node

    Returns:
        Frozen set of variable names (without $ prefix)

    Example:
        >>> vars = extract_variables(msg)
        >>> assert 'name' in vars
    """
    return introspect_message(message).get_variable_names()
