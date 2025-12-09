"""FluentBundle - Main API for Fluent message formatting.

Python 3.13+. Minimal external dependencies (returns, Babel).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ftllexbuffer.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    ErrorTemplate,
    FluentError,
    FluentReferenceError,
    FluentResolutionError,
    FluentSyntaxError,
)
from ftllexbuffer.introspection import extract_variables, introspect_message
from ftllexbuffer.runtime.cache import FormatCache
from ftllexbuffer.runtime.functions import FUNCTION_REGISTRY
from ftllexbuffer.runtime.locale_context import LocaleContext
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
        # v0.9.0: No need to call super() - generic_visit handles traversal automatically
        self.generic_visit(node)

    def visit_TermReference(self, node: TermReference) -> None:  # noqa: N802
        """Collect term reference."""
        self.term_refs.add(node.id.name)
        # v0.9.0: No need to call super() - generic_visit handles traversal automatically
        self.generic_visit(node)


@dataclass(frozen=True, slots=True)
class ValidationError:
    """Structured syntax error from FTL validation.

    v0.9.0: Replaces list[Junk] for better separation of concerns.

    Attributes:
        code: Error code (e.g., "parse-error", "malformed-entry")
        message: Human-readable error message
        content: The unparseable FTL content
        line: Line number where error occurred (1-indexed, optional)
        column: Column number where error occurred (1-indexed, optional)
    """

    code: str
    message: str
    content: str
    line: int | None = None
    column: int | None = None


@dataclass(frozen=True, slots=True)
class ValidationWarning:
    """Structured semantic warning from FTL validation.

    v0.9.0: Replaces list[str] for better structure and error codes.

    Attributes:
        code: Warning code (e.g., "duplicate-id", "undefined-reference")
        message: Human-readable warning message
        context: Additional context (e.g., the duplicate ID name)
    """

    code: str
    message: str
    context: str | None = None


@dataclass
class ValidationResult:
    """Result of FTL validation.

    v0.9.0: errors and warnings now use structured types instead of Junk/str.

    Returned by FluentBundle.validate_resource() to provide feedback
    about FTL source code before adding it to the bundle.

    Performs two levels of validation:
    - Syntax validation (errors): Parse failures, malformed FTL
    - Semantic validation (warnings): Duplicate IDs, messages without values,
      undefined references, circular dependencies

    Attributes:
        errors: List of structured validation errors
        warnings: List of structured validation warnings

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

    errors: list[ValidationError]
    warnings: list[ValidationWarning]

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
            Count of syntax errors
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

    v0.9.0: Added __slots__ for memory efficiency.

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

    __slots__ = (
        "_cache",
        "_cache_size",
        "_function_registry",
        "_locale",
        "_messages",
        "_parser",
        "_terms",
        "_use_isolating",
    )

    def __init__(
        self,
        locale: str,
        *,
        use_isolating: bool = True,
        enable_cache: bool = False,
        cache_size: int = 1000,
    ) -> None:
        """Initialize bundle for locale.

        Args:
            locale: Locale code (lv_LV, en_US, de_DE, pl_PL)
            use_isolating: Wrap interpolated values in Unicode bidi isolation marks (default: True)
                          Set to False only if you're certain RTL languages won't be used.
                          See Unicode TR9: http://www.unicode.org/reports/tr9/
            enable_cache: Enable format caching for performance (default: False)
                         Cache provides 50x speedup on repeated format calls.
            cache_size: Maximum cache entries when caching enabled (default: 1000)
        """
        self._locale = locale
        self._use_isolating = use_isolating
        self._messages: dict[str, Message] = {}
        self._terms: dict[str, Term] = {}
        self._parser = FluentParserV1()
        self._function_registry = FUNCTION_REGISTRY.copy()

        # Format cache (opt-in)
        self._cache: FormatCache | None = None
        self._cache_size = cache_size
        if enable_cache:
            self._cache = FormatCache(maxsize=cache_size)

        logger.info(
            "FluentBundle initialized for locale: %s (use_isolating=%s, cache=%s)",
            locale,
            use_isolating,
            "enabled" if enable_cache else "disabled",
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

    @property
    def cache_enabled(self) -> bool:
        """Get whether format caching is enabled (read-only).

        Returns:
            bool: True if caching is enabled, False otherwise

        Example:
            >>> bundle = FluentBundle("en", enable_cache=True)
            >>> bundle.cache_enabled
            True
            >>> bundle_no_cache = FluentBundle("en")
            >>> bundle_no_cache.cache_enabled
            False
        """
        return self._cache is not None

    @property
    def cache_size(self) -> int:
        """Get maximum cache size configuration (read-only).

        Returns:
            int: Maximum cache entries (0 if caching disabled)

        Example:
            >>> bundle = FluentBundle("en", enable_cache=True, cache_size=500)
            >>> bundle.cache_size
            500
            >>> bundle_no_cache = FluentBundle("en")
            >>> bundle_no_cache.cache_size
            0

        Note:
            Returns configured size even if cache is disabled.
            Use cache_enabled to check if caching is active.
        """
        return self._cache_size if self.cache_enabled else 0

    def __repr__(self) -> str:
        """Return string representation for debugging.

        v0.9.0: Added for better REPL and debugging experience.

        Returns:
            String representation showing locale and loaded messages count

        Example:
            >>> bundle = FluentBundle("lv_LV")
            >>> repr(bundle)
            "FluentBundle(locale='lv_LV', messages=0, terms=0)"
        """
        return (
            f"FluentBundle(locale={self._locale!r}, "
            f"messages={len(self._messages)}, "
            f"terms={len(self._terms)})"
        )

    def get_babel_locale(self) -> str:
        """Get the Babel locale identifier for this bundle (introspection API).

        This is a debugging/introspection method that returns the actual Babel locale
        identifier being used for NUMBER(), DATETIME(), and CURRENCY() formatting.

        Useful for troubleshooting locale-related formatting issues, especially when
        verifying which CLDR data is being applied.

        Returns:
            str: Babel locale identifier (e.g., "en_US", "lv_LV", "ar_EG")

        Example:
            >>> bundle = FluentBundle("lv")
            >>> bundle.get_babel_locale()
            'lv'
            >>> bundle_us = FluentBundle("en-US")
            >>> bundle_us.get_babel_locale()
            'en_US'

        Note:
            This creates a LocaleContext temporarily to access Babel locale information.
            The return value shows what locale Babel is using for CLDR-based formatting.

        See Also:
            - bundle.locale: The original locale code passed to FluentBundle
            - LocaleContext.babel_locale: The underlying Babel Locale object
        """
        ctx = LocaleContext(self._locale)
        return str(ctx.babel_locale)

    @staticmethod
    def _detect_circular_references(
        messages_dict: dict[str, Message],
        terms_dict: dict[str, Term],
        warnings: list[ValidationWarning],
        detected_cycles: set[str],
    ) -> None:
        """Detect circular dependencies in messages and terms.

        Args:
            messages_dict: Map of message IDs to Message nodes
            terms_dict: Map of term IDs to Term nodes
            warnings: List to append structured warnings to
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
                        warnings.append(
                            ValidationWarning(
                                code="circular-reference",
                                message=f"Circular message reference: {cycle_str}",
                                context=cycle_str,
                            )
                        )

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
                        warnings.append(
                            ValidationWarning(
                                code="circular-reference",
                                message=f"Circular term reference: {cycle_str}",
                                context=cycle_str,
                            )
                        )

    def add_resource(  # pylint: disable=too-many-branches
        self, source: str, *, source_path: str | None = None
    ) -> None:
        """Add FTL resource to bundle.

        Parses FTL source and adds messages/terms to registry.

        Args:
            source: FTL file content
            source_path: Optional path to source file for better error messages
                        (e.g., "locales/lv/ui.ftl")

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
                        # Include source path in error message if available
                        if source_path:
                            logger.warning(
                                "Syntax error in %s: %s", source_path, entry.content[:100]
                            )
                        else:
                            logger.debug("Junk entry (non-critical): %s", entry.content[:50])
                    case _:
                        # Comments or other entry types don't need registration
                        pass

            # Log summary with file context
            if source_path:
                logger.info(
                    "Added resource %s: %d messages, %d terms, %d junk entries",
                    source_path,
                    len(self._messages),
                    len(self._terms),
                    junk_count,
                )
            else:
                logger.info(
                    "Added resource: %d messages, %d terms, %d junk entries",
                    len(self._messages),
                    len(self._terms),
                    junk_count,
                )

            # Invalidate cache (messages changed)
            if self._cache is not None:
                self._cache.clear()
                logger.debug("Cache cleared after add_resource")

        except FluentSyntaxError as e:
            if source_path:
                logger.error("Failed to parse resource %s: %s", source_path, e)
            else:
                logger.error("Failed to parse resource: %s", e)
            raise

    # pylint: disable-next=too-many-locals,too-many-branches
    def validate_resource(self, source: str) -> ValidationResult:
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
            ...         print(f"Error [{error.code}]: {error.message}")
            >>> if result.warning_count > 0:
            ...     for warning in result.warnings:
            ...         print(f"Warning [{warning.code}]: {warning.message}")
        """
        try:
            resource = self._parser.parse(source)

            # Convert Junk entries to structured ValidationError
            errors: list[ValidationError] = []
            for entry in resource.entries:
                if isinstance(entry, Junk):
                    # Extract location from span if available
                    line = None
                    column = None
                    if entry.span:
                        # Compute line/column from span (would need cursor for accurate computation)
                        # For now, leave as None - proper implementation would use cursor
                        pass

                    errors.append(
                        ValidationError(
                            code="parse-error",
                            message="Failed to parse FTL content",
                            content=entry.content,
                            line=line,
                            column=column,
                        )
                    )

            # Semantic validation warnings
            warnings: list[ValidationWarning] = []
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
                                ValidationWarning(
                                    code="duplicate-id",
                                    message=(
                                        f"Duplicate message ID '{msg_id.name}' "
                                        f"(later definition will overwrite earlier)"
                                    ),
                                    context=msg_id.name,
                                )
                            )
                        seen_ids.add(msg_id.name)
                        messages_dict[msg_id.name] = entry

                        # Check for messages without values (only attributes)
                        if value is None and len(attributes) == 0:
                            warnings.append(
                                ValidationWarning(
                                    code="no-value-or-attributes",
                                    message=f"Message '{msg_id.name}' has neither value nor attributes",
                                    context=msg_id.name,
                                )
                            )
                    case Term(id=term_id):
                        # Check for duplicate term IDs
                        if term_id.name in seen_ids:
                            warnings.append(
                                ValidationWarning(
                                    code="duplicate-id",
                                    message=(
                                        f"Duplicate term ID '{term_id.name}' "
                                        f"(later definition will overwrite earlier)"
                                    ),
                                    context=term_id.name,
                                )
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
                            ValidationWarning(
                                code="undefined-reference",
                                message=f"Message '{msg_name}' references undefined message '{ref}'",
                                context=ref,
                            )
                        )

                # Check term references
                for ref in extractor.term_refs:
                    if ref not in terms_dict:
                        warnings.append(
                            ValidationWarning(
                                code="undefined-reference",
                                message=f"Message '{msg_name}' references undefined term '-{ref}'",
                                context=f"-{ref}",
                            )
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
                            ValidationWarning(
                                code="undefined-reference",
                                message=f"Term '-{term_name}' references undefined message '{ref}'",
                                context=ref,
                            )
                        )

                # Check term references
                for ref in extractor.term_refs:
                    if ref not in terms_dict:
                        warnings.append(
                            ValidationWarning(
                                code="undefined-reference",
                                message=f"Term '-{term_name}' references undefined term '-{ref}'",
                                context=f"-{ref}",
                            )
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
            # Create a ValidationError for the critical parse failure
            error = ValidationError(
                code="critical-parse-error",
                message=str(e),
                content=str(e),
            )
            return ValidationResult(errors=[error], warnings=[])

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
        # Check cache first (if enabled)
        if self._cache is not None:
            cached = self._cache.get(message_id, args, attribute, self._locale)
            if cached is not None:
                return cached

        # Validate message_id is non-empty string
        if not message_id or not isinstance(message_id, str):
            logger.warning("Invalid message ID: empty or non-string")
            diagnostic = Diagnostic(
                code=DiagnosticCode.MESSAGE_NOT_FOUND,
                message="Invalid message ID: empty or non-string",
            )
            error = FluentReferenceError(diagnostic)
            # Don't cache errors
            return ("{???}", [error])

        # Check if message exists
        if message_id not in self._messages:
            logger.warning("Message '%s' not found", message_id)
            error = FluentReferenceError(ErrorTemplate.message_not_found(message_id))
            # Don't cache missing message errors
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

            # Cache successful resolution (even if there are non-critical errors)
            if self._cache is not None:
                self._cache.put(message_id, args, attribute, self._locale, (result, errors))

            return (result, errors)

        except Exception as e:  # pylint: disable=broad-exception-caught
            # Unexpected: catch-all for truly unexpected errors
            # (resolver should handle everything, but be defensive)
            logger.error("Unexpected error resolving '%s': %s", message_id, e, exc_info=True)
            # Wrap in FluentResolutionError to maintain type safety
            resolution_error = FluentResolutionError(f"Unexpected error: {e}")
            # Don't cache unexpected errors
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
        if message_id not in self._messages:
            msg = f"Message '{message_id}' not found"
            raise KeyError(msg)

        return extract_variables(self._messages[message_id])

    def get_all_message_variables(self) -> dict[str, frozenset[str]]:
        """Get variables for all messages in bundle (batch introspection API).

        Convenience method for extracting variables from all messages at once.
        Useful for CI/CD validation pipelines that need to analyze entire
        FTL resources in a single operation.

        This is equivalent to calling get_message_variables() for each message
        ID, but provides a cleaner API for batch operations.

        Returns:
            Dictionary mapping message IDs to their required variable sets.
            Empty dict if bundle has no messages.

        Example:
            >>> bundle.add_resource('''
            ... greeting = Hello, { $name }!
            ... farewell = Goodbye, { $firstName } { $lastName }!
            ... simple = No variables here
            ... ''')
            >>> all_vars = bundle.get_all_message_variables()
            >>> assert all_vars["greeting"] == frozenset({"name"})
            >>> assert all_vars["farewell"] == frozenset({"firstName", "lastName"})
            >>> assert all_vars["simple"] == frozenset()

        See Also:
            - get_message_variables(): Get variables for single message
            - introspect_message(): Get complete metadata (variables + functions + references)
        """
        return {
            message_id: self.get_message_variables(message_id)
            for message_id in self.get_message_ids()
        }

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

        # Invalidate cache (functions changed)
        if self._cache is not None:
            self._cache.clear()
            logger.debug("Cache cleared after add_function")

    def clear_cache(self) -> None:
        """Clear format cache.

        Call this when you want to force cache invalidation.
        Automatically called by add_resource() and add_function().

        Example:
            >>> bundle = FluentBundle("en", enable_cache=True)
            >>> bundle.add_resource("msg = Hello")
            >>> bundle.format_pattern("msg")  # Caches result
            >>> bundle.clear_cache()  # Manual invalidation
        """
        if self._cache is not None:
            self._cache.clear()
            logger.debug("Cache manually cleared")

    def get_cache_stats(self) -> dict[str, int] | None:
        """Get cache statistics.

        Returns:
            Dict with cache metrics (size, hits, misses, hit_rate) or None if caching disabled

        Example:
            >>> bundle = FluentBundle("en", enable_cache=True)
            >>> bundle.add_resource("msg = Hello")
            >>> bundle.format_pattern("msg", {})  # Cache miss
            >>> bundle.format_pattern("msg", {})  # Cache hit
            >>> stats = bundle.get_cache_stats()
            >>> stats["hits"]
            1
            >>> stats["misses"]
            1
        """
        if self._cache is not None:
            return self._cache.get_stats()
        return None
