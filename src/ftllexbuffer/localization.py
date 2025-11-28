"""Multi-locale orchestration with fallback chains.

Implements FluentLocalization following Mozilla's python-fluent architecture.
Separates multi-locale orchestration (FluentLocalization) from single-locale
formatting (FluentBundle).

Key architectural decisions:
- Lazy bundle generation using generators (memory efficient)
- Protocol-based ResourceLoader (dependency inversion)
- Immutable locale chain (established at construction)
- Python 3.13 features: pattern matching, TypeIs, frozen dataclasses

Python 3.13+.
"""

from __future__ import annotations

from collections.abc import Generator, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from .diagnostics.codes import Diagnostic, DiagnosticCode
from .diagnostics.errors import FluentError
from .runtime.bundle import FluentBundle

if TYPE_CHECKING:
    pass

# Type aliases using Python 3.13 type keyword
type MessageId = str
type LocaleCode = str
type ResourceId = str
type FTLSource = str


class ResourceLoader(Protocol):
    """Protocol for loading FTL resources for specific locales.

    Implementations must provide a load() method that retrieves FTL source
    for a given locale and resource identifier.

    This is a Protocol (structural typing) rather than ABC to allow
    maximum flexibility for users implementing custom loaders.

    Example:
        >>> class DiskLoader:
        ...     def load(self, locale: str, resource_id: str) -> str:
        ...         path = Path(f"locales/{locale}/{resource_id}")
        ...         return path.read_text(encoding="utf-8")
        ...
        >>> loader = DiskLoader()
        >>> l10n = FluentLocalization(['en', 'fr'], ['main.ftl'], loader)
    """

    def load(self, locale: LocaleCode, resource_id: ResourceId) -> FTLSource:
        """Load FTL resource for given locale.

        Args:
            locale: Locale code (e.g., 'en', 'fr', 'lv')
            resource_id: Resource identifier (e.g., 'main.ftl', 'errors.ftl')

        Returns:
            FTL source code as string

        Raises:
            FileNotFoundError: If resource doesn't exist for this locale
            OSError: If file cannot be read
        """


@dataclass(frozen=True, slots=True)
class PathResourceLoader:
    """File system resource loader using path templates.

    Implements ResourceLoader protocol for loading FTL files from disk.
    Uses {locale} placeholder in path template for locale substitution.

    Uses Python 3.13 frozen dataclass with slots for zero-allocation overhead.

    Example:
        >>> loader = PathResourceLoader("locales/{locale}")
        >>> ftl = loader.load("en", "main.ftl")
        # Loads from: locales/en/main.ftl

    Attributes:
        base_path: Path template with {locale} placeholder
    """

    base_path: str

    def load(self, locale: LocaleCode, resource_id: ResourceId) -> FTLSource:
        """Load FTL file from disk.

        Args:
            locale: Locale code to substitute in path template
            resource_id: FTL filename (e.g., 'main.ftl')

        Returns:
            FTL source code

        Raises:
            FileNotFoundError: If file doesn't exist
            OSError: If file cannot be read
        """
        # Substitute {locale} in path template
        locale_path = self.base_path.format(locale=locale)
        full_path = Path(locale_path) / resource_id

        return full_path.read_text(encoding="utf-8")


