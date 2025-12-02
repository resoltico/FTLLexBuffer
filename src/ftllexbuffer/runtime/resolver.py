"""Fluent message resolver - converts AST to formatted strings.

Resolves patterns by walking AST, interpolating variables, evaluating selectors.
Python 3.13+. Zero external dependencies.
"""

from __future__ import annotations

from typing import Any

from ftllexbuffer.diagnostics import (
    ErrorTemplate,
    FluentCyclicReferenceError,
    FluentError,
    FluentReferenceError,
    FluentResolutionError,
)
from ftllexbuffer.runtime.function_bridge import FunctionRegistry
from ftllexbuffer.runtime.plural_rules import select_plural_category
from ftllexbuffer.syntax import (
    FunctionReference,
    Identifier,
    Message,
    MessageReference,
    NumberLiteral,
    Pattern,
    Placeable,
    SelectExpression,
    StringLiteral,
    Term,
    TermReference,
    TextElement,
    VariableReference,
)


class FluentResolver:
    """Resolves Fluent messages to strings.

    Aligned with Mozilla python-fluent error handling:
    - Collects errors instead of embedding them in output
    - Returns (result, errors) tuples
    - Provides readable fallbacks per Fluent specification
    """

    def __init__(
        self,
        locale: str,
        messages: dict[str, Message],
        terms: dict[str, Term],
        *,
        function_registry: FunctionRegistry,
        use_isolating: bool = True,
    ) -> None:
        """Initialize resolver.

        Args:
            locale: Locale code for plural selection
            messages: Message registry
            terms: Term registry
            function_registry: Function registry with camelCase conversion (keyword-only)
            use_isolating: Wrap interpolated values in Unicode bidi marks (keyword-only)
        """
        self.locale = locale
        self.use_isolating = use_isolating
        self.messages = messages
        self.terms = terms
        self.function_registry = function_registry
        self._resolution_stack: list[str] = []  # Circular reference detection
        self.errors: list[FluentError] = []  # Error accumulator (Mozilla-aligned)

    def resolve_message(
        self,
        message: Message,
        args: dict[str, Any] | None = None,
        attribute: str | None = None,
    ) -> tuple[str, list[FluentError]]:
        """Resolve message to final string with error collection.

        Mozilla python-fluent aligned API:
        - Returns (result, errors) tuple
        - Collects all errors during resolution
        - Never raises exceptions (graceful degradation)

        Args:
            message: Message AST
            args: Variable arguments
            attribute: Attribute name (optional)

        Returns:
            Tuple of (formatted_string, errors)
            - formatted_string: Best-effort output (never empty)
            - errors: List of exceptions encountered

        Note:
            Per Fluent spec, resolution never fails catastrophically.
            Errors are collected and fallback values are used.
        """
        self.errors = []  # Reset error list for this resolution
        args = args or {}

        # Select pattern (value or attribute)
        if attribute:
            attr = next((a for a in message.attributes if a.id.name == attribute), None)
            if not attr:
                error = FluentReferenceError(
                    ErrorTemplate.attribute_not_found(attribute, message.id.name)
                )
                self.errors.append(error)
                return (f"{{{message.id.name}.{attribute}}}", self.errors)
            pattern = attr.value
        else:
            if message.value is None:
                error = FluentReferenceError(ErrorTemplate.message_no_value(message.id.name))
                self.errors.append(error)
                return (f"{{{message.id.name}}}", self.errors)
            pattern = message.value

        # Check for circular references
        msg_key = f"{message.id.name}.{attribute}" if attribute else message.id.name
        if msg_key in self._resolution_stack:
            cycle_path = [*self._resolution_stack, msg_key]
            error = FluentCyclicReferenceError(ErrorTemplate.cyclic_reference(cycle_path))
            self.errors.append(error)
            return (f"{{{msg_key}}}", self.errors)

        try:
            self._resolution_stack.append(msg_key)
            result = self._resolve_pattern(pattern, args)
            return (result, self.errors)
        finally:
            self._resolution_stack.pop()

    def _resolve_pattern(self, pattern: Pattern, args: dict[str, Any]) -> str:
        """Resolve pattern by walking elements."""
        result = ""

        for element in pattern.elements:
            match element:
                case TextElement():
                    result += element.value
                case Placeable():
                    try:
                        value = self._resolve_expression(element.expression, args)
                        formatted = self._format_value(value)

                        # Wrap in Unicode bidi isolation marks (FSI/PDI)
                        # Per Unicode TR9, prevents RTL/LTR text interference
                        if self.use_isolating:
                            # U+2068 FIRST STRONG ISOLATE (FSI)
                            # U+2069 POP DIRECTIONAL ISOLATE (PDI)
                            result += f"\u2068{formatted}\u2069"
                        else:
                            result += formatted

                    except (FluentReferenceError, FluentResolutionError) as e:
                        # Mozilla-aligned error handling:
                        # Collect error, show readable fallback (not {ERROR: ...})
                        self.errors.append(e)
                        fallback = self._get_fallback_for_placeable(element.expression)
                        result += fallback

        return result

    def _resolve_expression(self, expr: Any, args: dict[str, Any]) -> Any:  # noqa: PLR0911
        """Resolve expression to value.

        Uses pattern matching (PEP 636) to reduce complexity.
        Each case delegates to a specialized resolver method.

        Note: PLR0911 (too many returns) is acceptable here - each case
        represents a distinct expression type in the Fluent AST.
        """
        match expr:
            case SelectExpression():
                return self._resolve_select_expression(expr, args)
            case VariableReference():
                return self._resolve_variable_reference(expr, args)
            case MessageReference():
                return self._resolve_message_reference(expr, args)
            case TermReference():
                return self._resolve_term_reference(expr, args)
            case FunctionReference():
                return self._resolve_function_call(expr, args)
            case StringLiteral():
                return expr.value
            case NumberLiteral():
                return expr.parsed_value
            case Placeable():
                return self._resolve_expression(expr.expression, args)
            case _:
                raise FluentResolutionError(ErrorTemplate.unknown_expression(type(expr).__name__))

    def _resolve_variable_reference(self, expr: VariableReference, args: dict[str, Any]) -> Any:
        """Resolve variable reference from args."""
        var_name = expr.id.name
        if var_name not in args:
            raise FluentReferenceError(ErrorTemplate.variable_not_provided(var_name))
        return args[var_name]

    def _resolve_message_reference(self, expr: MessageReference, args: dict[str, Any]) -> Any:
        """Resolve message reference."""
        msg_id = expr.id.name
        if msg_id not in self.messages:
            raise FluentReferenceError(ErrorTemplate.message_not_found(msg_id))
        message = self.messages[msg_id]
        # resolve_message returns (result, errors) tuple
        # We need to accumulate nested errors into our current errors list
        result, nested_errors = self.resolve_message(
            message,
            args,
            attribute=expr.attribute.name if expr.attribute else None,
        )
        # Add nested errors to our error list
        self.errors.extend(nested_errors)
        return result

    def _resolve_term_reference(self, expr: TermReference, args: dict[str, Any]) -> str:
        """Resolve term reference."""
        term_id = expr.id.name
        if term_id not in self.terms:
            raise FluentReferenceError(ErrorTemplate.term_not_found(term_id))
        term = self.terms[term_id]

        # Select pattern (value or attribute)
        if expr.attribute:
            attr = next((a for a in term.attributes if a.id.name == expr.attribute.name), None)
            if not attr:
                raise FluentReferenceError(
                    ErrorTemplate.term_attribute_not_found(expr.attribute.name, term_id)
                )
            pattern = attr.value
        else:
            pattern = term.value

        return self._resolve_pattern(pattern, args)

    def _resolve_select_expression(self, expr: SelectExpression, args: dict[str, Any]) -> str:
        """Resolve select expression by matching variant."""
        # Evaluate selector
        selector_value = self._resolve_expression(expr.selector, args)

        # Find matching variant
        matched_variant = None
        default_variant = None

        for variant in expr.variants:
            # Track default
            if variant.default:
                default_variant = variant

            # Try exact match
            if isinstance(variant.key, Identifier):
                # String key
                if str(selector_value) == variant.key.name:
                    matched_variant = variant
                    break
            elif (
                isinstance(variant.key, NumberLiteral)
                and selector_value == variant.key.parsed_value
            ):
                # Number key
                matched_variant = variant
                break

        # Try plural category match for numbers
        if matched_variant is None and isinstance(selector_value, (int, float)):
            plural_category = select_plural_category(selector_value, self.locale)
            for variant in expr.variants:
                if isinstance(variant.key, Identifier) and variant.key.name == plural_category:
                    matched_variant = variant
                    break

        # Fallback chain
        if matched_variant is None:
            matched_variant = default_variant

        if matched_variant is None and expr.variants:
            # Last resort: use first variant
            matched_variant = expr.variants[0]

        if matched_variant is None:
            raise FluentResolutionError(ErrorTemplate.no_variants())

        # Resolve matched variant pattern
        return self._resolve_pattern(matched_variant.value, args)

    def _resolve_function_call(self, func_ref: FunctionReference, args: dict[str, Any]) -> Any:
        """Resolve function call.

        Uses FunctionRegistry to handle camelCase → snake_case parameter conversion.
        Uses metadata system to determine if locale injection is needed.
        """
        from ftllexbuffer.runtime.function_metadata import should_inject_locale

        func_name = func_ref.id.name

        # Evaluate positional arguments
        positional_values = [
            self._resolve_expression(arg, args) for arg in func_ref.arguments.positional
        ]

        # Evaluate named arguments (camelCase from FTL)
        named_values = {
            arg.name.name: self._resolve_expression(arg.value, args)
            for arg in func_ref.arguments.named
        }

        # Check if locale injection is needed (metadata-driven, not magic tuple)
        # This correctly handles custom functions with same name as built-ins
        if should_inject_locale(func_name, self.function_registry):
            # Built-in formatting function: inject locale as second positional argument
            # FunctionRegistry.call() handles camelCase → snake_case conversion
            return self.function_registry.call(
                func_name,
                [*positional_values, self.locale],
                named_values,
            )

        # Custom function or built-in that doesn't need locale: pass args as-is
        return self.function_registry.call(
            func_name,
            positional_values,
            named_values,
        )

    def _format_value(self, value: Any) -> str:
        """Format value to string."""
        if isinstance(value, str):
            return value
        # Check bool BEFORE int/float (bool is subclass of int in Python)
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        if value is None:
            return ""
        return str(value)

    def _get_fallback_for_placeable(self, expr: Any) -> str:
        """Get readable fallback for failed placeable per Fluent spec.

        Per Fluent specification, when a placeable fails to resolve,
        we return a human-readable representation of what was attempted.
        This is superior to {ERROR: ...} as it:
        1. Doesn't expose internal diagnostics
        2. Shows what the translator expected
        3. Makes errors visible but not alarming

        Args:
            expr: The expression that failed to resolve

        Returns:
            Readable fallback string

        Examples:
            VariableReference($name) → "{$name}"
            MessageReference(welcome) → "{welcome}"
            TermReference(-brand) → "{-brand}"
            FunctionReference(NUMBER) → "{NUMBER(...)}"
        """
        match expr:
            case VariableReference():
                return f"{{${expr.id.name}}}"
            case MessageReference():
                attr_suffix = f".{expr.attribute.name}" if expr.attribute else ""
                return f"{{{expr.id.name}{attr_suffix}}}"
            case TermReference():
                attr_suffix = f".{expr.attribute.name}" if expr.attribute else ""
                return f"{{-{expr.id.name}{attr_suffix}}}"
            case FunctionReference():
                return f"{{{expr.id.name}(...)}}"
            case SelectExpression():
                return "{???}"  # Select expressions are complex, use generic fallback
            case _:
                return "{???}"  # Unknown expression type
