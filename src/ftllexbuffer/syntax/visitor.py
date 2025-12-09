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

from dataclasses import fields, replace
from typing import TYPE_CHECKING

from .ast import (
    ASTNode,
    Attribute,
    CallArguments,
    FunctionReference,
    Message,
    MessageReference,
    NamedArgument,
    Pattern,
    Placeable,
    Resource,
    SelectExpression,
    Term,
    TermReference,
    VariableReference,
    Variant,
)

if TYPE_CHECKING:
    pass


class ASTVisitor:
    """Base visitor for traversing Fluent AST.

    Follows stdlib ast.NodeVisitor convention: generic_visit() automatically
    traverses all child nodes. Override visit_NodeType methods to add custom
    behavior.

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
        ...     def visit_Message(self, node: Message) -> ASTNode:
        ...         self.count += 1
        ...         return self.generic_visit(node)  # Traverse children
        ...
        >>> visitor = CountMessagesVisitor()
        >>> visitor.visit(resource)
        >>> print(visitor.count)
    """

    def visit(self, node: ASTNode) -> ASTNode:
        """Visit a node (dispatcher).

        Args:
            node: AST node to visit

        Returns:
            Result of visiting the node
        """
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, self.generic_visit)
        return method(node)

    def generic_visit(self, node: ASTNode) -> ASTNode:
        """Default visitor (traverses children).

        Follows stdlib ast.NodeVisitor convention: automatically traverses
        all child nodes. Override visit_* methods to customize behavior.

        Args:
            node: AST node to visit

        Returns:
            The node itself (identity)
        """
        # Introspect dataclass fields to find and visit children
        for field in fields(node):
            value = getattr(node, field.name)

            # Skip None values and non-node fields (str, int, bool, etc.)
            if value is None or isinstance(value, (str, int, float, bool)):
                continue

            # Handle tuple of nodes (entries, elements, attributes, variants, etc.)
            if isinstance(value, tuple):
                for item in value:
                    # Only visit if item looks like an ASTNode (has dataclass fields)
                    if hasattr(item, "__dataclass_fields__"):
                        self.visit(item)
            # Handle single child node
            elif hasattr(value, "__dataclass_fields__"):
                self.visit(value)

        return node

    # Note: All visit_* methods now delegate to generic_visit() which handles
    # traversal automatically. Override these methods to add custom behavior
    # before/after visiting children.
    #
    # Example custom visitor:
    #     def visit_Message(self, node: Message) -> ASTNode:
    #         print(f"Visiting message: {node.id.name}")
    #         return self.generic_visit(node)  # Traverse children


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

    def transform(self, node: ASTNode) -> ASTNode | None | list[ASTNode]:
        """Transform an AST node or tree.

        This is the main entry point for transformations.

        Args:
            node: AST node to transform

        Returns:
            Transformed node (may be different type, None, or list)
        """
        return self.visit(node)

    def generic_visit(self, node: ASTNode) -> ASTNode:
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

    def _transform_list(self, nodes: tuple[ASTNode, ...]) -> tuple[ASTNode, ...]:
        """Transform a tuple of nodes.

        Handles node removal (None) and expansion (lists) using Python 3.13 features.
        AST nodes use tuples (immutable) instead of lists.

        Args:
            nodes: Tuple of AST nodes

        Returns:
            Transformed tuple (flattened, with None removed)
        """
        result: list[ASTNode] = []
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
