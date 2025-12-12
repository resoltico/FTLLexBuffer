<!--
RETRIEVAL_HINTS:
  keywords: [changelog, release notes, version history, breaking changes, migration, what's new]
  answers: [what changed in version, breaking changes, release history, version changes]
  related: [docs/MIGRATION.md, VERSIONING.md]
-->
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.11.1] - 2025-12-12

### Fixed

- **Documentation**
  - Fixed docstring examples in `__init__.py` to show tuple returns `()` instead of list returns `[]` (matches v0.11.0 API)
  - Fixed `FluentLocalization` docstring example to show tuple return (matches v0.11.0 API)

### Changed

- **Documentation**
  - Documentation overhaul, generally

## [0.11.0] - 2025-12-10

### Breaking Changes

- **Immutable error collections - All error tuples instead of lists**
  - `FluentBundle.format_pattern()` now returns `tuple[str, tuple[FluentError, ...]]` (was `tuple[str, list[FluentError]]`)
  - `FluentBundle.format_value()` now returns `tuple[str, tuple[FluentError, ...]]` (was `tuple[str, list[FluentError]]`)
  - `FluentResolver.resolve_message()` now returns `tuple[str, tuple[FluentError, ...]]` (was `tuple[str, list[FluentError]]`)
  - `ParseError.expected` changed from `list[str]` to `tuple[str, ...]`
  - `FormatCache._CacheValue` changed from `tuple[str, list[FluentError]]` to `tuple[str, tuple[FluentError, ...]]`
  - **Rationale**: Immutable data structures prevent accidental mutation, align with frozen dataclasses, and improve thread safety
  - **Impact**: Code that mutates error lists or compares with empty lists must be updated
  - **Migration**:
    ```python
    # OLD (v0.10.0):
    result, errors = bundle.format_pattern("hello")
    assert errors == []  # Compare with empty list
    errors.append(custom_error)  # Mutation allowed

    # NEW (v0.11.0):
    result, errors = bundle.format_pattern("hello")
    assert errors == ()  # Compare with empty tuple
    # errors.append(...) would raise AttributeError
    ```

### Changed

- **Parser architecture refactored into focused modules**
  - Monolithic `parser.py` (1,872 lines) split into 7 specialized modules:
    - `parser/core.py` - FluentParserV1 class and parse() entry point
    - `parser/primitives.py` - Identifier, number, string literal parsers
    - `parser/whitespace.py` - Whitespace utilities and continuation detection
    - `parser/patterns.py` - Pattern and placeable parsing
    - `parser/expressions.py` - Select expressions, inline expressions, function calls
    - `parser/entries.py` - Message, term, attribute, comment parsing
    - `parser/__init__.py` - Public API re-exports
  - **100% backward compatible**: `from ftllexbuffer.syntax.parser import FluentParserV1` still works
  - **Rationale**: Improves code maintainability, reduces cognitive load, enables better testing isolation
  - **Impact**: No user-visible changes - internal refactoring only
  - **Benefits**:
    - Cleaner separation of concerns (primitives → patterns → expressions → entries)
    - Easier to locate and modify specific parsing logic
    - Reduced file size enables faster IDE navigation and code review
    - Each module has focused, testable responsibility

### Internal

- **Circular import handling with runtime imports**
  - Parser modules use runtime imports with `# noqa: PLC0415` to avoid circular dependencies
  - Circular dependency: `expressions.py` ↔ `patterns.py` (select expressions contain patterns, patterns contain placeables from expressions)
  - **Pattern**: Import within function scope only where needed
  - Added Pylint `cyclic-import` to global disable list (architectural necessity for grammar implementation)

- **Absolute imports throughout parser modules**
  - All parser modules use absolute imports (`from ftllexbuffer.syntax.ast import ...`)
  - Eliminates relative import confusion (`from ..ast` vs `from ...ast`)
  - Ruff TID252 compliance enforced via linting

- **Complexity suppressions**
  - Added `# noqa: PLR0912` to complex grammar-driven methods:
    - `parse_pattern()` - 13 branches (handles multiline continuations, placeables, stop conditions)
    - `parse_term()` - 14 branches (handles term syntax, attributes, multiline patterns)
    - `parse_inline_expression()` - 20 branches (dispatches to all expression types)
  - **Rationale**: Parser complexity is inherent to FTL grammar, not code smell

### Migration Notes

#### For Users

**BREAKING CHANGES SUMMARY**:

1. **Error tuple returns**: Format functions return immutable tuples instead of mutable lists
2. **Empty error checks**: Compare with `()` instead of `[]`
3. **No error mutation**: Cannot append/modify error collections

**Migration Steps**:

```python
# 1. Update empty error checks
# OLD (v0.10.0):
result, errors = bundle.format_pattern("hello")
if errors == []:
    print("Success")

# NEW (v0.11.0):
result, errors = bundle.format_pattern("hello")
if errors == ():  # or: if not errors
    print("Success")

# 2. Update error iteration (no changes needed - tuples are iterable)
for error in errors:
    print(error)  # Works the same

# 3. Remove error mutation
# OLD (v0.10.0):
result, errors = bundle.format_pattern("hello")
errors.append(custom_error)  # Mutation

# NEW (v0.11.0):
result, errors = bundle.format_pattern("hello")
# Create new tuple with additional error
errors = (*errors, custom_error)
```

#### For Library Developers

**Parser module structure** (internal API):
```python
# All parser functionality still available from single import
from ftllexbuffer.syntax.parser import FluentParserV1

# Internal modules (not part of public API):
# - ftllexbuffer.syntax.parser.core
# - ftllexbuffer.syntax.parser.primitives
# - ftllexbuffer.syntax.parser.whitespace
# - ftllexbuffer.syntax.parser.patterns
# - ftllexbuffer.syntax.parser.expressions
# - ftllexbuffer.syntax.parser.entries
```

**Updated type signatures**:
```python
# Format functions
FluentBundle.format_pattern(
    message_id: str,
    args: Mapping[str, FluentValue] | None = None,
    *,
    attribute: str | None = None,
) -> tuple[str, tuple[FluentError, ...]]  # Changed from list[FluentError]

FluentBundle.format_value(
    message_id: str,
    args: dict[str, FluentValue] | None = None
) -> tuple[str, tuple[FluentError, ...]]  # Changed from list[FluentError]

# Resolver
FluentResolver.resolve_message(
    message: Message,
    args: Mapping[str, FluentValue] | None = None,
    attribute: str | None = None,
) -> tuple[str, tuple[FluentError, ...]]  # Changed from list[FluentError]

# ParseError
@dataclass(frozen=True, slots=True)
class ParseError:
    message: str
    cursor: Cursor
    expected: tuple[str, ...] = field(default_factory=tuple)  # Changed from list[str]
```

## [0.10.0] - 2025-12-10

### Breaking Changes

- **Minimal root API - Advanced features require submodule imports**
  - Root `ftllexbuffer` now exports only 12 essential symbols (was 84)
  - Core API (4): `FluentBundle`, `FluentLocalization`, `parse_ftl`, `serialize_ftl`
  - Exceptions (4): `FluentError`, `FluentSyntaxError`, `FluentReferenceError`, `FluentResolutionError`
  - Metadata (4): `__version__`, `__fluent_spec_version__`, `__spec_url__`, `__recommended_encoding__`
  - **Impact**: All advanced features now require explicit submodule imports
  - **Migration**: Import from specific submodules instead of root
    ```python
    # OLD (v0.9.x - no longer works):
    from ftllexbuffer import Resource, Message, extract_variables, CommentType

    # NEW (v0.10.0 - required):
    from ftllexbuffer import FluentBundle, parse_ftl
    from ftllexbuffer.syntax.ast import Resource, Message
    from ftllexbuffer.introspection import extract_variables
    from ftllexbuffer.enums import CommentType
    ```
  - **Available submodules**:
    - `ftllexbuffer.syntax.ast` - All AST node types (Resource, Message, Term, etc.)
    - `ftllexbuffer.introspection` - Message introspection utilities
    - `ftllexbuffer.parsing` - Bidirectional parsing functions
    - `ftllexbuffer.diagnostics` - All diagnostic and error types
    - `ftllexbuffer.localization` - Resource loaders
    - `ftllexbuffer.runtime.functions` - Formatting function implementations
    - `ftllexbuffer.syntax.visitor` - AST traversal utilities
    - `ftllexbuffer.enums` - Enumeration types

