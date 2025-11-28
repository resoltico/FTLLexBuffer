"""Visitor pattern for AST traversal.

Enables tools to traverse and transform Fluent AST without modifying node classes.

NOTE: This module follows Python stdlib ast.NodeVisitor naming convention.
Methods are named visit_NodeName (PascalCase) rather than visit_node_name (snake_case).
This is an intentional architectural decision to maintain consistency with Python's
AST visitor pattern. See: https://docs.python.org/3/library/ast.html#ast.NodeVisitor

Python 3.13+.
"""
# pylint: disable=invalid-name  # visit_NodeName is stdlib convention

from __future__ import annotations

from dataclasses import replace
from typing import Any

from .ast import (
    Attribute,
    CallArguments,
    Comment,
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
    Variant,
)


class ASTVisitor:
    """Base visitor for traversing Fluent AST.

    Implement visit_NodeType methods to process specific node types.
    Use this to create:
    - Validators
    - Transformers
    - Code generators
    - Linters
    - Serializers

    Example:
        >>> class CountMessagesVisitor(ASTVisitor):
        ...     def __init__(self):
        ...         self.count = 0
        ...
        ...     def visit_Message(self, node: Message) -> Any:
        ...         self.count += 1
        ...         return self.generic_visit(node)
        ...
        >>> visitor = CountMessagesVisitor()
        >>> visitor.visit(resource)
        >>> print(visitor.count)
    """

    def visit(self, node: Any) -> Any:
        """Visit a node (dispatcher).

        Args:
            node: AST node to visit

        Returns:
            Result of visiting the node
        """
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, self.generic_visit)
        return method(node)

    def generic_visit(self, node: Any) -> Any:
        """Default visitor (traverses children).

        Override to change default behavior.

        Args:
            node: AST node to visit

        Returns:
            The node itself (identity)
        """
        return node

    # Resource and entries
    def visit_Resource(self, node: Resource) -> Any:
        """Visit Resource node."""
        for entry in node.entries:
            self.visit(entry)
        return self.generic_visit(node)

    def visit_Message(self, node: Message) -> Any:
        """Visit Message node."""
        self.visit(node.id)
        if node.value:
            self.visit(node.value)
        for attr in node.attributes:
            self.visit(attr)
        if node.comment:
            self.visit(node.comment)
        return self.generic_visit(node)

    def visit_Term(self, node: Term) -> Any:
        """Visit Term node."""
        self.visit(node.id)
        self.visit(node.value)
        for attr in node.attributes:
            self.visit(attr)
        if node.comment:
            self.visit(node.comment)
        return self.generic_visit(node)

    def visit_Attribute(self, node: Attribute) -> Any:
        """Visit Attribute node."""
        self.visit(node.id)
        self.visit(node.value)
        return self.generic_visit(node)

    def visit_Comment(self, node: Comment) -> Any:
        """Visit Comment node."""
        return self.generic_visit(node)

    def visit_Junk(self, node: Junk) -> Any:
        """Visit Junk node."""
        return self.generic_visit(node)

    # Patterns and elements
    def visit_Pattern(self, node: Pattern) -> Any:
        """Visit Pattern node."""
        for element in node.elements:
            self.visit(element)
        return self.generic_visit(node)

    def visit_TextElement(self, node: TextElement) -> Any:
        """Visit TextElement node."""
        return self.generic_visit(node)

    def visit_Placeable(self, node: Placeable) -> Any:
        """Visit Placeable node."""
        self.visit(node.expression)
        return self.generic_visit(node)

    # Expressions
    def visit_StringLiteral(self, node: StringLiteral) -> Any:
        """Visit StringLiteral node."""
        return self.generic_visit(node)

    def visit_NumberLiteral(self, node: NumberLiteral) -> Any:
        """Visit NumberLiteral node."""
        return self.generic_visit(node)

    def visit_MessageReference(self, node: MessageReference) -> Any:
        """Visit MessageReference node."""
        self.visit(node.id)
        if node.attribute:
            self.visit(node.attribute)
        return self.generic_visit(node)

    def visit_TermReference(self, node: TermReference) -> Any:
        """Visit TermReference node."""
        self.visit(node.id)
        if node.attribute:
            self.visit(node.attribute)
        if node.arguments:
            self.visit(node.arguments)
        return self.generic_visit(node)

    def visit_VariableReference(self, node: VariableReference) -> Any:
        """Visit VariableReference node."""
        self.visit(node.id)
        return self.generic_visit(node)

    def visit_FunctionReference(self, node: FunctionReference) -> Any:
        """Visit FunctionReference node."""
        self.visit(node.id)
        self.visit(node.arguments)
        return self.generic_visit(node)

    def visit_SelectExpression(self, node: SelectExpression) -> Any:
        """Visit SelectExpression node."""
        self.visit(node.selector)
        for variant in node.variants:
            self.visit(variant)
        return self.generic_visit(node)

    def visit_Variant(self, node: Variant) -> Any:
        """Visit Variant node."""
        self.visit(node.key)
        self.visit(node.value)
        return self.generic_visit(node)

    # Identifiers and arguments
    def visit_Identifier(self, node: Identifier) -> Any:
        """Visit Identifier node."""
        return self.generic_visit(node)

    def visit_CallArguments(self, node: CallArguments) -> Any:
        """Visit CallArguments node."""
        for arg in node.positional:
            self.visit(arg)
        for named_arg in node.named:
            self.visit(named_arg)
        return self.generic_visit(node)

    def visit_NamedArgument(self, node: NamedArgument) -> Any:
        """Visit NamedArgument node."""
        self.visit(node.name)
        self.visit(node.value)
        return self.generic_visit(node)


