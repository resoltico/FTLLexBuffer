"""Serialize Fluent AST back to FTL syntax.

Converts AST nodes to FTL source code. Useful for:
- Formatters
- Code generators
- Property-based testing (roundtrip: parse → serialize → parse)

Python 3.13+.
"""

from ftllexbuffer.enums import CommentType

from .ast import (
    Attribute,
    CallArguments,
    Comment,
    Expression,
    FunctionReference,
    Identifier,
    Junk,
    Message,
    MessageReference,
    NamedArgument,
    NumberLiteral,
    Pattern,
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

    Thread-safe serializer with no mutable instance state.
    All serialization state is local to the serialize() call.

    Usage:
        >>> from ftllexbuffer.syntax import parse, FluentSerializer
        >>> ast = parse("hello = Hello, world!")
        >>> serializer = FluentSerializer()
        >>> ftl = serializer.serialize(ast)
        >>> print(ftl)
        hello = Hello, world!
    """

    def serialize(self, resource: Resource) -> str:
        """Serialize Resource to FTL string.

        Pure function - builds output locally without mutating instance state.
        Thread-safe and reusable.

        Args:
            resource: Resource AST node

        Returns:
            FTL source code
        """
        output: list[str] = []
        self._serialize_resource(resource, output)
        return "".join(output)

    def _serialize_resource(self, node: Resource, output: list[str]) -> None:
        """Serialize Resource to output list."""
        for i, entry in enumerate(node.entries):
            if i > 0:
                output.append("\n")
            self._serialize_entry(entry, output)

    def _serialize_entry(
        self,
        entry: Message | Term | Comment | Junk,
        output: list[str],
    ) -> None:
        """Serialize a top-level entry."""
        match entry:
            case Message():
                self._serialize_message(entry, output)
            case Term():
                self._serialize_term(entry, output)
            case Comment():
                self._serialize_comment(entry, output)
            case Junk():
                self._serialize_junk(entry, output)

    def _serialize_message(self, node: Message, output: list[str]) -> None:
        """Serialize Message."""
        # Comment if present
        if node.comment:
            self._serialize_comment(node.comment, output)
            output.append("\n")

        # Message ID
        output.append(node.id.name)

        # Value
        if node.value:
            output.append(" = ")
            self._serialize_pattern(node.value, output)

        # Attributes
        for attr in node.attributes:
            output.append("\n    ")
            self._serialize_attribute(attr, output)

        output.append("\n")

    def _serialize_term(self, node: Term, output: list[str]) -> None:
        """Serialize Term."""
        # Comment if present
        if node.comment:
            self._serialize_comment(node.comment, output)
            output.append("\n")

        # Term ID (with leading -)
        output.append(f"-{node.id.name} = ")

        # Value
        self._serialize_pattern(node.value, output)

        # Attributes
        for attr in node.attributes:
            output.append("\n    ")
            self._serialize_attribute(attr, output)

        output.append("\n")

    def _serialize_attribute(self, node: Attribute, output: list[str]) -> None:
        """Serialize Attribute."""
        output.append(f".{node.id.name} = ")
        self._serialize_pattern(node.value, output)

    def _serialize_comment(self, node: Comment, output: list[str]) -> None:
        """Serialize Comment."""
        if node.type is CommentType.COMMENT:
            prefix = "#"
        elif node.type is CommentType.GROUP:
            prefix = "##"
        else:  # CommentType.RESOURCE
            prefix = "###"

        lines = node.content.split("\n")
        for line in lines:
            output.append(f"{prefix} {line}\n")

    def _serialize_junk(self, node: Junk, output: list[str]) -> None:
        """Serialize Junk (keep as-is)."""
        output.append(node.content)
        output.append("\n")

    def _serialize_pattern(self, pattern: Pattern, output: list[str]) -> None:
        """Serialize Pattern elements."""
        for element in pattern.elements:
            if isinstance(element, TextElement):
                output.append(element.value)
            elif isinstance(element, Placeable):
                output.append("{ ")
                self._serialize_expression(element.expression, output)
                output.append(" }")

    def _serialize_expression(self, expr: Expression, output: list[str]) -> None:
        """Serialize Expression nodes using structural pattern matching."""
        match expr:
            case StringLiteral():
                # Escape special characters
                escaped = expr.value.replace("\\", "\\\\").replace('"', '\\"')
                output.append(f'"{escaped}"')

            case NumberLiteral():
                output.append(expr.raw)

            case VariableReference():
                output.append(f"${expr.id.name}")

            case MessageReference():
                output.append(expr.id.name)
                if expr.attribute:
                    output.append(f".{expr.attribute.name}")

            case TermReference():
                output.append(f"-{expr.id.name}")
                if expr.attribute:
                    output.append(f".{expr.attribute.name}")
                if expr.arguments:
                    self._serialize_call_arguments(expr.arguments, output)

            case FunctionReference():
                output.append(expr.id.name)
                self._serialize_call_arguments(expr.arguments, output)

            case SelectExpression():
                self._serialize_select_expression(expr, output)

    def _serialize_call_arguments(self, args: CallArguments, output: list[str]) -> None:
        """Serialize CallArguments."""
        output.append("(")

        # Positional arguments
        for i, arg in enumerate(args.positional):
            if i > 0:
                output.append(", ")
            self._serialize_expression(arg, output)

        # Named arguments
        named_arg: NamedArgument
        for i, named_arg in enumerate(args.named):
            if i > 0 or args.positional:
                output.append(", ")
            output.append(f"{named_arg.name.name}: ")
            self._serialize_expression(named_arg.value, output)

        output.append(")")

    def _serialize_select_expression(
        self,
        expr: SelectExpression,
        output: list[str],
    ) -> None:
        """Serialize SelectExpression."""
        self._serialize_expression(expr.selector, output)
        output.append(" ->")

        for variant in expr.variants:
            output.append("\n   ")
            if variant.default:
                output.append("*")
            output.append("[")

            # Variant key (Identifier or NumberLiteral)
            if isinstance(variant.key, Identifier):
                output.append(variant.key.name)
            else:  # NumberLiteral
                output.append(variant.key.raw)

            output.append("] ")
            self._serialize_pattern(variant.value, output)

        output.append("\n")


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