class FluentLocalization:
    """Multi-locale message formatting with fallback chains.

    Orchestrates multiple FluentBundle instances (one per locale) and implements
    locale fallback logic. Follows Mozilla's python-fluent architecture.

    Architecture:
    - FluentBundle: Single-locale formatting (1 bundle = 1 locale)
    - FluentLocalization: Multi-locale orchestration (manages N bundles)

    This class does NOT subclass FluentBundle - it wraps multiple instances.

    Uses Python 3.13 features:
    - Pattern matching for fallback logic
    - Generator expressions for lazy bundle creation
    - Match statements for error handling

    Example - Disk-based resources:
        >>> loader = PathResourceLoader("locales/{locale}")
        >>> l10n = FluentLocalization(['lv', 'en'], ['ui.ftl'], loader)
        >>> result = l10n.format_value('welcome', {'name': 'Anna'})
        # Tries 'lv' first, falls back to 'en' if message not found

    Example - Direct resource provision:
        >>> l10n = FluentLocalization(['lv', 'en'])
        >>> l10n.add_resource('lv', 'welcome = Sveiki, { $name }!')
        >>> l10n.add_resource('en', 'welcome = Hello, { $name }!')
        >>> result = l10n.format_value('welcome', {'name': 'Anna'})
        # Returns: ('Sveiki, Anna!', [])

    Attributes:
        locales: Immutable tuple of locale codes in fallback priority order
    """

    __slots__ = (
        "_bundles",
        "_locales",
        "_resource_ids",
        "_resource_loader",
        "_use_isolating",
    )

    def __init__(
        self,
        locales: Iterable[LocaleCode],
        resource_ids: Iterable[ResourceId] | None = None,
        resource_loader: ResourceLoader | None = None,
        *,
        use_isolating: bool = True,
    ) -> None:
        """Initialize multi-locale localization.

        Args:
            locales: Locale codes in fallback order (e.g., ['lv', 'en', 'lt'])
            resource_ids: FTL file identifiers to load (e.g., ['ui.ftl', 'errors.ftl'])
            resource_loader: Loader for fetching FTL resources (optional)
            use_isolating: Wrap placeables in Unicode bidi isolation marks

        Raises:
            ValueError: If locales is empty
            ValueError: If resource_ids provided but no resource_loader
        """
        # Validate inputs
        locale_list = list(locales)
        if not locale_list:
            msg = "At least one locale is required"
            raise ValueError(msg)

        if resource_ids and not resource_loader:
            msg = "resource_loader required when resource_ids provided"
            raise ValueError(msg)

        # Store immutable locale chain
        self._locales: tuple[LocaleCode, ...] = tuple(locale_list)
        self._resource_ids: tuple[ResourceId, ...] = (
            tuple(resource_ids) if resource_ids else ()
        )
        self._resource_loader: ResourceLoader | None = resource_loader
        self._use_isolating = use_isolating

        # Create bundle instances for each locale
        self._bundles: dict[LocaleCode, FluentBundle] = {}
        for locale in self._locales:
            bundle = FluentBundle(locale, use_isolating=use_isolating)
            self._bundles[locale] = bundle

        # Load resources if loader provided
        if resource_loader and resource_ids:
            for locale in self._locales:
                for resource_id in self._resource_ids:
                    try:
                        ftl_source = resource_loader.load(locale, resource_id)
                        bundle = self._bundles[locale]
                        bundle.add_resource(ftl_source)
                    except FileNotFoundError:
                        # Resource doesn't exist for this locale - skip it
                        # Fallback will try next locale in chain
                        continue

    @property
    def locales(self) -> tuple[LocaleCode, ...]:
        """Get immutable locale fallback chain.

        Returns:
            Tuple of locale codes in priority order
        """
        return self._locales

    def add_resource(self, locale: LocaleCode, ftl_source: FTLSource) -> None:
        """Add FTL resource to specific locale bundle.

        Allows dynamic resource loading without ResourceLoader.

        Args:
            locale: Locale code (must be in fallback chain)
            ftl_source: FTL source code

        Raises:
            ValueError: If locale not in fallback chain
        """
        if locale not in self._bundles:
            msg = f"Locale '{locale}' not in fallback chain {self._locales}"
            raise ValueError(msg)

        bundle = self._bundles[locale]
        bundle.add_resource(ftl_source)

    def format_value(
        self, message_id: MessageId, args: dict[str, object] | None = None
    ) -> tuple[str, list[FluentError]]:
        """Format message with fallback chain.

        Tries each locale in priority order until message is found.
        Uses Python 3.13 pattern matching for elegant fallback logic.

        Args:
            message_id: Message identifier (e.g., 'welcome', 'error-404')
            args: Message arguments for variable interpolation

        Returns:
            Tuple of (formatted_value, errors)
            - If message found: Returns formatted result from first bundle with message
            - If not found: Returns ({message_id}, [error])

        Example:
            >>> l10n = FluentLocalization(['lv', 'en'])
            >>> l10n.add_resource('lv', 'welcome = Sveiki!')
            >>> l10n.add_resource('en', 'welcome = Hello!')
            >>> result, errors = l10n.format_value('welcome')
            >>> result
            'Sveiki!'
        """
        errors: list[FluentError] = []

        # Try each locale in priority order (fallback chain)
        for locale in self._locales:
            bundle = self._bundles[locale]

            # Check if this bundle has the message
            if bundle.has_message(message_id):
                # Message exists in this locale - format it
                value, bundle_errors = bundle.format_pattern(message_id, args)
                # FluentBundle.format_pattern returns list[FluentError]
                errors.extend(bundle_errors)
                return (value, errors)

        # No locale had the message - return fallback
        # Use pattern matching for graceful degradation
        match message_id:
            case str() if message_id:
                # Return message ID wrapped in braces (Fluent convention)
                diagnostic = Diagnostic(
                    code=DiagnosticCode.MESSAGE_NOT_FOUND,
                    message=f"Message '{message_id}' not found in any locale",
                )
                errors.append(FluentError(diagnostic))
                return (f"{{{message_id}}}", errors)
            case _:
                # Invalid message ID - treat as simple string error
                errors.append(FluentError("Empty message ID"))
                return ("{???}", errors)

    def has_message(self, message_id: MessageId) -> bool:
        """Check if message exists in any locale.

        Args:
            message_id: Message identifier

        Returns:
            True if message exists in at least one locale
        """
        return any(bundle.has_message(message_id) for bundle in self._bundles.values())

    def get_bundles(self) -> Generator[FluentBundle]:
        """Lazy generator yielding bundles in fallback order.

        Enables advanced use cases where direct bundle access is needed.
        Uses Python 3.13 generator expressions for memory efficiency.

        Yields:
            FluentBundle instances in locale priority order
        """
        yield from (self._bundles[locale] for locale in self._locales)


# ruff: noqa: RUF022 - __all__ organized by category for readability, not alphabetically
__all__ = [
    "FluentLocalization",
    "PathResourceLoader",
    "ResourceLoader",
    # Type aliases for user code type annotations
    "MessageId",
    "LocaleCode",
    "ResourceId",
    "FTLSource",
]
