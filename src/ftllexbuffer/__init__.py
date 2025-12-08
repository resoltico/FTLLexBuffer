"""FTLLexBuffer - Best-in-class Python implementation of FTL (Fluent Template Language).

Production-ready FTL parser with 100% test coverage, type safety, and battle-tested reliability.
Supports multilingual applications with English, Latvian, German, and Polish locales.

Public API - Core:
    FluentBundle - Single-locale message formatting
    FluentLocalization - Multi-locale orchestration with fallback chains
    PathResourceLoader - Disk-based resource loader
    ResourceLoader - Protocol for custom resource loaders
    parse_ftl - Parse FTL source to AST
    serialize_ftl - Serialize AST to FTL source

Public API - Exceptions:
    FluentError - Base exception
    FluentSyntaxError - Parse error
    FluentReferenceError - Unknown message/term
    FluentResolutionError - Runtime error
    FluentCyclicReferenceError - Circular reference

Public API - AST Manipulation:
    Resource, Message, Term, Comment, Junk - AST entry types
    Pattern, TextElement, Placeable - Pattern elements
    VariableReference, MessageReference, FunctionReference - Expression types
    ASTVisitor, ASTTransformer - Visitor pattern for AST traversal

Public API - Advanced:
    FluentParserV1 - Direct parser access
    FUNCTION_REGISTRY - Global function registry
    MessageIntrospection - Message metadata extraction

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
    ('Sveiki!', [])
    >>> l10n.format_value('goodbye')  # Falls back to English
    ('Goodbye!', [])
"""

from __future__ import annotations

from .diagnostics import (
    FluentCyclicReferenceError,
    FluentError,
    FluentParseError,
    FluentReferenceError,
    FluentResolutionError,
    FluentSyntaxError,
)
from .introspection import (
    FunctionCallInfo,
    MessageIntrospection,
    ReferenceInfo,
    VariableInfo,
    extract_variables,
    introspect_message,
)
from .localization import (
    FluentLocalization,
    FTLSource,
    LocaleCode,
    MessageId,
    PathResourceLoader,
    ResourceId,
    ResourceLoader,
)

# Parsing API - Bi-directional localization (v0.8.0 - tuple return types)
from .parsing import (
    has_parse_errors,
    parse_currency,
    parse_date,
    parse_datetime,
    parse_decimal,
    parse_number,
)
from .runtime import FluentBundle
from .runtime.bundle import ValidationResult
from .runtime.function_bridge import FunctionRegistry, FunctionSignature
from .runtime.functions import (
    FUNCTION_REGISTRY,
    currency_format,
    datetime_format,
    number_format,
)
from .syntax import parse as parse_ftl
from .syntax import serialize as serialize_ftl
from .syntax.ast import (
    Annotation,
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
    Span,
    StringLiteral,
    Term,
    TermReference,
    TextElement,
    VariableReference,
    Variant,
)
from .syntax.parser import FluentParserV1
from .syntax.type_guards import (
    has_value,
    is_comment,
    is_junk,
    is_message,
    is_placeable,
    is_term,
    is_text_element,
)
from .syntax.visitor import ASTTransformer, ASTVisitor

# Version information - Auto-populated from package metadata
# SINGLE SOURCE OF TRUTH: pyproject.toml [project] version
try:
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as _get_version
except ImportError as e:
    # This should never happen on Python 3.13+ (importlib.metadata is stdlib since 3.8)
    raise RuntimeError(
        "importlib.metadata unavailable - Python version too old? " + str(e)
    ) from e

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

# ruff: noqa: RUF022 - __all__ organized by category for readability, not alphabetically
__all__ = [
    # Core API - Message formatting
    "FluentBundle",
    "FluentLocalization",
    "ValidationResult",
    # Resource loading
    "PathResourceLoader",
    "ResourceLoader",
    # Type aliases for user code annotations
    "MessageId",
    "LocaleCode",
    "ResourceId",
    "FTLSource",
    # Parsing and serialization
    "FluentParserV1",
    "parse_ftl",
    "serialize_ftl",
    # Exception hierarchy
    "FluentError",
    "FluentParseError",
    "FluentSyntaxError",
    "FluentReferenceError",
    "FluentResolutionError",
    "FluentCyclicReferenceError",
    # Introspection
    "MessageIntrospection",
    "VariableInfo",
    "FunctionCallInfo",
    "ReferenceInfo",
    "extract_variables",
    "introspect_message",
    # Advanced - Function registry and formatting
    "FunctionRegistry",
    "FunctionSignature",
    "FUNCTION_REGISTRY",
    "number_format",
    "datetime_format",
    "currency_format",
    # Parsing API - Bi-directional (v0.8.0 - tuple return types)
    "has_parse_errors",
    "parse_number",
    "parse_decimal",
    "parse_date",
    "parse_datetime",
    "parse_currency",
    # AST - Core entry types
    "Resource",
    "Message",
    "Term",
    "Attribute",
    "Comment",
    "Junk",
    # AST - Pattern elements
    "Pattern",
    "TextElement",
    "Placeable",
    # AST - Expression types
    "VariableReference",
    "MessageReference",
    "TermReference",
    "FunctionReference",
    "SelectExpression",
    "Variant",
    "NumberLiteral",
    "StringLiteral",
    # AST - Support types
    "Identifier",
    "CallArguments",
    "NamedArgument",
    "Span",
    "Annotation",
    # AST - Visitor pattern
    "ASTVisitor",
    "ASTTransformer",
    # AST - Type guards
    "is_message",
    "is_term",
    "is_comment",
    "is_junk",
    "is_placeable",
    "is_text_element",
    "has_value",
    # Module constants
    "__version__",
    "__fluent_spec_version__",
    "__spec_url__",
    "__recommended_encoding__",
]