- **Unified ValidationResult structure**
  - Merged two different `ValidationResult` classes into single unified type
  - Now located in `ftllexbuffer.diagnostics.validation`
  - Structure changed to include all validation outputs:
    - `errors: tuple[ValidationError, ...]` - Syntax errors
    - `warnings: tuple[ValidationWarning, ...]` - Semantic warnings
    - `annotations: tuple[Annotation, ...]` - Parser annotations (Junk entries)
  - `is_valid` is now a computed property (returns `True` if no errors and no annotations)
  - **Impact**: Code accessing `ValidationResult` must update imports and field access
  - **Migration**:
    ```python
    # OLD (v0.9.x):
    from ftllexbuffer.runtime.bundle import ValidationResult
    result = bundle.validate_resource(ftl_source)
    if result.errors:
        print(result.errors[0].message)

    # NEW (v0.10.0):
    from ftllexbuffer.diagnostics.validation import ValidationResult
    result = bundle.validate_resource(ftl_source)
    if not result.is_valid:  # Computed property
        for error in result.errors:
            print(error.message)
        for annotation in result.annotations:
            print(annotation.content)
    ```
  - Factory methods available: `ValidationResult.valid()`, `ValidationResult.invalid(...)`, `ValidationResult.from_annotations(...)`

- **Explicit locale validation - No more silent failures**
  - `LocaleContext` no longer silently swallows locale validation errors
  - Invalid locales now return explicit error results or raise exceptions
  - **Impact**: Invalid locale codes no longer silently fall back to default formatting
  - **Behavior change**: Formatting functions return Fluent error placeholders when locale is invalid
  - **Example**:
    ```python
    # v0.9.x - silently used fallback formatting
    bundle = FluentBundle("invalid_locale")  # Warning logged, continues

    # v0.10.0 - explicit error handling
    bundle = FluentBundle("invalid_locale")  # Same behavior at bundle level
    # But format calls with invalid locale return error placeholders: "{Message}"
    ```
  - **For custom functions**: Use `LocaleContext.create()` to get explicit validation results

- **Specific exception handling - More precise error reporting**
  - Broad `Exception` catches replaced with specific exception types
  - Unexpected errors from Babel and internal operations now propagate instead of being swallowed
  - Circular reference detection now uses explicit `RecursionError` handling
  - **Impact**: Different exceptions may be raised in error conditions
  - **Migration**: If you catch exceptions, update to handle specific types:
    - `TypeError`, `ValueError`, `KeyError` for function argument errors
    - `RecursionError` for circular message references
    - `InvalidOperation` (from decimal module) for numeric formatting errors

- **Stricter type safety - `Any` types replaced with precise unions**
  - All public APIs now use specific union types instead of `Any`
  - New type aliases:
    - `FluentValue = str | int | float | bool | Decimal | datetime | date | None`
    - `FluentFunction` is now a Protocol with typed signature
  - **Impact**: Better type checking, may reveal previously hidden type errors
  - **Benefit**: IDEs and type checkers provide more accurate completions and error detection

### Improved

- **Currency parsing now uses comprehensive CLDR data**
  - Replaced 20 hardcoded currency mappings with dynamic CLDR extraction
  - **Coverage**: 690 locales with territory-specific currency defaults (35x improvement)
  - **Accuracy**: All currency symbols and locale defaults automatically sourced from Unicode CLDR
  - **Maintainability**: Automatically updated with Babel/CLDR releases, no manual maintenance
  - **Impact**: Currency parsing now supports 35x more locales with correct defaults
  - **Example**:
    ```python
    # v0.9.x: Only 20 hardcoded locales (e.g., sv_SE not supported)
    parse_currency("$100", "sv_SE", infer_from_locale=True)  # Error

    # v0.10.0: 690 locales automatically supported from CLDR
    parse_currency("$100", "sv_SE", infer_from_locale=True)  # Works! SEK inferred
    ```
  - Ambiguous symbols ($, ¢, ₨, ₱, kr) still require explicit `default_currency` or `infer_from_locale=True`

- **Enhanced type safety across entire codebase**
  - Python 3.13 baseline enables native PEP 695 generics and type aliases
  - All type aliases use modern `type` statement syntax
  - Removed obsolete `from __future__ import annotations` (Python 3.13 has PEP 649 by default)
  - `FluentFunction` is now a proper Protocol with typed parameters
  - `FunctionCategory` uses Enum instead of Literal for better extensibility
  - **Impact**: Better IDE support, more accurate type checking, fewer runtime type errors

### Changed

- **Locale normalization centralized**
  - New `normalize_locale()` utility function in `ftllexbuffer.locale_utils`
  - Handles BCP 47 (en-US) to POSIX (en_US) conversion consistently
  - Used throughout parsing and formatting modules
  - **Impact**: More consistent locale handling, easier to maintain

- **Validation result immutability enforced**
  - `ValidationResult` now uses frozen dataclass with immutable tuples
  - Fields: `errors`, `warnings`, `annotations` are all tuples (not lists)
  - **Impact**: Prevents accidental mutation of validation results

### Internal

- **Parser optimization**
  - Added cursor methods for whitespace handling: `skip_spaces()`, `skip_whitespace()`, `expect()`
  - Eliminated 7 duplicate whitespace-skipping loops in parser
  - Improved parser maintainability and reduced code duplication

- **Visitor pattern performance**
  - `ASTVisitor` now caches method dispatch for significant performance improvement
  - Reduces repeated string formatting and `getattr` lookups on every node visit

- **Thread-safe serialization and validation**
  - `FluentSerializer` no longer uses mutable instance state
  - `SemanticValidator` no longer uses mutable instance state
  - Both are now fully reentrant and thread-safe

- **Centralized linter configuration**
  - Consolidated 193 lines of per-file lint ignores to 63 lines (67% reduction)
  - All Pylint suppressions moved from inline comments to global configuration
  - Cleaner code with centralized quality control rules

### Migration Guide

#### Import Changes

The most significant breaking change is the slimmed-down root API. Update your imports:

```python
# OLD (v0.9.x) - importing from root
from ftllexbuffer import (
    Resource, Message, Term, Comment, Junk,
    extract_variables, extract_references,
    CommentType, VariableContext, ReferenceKind,
    ValidationError, ValidationWarning,
)

# NEW (v0.10.0) - import from submodules
from ftllexbuffer import FluentBundle, parse_ftl, serialize_ftl
from ftllexbuffer.syntax.ast import Resource, Message, Term, Comment, Junk
from ftllexbuffer.introspection import extract_variables, extract_references
from ftllexbuffer.enums import CommentType, VariableContext, ReferenceKind
from ftllexbuffer.diagnostics.validation import ValidationError, ValidationWarning
```

#### ValidationResult Changes

```python
# OLD (v0.9.x) - list-based, mutable
from ftllexbuffer.runtime.bundle import ValidationResult
result = bundle.validate_resource(ftl_source)
for error in result.errors:  # list
    print(error.message)

# NEW (v0.10.0) - tuple-based, immutable
from ftllexbuffer.diagnostics.validation import ValidationResult
result = bundle.validate_resource(ftl_source)
if not result.is_valid:  # Computed property
    for error in result.errors:  # tuple
        print(error.message)
    for annotation in result.annotations:  # tuple
        print(annotation.content)
```

#### Exception Handling

```python
# OLD (v0.9.x) - broad catches
try:
    result = bundle.format_pattern("message")
except Exception as e:
    log_error(e)

# NEW (v0.10.0) - specific catches
try:
    result = bundle.format_pattern("message")
except RecursionError:
    log_error("Circular reference detected")
except (TypeError, ValueError, KeyError) as e:
    log_error(f"Function argument error: {e}")
```

#### Type Annotations

If you use type annotations with FTLLexBuffer:

```python
# OLD (v0.9.x) - Any types accepted
from typing import Any

def process_value(value: Any) -> str:
    return bundle.format_pattern("msg", {"val": value})

# NEW (v0.10.0) - use FluentValue
from ftllexbuffer.runtime.resolver import FluentValue

def process_value(value: FluentValue) -> str:
    return bundle.format_pattern("msg", {"val": value})[0]
```

## [0.9.1] - 2025-12-09

### Fixed

- Fixes overly broad import mocking in tests by restricting blocked modules to `importlib.metadata` and related backports, restoring correct imports for internal `function_metadata`.

## [0.9.0] - 2025-12-09