class ASTTransformer(ASTVisitor):
    """AST transformer for in-place modifications using Python 3.13+ features.

    Extends ASTVisitor to enable transforming AST nodes in-place. Each visit method
    can return:
    - The modified node (replaces original)
    - None (removes node from parent)
    - A list of nodes (replaces single node with multiple)

    Uses Python 3.13's pattern matching for elegant node type handling.

    Example - Remove all comments:
        >>> class RemoveCommentsTransformer(ASTTransformer):
        ...     def visit_Comment(self, node: Comment) -> None:
        ...         return None  # Remove comments
        ...
        >>> transformer = RemoveCommentsTransformer()
        >>> cleaned_resource = transformer.transform(resource)

    Example - Rename all variables:
        >>> class RenameVariablesTransformer(ASTTransformer):
        ...     def __init__(self, mapping: dict[str, str]):
        ...         self.mapping = mapping
        ...
        ...     def visit_VariableReference(self, node: VariableReference) -> VariableReference:
        ...         if node.id.name in self.mapping:
        ...             return VariableReference(
        ...                 id=Identifier(name=self.mapping[node.id.name])
        ...             )
        ...         return node
        ...
        >>> transformer = RenameVariablesTransformer({"old": "new"})
        >>> modified_resource = transformer.transform(resource)

    Example - Expand messages (1 → multiple):
        >>> class ExpandPluralsTransformer(ASTTransformer):
        ...     def visit_Message(self, node: Message) -> list[Message]:
        ...         # Generate multiple messages from select expressions
        ...         return [node, expanded_variant_1, expanded_variant_2]
        ...
        >>> transformer = ExpandPluralsTransformer()
        >>> expanded_resource = transformer.transform(resource)
    """

    def transform(self, node: Any) -> Any:
        """Transform an AST node or tree.

        This is the main entry point for transformations.

        Args:
            node: AST node to transform

        Returns:
            Transformed node (may be different type, None, or list)
        """
        return self.visit(node)

    def generic_visit(self, node: Any) -> Any:
        """Transform node children (default behavior).

        Recursively transforms all child nodes. Uses dataclasses.replace()
        to create new immutable nodes (AST nodes are frozen).

        Args:
            node: AST node to transform

        Returns:
            New node with transformed children
        """
        # Use pattern matching for type-safe child transformation
        match node:
            case Resource(entries=entries):
                return replace(node, entries=self._transform_list(entries))
            case Message(id=id_node, value=value, attributes=attrs, comment=comment):
                return replace(
                    node,
                    id=self.visit(id_node),
                    value=self.visit(value) if value else None,
                    attributes=self._transform_list(attrs),
                    comment=self.visit(comment) if comment else None,
                )
            case Term(id=id_node, value=value, attributes=attrs, comment=comment):
                return replace(
                    node,
                    id=self.visit(id_node),
                    value=self.visit(value),
                    attributes=self._transform_list(attrs),
                    comment=self.visit(comment) if comment else None,
                )
            case Pattern(elements=elements):
                return replace(node, elements=self._transform_list(elements))
            case Placeable(expression=expr):
                return replace(node, expression=self.visit(expr))
            case SelectExpression(selector=selector, variants=variants):
                return replace(
                    node,
                    selector=self.visit(selector),
                    variants=self._transform_list(variants),
                )
            case Variant(key=key, value=value):
                return replace(node, key=self.visit(key), value=self.visit(value))
            case FunctionReference(id=id_node, arguments=args):
                # FunctionReference.arguments is not optional - always present
                return replace(
                    node,
                    id=self.visit(id_node),
                    arguments=self.visit(args),
                )
            case MessageReference(id=id_node, attribute=attr):
                return replace(
                    node,
                    id=self.visit(id_node),
                    attribute=self.visit(attr) if attr else None,
                )
            case TermReference(id=id_node, attribute=attr, arguments=args):
                return replace(
                    node,
                    id=self.visit(id_node),
                    attribute=self.visit(attr) if attr else None,
                    arguments=self.visit(args) if args else None,
                )
            case VariableReference(id=id_node):
                return replace(node, id=self.visit(id_node))
            case CallArguments(positional=pos, named=named):
                return replace(
                    node,
                    positional=self._transform_list(pos),
                    named=self._transform_list(named),
                )
            case NamedArgument(name=name, value=value):
                return replace(node, name=self.visit(name), value=self.visit(value))
            case Attribute(id=id_node, value=value):
                return replace(node, id=self.visit(id_node), value=self.visit(value))
            case _:
                # Leaf nodes (Identifier, TextElement, StringLiteral, NumberLiteral, Comment, Junk)
                # Return as-is (immutable)
                return node

    def _transform_list(self, nodes: tuple[Any, ...]) -> tuple[Any, ...]:
        """Transform a tuple of nodes.

        Handles node removal (None) and expansion (lists) using Python 3.13 features.
        AST nodes use tuples (immutable) instead of lists.

        Args:
            nodes: Tuple of AST nodes

        Returns:
            Transformed tuple (flattened, with None removed)
        """
        result: list[Any] = []
        for node in nodes:
            transformed = self.visit(node)

            # Pattern match on transformation result
            match transformed:
                case None:
                    # Remove node (don't add to result)
                    continue
                case list():
                    # Expand node (add all items)
                    result.extend(transformed)
                case _:
                    # Replace node (add single item)
                    result.append(transformed)

        return tuple(result)
