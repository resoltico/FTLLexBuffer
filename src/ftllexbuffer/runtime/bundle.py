"""FluentBundle - Main API for Fluent message formatting.

Python 3.13+. Minimal external dependencies (returns, Babel).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ftllexbuffer.diagnostics import (
    FluentError,
    FluentReferenceError,
    FluentResolutionError,
    FluentSyntaxError,
)
from ftllexbuffer.runtime.functions import FUNCTION_REGISTRY
from ftllexbuffer.runtime.resolver import FluentResolver
from ftllexbuffer.syntax import Junk, Message, Term
from ftllexbuffer.syntax.ast import MessageReference, TermReference
from ftllexbuffer.syntax.parser import FluentParserV1
from ftllexbuffer.syntax.visitor import ASTVisitor

if TYPE_CHECKING:
    from ftllexbuffer.introspection import MessageIntrospection

logger = logging.getLogger(__name__)


class _ReferenceExtractor(ASTVisitor):
    """Extract message and term references from AST for validation."""

    def __init__(self) -> None:
        """Initialize reference collector."""
        self.message_refs: set[str] = set()
        self.term_refs: set[str] = set()

    def visit_MessageReference(self, node: MessageReference) -> None:  # noqa: N802
        """Collect message reference."""
        self.message_refs.add(node.id.name)
        super().visit_MessageReference(node)

    def visit_TermReference(self, node: TermReference) -> None:  # noqa: N802
        """Collect term reference."""
        self.term_refs.add(node.id.name)
        super().visit_TermReference(node)


@dataclass
class ValidationResult:
    """Result of FTL validation.

    Returned by FluentBundle.validate_resource() to provide feedback
    about FTL source code before adding it to the bundle.

    Performs two levels of validation:
    - Syntax validation (errors): Parse failures, malformed FTL
    - Semantic validation (warnings): Duplicate IDs, messages without values,
      undefined references, circular dependencies

    Attributes:
        errors: List of Junk entries (parse errors)
        warnings: List of semantic warning messages including duplicate IDs, messages
            without values, undefined references, and circular dependencies

    Example:
        >>> bundle = FluentBundle("en")
        >>> result = bundle.validate_resource("hello = Hello")
        >>> result.is_valid
        True
        >>> result.error_count
        0
        >>> result.warning_count
        0
        >>>
        >>> # Duplicate IDs trigger warnings
        >>> result = bundle.validate_resource("msg = A\\nmsg = B")
        >>> result.is_valid
        True  # No syntax errors
        >>> result.warning_count
        1  # Semantic warning about duplicate
    """

    errors: list[Junk]
    warnings: list[str]

    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors).

        Returns:
            True if no errors found
        """
        return len(self.errors) == 0

    @property
    def error_count(self) -> int:
        """Get number of errors found.

        Returns:
            Count of Junk entries (parse errors)
        """
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        """Get number of warnings found.

        Returns:
            Count of warnings
        """
        return len(self.warnings)