### Breaking Changes

- **Enums replace magic strings**
  - `Comment.type` changed from `str` to `CommentType` enum
    - `CommentType.COMMENT`, `CommentType.GROUP`, `CommentType.RESOURCE`
  - `VariableInfo.context` changed from `str` to `VariableContext` enum
    - `VariableContext.PATTERN`, `VariableContext.SELECTOR`, `VariableContext.VARIANT`, `VariableContext.FUNCTION_ARG`
  - `ReferenceInfo.kind` changed from `str` to `ReferenceKind` enum
    - `ReferenceKind.MESSAGE`, `ReferenceKind.TERM`
  - **Impact**: All string comparisons must be updated to use enum values
  - **Migration**: Import enums from `ftllexbuffer` and use enum values instead of strings

- **NumberLiteral structure changed**
  - `NumberLiteral.value` changed from `str` to `int | float` (parsed value)
  - Added `NumberLiteral.raw: str` for original source representation
  - Removed `NumberLiteral.parsed_value` property
  - **Impact**: Code accessing `.value` expecting string will break
  - **Impact**: Code using `.parsed_value` must change to `.value`
  - **Migration**: Use `.value` for numeric value, `.raw` for serialization

- **Cursor.line_col property removed**
  - Property was misleading (O(n) operation appearing as O(1))
  - Use `cursor.compute_line_col()` method instead
  - **Impact**: All `cursor.line_col` must change to `cursor.compute_line_col()`

- **Parsing API standardized to return None on failure**
  - `parse_number()` now returns `tuple[float | None, list[FluentParseError]]`
  - `parse_decimal()` now returns `tuple[Decimal | None, list[FluentParseError]]`
  - Previously returned sentinel values (0.0, Decimal("0")) on failure
  - **Impact**: Code checking for sentinel values must change to check for None
  - **Migration**: Use `if result is not None:` instead of `if result != 0.0:`

- **Visitor pattern matches stdlib convention**
  - `ASTVisitor.generic_visit()` now automatically traverses all child nodes
  - Previously, each `visit_*()` method explicitly traversed children
  - All `visit_*()` methods removed - override only when custom behavior needed
  - **Impact**: All custom visitors must be updated
  - **Migration**: Override `visit_*()` methods only for custom behavior, call `self.generic_visit(node)` for traversal

- **Visitor type safety improved**
  - All visitor methods now use `ASTNode` instead of `Any`
  - Added `ASTNode` Protocol for structural typing
  - **Impact**: Better type checking, catches more errors at type-check time
  - **Migration**: Ensure custom visitors follow protocol

- **ValidationResult uses structured errors**
  - `ValidationResult.errors` changed from `list[Junk]` to `list[ValidationError]`
  - `ValidationResult.warnings` changed from `list[str]` to `list[ValidationWarning]`
  - `ValidationError` has fields: `code`, `message`, `content`, `line`, `column`
  - `ValidationWarning` has fields: `code`, `message`, `context`
  - **Impact**: Code accessing error/warning fields must be updated
  - **Migration**: Access structured fields instead of Junk nodes or plain strings

- **Span handling standardized**
  - Only top-level entry nodes have spans: `Message`, `Term`, `Comment`, `Junk`
  - Removed spans from: `Attribute`, `SelectExpression`, `Variant`
  - **Impact**: Code accessing `.span` on these nodes will fail
  - **Migration**: Track spans externally or use parent entry span

- **Type guards consolidated to AST nodes**
  - Removed `guards.py` and `syntax/type_guards.py` modules
  - All type guards now live as static `.guard()` methods on AST node classes
  - Removed `is_message`, `is_term`, `is_comment`, `is_junk`, `is_placeable`, `is_text_element`, `has_value` from package exports
  - **Impact**: Code using standalone type guard functions will break
  - **Migration**: Use static methods directly: `Message.guard(entry)` instead of `is_message(entry)`

- **Import structure simplified**
  - Eliminated all unnecessary runtime imports (PLC0415)
  - All module imports now at top-level except one legitimate lazy import
  - Cleaner module dependencies: `diagnostics → syntax → runtime`
  - **Impact**: Import performance slightly improved
  - **No user migration needed**: This is an internal refactoring

- **Parser error messages simplified**
  - Removed internal Result monad abstraction from parser implementation
  - Parser methods now use stdlib `ParseResult[T] | None` pattern instead of custom `Success[T] | Failure[E]`
  - Junk entry annotations now contain generic "Parse error" message instead of detailed error descriptions
  - Parser robustness unchanged: still creates Junk entries for invalid syntax
  - **Impact**: Error messages in Junk annotations are less specific
  - **Migration**: If code depends on specific error message text in Junk annotations, use alternative error detection strategies

### Added

- **Type-safe enums** (`ftllexbuffer.enums`)
  - `CommentType` - Comment type enumeration
  - `VariableContext` - Variable context enumeration
  - `ReferenceKind` - Reference kind enumeration
  - All enums have `__str__()` returning value for serialization

- **Structured validation errors** (`ftllexbuffer.runtime.bundle`)
  - `ValidationError` - Structured syntax error with code, message, content, line, column
  - `ValidationWarning` - Structured semantic warning with code, message, context
  - Both exported from main package for easy import

- **ASTNode Protocol** (`ftllexbuffer.syntax.ast`)
  - Base protocol for all AST nodes
  - Enables type-safe visitor patterns
  - Uses structural typing (no inheritance required)

- **__slots__ for memory efficiency**
  - `FluentParserV1` - Empty slots (stateless)
  - `FluentBundle` - 8 slots (sorted alphabetically)
  - `FluentResolver` - 7 slots (sorted alphabetically)
  - Reduces memory usage per instance

- **__repr__() methods for debugging**
  - `FluentBundle` - Shows locale and message/term counts
  - `FluentLocalization` - Shows locale list and bundle count
  - `FunctionRegistry` - Shows function count
  - Better REPL and debugging experience

### Changed

- **Parser creates parsed numbers immediately**
  - NumberLiteral constructed with parsed value and raw string
  - No lazy parsing
  - **Performance**: Single parse instead of multiple accesses

- **Serializer uses NumberLiteral.raw**
  - Preserves original number format in round-trip
  - Uses `.raw` field instead of `.value`

### Improved

- **Plural rules now use Babel's CLDR data**
  - Refactored from 352 lines of hardcoded rules to Babel's CLDR implementation
  - **Locale support**: Expanded from 30 to 200+ locales with full CLDR compliance
  - **Accuracy**: CLDR-compliant plural rules match official Unicode specifications
  - **Maintainability**: Automatically updated with Babel releases, no manual rule maintenance
  - **Impact**: More languages supported with correct plural rules, including complex cases (Latvian fractions, Arabic 6-category system)
  - **Example**: Latvian decimal `10.1` now correctly returns `"one"` per CLDR fractional digit rules

- **Locale format handling standardized**
  - All parsing functions now accept both BCP 47 (`en-US`) and POSIX (`en_US`) locale formats
  - Automatic normalization to underscore format for Babel compatibility
  - **Functions updated**: `parse_number()`, `parse_decimal()`, `parse_currency()`
  - **Impact**: More flexible API, accepts both common locale format conventions
  - **No migration needed**: Both formats work seamlessly

### Removed

- **Dead code elimination**
  - Removed try/except for TypeIs import (Python 3.13 baseline)
  - Removed empty `TYPE_CHECKING` blocks
  - Cleaned up unnecessary compatibility code

### Internal

- **Code quality improvements**
  - All async operations properly tracked
  - Consistent code organization
  - Improved type safety throughout

### Migration Guide

#### Enum Migration

```python
# OLD (0.8.0):
if comment.type == "comment":
    ...
if var_info.context == "pattern":
    ...
if ref.kind == "message":
    ...

# NEW (0.9.0):
from ftllexbuffer import CommentType, VariableContext, ReferenceKind

if comment.type == CommentType.COMMENT:
    ...
if var_info.context == VariableContext.PATTERN:
    ...
if ref.kind == ReferenceKind.MESSAGE:
    ...
```

#### NumberLiteral Migration

```python
# OLD (0.8.0):
number_str = num_literal.value  # Was string
number_val = num_literal.parsed_value  # Property

# NEW (0.9.0):
number_val = num_literal.value  # Now int|float
number_str = num_literal.raw  # Original string
```

#### Cursor Migration

