"""FTLLexBuffer - Best-in-class Python implementation of FTL (Fluent Template Language).

Production-ready FTL parser with 100% test coverage, type safety, and battle-tested reliability.
Supports multilingual applications with comprehensive locale support.

Essential Public API:
    FluentBundle - Single-locale message formatting
    FluentLocalization - Multi-locale orchestration with fallback chains
    parse_ftl - Parse FTL source to AST
    serialize_ftl - Serialize AST to FTL source

    FluentError - Base exception class
    FluentSyntaxError - Parse errors
    FluentReferenceError - Unknown message/term references
    FluentResolutionError - Runtime resolution errors

Advanced Features (via submodules):
    ftllexbuffer.syntax.ast - All AST node types (Resource, Message, Term, Pattern, etc.)
    ftllexbuffer.introspection - Message introspection and variable extraction
    ftllexbuffer.parsing - Bidirectional parsing (parse_number, parse_date, parse_currency, etc.)
    ftllexbuffer.diagnostics - All error types and validation results
    ftllexbuffer.localization - Resource loaders and type aliases
    ftllexbuffer.runtime.functions - Formatting functions (number_format, datetime_format, etc.)

Example - Single locale:
    >>> from ftllexbuffer import FluentBundle
    >>>
    >>> bundle = FluentBundle("lv_LV")
    >>> bundle.add_resource('''
    ... hello = Sveiki, pasaule!
    ... entries-count = {$count ->
    ...     [zero] { $count } ierakstu
    ...     [one] { $count } ieraksts
    ...    *[other] { $count } ieraksti
    ... }
    ... ''')
    >>> bundle.format_pattern("hello")
    'Sveiki, pasaule!'
    >>> bundle.format_pattern("entries-count", {"count": 1})
    '1 ieraksts'
    >>> bundle.format_pattern("entries-count", {"count": 5})
    '5 ieraksti'

Example - Multi-locale fallback:
    >>> from ftllexbuffer import FluentLocalization
    >>>
    >>> l10n = FluentLocalization(['lv', 'en'])
    >>> l10n.add_resource('lv', 'hello = Sveiki!')
    >>> l10n.add_resource('en', 'hello = Hello!\\ngoodbye = Goodbye!')
    >>> l10n.format_value('hello')
    ('Sveiki!', ())
    >>> l10n.format_value('goodbye')  # Falls back to English
    ('Goodbye!', ())

Example - AST manipulation:
    >>> from ftllexbuffer import parse_ftl
    >>> from ftllexbuffer.syntax.ast import Resource, Message
    >>>
    >>> resource = parse_ftl('hello = World')
    >>> assert isinstance(resource, Resource)
    >>> assert isinstance(resource.entries[0], Message)
"""

# Essential Public API - Minimal exports for clean namespace
from .diagnostics import (
    FluentError,
    FluentReferenceError,
    FluentResolutionError,
    FluentSyntaxError,
)
from .localization import FluentLocalization
from .runtime import FluentBundle
from .syntax import parse as parse_ftl
from .syntax import serialize as serialize_ftl

# Version information - Auto-populated from package metadata
# SINGLE SOURCE OF TRUTH: pyproject.toml [project] version
try:
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as _get_version
except ImportError as e:
    # This should never happen on Python 3.13+ (importlib.metadata is stdlib since 3.8)
    raise RuntimeError("importlib.metadata unavailable - Python version too old? " + str(e)) from e

try:
    __version__ = _get_version("ftllexbuffer")
except PackageNotFoundError:
    # Development mode: package not installed yet
    # Run: pip install -e .
    __version__ = "0.0.0+dev"

# Fluent specification conformance
__fluent_spec_version__ = "1.0"  # FTL (Fluent Template Language) Specification v1.0
__spec_url__ = "https://github.com/projectfluent/fluent/blob/master/spec/fluent.ebnf"

# Encoding requirements per Fluent spec recommendations.md
__recommended_encoding__ = "UTF-8"  # Per spec: "The recommended encoding for Fluent files is UTF-8"

# Essential Public API - Reduced from 84 to 8 exports
# Advanced features available via explicit submodule imports
__all__ = [
    # Core API
    "FluentBundle",
    # Exception hierarchy
    "FluentError",
    "FluentLocalization",
    "FluentReferenceError",
    "FluentResolutionError",
    "FluentSyntaxError",
    "__fluent_spec_version__",
    "__recommended_encoding__",
    "__spec_url__",
    # Module metadata
    "__version__",
    "parse_ftl",
    "serialize_ftl",
]