class FluentBundle:
    """Fluent message bundle for specific locale.

    Main public API for Fluent localization. Aligned with Mozilla python-fluent
    error handling that returns (result, errors) tuples.

    Examples:
        >>> bundle = FluentBundle("lv_LV")
        >>> bundle.add_resource('''
        ... hello = Sveiki, pasaule!
        ... welcome = Laipni lūdzam, { $name }!
        ... ''')
        >>> result, errors = bundle.format_pattern("hello")
        >>> assert result == 'Sveiki, pasaule!'
        >>> assert errors == []
        >>>
        >>> result, errors = bundle.format_pattern("welcome", {"name": "Jānis"})
        >>> assert result == 'Laipni lūdzam, Jānis!'
        >>> assert errors == []
    """

    def __init__(self, locale: str, *, use_isolating: bool = True) -> None:
        """Initialize bundle for locale.

        Args:
            locale: Locale code (lv_LV, en_US, de_DE, pl_PL)
            use_isolating: Wrap interpolated values in Unicode bidi isolation marks (default: True)
                          Set to False only if you're certain RTL languages won't be used.
                          See Unicode TR9: http://www.unicode.org/reports/tr9/
        """
        self._locale = locale
        self._use_isolating = use_isolating
        self._messages: dict[str, Message] = {}
        self._terms: dict[str, Term] = {}
        self._parser = FluentParserV1()
        self._function_registry = FUNCTION_REGISTRY

        logger.info(
            "FluentBundle initialized for locale: %s (use_isolating=%s)",
            locale,
            use_isolating,
        )

    @property
    def locale(self) -> str:
        """Get the locale code for this bundle (read-only).

        Returns:
            str: Locale code (e.g., "en_US", "lv_LV")

        Example:
            >>> bundle = FluentBundle("lv_LV")
            >>> bundle.locale
            'lv_LV'
        """
        return self._locale

    @property
    def use_isolating(self) -> bool:
        """Get whether Unicode bidi isolation is enabled (read-only).

        Returns:
            bool: True if bidi isolation is enabled, False otherwise

        Example:
            >>> bundle = FluentBundle("ar_EG", use_isolating=True)
            >>> bundle.use_isolating
            True
        """
        return self._use_isolating

    @staticmethod
    def _detect_circular_references(  # noqa: PLR0912
        messages_dict: dict[str, Message],
        terms_dict: dict[str, Term],
        warnings: list[str],
        detected_cycles: set[str],
    ) -> None:
        """Detect circular dependencies in messages and terms.

        Args:
            messages_dict: Map of message IDs to Message nodes
            terms_dict: Map of term IDs to Term nodes
            warnings: List to append warning messages to
            detected_cycles: Set to track already-detected cycles
        """
        # Build dependency graph for messages
        dependencies: dict[str, set[str]] = {}
        for msg_name, message in messages_dict.items():
            extractor = _ReferenceExtractor()
            if message.value:
                extractor.visit(message.value)
            for attr in message.attributes:
                extractor.visit(attr.value)
            dependencies[msg_name] = extractor.message_refs

        # Build dependency graph for terms
        term_dependencies: dict[str, set[str]] = {}
        for term_name, term in terms_dict.items():
            extractor = _ReferenceExtractor()
            extractor.visit(term.value)
            for attr in term.attributes:
                extractor.visit(attr.value)
            term_dependencies[term_name] = extractor.term_refs

        # Detect cycles using DFS
        def _detect_cycle(
            node: str, visited: set[str], rec_stack: set[str], dep_graph: dict[str, set[str]]
        ) -> list[str] | None:
            """Detect cycle using DFS. Returns cycle path if found."""
            visited.add(node)
            rec_stack.add(node)

            for neighbor in dep_graph.get(node, set()):
                if neighbor not in visited:
                    cycle = _detect_cycle(neighbor, visited, rec_stack, dep_graph)
                    if cycle is not None:
                        return [node, *cycle]
                elif neighbor in rec_stack:
                    return [node, neighbor]

            rec_stack.remove(node)
            return None

        visited: set[str] = set()

        # Check for circular message references
        for msg_name in dependencies:
            if msg_name not in visited:
                cycle = _detect_cycle(msg_name, visited, set(), dependencies)
                if cycle:
                    cycle_key = " → ".join(sorted(set(cycle)))
                    if cycle_key not in detected_cycles:
                        detected_cycles.add(cycle_key)
                        cycle_str = " → ".join(cycle)
                        warnings.append(f"Circular message reference: {cycle_str}")

        # Check for circular term references
        visited_terms: set[str] = set()
        for term_name in term_dependencies:
            if term_name not in visited_terms:
                cycle = _detect_cycle(term_name, visited_terms, set(), term_dependencies)
                if cycle:
                    cycle_key = " → ".join(sorted(set(cycle)))
                    if cycle_key not in detected_cycles:
                        detected_cycles.add(cycle_key)
                        cycle_str = " → ".join([f"-{t}" for t in cycle])
                        warnings.append(f"Circular term reference: {cycle_str}")

    def add_resource(self, source: str) -> None:
        """Add FTL resource to bundle.

        Parses FTL source and adds messages/terms to registry.

        Args:
            source: FTL file content

        Raises:
            FluentSyntaxError: On critical parse error

        Note:
            Non-critical syntax errors become Junk entries and are logged.
            Parser continues after errors (robustness principle).
        """
        try:
            resource = self._parser.parse(source)

            # Register messages and terms using structural pattern matching
            junk_count = 0
            for entry in resource.entries:
                match entry:
                    case Message():
                        self._messages[entry.id.name] = entry
                        logger.debug("Registered message: %s", entry.id.name)
                    case Term():
                        self._terms[entry.id.name] = entry
                        logger.debug("Registered term: %s", entry.id.name)
                    case Junk():
                        # Count junk entries, log at debug level (non-critical parse artifacts)
                        junk_count += 1
                        logger.debug("Junk entry (non-critical): %s", entry.content[:50])
                    case _:
                        # Comments or other entry types don't need registration
                        pass

            # Log summary
            logger.info(
                "Added resource: %d messages, %d terms, %d junk entries",
                len(self._messages),
                len(self._terms),
                junk_count,
            )

        except FluentSyntaxError as e:
            logger.error("Failed to parse resource: %s", e)
            raise

    # pylint: disable-next=too-many-locals,too-many-branches
    def validate_resource(self, source: str) -> ValidationResult:  # noqa: PLR0912
        """Validate FTL resource without adding to bundle.

        Use this to check FTL files in CI/tooling before adding them.
        Unlike add_resource(), this does not modify the bundle.

        Performs both syntax validation (errors) and semantic validation (warnings):
        - Errors: Parse failures (Junk entries)
        - Warnings: Duplicate IDs, messages without values, undefined references,
          circular dependencies

        Args:
            source: FTL file content

        Returns:
            ValidationResult with parse errors and semantic warnings

        Example:
            >>> bundle = FluentBundle("lv")
            >>> result = bundle.validate_resource(ftl_source)
            >>> if not result.is_valid:
            ...     for error in result.errors:
            ...         print(f"Error: {error.content}")
            >>> if result.warning_count > 0:
            ...     for warning in result.warnings:
            ...         print(f"Warning: {warning}")
        """
        try:
            resource = self._parser.parse(source)

            # Extract Junk entries (parse errors)
            errors = [entry for entry in resource.entries if isinstance(entry, Junk)]

            # Semantic validation warnings
            warnings: list[str] = []
            seen_ids: set[str] = set()
            messages_dict: dict[str, Message] = {}
            terms_dict: dict[str, Term] = {}

            # First pass: collect all message/term IDs and check for duplicates
            for entry in resource.entries:
                match entry:
                    case Message(id=msg_id, value=value, attributes=attributes):
                        # Check for duplicate message IDs
                        if msg_id.name in seen_ids:
                            warnings.append(
                                f"Duplicate message ID '{msg_id.name}' "
                                f"(later definition will overwrite earlier)"
                            )
                        seen_ids.add(msg_id.name)
                        messages_dict[msg_id.name] = entry

                        # Check for messages without values (only attributes)
                        if value is None and len(attributes) == 0:
                            warnings.append(
                                f"Message '{msg_id.name}' has neither value nor attributes"
                            )
                    case Term(id=term_id):
                        # Check for duplicate term IDs
                        if term_id.name in seen_ids:
                            warnings.append(
                                f"Duplicate term ID '{term_id.name}' "
                                f"(later definition will overwrite earlier)"
                            )
                        seen_ids.add(term_id.name)
                        terms_dict[term_id.name] = entry

            # Second pass: check for undefined references
            for msg_name, message in messages_dict.items():
                extractor = _ReferenceExtractor()
                if message.value:
                    extractor.visit(message.value)
                for attr in message.attributes:
                    extractor.visit(attr.value)

                # Check message references
                for ref in extractor.message_refs:
                    if ref not in messages_dict:
                        warnings.append(
                            f"Message '{msg_name}' references undefined message '{ref}'"
                        )

                # Check term references
                for ref in extractor.term_refs:
                    if ref not in terms_dict:
                        warnings.append(
                            f"Message '{msg_name}' references undefined term '-{ref}'"
                        )

            # Check term references
            for term_name, term in terms_dict.items():
                extractor = _ReferenceExtractor()
                extractor.visit(term.value)
                for attr in term.attributes:
                    extractor.visit(attr.value)

                # Check message references
                for ref in extractor.message_refs:
                    if ref not in messages_dict:
                        warnings.append(
                            f"Term '-{term_name}' references undefined message '{ref}'"
                        )

                # Check term references
                for ref in extractor.term_refs:
                    if ref not in terms_dict:
                        warnings.append(
                            f"Term '-{term_name}' references undefined term '-{ref}'"
                        )

            # Third pass: detect circular dependencies
            self._detect_circular_references(
                messages_dict, terms_dict, warnings, detected_cycles=set()
            )

            logger.debug("Validated resource: %d errors, %d warnings", len(errors), len(warnings))

            return ValidationResult(errors=errors, warnings=warnings)

        except FluentSyntaxError as e:
            # Critical parse error - return as single error
            logger.error("Critical validation error: %s", e)
            # Create a Junk entry representing the critical error
            junk = Junk(content=str(e))
            return ValidationResult(errors=[junk], warnings=[])

    def format_pattern(
        self,
        message_id: str,
        args: dict[str, Any] | None = None,
        *,
        attribute: str | None = None,
    ) -> tuple[str, list[FluentError]]:
        """Format message to string with error reporting.

        Mozilla python-fluent aligned API that returns both the formatted
        string and any errors encountered during resolution.

        Args:
            message_id: Message identifier
            args: Variable arguments for interpolation
            attribute: Attribute name (optional)

        Returns:
            Tuple of (formatted_string, errors)
            - formatted_string: Best-effort formatted output (never empty)
            - errors: List of exceptions encountered during resolution

        Note:
            This method NEVER raises exceptions. All errors are collected
            and returned in the errors list. The formatted string always
            contains a readable fallback value per Fluent specification.

        Examples:
            >>> # Successful formatting
            >>> result, errors = bundle.format_pattern("hello")
            >>> assert result == 'Sveiki, pasaule!'
            >>> assert errors == []

            >>> # Missing variable - returns fallback and error
            >>> bundle.add_resource('msg = Hello { $name }!')
            >>> result, errors = bundle.format_pattern("msg", {})
            >>> assert result == 'Hello {$name}!'  # Readable fallback
            >>> assert len(errors) == 1
            >>> assert isinstance(errors[0], FluentReferenceError)

            >>> # Attribute access
            >>> result, errors = bundle.format_pattern("button-save", attribute="tooltip")
            >>> assert result == 'Saglabā pašreizējo ierakstu datubāzē'
            >>> assert errors == []
        """
        # Validate message_id is non-empty string
        if not message_id or not isinstance(message_id, str):
            logger.warning("Invalid message ID: empty or non-string")
            from ftllexbuffer.diagnostics import Diagnostic, DiagnosticCode

            diagnostic = Diagnostic(
                code=DiagnosticCode.MESSAGE_NOT_FOUND,
                message="Invalid message ID: empty or non-string",
            )
            error = FluentReferenceError(diagnostic)
            return ("{???}", [error])

        # Check if message exists
        if message_id not in self._messages:
            logger.warning("Message '%s' not found", message_id)
            from ftllexbuffer.diagnostics import ErrorTemplate

            error = FluentReferenceError(ErrorTemplate.message_not_found(message_id))
            return (f"{{{message_id}}}", [error])

        message = self._messages[message_id]

        # Create resolver
        resolver = FluentResolver(
            locale=self._locale,
            messages=self._messages,
            terms=self._terms,
            function_registry=self._function_registry,
            use_isolating=self._use_isolating,
        )

        # Resolve message (resolver handles all errors internally)
        try:
            result, errors = resolver.resolve_message(message, args, attribute)

            if errors:
                logger.warning(
                    "Message resolution errors for '%s': %d error(s)", message_id, len(errors)
                )
                for err in errors:
                    logger.debug("  - %s: %s", type(err).__name__, err)
            else:
                logger.debug("Resolved message '%s': %s", message_id, result[:50])

            return (result, errors)

        except Exception as e:  # pylint: disable=broad-exception-caught
            # Unexpected: catch-all for truly unexpected errors
            # (resolver should handle everything, but be defensive)
            logger.error("Unexpected error resolving '%s': %s", message_id, e, exc_info=True)
            # Wrap in FluentResolutionError to maintain type safety
            resolution_error = FluentResolutionError(f"Unexpected error: {e}")
            return (f"{{{message_id}}}", [resolution_error])

    def format_value(
        self, message_id: str, args: dict[str, Any] | None = None
    ) -> tuple[str, list[FluentError]]:
        """Format message to string (alias for format_pattern without attribute access).

        This method provides API consistency with FluentLocalization.format_value()
        for users who don't need attribute access. It's an alias for
        format_pattern(message_id, args, attribute=None).

        Args:
            message_id: Message identifier
            args: Variable arguments for interpolation

        Returns:
            Tuple of (formatted_string, errors)
            - formatted_string: Best-effort formatted output (never empty)
            - errors: List of FluentError instances encountered during resolution

        Note:
            This method NEVER raises exceptions. All errors are collected
            and returned in the errors list.

        Example:
            >>> bundle.add_resource("welcome = Hello, { $name }!")
            >>> result, errors = bundle.format_value("welcome", {"name": "Alice"})
            >>> assert result == "Hello, Alice!"
            >>> assert errors == []
        """
        return self.format_pattern(message_id, args, attribute=None)

    def has_message(self, message_id: str) -> bool:
        """Check if message exists.

        Args:
            message_id: Message identifier

        Returns:
            True if message exists in bundle
        """
        return message_id in self._messages

    def get_message_ids(self) -> list[str]:
        """Get all message IDs in bundle.

        Returns:
            List of message identifiers
        """
        return list(self._messages.keys())

    def get_message_variables(self, message_id: str) -> frozenset[str]:
        """Get all variables required by a message (introspection API).

        This is a value-add feature not present in Mozilla's python-fluent.
        Enables FTL file validation in CI/CD pipelines.

        Args:
            message_id: Message identifier

        Returns:
            Frozen set of variable names (without $ prefix)

        Raises:
            KeyError: If message doesn't exist

        Example:
            >>> bundle.add_resource("greeting = Hello, { $name }!")
            >>> vars = bundle.get_message_variables("greeting")
            >>> assert "name" in vars
        """
        from ftllexbuffer.introspection import extract_variables

        if message_id not in self._messages:
            msg = f"Message '{message_id}' not found"
            raise KeyError(msg)

        return extract_variables(self._messages[message_id])

    def introspect_message(self, message_id: str) -> MessageIntrospection:
        """Get complete introspection data for a message.

        Returns comprehensive metadata about variables, functions, and references
        used in the message. Uses Python 3.13's TypeIs for type-safe results.

        Args:
            message_id: Message identifier

        Returns:
            MessageIntrospection with complete metadata

        Raises:
            KeyError: If message doesn't exist

        Example:
            >>> bundle.add_resource("price = { NUMBER($amount, minimumFractionDigits: 2) }")
            >>> info = bundle.introspect_message("price")
            >>> assert "amount" in info.get_variable_names()
            >>> assert "NUMBER" in info.get_function_names()
        """
        from ftllexbuffer.introspection import introspect_message

        if message_id not in self._messages:
            msg = f"Message '{message_id}' not found"
            raise KeyError(msg)

        return introspect_message(self._messages[message_id])

    def add_function(self, name: str, func: Any) -> None:
        """Add custom function to bundle.

        Args:
            name: Function name (UPPERCASE by convention)
            func: Callable function

        Example:
            >>> def CUSTOM(value):
            ...     return value.upper()
            >>> bundle.add_function("CUSTOM", CUSTOM)
        """
        self._function_registry.register(func, ftl_name=name)
        logger.debug("Added custom function: %s", name)