```python
# OLD (0.8.0):
line, col = cursor.line_col  # Property

# NEW (0.9.0):
line, col = cursor.compute_line_col()  # Method (makes O(n) cost explicit)
```

#### Parsing API Migration

```python
# OLD (0.8.0):
from ftllexbuffer.parsing import parse_number
result, errors = parse_number("invalid", "en_US")
if result == 0.0:  # Sentinel value
    print("Parse failed")

# NEW (0.9.0):
result, errors = parse_number("invalid", "en_US")
if result is None:  # Explicit None
    print("Parse failed")
```

#### Visitor Pattern Migration

```python
# OLD (0.8.0):
class MyVisitor(ASTVisitor):
    def visit_Message(self, node):
        print(f"Message: {node.id.name}")
        # Manually traverse children
        self.visit(node.id)
        if node.value:
            self.visit(node.value)
        return self.generic_visit(node)

# NEW (0.9.0):
class MyVisitor(ASTVisitor):
    def visit_Message(self, node):
        print(f"Message: {node.id.name}")
        # generic_visit() automatically traverses children
        return self.generic_visit(node)
```

#### ValidationResult Migration

```python
# OLD (0.8.0):
result = bundle.validate_resource(ftl_source)
for error in result.errors:
    print(f"Error: {error.content}")  # Junk node
for warning in result.warnings:
    print(f"Warning: {warning}")  # Plain string

# NEW (0.9.0):
result = bundle.validate_resource(ftl_source)
for error in result.errors:
    print(f"Error [{error.code}]: {error.message}")  # Structured
for warning in result.warnings:
    print(f"Warning [{warning.code}]: {warning.message}")  # Structured
```

#### Span Handling Migration

```python
# OLD (0.8.0):
select_expr = ...  # SelectExpression
if select_expr.span:
    print(f"Located at: {select_expr.span}")

# NEW (0.9.0):
# SelectExpression no longer has span
# Use parent Message/Term span or track externally
message = ...  # Message containing SelectExpression
if message.span:
    print(f"Located at: {message.span}")
```

#### Type Guard Migration

```python
# OLD (0.8.0):
from ftllexbuffer import is_message, is_term, is_placeable
for entry in resource.entries:
    if is_message(entry):
        print(f"Message: {entry.id.name}")

# NEW (0.9.0):
from ftllexbuffer import Message, Term, Placeable
for entry in resource.entries:
    if Message.guard(entry):
        print(f"Message: {entry.id.name}")
```

## [0.8.0] - 2025-12-08

### Breaking Changes

- **All parsing functions now return tuple instead of raising exceptions**
  - `parse_number()` returns `tuple[float, list[FluentParseError]]`
  - `parse_decimal()` returns `tuple[Decimal, list[FluentParseError]]`
  - `parse_date()` returns `tuple[date | None, list[FluentParseError]]`
  - `parse_datetime()` returns `tuple[datetime | None, list[FluentParseError]]`
  - `parse_currency()` returns `tuple[tuple[Decimal, str] | None, list[FluentParseError]]`
  - **Rationale**: Consistent with "never raise" philosophy - errors are data, not control flow
  - **Impact**: All code using parse_* functions must be updated to handle tuple returns

- **Removed `strict` parameter from all parsing functions**
  - Functions NEVER raise exceptions - errors are always returned in the list
  - No more strict/non-strict distinction
  - **Migration**: Remove `strict=True/False` arguments, check error list instead

- **Type guards updated for new API**
  - `is_valid_decimal(value: Decimal)` - validates finite Decimal (not NaN/Infinity)
  - `is_valid_number(value: float)` - validates finite float (not NaN/Infinity)
  - `is_valid_currency(value: tuple[Decimal, str] | None)` - validates non-None with finite amount
  - `is_valid_date(value: date | None)` - validates non-None date
  - `is_valid_datetime(value: datetime | None)` - validates non-None datetime
  - Note: `is_valid_decimal` and `is_valid_number` no longer accept None (parse functions return default values on error, not None)

### Added

- **`has_parse_errors()` helper function**
  - Check if parsing returned any errors: `has_parse_errors(errors) -> bool`
  - Returns True if error list is non-empty
  - **Use case**: Clean pattern for checking parse success before using result
  - **Example**:
    ```python
    from ftllexbuffer.parsing import parse_decimal
    from ftllexbuffer.parsing.guards import has_parse_errors, is_valid_decimal

    result, errors = parse_decimal("1,234.56", "en_US")
    if not has_parse_errors(errors) and is_valid_decimal(result):
        # Safe to use result
        total = result * Decimal("1.21")
    ```

- **Runtime type checking for non-string inputs**
  - Parse functions now gracefully handle non-string inputs (return error instead of TypeError)
  - **Example**: `parse_date(123, "en_US")` returns `(None, [FluentParseError(...)])`

- **Parsing diagnostic codes (4000-4999)**
  - `PARSE_NUMBER_FAILED` (4001)
  - `PARSE_DECIMAL_FAILED` (4002)
  - `PARSE_DATE_FAILED` (4003)
  - `PARSE_DATETIME_FAILED` (4004)
  - `PARSE_CURRENCY_FAILED` (4005)
  - `PARSE_LOCALE_UNKNOWN` (4006)
  - `PARSE_CURRENCY_AMBIGUOUS` (4007)
  - `PARSE_CURRENCY_SYMBOL_UNKNOWN` (4008)
  - `PARSE_AMOUNT_INVALID` (4009)

- **Cache unhashable argument handling**
  - `FormatCache` now gracefully handles unhashable args (lists, dicts)
  - Returns cache miss instead of crashing with `TypeError`
  - New `unhashable_skips` property for monitoring

### Fixed

- **Date parsing regex boundary issue**
  - Token-based Babel-to-strptime converter replaces fragile regex approach
  - Correctly handles patterns like `d.MM.yyyy` where `d` is adjacent to punctuation
  - `_tokenize_babel_pattern()` properly extracts pattern tokens

### Changed

- **Error handling philosophy**: Parse functions now follow the same "never raise" pattern as format functions
- **Default return values on error**:
  - `parse_number()` returns `0.0` on error
  - `parse_decimal()` returns `Decimal("0")` on error
  - `parse_date()` returns `None` on error
  - `parse_datetime()` returns `None` on error
  - `parse_currency()` returns `None` on error

### Migration Notes

#### For Users

**BREAKING CHANGES SUMMARY**:

1. **Tuple return type**: All parse functions return `(result, errors)` tuple
2. **No more exceptions**: Check `errors` list instead of catching `ValueError`
3. **No `strict` parameter**: Remove `strict=True/False` arguments

**Migration Steps**:

```python
# OLD (v0.7.0): Exception-based error handling
try:
    amount = parse_decimal(user_input, locale)
except ValueError as e:
    show_error(f"Invalid: {e}")
    return

# NEW (v0.8.0): Tuple-based error handling
result, errors = parse_decimal(user_input, locale)
if errors:
    show_error(f"Invalid: {errors[0]}")
    return
amount = result

# OLD (v0.7.0): Non-strict mode
amount = parse_decimal(user_input, locale, strict=False)
if amount is None:
    amount = Decimal("0")

# NEW (v0.8.0): Check errors list
result, errors = parse_decimal(user_input, locale)
if errors:
    result = Decimal("0")
amount = result

# NEW (v0.8.0): Using type guards
from ftllexbuffer.parsing.guards import has_parse_errors, is_valid_decimal

result, errors = parse_decimal(user_input, locale)
if not has_parse_errors(errors) and is_valid_decimal(result):
    # mypy knows result is finite Decimal
    process_payment(result)
```

#### For Library Developers

**Updated Public API**:
```python
from ftllexbuffer.parsing import (
    parse_number,    # -> tuple[float, list[FluentParseError]]
    parse_decimal,   # -> tuple[Decimal, list[FluentParseError]]
    parse_date,      # -> tuple[date | None, list[FluentParseError]]
    parse_datetime,  # -> tuple[datetime | None, list[FluentParseError]]
    parse_currency,  # -> tuple[tuple[Decimal, str] | None, list[FluentParseError]]
)

from ftllexbuffer.parsing.guards import (
    has_parse_errors,    # NEW: Check if errors list is non-empty
    is_valid_decimal,    # Updated: No longer accepts None
    is_valid_number,     # Updated: No longer accepts None
    is_valid_currency,   # Validates non-None tuple with finite amount
    is_valid_date,       # Validates non-None date
    is_valid_datetime,   # Validates non-None datetime
)
```

