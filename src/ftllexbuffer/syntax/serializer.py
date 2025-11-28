"""Serialize Fluent AST back to FTL syntax.

Converts AST nodes to FTL source code. Useful for:
- Formatters
- Code generators
- Property-based testing (roundtrip: parse → serialize → parse)

Python 3.13+.
"""

from __future__ import annotations

from typing import Any

from .ast import (
    Attribute,
    Comment,
    FunctionReference,
    Identifier,
    Junk,
    Message,
    MessageReference,
    NumberLiteral,
    Placeable,
    Resource,
    SelectExpression,
    StringLiteral,
    Term,
    TermReference,
    TextElement,
    VariableReference,
)
from .visitor import ASTVisitor


class FluentSerializer(ASTVisitor):
    """Converts AST back to FTL source string.

    Usage:
        >>> from ftllexbuffer.syntax import parse, FluentSerializer
        >>> ast = parse("hello = Hello, world!")
        >>> serializer = FluentSerializer()
        >>> ftl = serializer.serialize(ast)
        >>> print(ftl)
        hello = Hello, world!
    """

    def __init__(self) -> None:
        """Initialize serializer."""
        self._output: list[str] = []

    def serialize(self, resource: Resource) -> str:
        """Serialize Resource to FTL string.

        Args:
            resource: Resource AST node

        Returns:
            FTL source code
        """
        self._output = []
        self.visit(resource)
        return "".join(self._output)

    def visit_Resource(self, node: Resource) -> None:
        """Serialize Resource."""
        for i, entry in enumerate(node.entries):
            if i > 0:
                self._output.append("\n")
            self.visit(entry)

    def visit_Message(self, node: Message) -> None:
        """Serialize Message."""
        # Comment if present
        if node.comment:
            self.visit(node.comment)
            self._output.append("\n")

        # Message ID
        self._output.append(node.id.name)

        # Value
        if node.value:
            self._output.append(" = ")
            self._visit_pattern(node.value)

        # Attributes
        for attr in node.attributes:
            self._output.append("\n    ")
            self.visit(attr)

        self._output.append("\n")

    def visit_Term(self, node: Term) -> None:
        """Serialize Term."""
        # Comment if present
        if node.comment:
            self.visit(node.comment)
            self._output.append("\n")

        # Term ID (with leading -)
        self._output.append(f"-{node.id.name} = ")

        # Value
        self._visit_pattern(node.value)

        # Attributes
        for attr in node.attributes:
            self._output.append("\n    ")
            self.visit(attr)

        self._output.append("\n")

    def visit_Attribute(self, node: Attribute) -> None:
        """Serialize Attribute."""
        self._output.append(f".{node.id.name} = ")
        self._visit_pattern(node.value)

    def visit_Comment(self, node: Comment) -> None:
        """Serialize Comment."""
        prefix = "#" if node.type == "comment" else ("##" if node.type == "group" else "###")
        lines = node.content.split("\n")
        for line in lines:
            self._output.append(f"{prefix} {line}\n")

    def visit_Junk(self, node: Junk) -> None:
        """Serialize Junk (keep as-is)."""
        self._output.append(node.content)
        self._output.append("\n")

    def _visit_pattern(self, pattern: Any) -> None:
        """Visit Pattern elements."""
        for element in pattern.elements:
            if isinstance(element, TextElement):
                self._output.append(element.value)
            elif isinstance(element, Placeable):
                self._output.append("{ ")
                self._visit_expression(element.expression)
                self._output.append(" }")

    def _visit_expression(self, expr: Any) -> None:
        """Visit Expression nodes using structural pattern matching."""
        match expr:
            case StringLiteral():
                # Escape special characters
                escaped = expr.value.replace("\\", "\\\\").replace('"', '\\"')
                self._output.append(f'"{escaped}"')

            case NumberLiteral():
                self._output.append(expr.value)

            case VariableReference():
                self._output.append(f"${expr.id.name}")

            case MessageReference():
                self._output.append(expr.id.name)
                if expr.attribute:
                    self._output.append(f".{expr.attribute.name}")

            case TermReference():
                self._output.append(f"-{expr.id.name}")
                if expr.attribute:
                    self._output.append(f".{expr.attribute.name}")
                if expr.arguments:
                    self._visit_call_arguments(expr.arguments)

            case FunctionReference():
                self._output.append(expr.id.name)
                self._visit_call_arguments(expr.arguments)

            case SelectExpression():
                self._visit_select_expression(expr)

    def _visit_call_arguments(self, args: Any) -> None:
        """Visit CallArguments."""
        self._output.append("(")

        # Positional arguments
        for i, arg in enumerate(args.positional):
            if i > 0:
                self._output.append(", ")
            self._visit_expression(arg)

        # Named arguments
        for i, arg in enumerate(args.named):
            if i > 0 or args.positional:
                self._output.append(", ")
            self._output.append(f"{arg.name.name}: ")
            self._visit_expression(arg.value)

        self._output.append(")")

    def _visit_select_expression(self, expr: SelectExpression) -> None:
        """Visit SelectExpression."""
        self._visit_expression(expr.selector)
        self._output.append(" ->")

        for variant in expr.variants:
            self._output.append("\n   ")
            if variant.default:
                self._output.append("*")
            self._output.append("[")

            # Variant key (Identifier or NumberLiteral)
            if isinstance(variant.key, Identifier):
                self._output.append(variant.key.name)
            else:  # NumberLiteral
                self._output.append(variant.key.value)

            self._output.append("] ")
            self._visit_pattern(variant.value)

        self._output.append("\n")


def serialize(resource: Resource) -> str:
    """Serialize Resource to FTL string.

    Convenience function for FluentSerializer.serialize().

    Args:
        resource: Resource AST node

    Returns:
        FTL source code

    Example:
        >>> from ftllexbuffer.syntax import parse, serialize
        >>> ast = parse("hello = Hello, world!")
        >>> ftl = serialize(ast)
        >>> assert ftl == "hello = Hello, world!\\n"
    """
    serializer = FluentSerializer()
    return serializer.serialize(resource)