**Error handling pattern**:
```python
result, errors = parse_decimal(value, locale)
if has_parse_errors(errors):
    # Handle errors - result is default value (Decimal("0"))
    for error in errors:
        log.warning(f"Parse error: {error}")
elif is_valid_decimal(result):
    # Safe to use result - mypy knows it's finite Decimal
    process(result)
```

---

## [0.7.0] - 2025-12-07

### Breaking Changes

- **parse_date() / parse_datetime() safety improvements**
  - Removed ambiguous fallback patterns to prevent silent misinterpretation
  - Now supports ONLY: ISO 8601 + locale-specific CLDR patterns
  - **Impact**: Ambiguous formats like "1/2/25" will ONLY parse if they match the locale's CLDR pattern
  - **Rationale**: Date ambiguity is a safety-critical issue in financial applications
    - "1/2/25" means Jan 2 in en_US but Feb 1 in en_GB
    - Previous fallback patterns could silently misinterpret dates
  - **Migration**: Use ISO 8601 (YYYY-MM-DD) for unambiguous, locale-independent dates
  - **2-digit year limitation**: Python's strptime interprets 00-68 as 2000-2068, 69-99 as 1969-1999
  - **Example**:
    ```python
    # v0.6.0 (unsafe): Ambiguous date accepted with fallback pattern
    parse_date("1/2/25", "en_GB")  # → Jan 2 (WRONG - should be Feb 1)

    # v0.7.0 (safe): Only CLDR patterns or ISO 8601
    parse_date("1/2/25", "en_US")   # → Jan 2 (matches en_US CLDR: M/d/yy)
    parse_date("1/2/25", "en_GB")   # → Feb 1 (matches en_GB CLDR: d/M/yy)
    parse_date("2025-01-02", "any") # → Jan 2 (ISO 8601 - always unambiguous)
    ```

- **parse_currency() ambiguous symbol handling**
  - Ambiguous currency symbols ($, ¢, ₨, ₱, kr) now require explicit `default_currency` or `infer_from_locale=True`
  - **Rationale**: Prevents silent misidentification in multi-currency applications
    - "$" is used by USD, CAD, AUD, SGD, HKD, NZD, MXN, and others
    - Previous behavior assumed USD, causing incorrect parsing for CAD/AUD/etc.
  - **Migration**: Specify `default_currency` parameter or use ISO codes (USD, CAD, EUR)
  - **Example**:
    ```python
    # v0.6.0 (unsafe): Assumed USD for all $ symbols
    parse_currency("$100", "en_CA")  # → (100, 'USD') - WRONG currency code

    # v0.7.0 (safe): Explicit currency required for ambiguous symbols
    parse_currency("$100", "en_CA", default_currency="CAD")  # → (100, 'CAD')
    parse_currency("$100", "en_CA", infer_from_locale=True)  # → (100, 'CAD')
    parse_currency("CAD 100", "en_CA")  # → (100, 'CAD') - ISO codes always work

    # Unambiguous symbols still work without default_currency
    parse_currency("€100", "en_US")  # → (100, 'EUR') - € is unambiguous
    ```

### Added

- **TypeIs guards for parsing module** (Python 3.13+ PEP 742)
  - New type guards for better mypy type narrowing: `is_valid_decimal()`, `is_valid_number()`, `is_valid_currency()`, `is_valid_date()`, `is_valid_datetime()`
  - **Use case**: Safe type narrowing after parsing with `strict=False`
  - **Example**:
    ```python
    from ftllexbuffer.parsing import parse_decimal, is_valid_decimal

    amount = parse_decimal("1,234.56", "en_US", strict=False)
    if is_valid_decimal(amount):
        # mypy knows amount is Decimal (not Decimal | None)
        total = amount.quantize(Decimal("0.01"))
    ```
  - **Available guards**:
    - `is_valid_decimal(value: Decimal | None) -> TypeIs[Decimal]`
    - `is_valid_number(value: float | None) -> TypeIs[float]`
    - `is_valid_currency(value: tuple[Decimal, str] | None) -> TypeIs[tuple[Decimal, str]]`
    - `is_valid_date(value: date | None) -> TypeIs[date]`
    - `is_valid_datetime(value: datetime | None) -> TypeIs[datetime]`

- **Enhanced caching documentation in API.md**
  - Added comprehensive "Format Caching (v0.6.0+)" section with best practices
  - Performance impact analysis: 50x speedup, ~200 bytes/entry memory cost
  - Cache size recommendations by application type (SPA: 100-500, API: 500-1000, Enterprise: 1000-5000)
  - Cache invalidation behavior documentation
  - Configuration examples for different use cases

### Changed

- **PARSING.md documentation** - Added prominent breaking changes warning at top with migration examples
- **API.md** - Updated version reference to 0.7.0, added caching best practices section

### Tests

- **Enhanced test suite** with comprehensive property-based testing for v0.7.0 changes

### Migration Notes

#### For Users

**BREAKING CHANGES SUMMARY**:

1. **Date/DateTime Parsing**: Remove ambiguous fallback patterns - use ISO 8601 for unambiguous dates
2. **Currency Parsing**: Specify `default_currency` for ambiguous symbols ($, ¢, ₨, ₱, kr)

**Migration Steps**:

```python
# 1. Update date parsing - use ISO 8601 for unambiguous dates
# OLD (v0.6.0): Relied on fallback patterns
user_input = "1/2/25"  # Ambiguous
date = parse_date(user_input, "en_US")

# NEW (v0.7.0): Use ISO 8601 or ensure locale matches input format
date = parse_date("2025-01-02", "en_US")  # ISO 8601 - always works
# OR ensure locale matches expected format:
date = parse_date("1/2/25", "en_US")  # Only works if en_US CLDR matches

# 2. Update currency parsing - specify default_currency
# OLD (v0.6.0): Assumed USD
amount, code = parse_currency("$100", "en_CA")

# NEW (v0.7.0): Explicit currency for $ symbol
amount, code = parse_currency("$100", "en_CA", default_currency="CAD")
# OR use infer_from_locale:
amount, code = parse_currency("$100", "en_CA", infer_from_locale=True)
# OR use ISO codes (always unambiguous):
amount, code = parse_currency("CAD 100", "en_CA")
```

**New Capabilities**:
- TypeIs guards for safer type narrowing with mypy --strict
- Enhanced caching documentation for performance optimization

#### For Library Developers

**New Public Exports**:
```python
from ftllexbuffer.parsing import (
    # Type guards (v0.7.0+)
    is_valid_decimal,
    is_valid_number,
    is_valid_currency,
    is_valid_date,
    is_valid_datetime,
)
```

**Breaking Changes in Parsing Behavior**:
- `parse_date()` and `parse_datetime()` no longer use fallback patterns
- `parse_currency()` raises `ValueError` for ambiguous symbols without `default_currency`
- 2-digit years limited to 2000-2068 range (Python strptime limitation)

**Implementation Details**:
- New `src/ftllexbuffer/parsing/guards.py` module for TypeIs guards
- Updated `_get_date_patterns()` to return empty list on locale parse failure (no fallbacks)
- Updated `_get_datetime_patterns()` to return empty list on locale parse failure (no fallbacks)
- Added ambiguous symbol detection in `parse_currency()` with explicit error messages

---

## [0.6.0] - 2025-12-04

### Added

- **FluentLocalization cache configuration** - Format caching now available for multi-locale applications
  - **New parameters**: `FluentLocalization.__init__()` accepts `enable_cache` and `cache_size` parameters
  - **API signature**:
    ```python
    FluentLocalization(
        locales,
        resource_ids=None,
        resource_loader=None,
        *,
        use_isolating=True,
        enable_cache=False,     # NEW: Enable format caching (50x speedup)
        cache_size=1000         # NEW: Max cache entries per bundle
    )
    ```
  - **Impact**: All bundles in fallback chain now support caching (previously only FluentBundle had cache support)
  - **Use case**: Applications with language switching, bundle pool architectures, multi-locale SPAs
  - **Performance**: 50x speedup on repeated format calls (same as FluentBundle caching)
  - **Example**:
    ```python
    l10n = FluentLocalization(
        ['lv', 'en'],
        ['ui.ftl'],
        loader,
        enable_cache=True,   # Cache enabled for all bundles
        cache_size=1000
    )
    ```
  - **Breaking**: None - new parameters are opt-in with backwards-compatible defaults

- **Cache introspection properties** - Query cache configuration at runtime
  - **New properties**:
    - `FluentBundle.cache_enabled` (bool) - Check if caching is enabled
    - `FluentBundle.cache_size` (int) - Get configured cache size (0 if disabled)
    - `FluentLocalization.cache_enabled` (bool) - Check if caching is enabled for all bundles
    - `FluentLocalization.cache_size` (int) - Get configured cache size per bundle (0 if disabled)
  - **Use cases**: Monitoring, debugging, conditional logic based on cache config
  - **Example**:
    ```python
    bundle = FluentBundle("en", enable_cache=True, cache_size=500)
    print(bundle.cache_enabled)  # True
    print(bundle.cache_size)     # 500

    l10n = FluentLocalization(['lv', 'en'], enable_cache=True)
    print(l10n.cache_enabled)    # True
    for bundle in l10n.get_bundles():
        print(f"{bundle.locale}: cache={bundle.cache_enabled}")
    ```
  - **Introspection**: Follows same pattern as existing `locale` and `use_isolating` properties

- **Enhanced test suite**

---

## [0.5.1] - 2025-12-04

### Fixed

- **CI performance test flakiness** - Replaced timing-based tests with scale-based complexity testing

---

## [0.5.0] - 2025-12-04

### Added

- **Bi-directional Localization** - Full parsing API for locale-aware input processing
  - `parse_number(value, locale)` - Parse locale-formatted number to `float`
  - `parse_decimal(value, locale)` - Parse locale-formatted number to `Decimal` (financial precision)
  - `parse_date(value, locale)` - Parse locale-formatted date to `date` object
  - `parse_datetime(value, locale, tzinfo=None)` - Parse locale-formatted datetime to `datetime` object
  - `parse_currency(value, locale)` - Parse currency string to `(Decimal, currency_code)` tuple
  - **Import**: `from ftllexbuffer.parsing import parse_decimal, parse_currency, ...`
  - **Use case**: Forms, invoices, financial applications requiring roundtrip format → parse → format
  - **Supports**: All 30 built-in locales with automatic CLDR-compliant formatting detection
  - **Currency parsing**: Detects currency symbols (€, $, £, ¥) and ISO codes (EUR, USD, GBP, JPY)
  - **Strict mode**: Optional `strict=False` for lenient parsing (returns None on error)
  - **Roundtrip validation**: format → parse → format preserves original value
  - **Implementation** (Date/DateTime parsing):
    - **Python 3.13 stdlib only** - No external dependencies beyond Babel
    - Uses `datetime.strptime()` with Babel CLDR patterns converted to strptime format
    - **Pattern conversion**: Babel CLDR → Python strptime directives
      - `"M/d/yy"` → `"%m/%d/%y"` (US short)
      - `"dd.MM.yyyy"` → `"%d.%m.%Y"` (EU format)
      - `"MMM d, yyyy"` → `"%b %d, %Y"` (Short month name)
      - `"EEEE, MMMM d, y"` → `"%A, %B %d, %Y"` (Full weekday + month)
    - **Fast path**: ISO 8601 dates use native `datetime.fromisoformat()` (fastest)
    - **Pattern fallback chain**: CLDR patterns → common formats (US, EU, ISO)
    - **Thread-safe**: No global state, immutable pattern lists
  - **Implementation** (Number/Currency parsing):
    - Uses Babel's `parse_decimal()` for CLDR-compliant number parsing
    - Returns `Decimal` for financial precision (no float rounding errors)
    - Currency symbol detection via Babel's currency data
    - **Special values**: Babel accepts `NaN`, `Infinity`, and `Inf` (case-insensitive) as valid Decimal values per IEEE 754 standard

- **Performance Caching** - Optional LRU cache for format results (up to 50x speedup)
  - **Opt-in**: `FluentBundle(locale, enable_cache=True, cache_size=1000)`
  - **Thread-safe**: Uses `threading.RLock` for concurrent read/write safety
  - **Automatic invalidation**: Cache cleared on `add_resource()` and `add_function()`
  - **Cache key**: Hashes `(message_id, args, attribute, locale)` tuple
  - **LRU eviction**: Oldest entries evicted when cache_size limit reached
  - **Introspection**: `get_cache_stats()` returns hits, misses, size, hit_rate
  - **Manual control**: `clear_cache()` for explicit cache clearing

- **FluentLocalization API Completeness** (feature parity with FluentBundle)
  - `format_pattern(message_id, args, attribute=None)` - Format with attribute support and fallback
  - `add_function(name, func)` - Register custom function on all bundles
  - `introspect_message(message_id)` - Get message metadata from first bundle with message
  - `get_babel_locale()` - Get Babel locale identifier from primary bundle
  - `validate_resource(ftl_source)` - Validate FTL resource using primary bundle
  - `clear_cache()` - Clear format cache on all bundles in fallback chain
  - **Rationale**: Eliminates need to call `get_bundles()[0]` for single-bundle operations

- **Rich Diagnostics** - Enhanced error objects with detailed context
  - Extended `Diagnostic` class with format-specific fields:
    - `function_name`: Function where error occurred
    - `argument_name`: Argument that caused error
    - `expected_type`: Expected type for argument
    - `received_type`: Actual type received
    - `ftl_location`: FTL file location (e.g., "ui.ftl:509")
    - `severity`: Error severity level ("error" or "warning")
  - New diagnostic codes for format errors:
    - `TYPE_MISMATCH` (2006): Type mismatch in function argument
    - `INVALID_ARGUMENT` (2007): Invalid argument value
    - `ARGUMENT_REQUIRED` (2008): Required argument not provided
    - `PATTERN_INVALID` (2009): Invalid format pattern
  - New error template methods:
    - `ErrorTemplate.type_mismatch()` - Rich type error diagnostics
    - `ErrorTemplate.invalid_argument()` - Argument validation errors
    - `ErrorTemplate.argument_required()` - Missing required argument
    - `ErrorTemplate.pattern_invalid()` - Pattern syntax errors
  - Enhanced error formatting with context:
    - `format_error()` includes function name, argument details, and helpful hints
    - IDE integration ready (jump to definition, quick fixes)
  - **100% backward compatible**: Existing error handling unchanged

- **Advanced Formatting** - Custom date/number patterns for regulatory compliance
  - Added `pattern` parameter to `NUMBER()` and `DATETIME()` functions
  - Number pattern support:
    - Accounting format: `pattern: "#,##0.00;(#,##0.00)"` (negatives in parentheses)
    - Fixed decimals: `pattern: "#,##0.000"` (always 3 decimal places)
    - No grouping: `pattern: "0.00"` (no thousands separator)
  - DateTime pattern support:
    - ISO 8601: `pattern: "yyyy-MM-dd"` (2025-01-28)
    - 24-hour time: `pattern: "HH:mm:ss"` (14:30:00)
    - Short month: `pattern: "MMM d, yyyy"` (Jan 28, 2025)
    - Full format: `pattern: "EEEE, MMMM d, yyyy"` (Monday, January 28, 2025)
  - Pattern parameter overrides other formatting options
  - Patterns are locale-aware (respect locale formatting rules)
  - Graceful degradation for invalid patterns (no crashes)
  - **Use cases**: ISO 8601 dates for regulatory compliance, accounting formats (GAAP), custom timestamps
  - **100% backward compatible**: Existing formatting unchanged when pattern not specified

- **Comprehensive Documentation**
  - **PARSING.md** (500+ lines) - Complete parsing guide
    - Quick start examples
    - API reference for all 5 parsing functions
    - Best practices (same locale, strict mode, Decimal precision, roundtrip validation)
    - Common patterns (invoice processing, form validation, CSV import)
    - Migration guide from direct Babel usage
    - Troubleshooting section
  - **README.md** - Added bi-directional localization section with examples
  - **API.md** - Parsing API reference and caching documentation (to be completed)

### Changed

- **FluentBundle constructor**: Added `enable_cache` and `cache_size` parameters (default: disabled)

### Tests

- **Enhanced test suite**

### Internal

- **src/ftllexbuffer/parsing/** - New parsing module with 5 submodules
  - `numbers.py` - parse_number(), parse_decimal()
  - `dates.py` - parse_date(), parse_datetime()
  - `currency.py` - parse_currency() with symbol mapping
  - `__init__.py` - Public API exports
- **src/ftllexbuffer/runtime/cache.py** - FormatCache implementation
  - Thread-safe LRU cache using OrderedDict + RLock
  - CacheKey and CacheValue type aliases for clarity
  - get(), put(), clear(), get_stats() methods
- **src/ftllexbuffer/runtime/bundle.py** - Integrated caching
  - Added _cache: FormatCache | None attribute
  - format_pattern() checks cache before resolution
  - add_resource() and add_function() clear cache
- **src/ftllexbuffer/localization.py** - Extended FluentLocalization
  - Added 6 new methods for feature parity with FluentBundle
- **tests/mypy.ini** - Enhanced type checking configuration for hypothesis tests
  - Added `[mypy-tests.test_parsing_currency_hypothesis]` section with `disable_error_code = arg-type`
  - Added `[mypy-tests.test_parsing_dates_hypothesis]` section with `disable_error_code = arg-type`
  - Added `[mypy-tests.test_parsing_numbers_hypothesis]` section with `disable_error_code = arg-type`
  - Added `[mypy-tests.test_serialization_hypothesis]` section with `disable_error_code = arg-type`
  - **Rationale**: Hypothesis character category strategies (`whitelist_categories`, `blacklist_characters`) use complex runtime filtering that doesn't align perfectly with mypy's static type inference
- **pyproject.toml** - Added ruff PLC0415 exceptions for hypothesis tests with runtime imports
  - Added exception for `tests/test_parsing_numbers_hypothesis.py` - Runtime import of formatting functions
  - Added exception for `tests/test_parsing_currency_hypothesis.py` - Runtime import of formatting functions
  - Added exception for `tests/test_serialization_hypothesis.py` - AST manipulation tests
  - **Rationale**: Hypothesis property tests import formatting functions at runtime to avoid circular dependencies and eager strategy evaluation

### Migration Notes

#### For Users

**No breaking changes** - This release is fully backward compatible.

**New capabilities**:
- **Parsing**: You can now parse user input back to data with locale-aware functions
  ```python
  from ftllexbuffer.parsing import parse_decimal
  amount = parse_decimal("1 234,56", "lv_LV")  # → Decimal('1234.56')
  ```
- **Caching**: Opt-in performance boost for repeated formatting
  ```python
  bundle = FluentBundle("en", enable_cache=True)
  # Repeated calls with same args are 50x faster
  ```
- **FluentLocalization**: New methods eliminate need for `get_bundles()[0]`
  ```python
  l10n.format_pattern("button", attribute="tooltip")  # Instead of l10n.get_bundles()[0].format_pattern(...)
  ```

**Recommended**:
- Use `parse_decimal()` for all financial calculations (Decimal precision)
- Enable caching in production for performance-critical applications
- Read [PARSING_GUIDE.md](https://github.com/resoltico/ftllexbuffer/blob/main/docs/PARSING_GUIDE.md) for best practices

#### For Library Developers

**New public exports**:
```python
from ftllexbuffer.parsing import (
    parse_number,
    parse_decimal,
    parse_date,
    parse_datetime,
    parse_currency,
)
```

**FluentBundle caching parameters**:
- `enable_cache: bool = False` (opt-in)
- `cache_size: int = 1000` (max entries)
- `clear_cache()` method
- `get_cache_stats()` method (returns dict or None)

**FluentLocalization new methods**:
- `format_pattern(message_id, args, attribute=None)`
- `add_function(name, func)`
- `introspect_message(message_id)`
- `get_babel_locale()`
- `validate_resource(ftl_source)`
- `clear_cache()`

**Thread safety**:
- FormatCache uses threading.RLock for safe concurrent access
- Cache automatically invalidated on bundle mutations

---

## [0.4.3] - 2025-12-03

### Fixed

- GitHub publishing workflow `publish.yml`

---

## [0.4.2] - 2025-12-03

### Fixed

- GitHub publishing workflow `publish.yml`

---

## [0.4.1] - 2025-12-03

### Fixed

- GitHub publishing workflow `publish.yml`

---

## [0.4.0] - 2025-12-03

### Added

- **FunctionRegistry Introspection API**: Dict-like API for discovering and inspecting registered functions at runtime
  - `list_functions()`: List all registered function names
  - `get_function_info(name)`: Get function metadata including parameter mappings
  - `__iter__`: Iterate over function names
  - `__len__`: Count registered functions
  - `__contains__`: Check function existence with `in` operator
  - **FunctionSignature** dataclass: Exported for working with function metadata
  - **Use cases**: Auto-documentation generation, function validation, debugging, IDE auto-complete

- **Enhanced test suite**

- **Enhanced NUMBER() documentation** in README.md:
  - Detailed parameter descriptions with financial precision guidelines
  - 10+ real-world examples: VAT calculations, price display, quantities, percentages
  - Financial use cases section with invoice totals and currency formatting
  - Locale-specific formatting examples (en-US, lv-LV, de-DE)
  - Parameter combination reference

- **Comprehensive custom function examples**:
  - Enhanced README.md add_function() documentation with 8 detailed examples
  - Parameter conversion (snake_case ↔ camelCase) demonstration
  - Error handling patterns for robust function implementations
  - Locale-aware custom functions (Latvian registration numbers, VAT calculations)
  - Financial domain functions (VAT breakdowns, percentages)
  - Type coercion best practices
  - Function discovery patterns using new introspection API

- **New example file**: `examples/function_introspection.py`
  - 7 comprehensive examples demonstrating all introspection capabilities
  - Basic introspection operations walkthrough
  - Function metadata inspection patterns
  - Custom function introspection workflows
  - Financial app validation patterns
  - Auto-documentation generation demo
  - Safe function usage with existence checks
  - Registry copying for isolated customization

### Changed

- **FunctionRegistry** now implements dict-like protocol
  - Can iterate: `for func_name in registry:`
  - Can check length: `len(registry)`
  - Can check membership: `"NUMBER" in registry`
  - Improves developer ergonomics for function management

### Internal

- Added `Iterator[str]` type annotation to `FunctionRegistry.__iter__`
- Exported `FunctionSignature` from main `ftllexbuffer` module
- Added per-file linting rules for new test and example files
- **All 2,950 tests pass** with **96.92% coverage** (exceeds 95% requirement)
- All lint checks pass: ruff, mypy (strict), pylint (10.00/10)
- **GitHub Actions workflow fixes**:
  - Added `__pycache__` filter to package detection in verification jobs
  - Added proper error messages on PyPI install failure
  - Prevents silent failures in CI/CD pipeline

### Migration Notes

#### For Users

**No breaking changes** - This release is fully backward compatible.

**New capabilities**:
- You can now discover functions at runtime: `bundle._function_registry.list_functions()`
- You can inspect parameter mappings: `bundle._function_registry.get_function_info("NUMBER")`
- Enhanced documentation makes NUMBER() parameters clearer for financial applications

**Recommended**: Review the new NUMBER() documentation examples for best practices in financial formatting

#### For Library Developers

**New public exports**:
- `ftllexbuffer.FunctionSignature`: Access function metadata dataclass
- New methods on `FunctionRegistry`: `list_functions()`, `get_function_info()`, `__iter__`, `__len__`, `__contains__`

**Example usage**:
```python
from ftllexbuffer import FluentBundle

bundle = FluentBundle("en_US")

# List all available functions
for func_name in bundle._function_registry:
    info = bundle._function_registry.get_function_info(func_name)
    print(f"{func_name}: {info.python_name}")

# Check if function exists before use
if "CURRENCY" in bundle._function_registry:
    bundle.add_resource('price = { CURRENCY($amount, currency: "EUR") }')
```

## [0.3.0] - 2025-12-02

### Fixed

- **[CRITICAL] CURRENCY() locale bug**: CURRENCY() function now correctly respects FluentBundle locale instead of always formatting in en_US
  - **Root cause**: CURRENCY was missing from locale injection check in resolver.py:307
  - **Impact**: All non-US locales now format currency correctly
    - Before: `FluentBundle("lv-LV")` with EUR → "€123.45" (incorrect US format)
    - After: `FluentBundle("lv-LV")` with EUR → "123,45 €" (correct Latvian format)
  - **Fix**: Added "CURRENCY" to locale injection check + replaced magic tuple with metadata system

### Added

- **Function metadata system** (`src/ftllexbuffer/runtime/function_metadata.py`)
  - Replaces fragile magic tuple `("NUMBER", "DATETIME")` with explicit metadata declarations
  - Type-safe helpers: `requires_locale_injection()`, `should_inject_locale()`
  - Prevents future locale injection bugs through self-validation
  - Correctly handles custom functions that override built-in names

- **Enhanced test suite**

- **Documentation validation CI** (`scripts/validate_docs.py`)
  - Parses all FTL code blocks in markdown files to ensure validity
  - Prevents shipping invalid FTL examples that mislead users
  - Auto-skips intentionally invalid examples (marked with comments)
  - Validates 37 FTL examples across 6 documentation files

- **Enhanced parser error messages** for variable named arguments
  - Explains WHY variables aren't allowed in named arguments (FTL spec restriction for static analysis)
  - Shows spec-compliant workaround using select expressions
  - Links to official Fluent documentation

### Changed

- **Resolver architecture**: Now uses metadata system instead of hardcoded function list
  - Old (fragile): `if func_name in ("NUMBER", "DATETIME"):`  # Easy to forget new functions
  - New (robust): `if should_inject_locale(func_name, registry):`  # Self-documenting, type-safe

- **Documentation**: Fixed all invalid FTL examples that violated spec
  - README.md: Replaced `currency: $code` with spec-compliant select expression workaround
  - API.md: Removed all variable named argument examples, added correct alternatives
  - All documentation examples now parse successfully with FluentParserV1

### Removed

- Removed invalid FTL examples showing `useGrouping: false` (boolean literals not supported in FTL spec)

### Internal

- Resolver now queries metadata system for locale injection decisions
- All built-in functions have explicit metadata entries with `requires_locale` flag
- Import-time validation ensures metadata completeness

### Migration Notes

#### For Users

**CURRENCY() output changes for non-US locales** (Bug fix, not breaking change):
- If you used CURRENCY() in v0.2.0 with non-US locales, output will now be correctly locale-formatted
- Example: `FluentBundle("de-DE")` with EUR now returns "123,45 €" instead of "€123.45"
- **Action required**: None - this is correct behavior. If you worked around the bug, remove your workaround.

**Variable named arguments now show helpful error**:
- If you tried `currency: $code`, you'll get a clear error explaining the FTL spec limitation
- Error message includes spec-compliant workaround using select expressions
- **Action required**: Update FTL to use select expressions (see error message for example)

#### For Contributors

**Adding new built-in functions**:
1. Add function implementation to `src/ftllexbuffer/runtime/functions.py`
2. **NEW**: Add metadata entry to `BUILTIN_FUNCTIONS` in `function_metadata.py`:
   ```python
   "MYFUNCTION": FunctionMetadata(
       python_name="my_function",
       ftl_name="MYFUNCTION",
       requires_locale=True,  # Set based on function needs
       category="formatting",
   )
   ```
3. Add contract tests to `tests/test_function_locale_contracts.py` if locale-dependent
4. Register in `FUNCTION_REGISTRY` (validation will fail if metadata missing)

---

## [0.2.0] - 2025-12-01

### Added
- **Built-in CURRENCY() function** - CLDR-compliant currency formatting via Babel
  - Supports all ISO 4217 currency codes (USD, EUR, JPY, GBP, etc.)
  - Respects currency-specific decimal places: JPY (0), BHD/KWD/OMR (3), most others (2)
  - Respects locale-specific symbol placement: en_US (before), lv_LV/de_DE (after with space)
  - Three display modes: `symbol` (default), `code`, `name`
  - Example: `price = { CURRENCY($amount, currency: "EUR") }`
- **currency_format() Python API** - Direct Python access to currency formatting
  - Import: `from ftllexbuffer import currency_format`
  - Signature: `currency_format(value, locale_code="en-US", *, currency, currency_display="symbol")`
  - Matches built-in NUMBER() and DATETIME() API patterns
- **FluentBundle.get_babel_locale()** - Introspection API to get Babel locale identifier
  - Returns the Babel locale string (e.g., "en_US", "de_DE", "lv_LV")
  - Useful for integrating custom functions with Babel
- **Enhanced error messages** - FluentLocalization now includes file context in error logs
  - `FluentBundle.add_resource()` accepts optional `source_path` parameter
  - Junk entries now logged with file paths for easier debugging
  - Example: `"Junk entry in locale/en/main.ftl:42: invalid syntax"`
- **ADVANCED_CUSTOM_FUNCTIONS.md** - Guide to creating custom functions
  - Function naming conventions (UPPERCASE)
  - Parameter conventions (keyword-only arguments, snake_case)
  - Error handling patterns (never raise exceptions)
  - Locale-aware functions (factory pattern)
  - Babel integration for i18n
  - Working examples (PHONE, MARKDOWN, FILESIZE, DURATION, GREETING)
  - Testing patterns (unit tests, property-based tests)
  - Best practices and common pitfalls

### Documentation
- **examples/custom_functions.py**: Updated CURRENCY example to demonstrate proper Babel integration
  - Renamed custom example to `CURRENCY_CUSTOM_EXAMPLE` (to avoid conflict with built-in)
  - Fixed hardcoded symbol placement (was incorrect for many locales)
  - Fixed hardcoded 2 decimal places (was incorrect for JPY, BHD, etc.)
  - Now shows correct Babel usage as educational reference
  - Added prominent note that users should use built-in `CURRENCY()` function instead
- **examples/README.md**: Added property_based_testing.py documentation
  - Complete section documenting all 7 property-based testing examples
  - Added cross-reference to ADVANCED_CUSTOM_FUNCTIONS.md in custom_functions.py section
  - Added ADVANCED_CUSTOM_FUNCTIONS.md to "See Also" section
- **README.md**: Added CURRENCY() examples showing locale-specific formatting
- **API.md**: Added complete CURRENCY() function documentation
  - FTL function reference with all parameters
  - Python API reference (currency_format)
  - Locale-specific behavior examples
  - BIDI isolation documentation
  - Error handling documentation
- **QUICK_REFERENCE.md**: Added CURRENCY() to built-in functions reference
  - Quick examples with all display modes
  - CLDR compliance notes
  - Updated custom functions section (replaced broken CURRENCY example with FILESIZE)

### Tests
- **Enhanced test suite**

## [0.1.1] - 2025-11-28

### Added
- `FluentBundle.get_all_message_variables()` - Batch introspection API for extracting variables from all messages at once. Useful for CI/CD validation pipelines.
- Property-based testing examples in `examples/property_based_testing.py` - 7 examples demonstrating Hypothesis usage with FTLLexBuffer.
- Test suite for batch introspection (`tests/test_bundle_batch_introspection.py`) - 23 tests including property-based tests.

## [0.1.0] - 2025-11-28

Initial release.

[0.11.0]: https://github.com/resoltico/ftllexbuffer/releases/tag/v0.11.0
[0.10.0]: https://github.com/resoltico/ftllexbuffer/releases/tag/v0.10.0
[0.9.1]: https://github.com/resoltico/ftllexbuffer/releases/tag/v0.9.1
[0.9.0]: https://github.com/resoltico/ftllexbuffer/releases/tag/v0.9.0
[0.8.0]: https://github.com/resoltico/ftllexbuffer/releases/tag/v0.8.0
[0.7.0]: https://github.com/resoltico/ftllexbuffer/releases/tag/v0.7.0
[0.6.0]: https://github.com/resoltico/ftllexbuffer/releases/tag/v0.6.0
[0.5.1]: https://github.com/resoltico/ftllexbuffer/releases/tag/v0.5.1
[0.5.0]: https://github.com/resoltico/ftllexbuffer/releases/tag/v0.5.0
[0.4.3]: https://github.com/resoltico/ftllexbuffer/releases/tag/v0.4.3
[0.4.2]: https://github.com/resoltico/ftllexbuffer/releases/tag/v0.4.2
[0.4.1]: https://github.com/resoltico/ftllexbuffer/releases/tag/v0.4.1
[0.4.0]: https://github.com/resoltico/ftllexbuffer/releases/tag/v0.4.0
[0.3.0]: https://github.com/resoltico/ftllexbuffer/releases/tag/v0.3.0
[0.2.0]: https://github.com/resoltico/ftllexbuffer/releases/tag/v0.2.0
[0.1.1]: https://github.com/resoltico/ftllexbuffer/releases/tag/v0.1.1
[0.1.0]: https://github.com/resoltico/ftllexbuffer/releases/tag/v0.1.0
