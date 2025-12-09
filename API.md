# API Reference

Complete reference documentation for FTLLexBuffer's public API.

**Latest Version**: 0.9.0 | [Changelog](CHANGELOG.md)

**Package**: `ftllexbuffer`
**Python Version**: 3.13+
**Dependencies**: `Babel>=2.17.0`

**Terminology Guide:**
- **Fluent** - The localization system and specification
- **FTL** or **.ftl files** - The file format (Fluent Translation List files)
- **Fluent syntax** - The language syntax used in .ftl files
- **Message** - A translatable unit with an ID
- **Message ID** - The identifier for a message (prose: "message ID", code: `message_id`)
- **Term** - A reusable translation (prefixed with `-`)
- **Pattern** - The text content of a message or term
- **Placeable** - An expression wrapped in `{ }` braces
- **Resource** - Context-dependent term with three meanings:
  - **FTL Resource (AST)**: The parsed AST root node containing all entries (`Resource` class from `parse_ftl()`)
  - **FTL source text**: The string content passed to `add_resource(source: str)`
  - **Resource loader**: System for loading .ftl files from disk/network (`PathResourceLoader`, `ResourceLoader` protocol)

---

## Importing from FTLLexBuffer

All public APIs are available as **top-level imports** from the `ftllexbuffer` package.

### Core API (Most Common)

```python
from ftllexbuffer import (
    # Message formatting
    FluentBundle,
    FluentLocalization,
    # Resource loading
    PathResourceLoader,
    ResourceLoader,
    # Type aliases for annotations
    MessageId,
    LocaleCode,
    ResourceId,
    FTLSource,
    # Parsing and serialization
    parse_ftl,
    serialize_ftl,
    # Exceptions
    FluentError,
    FluentSyntaxError,
    FluentReferenceError,
    FluentResolutionError,
    FluentCyclicReferenceError,
)
```

### AST Manipulation

```python
from ftllexbuffer import (
    # Parser
    parse_ftl,
    serialize_ftl,
    # AST entry types
    Resource,
    Message,
    Term,
    Comment,
    Junk,
    Attribute,
    # Pattern elements
    Pattern,
    TextElement,
    Placeable,
    # Expression types
    VariableReference,
    MessageReference,
    TermReference,
    FunctionReference,
    SelectExpression,
    Variant,
    NumberLiteral,
    StringLiteral,
    # Support types
    Identifier,
    CallArguments,
    NamedArgument,
    Span,
    Annotation,
    # Visitor pattern
    ASTVisitor,
    ASTTransformer,
)
```

### Introspection

```python
from ftllexbuffer import (
    introspect_message,
    extract_variables,
    MessageIntrospection,
    VariableInfo,
    FunctionCallInfo,
    ReferenceInfo,
)
```

### Advanced

```python
from ftllexbuffer import (
    FluentParserV1,          # Direct parser access
    FUNCTION_REGISTRY,        # Global function registry
    FunctionRegistry,         # Function registry class (for custom instances)
    FunctionSignature,        # Function metadata dataclass (Added in v0.4.0)
    ValidationResult,         # Validation result type
)
```

### Type Aliases

Python 3.13 type aliases for user code annotations:

```python
from ftllexbuffer import (
    MessageId,    # Type alias for message identifiers (str)
    LocaleCode,   # Type alias for locale codes (str)
    ResourceId,   # Type alias for resource identifiers (str)
    FTLSource,    # Type alias for FTL source strings (str)
)
```

**Purpose**: These type aliases improve code readability and IDE autocomplete:

```python
from ftllexbuffer import FluentBundle, MessageId, LocaleCode

def load_message(bundle: FluentBundle, msg_id: MessageId) -> str:
    result, _ = bundle.format_value(msg_id)
    return result

def create_bundle(locale: LocaleCode) -> FluentBundle:
    return FluentBundle(locale)
```

**Note**: These are Python 3.13 `type` keyword aliases, not runtime classes. They're purely for static type checking and documentation.

### Module Constants

```python
from ftllexbuffer import (
    __version__,              # Package version
    __fluent_spec_version__,  # FTL specification version
    __spec_url__,             # Specification URL
    __recommended_encoding__, # Recommended file encoding
)
```

### Import Styles

FTLLexBuffer supports both top-level and submodule import styles:

```python
# Top-level imports (all public APIs exported from main package)
from ftllexbuffer import Message, Term, Pattern, FluentBundle

# Submodule imports (explicit module paths)
from ftllexbuffer.syntax import Message, Term, Pattern
from ftllexbuffer.runtime import FluentBundle
```

Both styles work identically. Choose based on your project's preferences.

---

## Table of Contents

- [Importing from FTLLexBuffer](#importing-from-ftllexbuffer)
- [FluentBundle](#fluentbundle)
  - [add_resource()](#add_resource)
  - [format_pattern()](#format_pattern)
  - [validate_resource()](#validate_resource)
  - [has_message()](#has_message)
  - [get_message_ids()](#get_message_ids)
  - [get_message_variables()](#get_message_variables)
  - [introspect_message()](#introspect_message) (bundle method)
  - Properties
    - [locale](#locale)
    - [use_isolating](#use_isolating)
  - [add_function()](#add_function)
  - [FunctionRegistry (Advanced)](#functionregistry-advanced)
- [FluentLocalization](#fluentlocalization)
  - [add_resource()](#add_resource)
  - [format_value()](#format_value)
  - [has_message()](#has_message)
  - [get_bundles()](#get_bundles)
- [PathResourceLoader](#pathresourceloader)
- [ResourceLoader Protocol](#resourceloader-protocol)
- [ValidationResult](#validationresult)
- [Error Handling Patterns](#error-handling-patterns)
  - [Pattern 1: Production - Always Check Errors](#pattern-1-production---always-check-errors)
  - [Pattern 2: Tests/Examples - Explicitly Ignore](#pattern-2-testsexamples---explicitly-ignore)
  - [Pattern 3: Strict Mode - Fail on Errors](#pattern-3-strict-mode---fail-on-errors)
  - [Pattern 4: Application Wrapper - Centralized Error Handling](#pattern-4-application-wrapper---centralized-error-handling)
  - [Pattern 5: Error Categorization](#pattern-5-error-categorization)
  - [Pattern 6: Async/Background Error Reporting](#pattern-6-asyncbackground-error-reporting)
- [Exception Hierarchy](#exception-hierarchy)
- [Built-in Functions](#built-in-functions)
  - [NUMBER()](#number)
  - [DATETIME()](#datetime)
- [Parsing API](#parsing-api)
  - [parse_number()](#parse_number)
  - [parse_decimal()](#parse_decimal)
  - [parse_date()](#parse_date)
  - [parse_datetime()](#parse_datetime)
  - [parse_currency()](#parse_currency)
  - [Roundtrip Validation](#roundtrip-validation)
  - [Error Handling](#error-handling)
  - [Common Patterns](#common-patterns)
  - [Migration from Babel](#migration-from-babel)
- [Advanced APIs - Low-Level Functions](#advanced-apis---low-level-functions)
  - [number_format()](#number_format)
  - [datetime_format()](#datetime_format)
- [Common Pitfalls](#common-pitfalls)
  - [Variables Are Runtime-Provided](#variables-are-runtime-provided)
  - [Circular References Never Raise Exceptions](#circular-references-never-raise-exceptions)
  - [use_isolating=True Is CRITICAL for RTL Languages](#use_isolatingtrue-is-critical-for-rtl-languages)
  - [Parser Continues After Syntax Errors](#parser-continues-after-syntax-errors)
  - [Message Overwriting Is Last-Write-Wins](#message-overwriting-is-last-write-wins)
- [Advanced Usage](#advanced-usage)
- [AST Manipulation](#ast-manipulation)
  - [parse_ftl()](#parse_ftl)
  - [serialize_ftl()](#serialize_ftl)
- [AST Visitor Pattern](#ast-visitor-pattern)
  - [ASTVisitor](#astvisitor)
  - [ASTTransformer](#asttransformer)
- [AST Node Types](#ast-node-types)
  - [Core Entry Types](#core-entry-types)
    - Resource
    - Message
    - Term
    - Comment
    - Junk
    - Attribute
  - [Pattern Elements](#pattern-elements)
    - Pattern
    - TextElement
    - Placeable
  - [Expression Types](#expression-types)
    - VariableReference
    - MessageReference
    - TermReference
    - FunctionReference
    - SelectExpression
    - Variant
    - NumberLiteral
    - StringLiteral
  - [Support Types](#support-types)
    - Identifier
    - CallArguments
    - NamedArgument
  - [Parser Support Types](#parser-support-types)
    - Span
    - Annotation
    - Cursor
    - ParseResult
    - ParseError
- [AST Type Guards](#ast-type-guards)
  - Message.guard()
  - Term.guard()
  - Comment.guard()
  - Junk.guard()
  - Placeable.guard()
  - TextElement.guard()
  - has_value()
- [Message Introspection](#message-introspection)
  - [introspect_message()](#introspect_message) - Module-level function
  - [extract_variables()](#extract_variables)
- [Introspection Data Types](#introspection-data-types)
  - [MessageIntrospection](#messageintrospection)
  - [VariableInfo](#variableinfo)
  - [FunctionCallInfo](#functioncallinfo)
  - [ReferenceInfo](#referenceinfo)
- [Module Constants](#module-constants)
  - [__version__](#__version__)
  - [__fluent_spec_version__](#__fluent_spec_version__)
  - [__recommended_encoding__](#__recommended_encoding__)
  - [__spec_url__](#__spec_url__)

---

## FluentBundle

Main entry point for Fluent message formatting.

**Thread Safety**: FluentBundle instances are **NOT thread-safe** for writes. The `add_resource()` and `add_function()` methods mutate internal state. Once all resources are loaded, bundles are safe for concurrent reads (`format_pattern()`, `has_message()`, etc.).

**Recommended Pattern for Multi-threaded Applications**:
- Load all resources during application startup (single-threaded initialization)
- Share bundle instances across threads for read-only operations
- If dynamic resource loading is required, use locks or create per-thread bundles

### Constructor

```python
FluentBundle(locale: LocaleCode, *, use_isolating: bool = True)
```

**Parameters**:

- **`locale`** (LocaleCode): Locale code determining CLDR plural rules
  - Format: `"language_TERRITORY"` or `"language-TERRITORY"` (both separators supported)
  - Examples: `"en_US"`, `"en-US"`, `"ar_SA"`, `"ar-SA"`, `"lv_LV"`, `"lv-LV"`
  - Automatic normalization: Both BCP 47 (hyphen) and POSIX (underscore) formats supported
  - **v0.9.0**: Uses Babel's CLDR data (200+ locales supported)
  - Fallback: Simple one/other rules for unsupported/invalid locales

- **`use_isolating`** (bool, default=True): Wrap interpolated values in Unicode bidi isolation marks
  - **CRITICAL for RTL languages** (Arabic, Hebrew, Persian, Urdu)
  - Prevents text corruption when mixing LTR/RTL content
  - Follows Unicode TR9 Bidirectional Algorithm
  - Set to `False` only for LTR-only applications (performance optimization)

**Example**:

```python
from ftllexbuffer import FluentBundle

# LTR language (English) - default use_isolating=True for RTL safety
bundle_en = FluentBundle("en_US")

# RTL language (Arabic) - isolation REQUIRED
bundle_ar = FluentBundle("ar_EG", use_isolating=True)

# LTR-only apps - disable for cleaner output (use in examples/testing)
bundle_fast = FluentBundle("en", use_isolating=False)
```

---

### Methods

#### add_resource

```python
add_resource(source: FTLSource, *, source_path: str | None = None) -> None
```

Parse and load FTL source into bundle.

**Parameters**:

- **`source`** (FTLSource): FTL source (UTF-8 encoded string)
- **`source_path`** (str | None, optional): File path for error messages (Added in v0.2.0)

**Returns**:

- **None**: This method does not return a value (mutates bundle state in-place)

**Raises**:

- **`FluentSyntaxError`**: On critical parse errors (malformed grammar)

**Behavior**:

- **Robustness principle**: Parser continues after non-critical errors
- Non-critical syntax errors become `Junk` entries (logged at DEBUG level)
- Messages/Terms with duplicate IDs: **last-write-wins** (later definition replaces earlier)
- Comments are parsed but not stored (not needed for runtime)
- **source_path** (v0.2.0+): When provided, includes file context in error/warning logs for easier debugging

**Example**:

```python
from pathlib import Path

bundle = FluentBundle("lv", use_isolating=False)

# From string literal
bundle.add_resource("""
hello = Sveiki!
goodbye = Uz redzēšanos!
""")

# From file (with source_path for better error messages - v0.2.0+)
ftl_path = Path("locale/lv/main.ftl")
bundle.add_resource(ftl_path.read_text(encoding="utf-8"), source_path=str(ftl_path))
# Junk errors now logged as: "Junk entry in locale/lv/main.ftl:42: invalid syntax"

# Overwrite previous definition
bundle.add_resource("hello = Čau!")  # Replaces "Sveiki!"
```

---

#### format_pattern

```python
format_pattern(
    message_id: MessageId,
    args: dict[str, Any] | None = None,
    *,
    attribute: str | None = None
) -> tuple[str, list[FluentError]]
```

Format message to localized string with variable substitution.

**Parameters**:

- **`message_id`** (MessageId): Message identifier (without `-` prefix - that's for Terms)
- **`args`** (dict, optional): Variable arguments for `{ $variable }` interpolation
- **`attribute`** (str, optional): Access message attribute instead of value

**Returns**:

- **`tuple[str, list[FluentError]]`**: Tuple of (formatted_string, errors)
  - `formatted_string`: Best-effort formatted output (never empty, always contains readable fallback)
  - `errors`: List of FluentError instances encountered during resolution. May contain:
    - **FluentReferenceError**: Missing message, variable, or term
    - **FluentResolutionError**: Runtime error during function execution
    - **FluentCyclicReferenceError**: Circular reference detected (message references itself)

**Error Handling** (Mozilla python-fluent aligned):

- **Never raises exceptions**: All errors collected in list[FluentError] returned
- **Readable fallbacks**: `{$variable}`, `{message}`, `{-term}` (per Fluent spec)
- **Graceful degradation**: Always returns usable output, errors list available for logging
- **Circular references**: Returns `"{message_id}"` with FluentCyclicReferenceError in errors list
- **Missing variables**: Returns readable fallback `{$name}` with FluentReferenceError in errors list

**Examples**:

```python
bundle = FluentBundle("pl", use_isolating=False)
bundle.add_resource("""
hello = Cześć
welcome = Witaj, { $name }!
emails = Masz { $count ->
    [one] { $count } email
    [few] { $count } emaile
    [many] { $count } emaili
   *[other] { $count } emaila
}

save-button = Zapisz
    .tooltip = Zapisz bieżący dokument
    .aria-label = Przycisk zapisu
""")

# Simple message
result, errors = bundle.format_pattern("hello")
# result → "Cześć"
# errors → []

# Variable interpolation
result, errors = bundle.format_pattern("welcome", {"name": "Anna"})
# result → "Witaj, Anna!"
# errors → []

# SELECT expression (CLDR plural forms)
result, errors = bundle.format_pattern("emails", {"count": 1})   # → "Masz 1 email"
result, errors = bundle.format_pattern("emails", {"count": 2})   # → "Masz 2 emaile"
result, errors = bundle.format_pattern("emails", {"count": 5})   # → "Masz 5 emaili"
result, errors = bundle.format_pattern("emails", {"count": 1.5}) # → "Masz 1.5 emaila"

# Attribute access
result, errors = bundle.format_pattern("save-button", attribute="tooltip")
# result → "Zapisz bieżący dokument"
# errors → []

# Missing variable (returns fallback + error in list)
result, errors = bundle.format_pattern("welcome")  # Missing {"name": ...}
# result → "Witaj, {$name}!"  # Readable fallback
# errors → [FluentReferenceError(...)]
if errors:
    for error in errors:
        print(f"Translation error: {error}")

# Missing message (returns fallback + error)
result, errors = bundle.format_pattern("nonexistent")
# result → "{nonexistent}"  # Message ID as fallback
# errors → [FluentReferenceError('Message not found: nonexistent')]
```

---

#### format_value

```python
format_value(
    message_id: str,
    args: dict[str, Any] | None = None
) -> tuple[str, list[FluentError]]
```

Format message to string (alias for format_pattern without attribute access).

**Purpose**: Provides API consistency with `FluentLocalization.format_value()` for users who don't need attribute access. This is an alias for `format_pattern(message_id, args, attribute=None)`.

**Parameters**:

- **`message_id`** (str): Message identifier
- **`args`** (dict, optional): Variable arguments for interpolation

**Returns**:

- **`tuple[str, list[FluentError]]`**: Tuple of (formatted_string, errors)

**Note**: Identical behavior to `format_pattern()` without attribute parameter. Use this when you don't need to access message attributes.

**Example**:

```python
bundle = FluentBundle("en", use_isolating=False)
bundle.add_resource("welcome = Hello, { $name }!")

# format_value() - simpler API when no attributes needed
result, errors = bundle.format_value("welcome", {"name": "Alice"})
# result → "Hello, Alice!"

# Equivalent to:
result, errors = bundle.format_pattern("welcome", {"name": "Alice"}, attribute=None)
```

---

#### validate_resource

```python
validate_resource(source: str) -> ValidationResult
```

Validate FTL resource without adding to bundle.

**Use Cases**:

- CI/CD pipeline validation (fail build on syntax errors)
- IDE linting/validation tools
- Pre-deployment checks
- Translation quality assurance

**Parameters**:

- **`source`** (str): FTL source to validate

**Returns**:

- **`ValidationResult`**: Object with `.is_valid`, `.error_count`, `.errors`, `.warnings` properties (see [ValidationResult](#validationresult) for details)

**Note**: Does NOT modify bundle - pure validation.

**Example - Basic validation**:

```python
import sys
from pathlib import Path

bundle = FluentBundle("en", use_isolating=False)

# Load from file
ftl_source = Path("locale/en/main.ftl").read_text()

# Validate before deploying
result = bundle.validate_resource(ftl_source)

if not result.is_valid:
    print(f"[FAIL] Found {result.error_count} syntax errors:")
    for error in result.errors:
        location = f"line {error.line}" if error.line else "unknown"
        print(f"  - {location}: {error.message[:80]}")
    sys.exit(1)
else:
    print(f"[OK] FTL syntax valid ({len(ftl_source)} bytes)")
    bundle.add_resource(ftl_source)
```

**Example - Comprehensive validation with warnings**:

```python
import sys
from pathlib import Path

bundle = FluentBundle("en", use_isolating=False)
ftl_source = Path("locale/en/main.ftl").read_text()

# Validate with both error and warning checking
result = bundle.validate_resource(ftl_source)

print(f"Validation Results for {Path('locale/en/main.ftl').name}")
print(f"  Syntax valid: {result.is_valid}")
print(f"  Parse errors: {result.error_count}")
print(f"  Semantic warnings: {result.warning_count}")

# Check for syntax errors (fatal - prevent deployment)
if not result.is_valid:
    print("\n[ERROR] Syntax errors found:")
    for error in result.errors:
        location = f"line {error.line}" if error.line else "unknown"
        print(f"  - {location}: {error.message[:100]}")
    sys.exit(1)

# Check for semantic warnings (non-fatal - log and decide)
if result.warning_count > 0:
    print("\n[WARN] Semantic issues found:")
    for warning in result.warnings:
        location = f"line {warning.line}" if warning.line else "unknown"
        print(f"  - {location}: {warning.message}")

    # Production decision: warnings might indicate real problems
    # Option 1: Fail build (strict)
    # sys.exit(1)

    # Option 2: Log warnings but allow deployment (lenient)
    import logging
    logging.warning(f"{result.warning_count} FTL warnings in main.ftl")
    # Continue with deployment

# Safe to add resource
print(f"\n[OK] Validation passed - adding resource to bundle")
bundle.add_resource(ftl_source)
```

**Example - CI/CD validation script**:

```python
"""Validate all FTL files in CI/CD pipeline."""
import sys
from pathlib import Path
from ftllexbuffer import FluentBundle

def validate_all_ftl_files(locale_dir: Path, strict: bool = False) -> bool:
    """Validate all .ftl files in directory.

    Args:
        locale_dir: Directory containing .ftl files
        strict: If True, warnings cause validation failure

    Returns:
        True if validation passes, False otherwise
    """
    bundle = FluentBundle("en", use_isolating=False)
    total_errors = 0
    total_warnings = 0

    for ftl_file in sorted(locale_dir.rglob("*.ftl")):
        source = ftl_file.read_text(encoding="utf-8")
        result = bundle.validate_resource(source)

        if not result.is_valid:
            print(f"[FAIL] {ftl_file.relative_to(locale_dir)}: {result.error_count} error(s)")
            for error in result.errors:
                location = f"line {error.line}" if error.line else "unknown"
                print(f"  Parse error at {location}: {error.message[:80]}")
            total_errors += result.error_count
        elif result.warning_count > 0:
            status = "[WARN]" if strict else "[OK]"
            print(f"{status} {ftl_file.relative_to(locale_dir)}: {result.warning_count} warning(s)")
            for warning in result.warnings:
                location = f"line {warning.line}" if warning.line else "unknown"
                print(f"  {location}: {warning.message}")
            total_warnings += result.warning_count
        else:
            print(f"[OK] {ftl_file.relative_to(locale_dir)}")

    print(f"\nSummary: {total_errors} errors, {total_warnings} warnings")

    # Validation passes if:
    # - No errors (always)
    # - No warnings (if strict=True)
    return total_errors == 0 and (not strict or total_warnings == 0)

if __name__ == "__main__":
    locale_dir = Path("locale")
    strict_mode = "--strict" in sys.argv

    success = validate_all_ftl_files(locale_dir, strict=strict_mode)
    sys.exit(0 if success else 1)
```

---

#### has_message

```python
has_message(message_id: str) -> bool
```

Check if message exists in bundle (for conditional logic).

**Parameters**:

- **`message_id`** (str): Message identifier

**Returns**:

- (bool): `True` if message registered, `False` otherwise

**Use Cases**:

- Feature flags based on translation availability
- Fallback logic
- Debug/introspection

**Example**:

```python
bundle = FluentBundle("en", use_isolating=False)
bundle.add_resource("premium-feature = Premium Feature")

if bundle.has_message("premium-feature"):
    result, _ = bundle.format_pattern("premium-feature")
    print(result)
else:
    print("Feature not available in this locale")

# Fallback chain
for msg_id in ["welcome-user", "welcome-default", "hello"]:
    if bundle.has_message(msg_id):
        result, _ = bundle.format_pattern(msg_id, {"name": "Alice"})
        print(result)
        break
```

---

#### get_message_ids

```python
get_message_ids() -> list[str]
```

Get all registered message IDs (for debugging, testing, or UI generation).

**Returns**:

- (list[str]): List of message identifiers (unsorted)

**Use Cases**:

- Debug output (show loaded translations)
- Test assertions (verify resource loading)
- Dynamic UI generation (list available messages)

**Example**:

```python
bundle = FluentBundle("en", use_isolating=False)
bundle.add_resource("welcome = Welcome\nabout = About")

ids = bundle.get_message_ids()
print(f"Loaded {len(ids)} messages")

# Test assertion
assert "welcome" in bundle.get_message_ids()

# Debug output
for msg_id in sorted(bundle.get_message_ids()):
    print(f"  - {msg_id}")
```

---

#### get_message_variables

```python
get_message_variables(message_id: str) -> frozenset[str]
```

Get all variables required by a message (convenience method).

**Parameters**:

- **`message_id`** (str): Message identifier

**Returns**:

- (frozenset[str]): Set of variable names (without $ prefix) required by the message

**Use Cases**:

- Validate that all required variables are provided before formatting
- Generate type-safe wrappers
- Build translation validation tools

**Example**:

```python
bundle = FluentBundle("en", use_isolating=False)
bundle.add_resource("welcome = Hello, { $firstName } { $lastName }!")

variables = bundle.get_message_variables("welcome")
print(variables)  # frozenset({'firstName', 'lastName'})

# Validate before formatting
required_vars = bundle.get_message_variables("welcome")
provided_vars = {"firstName": "John", "lastName": "Doe"}
missing = required_vars - set(provided_vars.keys())
if missing:
    print(f"Missing variables: {missing}")
```

---

#### get_all_message_variables

> **Added in**: 0.1.1

```python
get_all_message_variables() -> dict[str, frozenset[str]]
```

Get variables for all messages in bundle (batch introspection API).

**Returns**:

- (dict[str, frozenset[str]]): Mapping of message IDs to their required variables

**Use Cases**:

- CI/CD validation pipelines analyzing entire FTL resources
- Batch variable extraction for documentation generation
- Translation completeness checking

**Example**:

```python
bundle = FluentBundle("en", use_isolating=False)
bundle.add_resource("""
welcome = Hello, { $firstName } { $lastName }!
emails = You have { $count } { $count ->
    [one] email
   *[other] emails
}
greeting = Hi!
""")

all_vars = bundle.get_all_message_variables()
print(all_vars)
# {
#     'welcome': frozenset({'firstName', 'lastName'}),
#     'emails': frozenset({'count'}),
#     'greeting': frozenset()
# }

# Validate all messages have required variables
for msg_id, required_vars in all_vars.items():
    if required_vars:
        print(f"{msg_id} requires: {', '.join(sorted(required_vars))}")
```

**Note**: This is equivalent to calling `get_message_variables()` for each message ID, but provides a cleaner API for batch operations.

---

#### introspect_message

```python
introspect_message(message_id: MessageId) -> MessageIntrospection
```

Get comprehensive metadata about a message (bundle convenience method).

**IMPORTANT**: `introspect_message()` has two forms:
- **This bundle method**: `bundle.introspect_message(message_id: str)` - takes message ID
- **Module-level function**: `introspect_message(message: Message)` - takes AST node (see [Introspection API](#introspect_message))

**Parameters**:

- **`message_id`** (MessageId): Message identifier

**Returns**:

- **`MessageIntrospection`**: Complete metadata including variables, functions, references, and selectors

**Note**: This is a convenience method that looks up the message by ID and calls the module-level `introspect_message()` function on the AST node.

**Example**:

```python
bundle = FluentBundle("en", use_isolating=False)
bundle.add_resource("""
welcome = Hello, { $name }! You have { NUMBER($count) } messages.
    .aria-label = Welcome message for { $name }
""")

info = bundle.introspect_message("welcome")

print(f"Variables: {info.get_variable_names()}")
# Output: Variables: frozenset({'name', 'count'})

print(f"Functions: {info.get_function_names()}")
# Output: Functions: frozenset({'NUMBER'})
```

---

#### get_babel_locale

**Added in v0.2.0**

```python
get_babel_locale() -> str
```

Get the Babel locale identifier for this bundle (introspection/debugging API).

**Returns**:

- (str): Babel locale identifier (e.g., "en_US", "lv_LV", "ar_EG")

**Use Cases**:

- Debugging locale-related formatting issues
- Verifying which CLDR data is being applied
- Integration with custom functions that use Babel directly

**Example**:

```python
bundle = FluentBundle("en-US")
print(bundle.get_babel_locale())
# Output: "en_US"

bundle_lv = FluentBundle("lv-LV")
print(bundle_lv.get_babel_locale())
# Output: "lv_LV"

# Use in custom functions
def CUSTOM_FORMAT(value: float) -> str:
    from babel import numbers
    locale = bundle.get_babel_locale()
    return numbers.format_decimal(value, locale=locale)
```

**Note**: This returns the actual Babel locale identifier being used internally for NUMBER(), DATETIME(), and CURRENCY() formatting. BCP-47 locale codes (with hyphens) are automatically converted to Babel's POSIX format (with underscores).

---

### Properties

#### locale

```python
locale: str
```

The locale code for this bundle (read-only).

**Example**:

```python
bundle = FluentBundle("lv_LV")
print(bundle.locale)  # "lv_LV"
```

---

#### use_isolating

```python
use_isolating: bool
```

Whether Unicode bidi isolation is enabled for this bundle (read-only).

**Example**:

```python
bundle = FluentBundle("ar_EG", use_isolating=True)
print(bundle.use_isolating)  # True
```

---

#### cache_enabled

```python
cache_enabled: bool
```

Whether format caching is enabled for this bundle (read-only).

**Example**:

```python
bundle = FluentBundle("en", enable_cache=True)
print(bundle.cache_enabled)  # True

bundle_no_cache = FluentBundle("en")
print(bundle_no_cache.cache_enabled)  # False
```

---

#### cache_size

```python
cache_size: int
```

Maximum cache size configuration for this bundle (read-only). Returns 0 if caching is disabled.

**Example**:

```python
bundle = FluentBundle("en", enable_cache=True, cache_size=500)
print(bundle.cache_size)  # 500

bundle_no_cache = FluentBundle("en")
print(bundle_no_cache.cache_size)  # 0
```

**Note**: Returns configured size even if cache is disabled. Use `cache_enabled` to check if caching is active.

---

#### add_function

```python
add_function(name: str, func: Callable) -> None
```

Register custom Fluent function.

**Parameters**:

- **`name`** (str): Function name (UPPERCASE by convention, e.g., `CURRENCY`, `PHONE`)
- **`func`** (Callable): Python function implementing logic

**Function Signature**:

```python
def custom_func(value: Any, **options: Any) -> str:
    """
    Args:
        value: First positional argument from FTL
        **options: Named arguments from FTL (both camelCase and snake_case supported)

    Returns:
        str: Formatted result (MUST return string per Fluent spec)
    """
    ...
```

**Advanced - Accessing Bundle Locale**:

Custom functions can access the bundle's locale by storing it during registration:

```python
def make_locale_aware_function(locale: str):
    """Factory for locale-aware functions."""
    def CUSTOM(value: Any, **options: Any) -> str:
        # Use captured locale for locale-specific formatting
        if locale.startswith("lv"):
            return f"Latvian: {value}"
        return f"Default: {value}"
    return CUSTOM

# Register locale-specific version
bundle = FluentBundle("lv_LV")
bundle.add_function("CUSTOM", make_locale_aware_function(bundle.locale))
```

Alternatively, use a class-based approach:

```python
class LocaleAwareFormatter:
    def __init__(self, bundle: FluentBundle):
        self.locale = bundle.locale

    def CUSTOM(self, value: Any, **options: Any) -> str:
        if self.locale.startswith("lv"):
            return f"Latvian: {value}"
        return f"Default: {value}"

bundle = FluentBundle("lv_LV")
formatter = LocaleAwareFormatter(bundle)
bundle.add_function("CUSTOM", formatter.CUSTOM)
```

**Example**:

```python
def CURRENCY(amount: float, *, currency_code: str = "USD") -> str:
    """Format currency with symbol."""
    symbols = {"USD": "$", "EUR": "€", "GBP": "£", "PLN": "zł"}
    symbol = symbols.get(currency_code, currency_code)
    return f"{symbol}{amount:,.2f}"

def PHONE(number: str, *, format_style: str = "international") -> str:
    """Format phone number."""
    # Remove non-digits
    digits = "".join(c for c in number if c.isdigit())

    if format_style == "international" and len(digits) >= 10:
        return f"+{digits[0]} ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    return number

bundle = FluentBundle("en", use_isolating=False)
bundle.add_function("CURRENCY", CURRENCY)
bundle.add_function("PHONE", PHONE)

bundle.add_resource("""
price = Total: { CURRENCY($amount, currency_code: "EUR") }
contact = Call { PHONE($number, format_style: "international") }
""")

bundle.format_pattern("price", {"amount": 1234.56})
# → "Total: €1,234.56"

bundle.format_pattern("contact", {"number": "15551234567"})
# → "Call +1 (555) 123-4567"
```

---

### FunctionRegistry (Advanced)

For advanced use cases requiring parameter mapping or global function registration, use the `FunctionRegistry` class directly.

**Import**:
```python
# Recommended: Use global registry instance (most common)
from ftllexbuffer import FUNCTION_REGISTRY

# Advanced: Import FunctionRegistry class for custom registry instances
from ftllexbuffer import FunctionRegistry
```

**Note**: Most users should use the global `FUNCTION_REGISTRY` instance (exported singleton). The `FunctionRegistry` class is also exported for creating custom registry instances (rare use case).

**Use Cases**:
- Register functions with parameter name mapping (camelCase ↔ snake_case)
- Share functions across multiple bundles
- Build custom function libraries
- Advanced function introspection

#### register()

```python
FunctionRegistry.register(
    func: Callable,
    *,
    ftl_name: str | None = None,
    param_map: dict[str, str] | None = None
) -> None
```

Register a function with advanced options.

**Parameters**:
- **`func`** (Callable): Python function to register
- **`ftl_name`** (str, optional): FTL function name (defaults to func.__name__.upper())
- **`param_map`** (dict[str, str], optional): Map FTL parameter names to Python parameter names

**Parameter Name Conversion**:

FunctionRegistry automatically converts between FTL's camelCase convention and Python's snake_case convention:

- **Python functions**: Use `snake_case` parameter names (PEP 8 compliant)
  ```python
  def number_format(value, minimum_fraction_digits=0): ...
  ```

- **FTL syntax**: Use `camelCase` parameter names (Fluent convention)
  ```ftl
  price = { NUMBER($amount, minimumFractionDigits: 2) }
  ```

- **Automatic mapping**: Registry converts `minimumFractionDigits` → `minimum_fraction_digits` automatically

**Built-in Functions**: NUMBER and DATETIME use this automatic conversion:

| FTL Parameter (camelCase) | Python Parameter (snake_case) |
|---------------------------|-------------------------------|
| `minimumFractionDigits` | `minimum_fraction_digits` |
| `maximumFractionDigits` | `maximum_fraction_digits` |
| `useGrouping` | `use_grouping` |
| `dateStyle` | `date_style` |
| `timeStyle` | `time_style` |

**Custom Functions**: For custom functions, provide `param_map` explicitly (see example below).

**Example - Parameter Mapping**:

```python
from ftllexbuffer import FluentBundle, FUNCTION_REGISTRY

# Python function with snake_case parameters
def format_currency(amount: float, *, currency_code: str = "USD", use_symbol: bool = True) -> str:
    """Format currency amount."""
    symbols = {"USD": "$", "EUR": "€", "GBP": "£"}
    symbol = symbols.get(currency_code, currency_code) if use_symbol else currency_code
    return f"{symbol}{amount:,.2f}"

# Register with camelCase → snake_case mapping
FUNCTION_REGISTRY.register(
    format_currency,
    ftl_name="CURRENCY",
    param_map={
        "currencyCode": "currency_code",  # FTL camelCase → Python snake_case
        "useSymbol": "use_symbol",
    }
)

# Use in FTL with camelCase (FTL convention)
bundle = FluentBundle("en", use_isolating=False)
bundle.add_resource("""
price = Total: { CURRENCY($amount, currencyCode: "EUR", useSymbol: true) }
""")

result, _ = bundle.format_pattern("price", {"amount": 1234.56})
print(result)  # "Total: €1,234.56"
```

**Example - Global Function Registry**:

```python
from ftllexbuffer import FluentBundle, FUNCTION_REGISTRY

# Register functions globally
def UPPER(text: str) -> str:
    return text.upper()

def LOWER(text: str) -> str:
    return text.lower()

FUNCTION_REGISTRY.register(UPPER)
FUNCTION_REGISTRY.register(LOWER)

# All bundles have access to these functions
bundle1 = FluentBundle("en", use_isolating=False)
bundle1.add_resource("msg = { UPPER($text) }")

bundle2 = FluentBundle("lv", use_isolating=False)
bundle2.add_resource("msg = { LOWER($text) }")

# Both bundles share the same function implementations
result1, _ = bundle1.format_pattern("msg", {"text": "hello"})
print(result1)  # "HELLO"

result2, _ = bundle2.format_pattern("msg", {"text": "SVEIKI"})
print(result2)  # "sveiki"
```

**Note**: Functions registered via `bundle.add_function()` are bundle-specific. Functions registered via `FUNCTION_REGISTRY.register()` are available to all bundles created after registration.

**Advanced Example - Complex Parameter Mapping**:

```python
from ftllexbuffer import FUNCTION_REGISTRY

def format_phone_number(
    number: str,
    *,
    country_code: str = "1",
    format_type: str = "international",
    include_plus: bool = True
) -> str:
    """Format phone number with complex options."""
    digits = "".join(c for c in number if c.isdigit())

    if format_type == "international":
        prefix = f"+{country_code} " if include_plus else f"{country_code} "
        return f"{prefix}({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif format_type == "national":
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    else:  # compact
        return digits

# Register with camelCase → snake_case mapping
FUNCTION_REGISTRY.register(
    format_phone_number,
    ftl_name="PHONE",
    param_map={
        "countryCode": "country_code",      # Maps FTL camelCase to Python snake_case
        "formatType": "format_type",
        "includePlus": "include_plus",
    }
)

# Use in FTL with camelCase (Fluent convention)
bundle = FluentBundle("en", use_isolating=False)
bundle.add_resource("""
contact = Call: { PHONE($number, countryCode: "44", formatType: "international", includePlus: false) }
""")

result, _ = bundle.format_pattern("contact", {"number": "2079460958"})
print(result)  # "Call: 44 (207) 946-0958"
```

**Example - Automatic Conversion vs Manual Mapping**:

```python
from ftllexbuffer import FUNCTION_REGISTRY

# Example 1: Automatic camelCase ↔ snake_case (no param_map needed)
def format_date(value, *, date_format: str = "iso"):
    """Simple function - auto-conversion works."""
    # FTLLexBuffer automatically converts dateFormat → date_format
    return str(value)

FUNCTION_REGISTRY.register(format_date, ftl_name="DATE")
# FTL: { DATE($value, dateFormat: "iso") }
# Python receives: format_date(value, date_format="iso")

# Example 2: Custom mapping needed (non-standard names)
def format_currency(
    amount: float,
    *,
    currency: str = "USD",  # Note: NOT currency_code
    show_symbol: bool = True  # Note: NOT use_symbol
) -> str:
    """Complex function - needs explicit param_map."""
    symbols = {"USD": "$", "EUR": "€", "GBP": "£"}
    symbol = symbols.get(currency, currency) if show_symbol else ""
    return f"{symbol}{amount:,.2f}"

# Must provide param_map because Python names don't follow convention
FUNCTION_REGISTRY.register(
    format_currency,
    ftl_name="MONEY",
    param_map={
        "curr": "currency",         # FTL uses short name
        "withSymbol": "show_symbol", # FTL uses different naming
    }
)
# FTL: { MONEY($amt, curr: "EUR", withSymbol: true) }
# Python receives: format_currency(amt, currency="EUR", show_symbol=True)
```

**Example - Multiple Functions with Shared Logic**:

```python
from ftllexbuffer import FUNCTION_REGISTRY

def _format_bytes(bytes_count: int | float, *, binary: bool = False, precision: int = 2) -> str:
    """Shared implementation for byte formatting."""
    divisor = 1024 if binary else 1000
    units = ["B", "KB", "MB", "GB", "TB"] if not binary else ["B", "KiB", "MiB", "GiB", "TiB"]

    size = float(bytes_count)
    for unit in units:
        if size < divisor:
            return f"{size:.{precision}f} {unit}"
        size /= divisor
    return f"{size:.{precision}f} {units[-1]}"

# Register as FILESIZE (decimal, base-1000)
def filesize_decimal(value, **opts):
    return _format_bytes(value, binary=False, **opts)

FUNCTION_REGISTRY.register(
    filesize_decimal,
    ftl_name="FILESIZE",
    param_map={"precision": "precision"}  # Optional: explicit mapping
)

# Register as BYTESIZE (binary, base-1024)
def filesize_binary(value, **opts):
    return _format_bytes(value, binary=True, **opts)

FUNCTION_REGISTRY.register(
    filesize_binary,
    ftl_name="BYTESIZE",
    param_map={"precision": "precision"}
)

# Use in FTL
bundle = FluentBundle("en", use_isolating=False)
bundle.add_resource("""
download = Download: { FILESIZE($bytes) } ({ BYTESIZE($bytes, precision: 0) })
""")

result, _ = bundle.format_pattern("download", {"bytes": 1536000})
print(result)  # "Download: 1.54 MB (1 MiB)"
```

---

#### has_function()

```python
FunctionRegistry.has_function(ftl_name: str) -> bool
```

Check if a function is registered in the registry.

**Parameters**:
- **`ftl_name`** (str): FTL function name (e.g., "NUMBER", "DATETIME")

**Returns**: bool - True if function is registered, False otherwise

**Example**:
```python
from ftllexbuffer import FUNCTION_REGISTRY

if FUNCTION_REGISTRY.has_function("NUMBER"):
    print("NUMBER function is available")

if not FUNCTION_REGISTRY.has_function("CUSTOM"):
    print("CUSTOM function not registered")
```

---

#### get_python_name()

```python
FunctionRegistry.get_python_name(ftl_name: str) -> str | None
```

Get the Python function name for a registered FTL function.

**Parameters**:
- **`ftl_name`** (str): FTL function name (e.g., "NUMBER")

**Returns**: str | None - Python function name (e.g., "number_format"), or None if not found

**Example**:
```python
from ftllexbuffer import FUNCTION_REGISTRY

python_name = FUNCTION_REGISTRY.get_python_name("NUMBER")
print(python_name)  # "number_format"

missing = FUNCTION_REGISTRY.get_python_name("UNKNOWN")
print(missing)  # None
```

---

#### list_functions()

**Added in v0.4.0**

```python
FunctionRegistry.list_functions() -> list[str]
```

List all registered function names (FTL names).

**Returns**: list[str] - List of registered FTL function names

**Example**:
```python
from ftllexbuffer import FUNCTION_REGISTRY

functions = FUNCTION_REGISTRY.list_functions()
print(functions)  # ["NUMBER", "DATETIME", "CURRENCY", ...]

# Count available functions
print(f"Available functions: {len(functions)}")
```

---

#### get_function_info()

**Added in v0.4.0**

```python
FunctionRegistry.get_function_info(ftl_name: str) -> FunctionSignature | None
```

Get comprehensive metadata for a registered function.

**Parameters**:
- **`ftl_name`** (str): FTL function name (e.g., "NUMBER")

**Returns**: FunctionSignature | None - Function metadata, or None if not found

**FunctionSignature attributes**:
- **`ftl_name`** (str): FTL function name
- **`python_name`** (str): Python function name
- **`param_mapping`** (dict[str, str]): Maps FTL parameter names to Python parameter names
- **`callable`** (Callable): The actual Python function

**Example**:
```python
from ftllexbuffer import FUNCTION_REGISTRY

# Get function metadata
info = FUNCTION_REGISTRY.get_function_info("NUMBER")
if info:
    print(f"FTL name: {info.ftl_name}")
    print(f"Python name: {info.python_name}")
    print("Parameter mappings:")
    for ftl_param, py_param in info.param_mapping.items():
        print(f"  {ftl_param} → {py_param}")
```

**Use cases**:
- Auto-documentation generation
- Function validation before use
- IDE auto-complete integration
- Debugging parameter mappings

---

#### `__iter__()`, `__len__()`, `__contains__()`

**Added in v0.4.0**

FunctionRegistry implements dict-like protocol for convenient iteration and membership testing.

```python
# Iterate over function names
for func_name in registry:
    print(func_name)

# Count registered functions
count = len(registry)

# Check membership
if "NUMBER" in registry:
    print("NUMBER is available")
```

**Example - Auto-documentation**:
```python
from ftllexbuffer import FluentBundle

bundle = FluentBundle("en_US")

print("Available Functions:")
print("=" * 60)

for func_name in bundle._function_registry:
    info = bundle._function_registry.get_function_info(func_name)
    print(f"\n{info.ftl_name} (Python: {info.python_name})")
    if info.param_mapping:
        print("  Parameters:")
        for ftl_param, py_param in sorted(info.param_mapping.items()):
            print(f"    - {ftl_param} → {py_param}")
```

**Example - Safe function usage**:
```python
from ftllexbuffer import FluentBundle

bundle = FluentBundle("en_US")

# Check if function exists before use
if "CURRENCY" in bundle._function_registry:
    bundle.add_resource('price = { CURRENCY($amount, currency: "EUR") }')
else:
    print("CURRENCY function not available")
```

---

#### call()

```python
FunctionRegistry.call(
    ftl_name: str,
    positional: list[Any],
    named: dict[str, Any]
) -> str
```

Call a registered function with FTL arguments (internal use).

**Note**: This method is primarily for internal use by the resolver. Most users should call functions via FTL syntax or bundle methods.

**Parameters**:
- **`ftl_name`** (str): FTL function name
- **`positional`** (list[Any]): Positional arguments
- **`named`** (dict[str, Any]): Named arguments (FTL camelCase)

**Returns**: str - Function result

**Raises**:
- **FluentResolutionError**: If function not found or execution fails

---

## ValidationResult

Result object returned by `validate_resource()`.

### Validation Capabilities

`ValidationResult` performs comprehensive two-level validation of FTL source files:

#### Syntax Validation (Errors)

Parse failures that create Junk entries:

- **Malformed FTL syntax**: Incomplete expressions, invalid grammar, unparseable content
- **Critical parse errors**: Fatal errors that prevent resource parsing

**Impact**: Errors make `is_valid = False` and populate the `errors` list.

#### Semantic Validation (Warnings)

Potential issues that don't prevent parsing but may cause runtime problems:

1. **Duplicate message IDs**: Later definitions silently overwrite earlier ones (last-write-wins)
   ```ftl
   # Warning: Duplicate message ID 'hello'
   hello = First
   hello = Second  # This overwrites the first definition
   ```

2. **Messages without values**: Messages that have neither a value pattern nor attributes
   ```ftl
   # Warning: Message 'empty' has neither value nor attributes
   empty =
   ```

3. **Undefined references**: References to non-existent messages or terms
   ```ftl
   # Warning: Message 'greeting' references undefined message 'name'
   greeting = Hello, { name }
   ```

4. **Circular dependencies**: Messages or terms that reference themselves (directly or indirectly)
   ```ftl
   # Warning: Circular message reference: a → b → a
   a = { b }
   b = { a }
   ```

**Impact**: Warnings populate the `warnings` list but don't affect `is_valid`. They indicate potential runtime errors that should be fixed.

**Use Cases**:
- **CI/CD pipelines**: Validate all FTL files before deployment
- **Translation tools**: Lint FTL files for quality issues
- **IDE plugins**: Real-time validation feedback

**See Also**:
- [FluentBundle.validate_resource()](#validate_resource) - Method that returns ValidationResult
- [Common Workflows → CI/CD Pipeline](#cicd-pipeline-validate-all-ftl-files) - Practical validation examples
- [Troubleshooting → Parse Errors](#parse-errors-junk-entries) - Debugging validation failures

### Properties

#### is_valid

```python
is_valid: bool
```

`True` if no parse errors found, `False` otherwise.

#### error_count

```python
error_count: int
```

Number of parse errors (Junk entries).

#### warning_count

```python
warning_count: int
```

Number of semantic warnings found (duplicate IDs, messages without values, etc.).

#### errors

```python
errors: list[ValidationError]
```

List of parse error entries. Each `ValidationError` object has structured fields:

- `.message` (str): Error description
- `.line` (int | None): Line number where error occurred
- `.column` (int | None): Column number where error occurred
- `.source_path` (str | None): Source file path (if available)

**Note**: In v0.9.0+, errors are structured `ValidationError` instances (not raw `Junk` AST nodes).

#### warnings

```python
warnings: list[ValidationWarning]
```

List of semantic validation warnings. Each `ValidationWarning` object has structured fields:

- `.message` (str): Warning description
- `.line` (int | None): Line number where warning occurred
- `.column` (int | None): Column number where warning occurred
- `.source_path` (str | None): Source file path (if available)

Warnings indicate potential issues that don't prevent parsing but may cause runtime problems:

- **Duplicate message IDs**: Later definitions overwrite earlier ones (last-write-wins behavior)
- **Messages without values**: Messages that have neither a value pattern nor attributes
- **Undefined references**: References to non-existent messages or terms
- **Circular dependencies**: Messages or terms that reference themselves

**Note**: Warnings don't affect `is_valid` - only syntax errors make validation fail.

### Example

```python
result = bundle.validate_resource(ftl_source)

print(f"Valid: {result.is_valid}")
print(f"Errors: {result.error_count}")
print(f"Warnings: {result.warning_count}")

# Check syntax errors (v0.9.0: ValidationError instances)
if not result.is_valid:
    for error in result.errors:
        location = f"line {error.line}" if error.line else "unknown location"
        print(f"Parse error at {location}: {error.message}")

# Check semantic warnings (v0.9.0: ValidationWarning instances)
if result.warning_count > 0:
    for warning in result.warnings:
        location = f"line {warning.line}" if warning.line else "unknown location"
        print(f"Warning at {location}: {warning.message}")

# Example: Duplicate IDs trigger warnings
ftl = "msg = First\\nmsg = Second"
result = bundle.validate_resource(ftl)
# result.is_valid → True (no syntax errors)
# result.warning_count → 1 (semantic warning about duplicate)
# result.warnings[0].message → "Duplicate message ID 'msg'"
```

---

## Error Handling Patterns

All formatting methods in FTLLexBuffer return `(result, errors)` tuples. This design is **intentional** - it makes error handling explicit and composable while ensuring **graceful degradation** in production.

### Core Principle: Errors Never Crash Your Application

**CRITICAL**: `format_pattern()` and `format_value()` **NEVER raise exceptions**. All errors are collected and returned in the `errors` list. The `result` string is **always usable**, providing a fallback value even on error.

```python
# This NEVER crashes - even with invalid input
result, errors = bundle.format_pattern("missing-message")
# result → "{missing-message}" (readable fallback)
# errors → [FluentReferenceError('Message not found: missing-message')]
```

### Pattern 1: Production - Always Check Errors

**Use Cases**: Production applications that need observability

```python
import logging

logger = logging.getLogger(__name__)

def localize(bundle, message_id, args=None):
    """Production-grade localization with error logging."""
    result, errors = bundle.format_pattern(message_id, args)

    if errors:
        # Log all errors for monitoring/alerting
        for error in errors:
            logger.warning(
                f"Translation error in '{message_id}': {error}",
                extra={
                    "message_id": message_id,
                    "error_type": type(error).__name__,
                    "args": args,
                }
            )

    return result

# Usage
greeting = localize(bundle, "welcome", {"name": "Alice"})
```

**When to use**: All production code

### Pattern 2: Tests/Examples - Explicitly Ignore

**Use Cases**: Tests and documentation where errors are not relevant

```python
# Explicitly ignore errors with underscore
result, _ = bundle.format_pattern("hello")
# Underscore signals intentional ignore

# Multiple calls - brevity in tests
name, _ = bundle.format_pattern("name")
greeting, _ = bundle.format_pattern("greeting", {"name": name})
```

**When to use**: Unit tests, integration tests, documentation examples

**Best Practice**: Add a comment in test setup explaining why errors are ignored:

```python
# Note: Tests ignore errors for brevity - production code should check
def format(msg_id, args=None):
    result, _ = self.bundle.format_pattern(msg_id, args)
    return result
```

### Pattern 3: Strict Mode - Fail on Errors

**Use Cases**: Critical translations where fallbacks are unacceptable

```python
def format_strict(bundle, message_id, args=None):
    """Format message, raising exception on any error."""
    result, errors = bundle.format_pattern(message_id, args)

    if errors:
        error_details = ", ".join(str(e) for e in errors)
        raise RuntimeError(
            f"Translation failed for '{message_id}': {error_details}"
        )

    return result

# Usage - will raise on missing messages
try:
    legal_text = format_strict(bundle, "terms-and-conditions")
except RuntimeError as e:
    # Handle critical translation failure
    logger.critical(f"Legal text missing: {e}")
    # Fall back to English or show error page
```

**When to use**: Legal text, security notices, critical user-facing content

### Pattern 4: Application Wrapper - Centralized Error Handling

**Use Cases**: Consistent error handling across entire application

```python
from typing import Any

class L10nHelper:
    """Application-specific localization helper with centralized error handling."""

    def __init__(self, bundle, logger, metrics=None):
        self.bundle = bundle
        self.logger = logger
        self.metrics = metrics

    def format(self, message_id, args=None, *, attribute=None):
        """Format with application-specific error handling."""
        result, errors = self.bundle.format_pattern(
            message_id, args, attribute=attribute
        )

        if errors:
            # Log errors
            self.logger.warning(f"L10n errors in {message_id}: {errors}")

            # Send metrics (optional)
            if self.metrics:
                self.metrics.increment(
                    "l10n.error",
                    tags={"message_id": message_id}
                )

        return result

    def format_or_none(self, message_id, args=None):
        """Format message, returning None on any error (useful for optional content)."""
        result, errors = self.bundle.format_pattern(message_id, args)
        return None if errors else result

# Application setup
import logging
logger = logging.getLogger("myapp.l10n")
bundle = FluentBundle("en_US")
bundle.add_resource(ftl_source)

l10n = L10nHelper(bundle, logger)

# Usage throughout application
greeting = l10n.format("welcome", {"name": user.name})
tooltip = l10n.format("save-button", attribute="tooltip")
optional_banner = l10n.format_or_none("promo-banner")  # None if missing
```

**When to use**: Medium to large applications with consistent error handling needs

### Pattern 5: Error Categorization

**Use Cases**: Different handling for different error types

```python
from ftllexbuffer import (
    FluentReferenceError,
    FluentResolutionError,
    FluentCyclicReferenceError,
)

def format_with_categorized_errors(bundle, message_id, args=None):
    """Handle different error types differently."""
    result, errors = bundle.format_pattern(message_id, args)

    for error in errors:
        if isinstance(error, FluentReferenceError):
            # Missing message/variable - log as warning
            logger.warning(f"Missing reference: {error}")

        elif isinstance(error, FluentResolutionError):
            # Runtime error (bad function call) - log as error
            logger.error(f"Resolution error: {error}")

        elif isinstance(error, FluentCyclicReferenceError):
            # Circular reference - log as critical (should be fixed in FTL)
            logger.critical(f"Circular reference detected: {error}")

    return result
```

### Pattern 6: Async/Background Error Reporting

**Use Cases**: Web applications with centralized error tracking (Sentry, Datadog, etc.)

```python
import sentry_sdk

def format_with_sentry(bundle, message_id, args=None):
    """Format with Sentry error reporting."""
    result, errors = bundle.format_pattern(message_id, args)

    if errors:
        # Report to Sentry for tracking
        with sentry_sdk.push_scope() as scope:
            scope.set_context("l10n", {
                "message_id": message_id,
                "args": args,
                "error_count": len(errors),
            })
            for error in errors:
                sentry_sdk.capture_message(
                    f"L10n error: {error}",
                    level="warning"
                )

    return result
```

### Best Practices Summary

#### DO

✅ **Always destructure the tuple** - `result, errors = ...`
✅ **Check errors in production** - Log, monitor, alert
✅ **Use underscore in tests** - `result, _ = ...` shows intent
✅ **Categorize error types** - Handle different errors differently
✅ **Build application wrappers** - Centralize error handling logic

#### DON'T

❌ **Don't ignore the errors tuple** - `result = bundle.format_pattern(...)` (won't work)
❌ **Don't expect exceptions** - Formatting never raises
❌ **Don't suppress errors silently** - At minimum, log them
❌ **Don't use format_pattern without understanding** - Read this section first

### Why This Design?

1. **Graceful Degradation**: Application continues running even with translation errors
2. **Observability**: All errors are trackable for monitoring/alerting
3. **Composability**: Applications can build their own error handling strategies
4. **Explicit**: Error handling is part of the API contract, not hidden
5. **Production-Ready**: No surprises - you control what happens on error

### Example: Complete Production Application

```python
import logging
from ftllexbuffer import FluentBundle, FluentLocalization

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("myapp")

# Create bundle
bundle = FluentBundle("en_US")
bundle.add_resource("""
welcome = Hello, { $name }!
items = You have { $count ->
    [one] one item
   *[other] { $count } items
}.
""")

# Production pattern with error handling
def render_user_dashboard(user):
    """Render user dashboard with proper L10n error handling."""

    # Format greeting with error checking
    greeting, errors = bundle.format_pattern("welcome", {"name": user.name})
    if errors:
        logger.warning(f"Greeting translation errors: {errors}")
        # Continue with fallback value

    # Format item count
    item_text, errors = bundle.format_pattern("items", {"count": user.item_count})
    if errors:
        logger.error(f"Critical error in item count: {errors}")
        # Could fall back to English or show generic message

    return {
        "greeting": greeting,
        "items": item_text,
    }

# Usage
dashboard = render_user_dashboard(current_user)
print(dashboard["greeting"])  # "Hello, Alice!"
print(dashboard["items"])     # "You have 5 items."
```

---

## Exception Hierarchy

All exceptions inherit from `FluentError`.

```
FluentError (base)
├── FluentSyntaxError (parse errors)
├── FluentReferenceError (missing message/term/variable)
├── FluentResolutionError (runtime errors during formatting)
└── FluentCyclicReferenceError (circular message references)
```

### FluentError

Base exception class for all Fluent errors.

**Attributes**:

- **`diagnostic`** (Diagnostic | None): Structured diagnostic info with line/column numbers

**Example**:

```python
from ftllexbuffer import FluentError

try:
    bundle.format_pattern("missing")
except FluentError as e:
    print(f"Fluent error: {e}")
    if e.diagnostic:
        print(f"  Line {e.diagnostic.line}, col {e.diagnostic.column}")
```

---

### FluentSyntaxError

Raised during `add_resource()` for **critical** parse errors (malformed grammar).

**Note**: Most syntax errors become `Junk` entries (logged but not raised). Only unrecoverable errors raise exceptions.

**Example**:

```python
from ftllexbuffer import FluentSyntaxError

try:
    bundle.add_resource("invalid = { $")  # Unclosed placeable
except FluentSyntaxError as e:
    print(f"Parse error: {e}")
```

---

### FluentReferenceError

Collected when resolving unknown message/term/variable references.

**Causes**:

- Message ID not found
- Term ID not found
- Variable not provided in `args`
- Attribute not found on message

**IMPORTANT**: Never raised - errors collected in list[FluentError] returned by `format_pattern()`.

**Example**:

```python
from ftllexbuffer import FluentReferenceError

bundle.add_resource("msg = Hello!")

# Missing message
result, errors = bundle.format_pattern("missing")
# result → "{missing}"  # Fallback
# errors → [FluentReferenceError('Message not found: missing')]

# Missing attribute
result, errors = bundle.format_pattern("msg", attribute="tooltip")
# result → "{msg.tooltip}"  # Fallback
# errors → [FluentReferenceError('Attribute not found...')]
```

---

### FluentResolutionError

Runtime error during message formatting (type mismatch, invalid function arguments).

**Causes**:

- Function receives invalid argument types
- Function execution fails
- Unknown expression type in AST

**IMPORTANT**: Never raised - errors collected in list[FluentError] returned by `format_pattern()`.

**Example**:

```python
from ftllexbuffer import FluentResolutionError

bundle.add_resource("msg = { NUMBER($val) }")

result, errors = bundle.format_pattern("msg", {"val": "not-a-number"})
# result → "{NUMBER(...)}"  # Fallback
# errors → [FluentResolutionError('Invalid argument type...')]
```

---

### FluentCyclicReferenceError

Circular message references detected.

**IMPORTANT**: Does NOT raise exception - error collected in list[FluentError] returned by format_pattern().

**Rationale**: i18n errors must never crash applications. Circular references are recoverable.

**Example**:

```python
bundle.add_resource("""
a = { b }
b = { a }
""")

result, errors = bundle.format_pattern("a")
print(result)
# → "{a}"  # Readable fallback (message ID)

print(errors)
# → [FluentCyclicReferenceError('Circular reference detected: a -> b -> a')]

# Does NOT raise exception - graceful degradation with error collection
```

---

## Built-in Functions

FTLLexBuffer provides built-in Fluent functions following ECMA-402 Internationalization API conventions.

### NUMBER

> **Added in**: 0.1.0

```python
NUMBER(value, options)
```

Format numeric values with locale-specific separators.

**Parameters**:

- **`value`** (int | float): Number to format
- **`minimumFractionDigits`** (int, default=0): Minimum decimal places
- **`maximumFractionDigits`** (int, default=3): Maximum decimal places
- **`useGrouping`** (bool, default=True): Use thousand separators
- **`pattern`** (string, optional): Custom number pattern (overrides other options) - **Added in v0.5.0**

**Returns**: Formatted number string

**Locale Behavior**:

- Uses Babel's `format_decimal()` (CLDR-compliant)
- Thread-safe (no global locale state mutation)
- Automatically adapts to bundle's locale
- Thousands separator: `,` (en_US), `.` (de_DE), ` ` (lv_LV)
- Decimal separator: `.` (en_US), `,` (de_DE/lv_LV)

**Implementation Details**:

- Locale is injected by `FluentBundle` (bundle-scoped, not process-global)
- Uses Unicode CLDR data via Babel
- Matches `Intl.NumberFormat` semantics from JavaScript

**Examples**:

```ftl
price = { NUMBER($amount, minimumFractionDigits: 2) }
percent = { NUMBER($ratio, maximumFractionDigits: 0) }%
accounting = { NUMBER($amount, pattern: "#,##0.00;(#,##0.00)") }
```

```python
bundle_en = FluentBundle("en_US")
bundle_en.add_resource("price = { NUMBER($amount, minimumFractionDigits: 2) }")
bundle_en.format_pattern("price", {"amount": 1234.5})
# → "1,234.50"

bundle_lv = FluentBundle("lv_LV")
bundle_lv.add_resource("price = { NUMBER($amount, minimumFractionDigits: 2) }")
bundle_lv.format_pattern("price", {"amount": 1234.5})
# → "1 234,50"

bundle_de = FluentBundle("de_DE")
bundle_de.add_resource("price = { NUMBER($amount, minimumFractionDigits: 2) }")
bundle_de.format_pattern("price", {"amount": 1234.5})
# → "1.234,50"
```

---

### DATETIME

> **Added in**: 0.1.0

```python
DATETIME(value, options)
```

Format datetime values with locale-specific patterns.

**Parameters**:

- **`value`** (datetime | str): datetime object or ISO 8601 string
- **`dateStyle`** ("short" | "medium" | "long" | "full", default="medium"): Date format
- **`timeStyle`** ("short" | "medium" | "long" | "full" | None, default=None): Time format
- **`pattern`** (string, optional): Custom datetime pattern (overrides style options) - **Added in v0.5.0**

**Returns**: Formatted datetime string

**Locale Behavior**:

- Uses Babel's `format_datetime()` and `format_date()` (CLDR-compliant)
- Thread-safe (no global locale state mutation)
- Automatically adapts patterns to bundle's locale
- Style mappings follow CLDR conventions (not Python strftime)

**Implementation Details**:

- Locale is injected by `FluentBundle` (bundle-scoped, not process-global)
- Uses Unicode CLDR date/time patterns via Babel
- Matches `Intl.DateTimeFormat` semantics from JavaScript
- Accepts datetime objects or parses ISO 8601 strings

**Examples**:

```ftl
today = { DATETIME($date, dateStyle: "short") }
timestamp = { DATETIME($time, dateStyle: "medium", timeStyle: "short") }
iso-date = { DATETIME($timestamp, pattern: "yyyy-MM-dd") }
custom-time = { DATETIME($timestamp, pattern: "HH:mm:ss") }
```

```python
from datetime import datetime, UTC

bundle = FluentBundle("en_US")
bundle.add_resource("""
today = { DATETIME($date, dateStyle: "short") }
timestamp = { DATETIME($time, dateStyle: "medium", timeStyle: "short") }
""")

dt = datetime(2025, 10, 27, 14, 30, tzinfo=UTC)

bundle.format_pattern("today", {"date": dt})
# → "10/27/25"

bundle.format_pattern("timestamp", {"time": dt})
# → "Oct 27, 2025 2:30 PM"
```

### CURRENCY

**Added in v0.2.0**

```python
CURRENCY(value, options)
```

Format currency amounts with locale-specific symbols, placement, and precision.

**Parameters**:

- **`value`** (int | float): Monetary amount
- **`currency`** (str, required): ISO 4217 currency code (EUR, USD, JPY, BHD, etc.)
- **`currencyDisplay`** ("symbol" | "code" | "name", default="symbol"): Display mode
  - `"symbol"`: Use currency symbol (€, $, ¥)
  - `"code"`: Use currency code (EUR, USD, JPY)
  - `"name"`: Use full currency name (euros, dollars, yen)

**Returns**: Formatted currency string

**Locale Behavior**:

- Uses Babel's `format_currency()` (CLDR-compliant)
- Thread-safe (no global locale state mutation)
- Automatically positions currency symbol based on locale
  - en_US: `$123.45` (symbol before, no space)
  - lv_LV: `123,45 €` (symbol after, with space)
  - de_DE: `123,45 €` (symbol after, with space)
- Uses currency-specific decimal places from CLDR:
  - JPY, KRW: 0 decimals (¥12,345)
  - BHD, KWD, OMR: 3 decimals (123.456 د.ب.)
  - Most others: 2 decimals (€123.45)
- Handles locale-specific grouping separators automatically

**Implementation Details**:

- Locale is injected by `FluentBundle` (bundle-scoped, not process-global)
- Uses Unicode CLDR currency data via Babel
- Matches `Intl.NumberFormat` with `style: 'currency'` from JavaScript
- Symbol placement and spacing per CLDR locale conventions

**Examples**:

```ftl
# Basic usage
price = { CURRENCY($amount, currency: "EUR") }

# Display as code
price-code = { CURRENCY($amount, currency: "USD", currencyDisplay: "code") }

# Variable currency code - use select expression (FTL spec requires literal named args)
price = { $currency ->
    [EUR] { CURRENCY($amount, currency: "EUR") }
    [USD] { CURRENCY($amount, currency: "USD") }
    [GBP] { CURRENCY($amount, currency: "GBP") }
   *[other] { $amount } { $currency }
}
```

```python
# US locale: symbol before, period decimal
bundle_us = FluentBundle("en_US")
bundle_us.add_resource('price = { CURRENCY($amount, currency: "EUR") }')
bundle_us.format_pattern("price", {"amount": 123.45})
# → "€123.45"

# Latvian locale: symbol after with space, comma decimal
bundle_lv = FluentBundle("lv_LV")
bundle_lv.add_resource('price = { CURRENCY($amount, currency: "EUR") }')
bundle_lv.format_pattern("price", {"amount": 123.45})
# → "123,45 €"

# Japanese locale: JPY has 0 decimals
bundle_jp = FluentBundle("ja_JP")
bundle_jp.add_resource('price = { CURRENCY($amount, currency: "JPY") }')
bundle_jp.format_pattern("price", {"amount": 12345})
# → "¥12,345"

# Bahrain: BHD has 3 decimals
bundle_bh = FluentBundle("ar_BH")
bundle_bh.add_resource('price = { CURRENCY($amount, currency: "BHD") }')
bundle_bh.format_pattern("price", {"amount": 123.456})
# → "123.456 د.ب."

# Currency code display
bundle = FluentBundle("en_US")
bundle.add_resource('price = { CURRENCY($amount, currency: "EUR", currencyDisplay: "code") }')
bundle.format_pattern("price", {"amount": 99.99})
# → "EUR 99.99"
```

#### BIDI Isolation Characters

For RTL language support (Arabic, Hebrew, Urdu), NUMBER(), DATETIME(), and CURRENCY() add Unicode BIDI isolation marks (U+2068 FSI, U+2069 PDI) around formatted output when `use_isolating=True` (default).

**Why BIDI marks are needed**:
- Prevents RTL/LTR text mixing issues in bidirectional text
- Essential for proper display of numbers and currency in RTL languages
- Follows Unicode TR9 bidirectional text algorithm

**Example**:
```python
bundle = FluentBundle("ar")  # use_isolating=True by default
bundle.add_resource("price = { NUMBER($amount) }")
result, _ = bundle.format_pattern("price", {"amount": 123.45})
# result → "\u2068123.45\u2069" (invisible FSI/PDI marks)
```

**Parsing Formatted Output**:

If you need to parse NUMBER() or CURRENCY() output back to numeric values (e.g., user copy/paste into input fields):

```python
# Strip BIDI marks before parsing
formatted = bundle.format_pattern("price", {"amount": 123.45})[0]
clean = formatted.replace("\u2068", "").replace("\u2069", "")
# Now parse clean string

# Alternative: Remove all Unicode format characters
import unicodedata
clean = "".join(c for c in formatted if unicodedata.category(c) != "Cf")
```

**Disabling BIDI isolation** (not recommended):

```python
bundle = FluentBundle("ar", use_isolating=False)
# WARNING: Only disable for non-production use (testing, examples)
# RTL languages require BIDI marks for correct display
```

---

## Parsing API

> **Added in**: 0.5.0

FTLLexBuffer provides bi-directional localization: both formatting (data → display) and parsing (display → data). The parsing API complements the formatting functions (NUMBER, DATETIME, CURRENCY) by providing the inverse operations.

**Module**: `ftllexbuffer.parsing`

**When to use**:
- Parse user input from locale-aware forms (invoices, reports, data entry)
- Import data from CSV/Excel with locale-specific formatting
- Validate user input before processing
- Roundtrip validation (format → parse → format must preserve value)

**Thread Safety**: All parsing functions are thread-safe. Uses Babel for CLDR-compliant parsing.

---

### parse_number()

> **Added in**: 0.5.0 | **Breaking change in**: 0.8.0

```python
from ftllexbuffer.parsing import parse_number
from ftllexbuffer.diagnostics import FluentParseError

parse_number(
    value: str,
    locale_code: str,
) -> tuple[float, list[FluentParseError]]
```

Parse locale-aware number string to `float`.

**Parameters**:

- **`value`** (str): Number string formatted according to locale (e.g., "1 234,56" for lv_LV)
- **`locale_code`** (str): BCP 47 locale identifier (e.g., "en_US", "lv_LV", "de_DE")

**Returns**:
- `tuple[float, list[FluentParseError]]`:
  - First element: Parsed float, or `0.0` if parsing failed
  - Second element: List of errors (empty on success)

**v0.8.0 Breaking Change**: Returns tuple instead of raising exceptions. The `strict` parameter was removed.

**Locale Behavior**:
- Uses Babel's `parse_decimal()` internally (CLDR-compliant)
- Automatically recognizes locale-specific separators:
  - US English: "1,234.5" → 1234.5
  - Latvian: "1 234,5" → 1234.5
  - German: "1.234,5" → 1234.5

**Examples**:

```python
from ftllexbuffer.parsing import parse_number

# US English format
result, errors = parse_number("1,234.5", "en_US")
# result → 1234.5, errors → []

# Latvian format (space separator, comma decimal)
result, errors = parse_number("1 234,5", "lv_LV")
# result → 1234.5, errors → []

# German format (dot separator, comma decimal)
result, errors = parse_number("1.234,5", "de_DE")
# result → 1234.5, errors → []

# Error handling (v0.8.0+)
result, errors = parse_number("invalid", "en_US")
if errors:
    print(f"Parse error: {errors[0]}")
else:
    print(f"Parsed: {result}")
```

**Use Cases**:
- Display values, UI elements
- Non-financial data (measurements, percentages, counts)
- When float precision is acceptable

**Financial Data**: Use `parse_decimal()` instead for currency amounts and financial calculations to avoid float precision loss.

---

### parse_decimal()

> **Added in**: 0.5.0 | **Breaking change in**: 0.8.0

```python
from decimal import Decimal
from ftllexbuffer.parsing import parse_decimal
from ftllexbuffer.diagnostics import FluentParseError

parse_decimal(
    value: str,
    locale_code: str,
) -> tuple[Decimal, list[FluentParseError]]
```

Parse locale-aware number string to `Decimal` (financial precision).

**Parameters**:

- **`value`** (str): Number string formatted according to locale (e.g., "1 234,56" for lv_LV)
- **`locale_code`** (str): BCP 47 locale identifier (e.g., "en_US", "lv_LV", "de_DE")

**Returns**:
- `tuple[Decimal, list[FluentParseError]]`:
  - First element: Parsed Decimal, or `Decimal("0")` if parsing failed
  - Second element: List of errors (empty on success)

**v0.8.0 Breaking Change**: Returns tuple instead of raising exceptions. The `strict` parameter was removed.

**Why Decimal for Financial Data**:

Float arithmetic has precision loss that accumulates in financial calculations:

```python
# WRONG - Float precision loss
amount = 100.50
vat = amount * 0.21  # → 21.105000000000004 (precision loss!)

# CORRECT - Decimal precision
from decimal import Decimal
amount = Decimal("100.50")
vat = amount * Decimal("0.21")  # → Decimal('21.105') (exact!)
```

**Locale Behavior**:
- Uses Babel's `parse_decimal()` internally (CLDR-compliant)
- Returns `Decimal` object with exact precision (no float rounding errors)
- Automatically recognizes locale-specific separators
- **Special values**: Accepts `NaN`, `Infinity`, and `Inf` (case-insensitive) per IEEE 754 standard - use `is_valid_decimal()` type guard to reject these for financial data

**Examples**:

```python
from decimal import Decimal
from ftllexbuffer.parsing import parse_decimal
from ftllexbuffer.parsing.guards import has_parse_errors, is_valid_decimal

# Financial precision - no float rounding errors
result, errors = parse_decimal("100,50", "lv_LV")
if not has_parse_errors(errors) and is_valid_decimal(result):
    vat = result * Decimal("0.21")  # → Decimal('21.105') - exact!

# US format
result, errors = parse_decimal("1,234.56", "en_US")
# result → Decimal('1234.56'), errors → []

# Latvian format
result, errors = parse_decimal("1 234,56", "lv_LV")
# result → Decimal('1234.56'), errors → []

# German format
result, errors = parse_decimal("1.234,56", "de_DE")
# result → Decimal('1234.56'), errors → []

# Error handling (v0.8.0+)
result, errors = parse_decimal("invalid", "en_US")
if errors:
    print(f"Parse error: {errors[0]}")
    # result is Decimal("0") - default fallback
```

**Use Cases**:
- **Financial calculations** (invoices, payments, VAT, taxes)
- **Currency amounts** (prices, balances, totals)
- **Accounting** (ledgers, reports, reconciliation)
- Any calculation where precision matters

**Best Practice**: Always use `Decimal` for financial data. Float precision loss accumulates and causes rounding errors in reports and calculations.

---

### parse_date()

> **Added in**: 0.5.0 | **Breaking change in**: 0.8.0

```python
from datetime import date
from ftllexbuffer.parsing import parse_date
from ftllexbuffer.diagnostics import FluentParseError

parse_date(
    value: str,
    locale_code: str,
) -> tuple[date | None, list[FluentParseError]]
```

Parse locale-aware date string to `date` object.

**Parameters**:

- **`value`** (str): Date string formatted according to locale (e.g., "28.01.2025" for lv_LV)
- **`locale_code`** (str): BCP 47 locale identifier (e.g., "en_US", "lv_LV", "de_DE")

**Returns**:
- `tuple[date | None, list[FluentParseError]]`:
  - First element: Parsed date object, or `None` if parsing failed
  - Second element: List of errors (empty on success)

**v0.8.0 Breaking Change**: Returns tuple instead of raising exceptions. The `strict` parameter was removed.

**Locale Behavior**:
- Uses Babel CLDR patterns with Python 3.13 `strptime` for flexible parsing
- Locale determines day-first vs month-first interpretation:
  - US: "01/02/2025" → January 2 (month-first)
  - Europe: "01/02/2025" → February 1 (day-first)
- ISO 8601 format ("2025-01-28") works universally (recommended for unambiguous dates)

**Supported Patterns** (v0.7.0+):
1. ISO 8601 format (fast path): "2025-01-28"
2. Locale-specific CLDR patterns from Babel
3. **No fallback patterns** - only ISO 8601 and locale CLDR patterns are supported

**Examples**:

```python
from ftllexbuffer.parsing import parse_date
from ftllexbuffer.parsing.guards import has_parse_errors, is_valid_date

# US format (month-first)
result, errors = parse_date("1/28/2025", "en_US")
# result → date(2025, 1, 28), errors → []

# European format (day-first)
result, errors = parse_date("28.01.2025", "lv_LV")
# result → date(2025, 1, 28), errors → []

# ISO 8601 (works everywhere, unambiguous)
result, errors = parse_date("2025-01-28", "en_US")
# result → date(2025, 1, 28), errors → []

# Error handling (v0.8.0+)
result, errors = parse_date("invalid", "en_US")
if errors:
    print(f"Parse error: {errors[0]}")
elif is_valid_date(result):
    print(f"Parsed: {result}")
```

**Ambiguous Dates**:

```python
# AMBIGUOUS: "01/02/2025" - January 2 or February 1?
result1, _ = parse_date("01/02/2025", "en_US")  # → date(2025, 1, 2) (month-first)
result2, _ = parse_date("01/02/2025", "lv_LV")  # → date(2025, 2, 1) (day-first)

# RECOMMENDED: Use ISO 8601 to avoid ambiguity
result, _ = parse_date("2025-01-02", locale)  # → Always January 2
```

**Implementation Note**:
- **Python 3.13 stdlib only** - Uses `datetime.strptime()` and `datetime.fromisoformat()` (no external date libraries)
- **Babel CLDR patterns** - Converts Babel date patterns to strptime format directives (e.g., `"M/d/yy"` → `"%m/%d/%y"`)
- **Fast path** - ISO 8601 dates use native `fromisoformat()` for maximum speed
- **No fallback patterns** (v0.7.0+) - Only ISO 8601 and locale CLDR patterns are supported
- **Thread-safe** - No global state, immutable pattern lists
- **Zero external dependencies** beyond Babel (already required for number formatting)

---

### parse_datetime()

> **Added in**: 0.5.0 | **Breaking change in**: 0.8.0

```python
from datetime import datetime, timezone
from ftllexbuffer.parsing import parse_datetime
from ftllexbuffer.diagnostics import FluentParseError

parse_datetime(
    value: str,
    locale_code: str,
    *,
    tzinfo: timezone | None = None
) -> tuple[datetime | None, list[FluentParseError]]
```

Parse locale-aware datetime string to `datetime` object.

**Parameters**:

- **`value`** (str): DateTime string formatted according to locale
- **`locale_code`** (str): BCP 47 locale identifier (e.g., "en_US", "lv_LV", "de_DE")
- **`tzinfo`** (timezone | None, default=None): Timezone to assign if not present in string

**Returns**:
- `tuple[datetime | None, list[FluentParseError]]`:
  - First element: Parsed datetime object, or `None` if parsing failed
  - Second element: List of errors (empty on success)

**v0.8.0 Breaking Change**: Returns tuple instead of raising exceptions. The `strict` parameter was removed.

**Timezone Handling**:
- If string contains timezone info, uses that timezone
- If string has no timezone and `tzinfo` parameter provided, assigns that timezone
- If string has no timezone and `tzinfo=None`, returns naive datetime

**Locale Behavior**:
- Uses Babel CLDR patterns with Python 3.13 `strptime` for flexible parsing
- ISO 8601 format works universally (recommended)

**Examples**:

```python
from datetime import timezone
from ftllexbuffer.parsing import parse_datetime
from ftllexbuffer.parsing.guards import has_parse_errors, is_valid_datetime

# Parse datetime
result, errors = parse_datetime("1/28/2025 14:30", "en_US")
# result → datetime(2025, 1, 28, 14, 30), errors → []

# ISO 8601 (recommended)
result, errors = parse_datetime("2025-01-28 14:30", "en_US")
# result → datetime(2025, 1, 28, 14, 30), errors → []

# With timezone
result, errors = parse_datetime("2025-01-28 14:30", "en_US", tzinfo=timezone.utc)
# result → datetime(2025, 1, 28, 14, 30, tzinfo=timezone.utc), errors → []

# Error handling (v0.8.0+)
result, errors = parse_datetime("invalid", "en_US")
if errors:
    print(f"Parse error: {errors[0]}")
elif is_valid_datetime(result):
    print(f"Parsed: {result}")
```

**Implementation Note**:
- Same implementation as `parse_date()` with time component support
- Uses Babel CLDR datetime patterns converted to strptime format
- Pattern conversion includes time directives: `"HH:mm:ss"` → `"%H:%M:%S"`
- Fast path for ISO 8601 datetime strings
- Thread-safe, zero external dependencies beyond Babel

---

### parse_currency()

> **Added in**: 0.5.0 | **Breaking change in**: 0.8.0

```python
from decimal import Decimal
from ftllexbuffer.parsing import parse_currency
from ftllexbuffer.diagnostics import FluentParseError

parse_currency(
    value: str,
    locale_code: str,
    *,
    default_currency: str | None = None,
    infer_from_locale: bool = False
) -> tuple[tuple[Decimal, str] | None, list[FluentParseError]]
```

Parse locale-aware currency string to `(Decimal, currency_code)` tuple.

**Parameters**:

- **`value`** (str): Currency string with amount and currency symbol/code (e.g., "100,50 €" for lv_LV)
- **`locale_code`** (str): BCP 47 locale identifier (e.g., "en_US", "lv_LV", "de_DE")
- **`default_currency`** (str | None, default=None): Currency code to use for ambiguous symbols ($, ¢, ₨, ₱, kr)
- **`infer_from_locale`** (bool, default=False): If True, infer currency from locale for ambiguous symbols

**Returns**:
- `tuple[tuple[Decimal, str] | None, list[FluentParseError]]`:
  - First element: Tuple of `(amount, currency_code)` or `None` if parsing failed
    - `amount`: Decimal with exact precision (no float rounding errors)
    - `currency_code`: ISO 4217 currency code (e.g., "EUR", "USD", "JPY")
  - Second element: List of errors (empty on success)

**v0.8.0 Breaking Change**: Returns nested tuple instead of raising exceptions. The `strict` parameter was removed.

**Supported Currencies**:
- All ISO 4217 currency codes (EUR, USD, GBP, JPY, etc.)
- Major currency symbols (€, $, £, ¥, etc.)
- Currency codes can appear before or after amount (locale-dependent)
- **v0.7.0+**: Ambiguous symbols ($, ¢, ₨, ₱, kr) require `default_currency` or `infer_from_locale`

**Locale Behavior**:
- Uses Babel's currency parsing (CLDR-compliant)
- Automatically recognizes:
  - Currency symbols: €, $, £, ¥
  - ISO codes: EUR, USD, GBP, JPY
  - Locale-specific separators
  - Position (€100 or 100€ depending on locale)

**Examples**:

```python
from ftllexbuffer.parsing import parse_currency
from ftllexbuffer.parsing.guards import has_parse_errors, is_valid_currency

# Parse EUR with symbol (unambiguous)
result, errors = parse_currency("€100.50", "en_US")
# result → (Decimal('100.50'), 'EUR'), errors → []

# Parse with ISO code
result, errors = parse_currency("USD 1,234.56", "en_US")
# result → (Decimal('1234.56'), 'USD'), errors → []

# Latvian format (space separator, comma decimal, symbol after)
result, errors = parse_currency("1 234,56 €", "lv_LV")
# result → (Decimal('1234.56'), 'EUR'), errors → []

# Ambiguous symbol ($) - requires default_currency (v0.7.0+)
result, errors = parse_currency("$100", "en_CA", default_currency="CAD")
# result → (Decimal('100'), 'CAD'), errors → []

# Or use infer_from_locale
result, errors = parse_currency("$100", "en_CA", infer_from_locale=True)
# result → (Decimal('100'), 'CAD'), errors → []

# Error handling (v0.8.0+)
result, errors = parse_currency("invalid", "en_US")
if errors:
    print(f"Parse error: {errors[0]}")
elif is_valid_currency(result):
    amount, currency = result
    print(f"Amount: {amount}, Currency: {currency}")
```

**Use Cases**:
- Parse user input from invoice forms
- Import financial data from spreadsheets
- Validate currency amounts before processing payments
- Extract currency from formatted reports

**Financial Precision**: Returns `Decimal` (not float) to preserve exact precision in financial calculations.

---

### Roundtrip Validation

A critical property of bi-directional localization is that format → parse → format must preserve the original value:

```python
from decimal import Decimal
from ftllexbuffer import FluentBundle
from ftllexbuffer.parsing import parse_currency
from ftllexbuffer.runtime.functions import currency_format

locale = "lv_LV"
original = Decimal("1234.56")

# Format for display
formatted = currency_format(float(original), locale, currency="EUR")
# → "1 234,56 €"

# Parse user input (v0.8.0 API)
result, errors = parse_currency(formatted, locale)
# result → (Decimal('1234.56'), 'EUR'), errors → []

# Roundtrip: Value must be preserved
assert not errors
parsed, currency = result
assert parsed == original  # Passes
assert currency == "EUR"   # Passes
```

**Best Practice**: Always use the **same locale** for formatting and parsing. Mixing locales breaks roundtrip correctness:

```python
# WRONG - Different locales break roundtrip
formatted = currency_format(1234.56, "lv_LV", currency="EUR")  # → "1 234,56 €"
result, errors = parse_currency(formatted, "en_US")
# errors will be non-empty - US parser expects "€1,234.56", not "1 234,56 €"

# CORRECT - Same locale for format and parse
locale = "lv_LV"
formatted = currency_format(1234.56, locale, currency="EUR")  # → "1 234,56 €"
result, errors = parse_currency(formatted, locale)  # Success
```

---

### Error Handling

> **v0.8.0 Breaking Change**: All parsing functions now return `tuple[result, list[FluentParseError]]` instead of raising exceptions. The `strict` parameter was removed.

All parsing functions follow the same error handling pattern:

```python
from decimal import Decimal
from ftllexbuffer.parsing import parse_decimal
from ftllexbuffer.parsing.guards import has_parse_errors, is_valid_decimal

# v0.8.0: Check errors list instead of catching exceptions
result, errors = parse_decimal(user_input, locale)

if has_parse_errors(errors):
    # Handle errors - result is default value (Decimal("0"))
    show_error_to_user(f"Invalid amount: {errors[0]}")
    return

# Validate result is finite (not NaN/Infinity)
if not is_valid_decimal(result):
    show_error_to_user("Amount must be a finite number")
    return

# Process valid amount
process_payment(result)
```

**Default values on error**:
- `parse_number()` returns `0.0`
- `parse_decimal()` returns `Decimal("0")`
- `parse_date()` returns `None`
- `parse_datetime()` returns `None`
- `parse_currency()` returns `None`

**Type guards** (from `ftllexbuffer.parsing.guards`):
- `has_parse_errors(errors)` - Check if error list is non-empty
- `is_valid_decimal(value)` - Check Decimal is finite (not NaN/Infinity)
- `is_valid_number(value)` - Check float is finite (not NaN/Infinity)
- `is_valid_currency(value)` - Check currency tuple is not None and has finite amount
- `is_valid_date(value)` - Check date is not None
- `is_valid_datetime(value)` - Check datetime is not None

---

### Common Patterns

#### Invoice Processing

```python
from decimal import Decimal
from ftllexbuffer import FluentBundle
from ftllexbuffer.parsing import parse_decimal
from ftllexbuffer.parsing.guards import has_parse_errors, is_valid_decimal

bundle = FluentBundle("lv_LV")
bundle.add_resource("""
    subtotal = Summa: { CURRENCY($amount, currency: "EUR") }
    vat = PVN (21%): { CURRENCY($vat, currency: "EUR") }
    total = Kopa: { CURRENCY($total, currency: "EUR") }
""")

def process_invoice(user_input: str) -> dict | None:
    # Parse user input (v0.8.0 API)
    subtotal, errors = parse_decimal(user_input, "lv_LV")

    if has_parse_errors(errors) or not is_valid_decimal(subtotal):
        return None  # Invalid input

    # Calculate VAT (financial precision)
    vat_rate = Decimal("0.21")
    vat = subtotal * vat_rate
    total = subtotal + vat

    # Format for display
    display = {
        "subtotal": bundle.format_value("subtotal", {"amount": float(subtotal)})[0],
        "vat": bundle.format_value("vat", {"vat": float(vat)})[0],
        "total": bundle.format_value("total", {"total": float(total)})[0],
    }

    return {
        "display": display,
        "data": {"subtotal": subtotal, "vat": vat, "total": total}
    }

# Example usage
result = process_invoice("1 234,56")
# display: {"subtotal": "Summa: 1 234,56 EUR", ...}
# data: {"subtotal": Decimal('1234.56'), ...}
```

#### Form Input Validation

```python
from decimal import Decimal
from ftllexbuffer.parsing import parse_decimal
from ftllexbuffer.parsing.guards import has_parse_errors, is_valid_decimal

def validate_amount_field(input_value: str, locale: str) -> tuple[Decimal | None, str | None]:
    """Validate and parse amount input field.

    Returns:
        (parsed_value, error_message) - error_message is None if valid
    """
    # Trim whitespace
    input_value = input_value.strip()

    # Check not empty
    if not input_value:
        return (None, "Amount is required")

    # Parse (v0.8.0 API)
    result, errors = parse_decimal(input_value, locale)
    if has_parse_errors(errors):
        return (None, f"Invalid amount format for {locale}")

    # Validate finite (not NaN/Infinity)
    if not is_valid_decimal(result):
        return (None, "Invalid numeric value")

    # Validate range
    if result <= 0:
        return (None, "Amount must be positive")

    if result > Decimal("1000000"):
        return (None, "Amount exceeds maximum (1,000,000)")

    return (result, None)

# Usage in web form
amount, error = validate_amount_field(request.form['amount'], user_locale)
if error:
    flash(error, 'error')
    return redirect(url_for('form'))

# Amount is valid Decimal, use in calculations
process_payment(amount)
```

#### Data Import from CSV

```python
from ftllexbuffer.parsing import parse_decimal, parse_date
from ftllexbuffer.parsing.guards import has_parse_errors

def import_transactions_csv(csv_path: str, locale: str) -> tuple[list[dict], list[str]]:
    """Import financial transactions from CSV."""
    import csv

    transactions = []
    errors = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            # Parse date (v0.8.0 API)
            date_result, date_errors = parse_date(row['date'], locale)
            if has_parse_errors(date_errors):
                errors.append(f"Row {row_num}: Invalid date '{row['date']}'")
                continue

            # Parse amount (v0.8.0 API)
            amount_result, amount_errors = parse_decimal(row['amount'], locale)
            if has_parse_errors(amount_errors):
                errors.append(f"Row {row_num}: Invalid amount '{row['amount']}'")
                continue

            transactions.append({
                "date": date_result,
                "amount": amount_result,
                "description": row['description']
            })

    return transactions, errors

# Usage
transactions, errors = import_transactions_csv("export.csv", "lv_LV")
if errors:
    print(f"Import completed with {len(errors)} errors:")
    for error in errors:
        print(f"  - {error}")
```

---

### Migration from Babel

If you're currently using Babel's parsing functions directly, migrating to FTLLexBuffer's parsing API provides a consistent interface:

**Before (Babel only)**:

```python
from babel.numbers import parse_decimal as babel_parse_decimal
from ftllexbuffer import FluentBundle

# Formatting: FTLLexBuffer
bundle = FluentBundle("lv_LV")
formatted = bundle.format_value("price", {"amount": 1234.56})

# Parsing: Babel directly
user_input = "1 234,56"
parsed = babel_parse_decimal(user_input, locale="lv_LV")
```

**After (FTLLexBuffer for both - v0.8.0+ API)**:

```python
from ftllexbuffer import FluentBundle
from ftllexbuffer.parsing import parse_decimal
from ftllexbuffer.parsing.guards import has_parse_errors

# Formatting: FTLLexBuffer
bundle = FluentBundle("lv_LV")
formatted = bundle.format_value("price", {"amount": 1234.56})

# Parsing: FTLLexBuffer (consistent API, v0.8.0+)
user_input = "1 234,56"
result, errors = parse_decimal(user_input, "lv_LV")  # Same locale format!
if not has_parse_errors(errors):
    parsed = result
```

**Benefits**:
- Single import source (`ftllexbuffer`)
- Consistent locale code format (underscore-separated: "lv_LV")
- Symmetric API design (format ↔ parse)
- Structured error handling (v0.8.0+) - errors as data, not exceptions
- Integrated documentation

---

### See Also

- [PARSING.md](PARSING.md) - Comprehensive parsing best practices guide
- [Built-in Functions](#built-in-functions) - Formatting functions (NUMBER, DATETIME, CURRENCY)
- [examples/bidirectional_formatting.py](examples/bidirectional_formatting.py) - Working example

---

## Advanced APIs - Low-Level Functions

For advanced use cases requiring direct access to formatting functions without the FTL syntax layer, FTLLexBuffer exports the underlying Python implementations of NUMBER, DATETIME, and CURRENCY.

**When to use these**:
- Building custom functions that need number/datetime formatting
- Direct Python API usage without FTL syntax
- Testing and validation tools
- Type-safe wrappers for specific locales

**When to use the FTL functions instead**:
- Standard message formatting (use `NUMBER()` and `DATETIME()` in FTL)
- Runtime message resolution with FluentBundle

**Import**:
```python
from ftllexbuffer import number_format, datetime_format, currency_format
```

---

### number_format()

> **Added in**: 0.1.0

```python
def number_format(
    value: int | float,
    locale_code: str = "en-US",
    *,
    minimum_fraction_digits: int = 0,
    maximum_fraction_digits: int = 3,
    use_grouping: bool = True,
) -> str
```

Format number with locale-specific separators using Python API (snake_case parameters).

**Parameters**:
- **`value`** (int | float): Number to format
- **`locale_code`** (str, default="en-US"): BCP 47 locale identifier (e.g., "en-US", "de-DE", "lv-LV")
- **`minimum_fraction_digits`** (int, default=0): Minimum decimal places
- **`maximum_fraction_digits`** (int, default=3): Maximum decimal places
- **`use_grouping`** (bool, default=True): Use thousands separator

**Returns**: str - Formatted number string

**Thread Safety**: Thread-safe. Uses Babel (no global locale state mutation).

**CLDR Compliance**: Implements CLDR formatting rules via Babel. Matches Intl.NumberFormat semantics.

**Examples**:
```python
from ftllexbuffer import number_format

# English formatting
number_format(1234.5, "en-US")
# → "1,234.5"

# German formatting
number_format(1234.5, "de-DE")
# → "1.234,5"

# Latvian formatting
number_format(1234.5, "lv-LV")
# → "1 234,5"

# Fixed decimal places
number_format(42, "en-US", minimum_fraction_digits=2)
# → "42.00"

# No grouping
number_format(1234567, "en-US", use_grouping=False)
# → "1234567"
```

**Relationship to NUMBER() function**:
- `NUMBER()` in FTL uses camelCase parameters (minimumFractionDigits)
- `number_format()` uses Python snake_case parameters (minimum_fraction_digits)
- FunctionRegistry bridges the two conventions automatically

---

### datetime_format()

> **Added in**: 0.1.0

```python
def datetime_format(
    value: datetime | str,
    locale_code: str = "en-US",
    *,
    date_style: Literal["short", "medium", "long", "full"] = "medium",
    time_style: Literal["short", "medium", "long", "full"] | None = None,
) -> str
```

Format datetime with locale-specific formatting using Python API (snake_case parameters).

**Parameters**:
- **`value`** (datetime | str): datetime object or ISO 8601 string
- **`locale_code`** (str, default="en-US"): BCP 47 locale identifier
- **`date_style`** ("short" | "medium" | "long" | "full", default="medium"): Date format style
- **`time_style`** ("short" | "medium" | "long" | "full" | None, default=None): Time format style (None = date only)

**Returns**: str - Formatted datetime string

**Thread Safety**: Thread-safe. Uses Babel (no global locale state mutation).

**CLDR Compliance**: Implements CLDR formatting rules via Babel. Matches Intl.DateTimeFormat semantics.

**Examples**:
```python
from datetime import datetime, UTC
from ftllexbuffer import datetime_format

dt = datetime(2025, 10, 27, 14, 30, tzinfo=UTC)

# Date only (default)
datetime_format(dt, "en-US", date_style="short")
# → "10/27/25"

datetime_format(dt, "de-DE", date_style="short")
# → "27.10.25"

# Date with time
datetime_format(dt, "en-US", date_style="medium", time_style="short")
# → "Oct 27, 2025, 2:30 PM"

# ISO string input
datetime_format("2025-10-27T14:30:00Z", "en-US", date_style="long")
# → "October 27, 2025"
```

**Relationship to DATETIME() function**:
- `DATETIME()` in FTL uses camelCase parameters (dateStyle, timeStyle)
- `datetime_format()` uses Python snake_case parameters (date_style, time_style)
- FunctionRegistry bridges the two conventions automatically

---

### currency_format()

**Added in v0.2.0**

```python
def currency_format(
    value: int | float,
    locale_code: str = "en-US",
    *,
    currency: str,
    currency_display: Literal["symbol", "code", "name"] = "symbol",
) -> str
```

Format currency with locale-specific formatting using Python API (snake_case parameters).

**Parameters**:
- **`value`** (int | float): Monetary amount to format
- **`locale_code`** (str, default="en-US"): BCP 47 locale identifier (e.g., "en-US", "de-DE", "lv-LV")
- **`currency`** (str, **required**): ISO 4217 currency code (e.g., "USD", "EUR", "JPY", "BHD")
- **`currency_display`** ("symbol" | "code" | "name", default="symbol"): Display format
  - `"symbol"`: Currency symbol (€, $, ¥)
  - `"code"`: ISO code (EUR, USD, JPY)
  - `"name"`: Full currency name (euros, US dollars)

**Returns**: str - Formatted currency string

**Thread Safety**: Thread-safe. Uses Babel (no global locale state mutation).

**CLDR Compliance**: Implements CLDR currency formatting rules via Babel. Respects:
- **Currency-specific decimal places**: JPY (0), BHD/KWD/OMR (3), most others (2)
- **Locale-specific symbol placement**: en_US (before), lv_LV/de_DE (after with space)
- **Locale-specific grouping**: en_US (comma), de_DE (period), lv_LV (space)

**Examples**:
```python
from ftllexbuffer import currency_format

# Symbol display (default) - locale determines placement
currency_format(1234.56, "en-US", currency="USD")
# → "$1,234.56"  (symbol before, no space)

currency_format(1234.56, "de-DE", currency="EUR")
# → "1.234,56 €"  (symbol after, with space)

currency_format(1234.56, "lv-LV", currency="EUR")
# → "1 234,56 €"  (space grouping, symbol after)

# Code display
currency_format(1234.56, "en-US", currency="EUR", currency_display="code")
# → "EUR 1,234.56"

# Name display
currency_format(1234.56, "en-US", currency="EUR", currency_display="name")
# → "1,234.56 euros"

# Currency-specific decimal places (CLDR rules)
currency_format(1234, "en-US", currency="JPY")
# → "¥1,234"  (0 decimals for JPY)

currency_format(1234.567, "en-US", currency="BHD")
# → "BHD 1,234.567"  (3 decimals for BHD)

# All major currencies
currency_format(99.99, "en-US", currency="GBP")  # → "£99.99"
currency_format(99.99, "en-US", currency="CAD")  # → "CA$99.99"
currency_format(99.99, "en-US", currency="AUD")  # → "A$99.99"
currency_format(99.99, "en-US", currency="CHF")  # → "CHF 99.99"
```

**Relationship to CURRENCY() function**:
- `CURRENCY()` in FTL uses camelCase parameters (currencyDisplay)
- `currency_format()` uses Python snake_case parameters (currency_display)
- FunctionRegistry bridges the two conventions automatically

**Error Handling**:
- Invalid currency codes: Falls back to `"{currency} {value}"` format
- Invalid values: Falls back to `"{currency} {value}"` format
- Never raises exceptions (graceful degradation)

**BIDI Isolation**:
- By default, formatted output includes Unicode FSI/PDI marks (U+2068, U+2069)
- Required for RTL language support (Arabic, Hebrew)
- Can be disabled with `FluentBundle(use_isolating=False)` (NOT recommended for production)
- See BIDI Isolation section for details on parsing formatted output

---

## Common Pitfalls

### Variables Are Runtime-Provided

**Pitfall**: Expecting FTL to declare variables like function parameters.

**Reality**: FTL variables (`$name`, `$count`) are NOT declared in FTL source - they're provided at runtime via `format_pattern()` args.

```ftl
# WRONG - No variable declaration syntax in FTL
$name: string
welcome = Hello, { $name }!

# CORRECT - Variables just referenced
welcome = Hello, { $name }!
```

```python
# Provide variables at format time
bundle.add_resource("welcome = Hello, { $name }!")
result, errors = bundle.format_pattern("welcome", {"name": "Alice"})
# result → "Hello, Alice!"

# Missing variable returns readable fallback
result, errors = bundle.format_pattern("welcome")  # Missing {"name": ...}
# result → "Hello, {$name}!"  # Readable fallback
# errors → [FluentReferenceError(...)]
```

---

### Circular References Never Raise Exceptions

**Pitfall**: Expecting `FluentCyclicReferenceError` to be raised like a normal exception.

**Reality**: Circular references are detected and returned in the errors list - NEVER raised.

```ftl
a = { b }
b = { a }
```

```python
result, errors = bundle.format_pattern("a")
# result → "{a}"  # Readable fallback
# errors → [FluentCyclicReferenceError('Circular reference detected: a -> b -> a')]

# Does NOT raise exception - graceful degradation
```

**Rationale**: i18n errors must never crash applications. All formatting errors are recoverable.

---

### use_isolating=True Is CRITICAL for RTL Languages

**Pitfall**: Disabling bidi isolation (`use_isolating=False`) for "cleaner output" then deploying to RTL languages.

**Reality**: RTL languages (Arabic, Hebrew, Persian, Urdu) will have **corrupted text** without bidi isolation.

```python
# WRONG - Disabling isolation breaks RTL
bundle = FluentBundle("ar_EG", use_isolating=False)
bundle.add_resource("msg = مرحبا { $name }!")
result, _ = bundle.format_pattern("msg", {"name": "John"})
# → Text corruption when mixing Arabic and English

# CORRECT - Keep isolation enabled (default)
bundle = FluentBundle("ar_EG", use_isolating=True)  # Default
bundle.add_resource("msg = مرحبا { $name }!")
result, _ = bundle.format_pattern("msg", {"name": "John"})
# → Correct rendering with FSI/PDI Unicode isolation marks
```

**Rule**: Only use `use_isolating=False` if:
1. Your application will NEVER support RTL languages
2. You need cleaner test assertions or documentation examples

**Systems-Based Decision**: Set `use_isolating` architecturally at bundle creation based on application scope:
- **Production apps**: Use default `use_isolating=True` (safety-first)
- **Documentation**: Use `use_isolating=False` explicitly (clarity)
- **Unit tests**: Use `use_isolating=False` explicitly (exact assertions)
- **LTR-only tools**: Use `use_isolating=False` explicitly (verifiable constraint)

**Note**: All examples in this API documentation use `use_isolating=False` for clean output. This is a documentation convention - production code should use the default (`use_isolating=True`).

**See**: Unicode TR9 Bidirectional Algorithm: http://www.unicode.org/reports/tr9/

---

### Parser Continues After Syntax Errors

**Pitfall**: Expecting `add_resource()` to reject entire FTL file if one message has syntax error.

**Reality**: Parser uses robustness principle - continues after non-critical errors.

```ftl
# FTL file with one syntax error
valid-message = Hello!
invalid-message = { $
another-valid = Goodbye!
```

```python
bundle.add_resource(ftl_source)
# Parser creates Junk entry for invalid-message, but continues
# valid-message and another-valid are successfully loaded
```

**Use `validate_resource()` for strict validation**:

```python
result = bundle.validate_resource(ftl_source)
if not result.is_valid:
    for error in result.errors:
        location = f"line {error.line}" if error.line else "unknown"
        print(f"Parse error at {location}: {error.message}")
    # Decide: reject file or log warnings
```

---

### Message Overwriting Is Last-Write-Wins

**Pitfall**: Expecting error when loading duplicate message IDs.

**Reality**: Later definitions silently replace earlier ones.

```python
bundle.add_resource("hello = First definition")
bundle.add_resource("hello = Second definition")

result, _ = bundle.format_pattern("hello")
# result → "Second definition"  # Later definition wins
```

**Best Practice**: Use `validate_resource()` to detect duplicates before production deployment.

---

## Troubleshooting

### Message Not Found Error

**Symptom**: `FluentReferenceError` with message "Message not found: {message_id}" in errors list

**Causes**:
1. Message ID doesn't exist in bundle
2. Typo in message ID
3. Message defined in different resource file not loaded yet

**Solutions**:
```python
# Verify message exists
if bundle.has_message("my-message"):
    result, errors = bundle.format_pattern("my-message")
else:
    print("Message not defined")

# List all available messages
print("Available messages:", bundle.get_message_ids())

# Check if resource was loaded
result = bundle.validate_resource(ftl_source)
if not result.is_valid:
    print("Resource failed to load:", result.errors)
```

---

### Circular Reference Detected

**Symptom**: `FluentCyclicReferenceError` in errors list, fallback value `{message_id}` returned

**Causes**:
1. Message references itself directly: `a = { a }`
2. Message references itself indirectly: `a = { b }`, `b = { a }`
3. Term references itself

**Solutions**:
```python
# Use validate_resource() to detect cycles before deployment
result = bundle.validate_resource(ftl_source)
if result.warning_count > 0:
    for warning in result.warnings:
        if "Circular" in warning.message:
            location = f"line {warning.line}" if warning.line else "unknown"
            print(f"Cycle detected at {location}: {warning.message}")

# Fix the circular reference in FTL source
# WRONG:
# a = { b }
# b = { a }

# CORRECT:
# a = Value A
# b = Value B referencing { a }
```

---

### Missing Variable Fallback

**Symptom**: Variable appears as `{$varName}` in output instead of being replaced

**Causes**:
1. Variable not provided in `args` dictionary
2. Typo in variable name (case-sensitive)
3. Variable value is None or undefined

**Solutions**:
```python
# Check required variables before formatting
required_vars = bundle.get_message_variables("welcome")
print(f"Message requires: {required_vars}")

provided_vars = {"name": "Alice"}
missing = required_vars - set(provided_vars.keys())
if missing:
    print(f"Missing variables: {missing}")

# Provide all required variables
result, errors = bundle.format_pattern("welcome", {"name": "Alice", "count": 5})
if errors:
    for error in errors:
        print(f"Error: {error}")
```

---

### Attribute Not Found

**Symptom**: `FluentReferenceError` with message "Attribute not found" in errors list

**Causes**:
1. Attribute doesn't exist on message
2. Typo in attribute name
3. Message has value but no attributes

**Solutions**:
```python
# Use introspection to check available attributes
info = bundle.introspect_message("button")
# Check AST or validate resource to see defined attributes

# Verify attribute exists in FTL source:
# button = Click here
#     .tooltip = Click to submit
#     .aria-label = Submit button

result, errors = bundle.format_pattern("button", attribute="tooltip")
if errors:
    # Attribute doesn't exist, fall back to message value
    result, errors = bundle.format_pattern("button")
```

---

### Parse Errors (Junk Entries)

**Symptom**: `validate_resource()` returns `is_valid = False`, Junk entries in errors list

**Causes**:
1. Malformed FTL syntax
2. Unclosed braces in placeables
3. Invalid select expression
4. Missing variant key

**Solutions**:
```python
# Validate before adding to bundle
result = bundle.validate_resource(ftl_source)
if not result.is_valid:
    print(f"Found {result.error_count} syntax errors:")
    for error in result.errors:
        location = f"line {error.line}" if error.line else "unknown"
        print(f"  {location}: {error.message[:100]}")
    # Fix syntax errors in FTL source before deployment

# Common syntax errors:
# WRONG: msg = { $var     # Unclosed brace
# WRONG: msg = { $count ->  # Missing variants
# WRONG: msg = {$var}     # Missing space after brace

# CORRECT:
# msg = { $var }
# msg = { $count ->
#     [one] one item
#    *[other] { $count } items
# }
```

---

### Function Not Found

**Symptom**: `FluentResolutionError` with "Unknown function" in errors list

**Causes**:
1. Function not registered (built-in or custom)
2. Typo in function name (case-sensitive)
3. Function registered after resource loaded

**Solutions**:
```python
# Check if function is registered
from ftllexbuffer import FUNCTION_REGISTRY

if FUNCTION_REGISTRY.has_function("CUSTOM"):
    print("CUSTOM function registered")
else:
    # Register custom function
    def CUSTOM(value, **options):
        return str(value).upper()

    bundle.add_function("CUSTOM", CUSTOM)

# Verify function available BEFORE adding resource
bundle.add_resource('msg = { CUSTOM($text) }')
```

---

### Type Errors with mypy

**Symptom**: mypy reports type errors when using FluentBundle

**Causes**:
1. Not using type annotations correctly
2. Missing type stubs for dependencies
3. Incorrect return type assumptions

**Solutions**:
```python
# Use proper type annotations
from ftllexbuffer import FluentBundle, MessageId

def format_message(bundle: FluentBundle, msg_id: MessageId) -> str:
    # mypy knows result is str, errors is list[FluentError]
    result, errors = bundle.format_pattern(msg_id)
    return result

# Handle errors list with proper typing
from ftllexbuffer import FluentError

result, errors = bundle.format_pattern("msg")
for error in errors:  # mypy knows error is FluentError
    print(error)
```

---

### Thread Safety Issues

**Symptom**: Intermittent errors, race conditions, corrupted bundle state in multi-threaded apps

**Causes**:
1. Calling `add_resource()` from multiple threads
2. Calling `add_function()` concurrently
3. Mutating bundle during request handling

**Solutions**:
```python
# CORRECT: Single-threaded initialization
bundle = FluentBundle("en")
bundle.add_resource(ftl_source)  # Load once at startup
bundle.add_function("CUSTOM", func)

# Then safe for concurrent reads
# Multiple threads can call format_pattern() simultaneously

# WRONG: Dynamic loading in request handlers
def handle_request():
    bundle.add_resource(ftl)  # NOT thread-safe!

# If dynamic loading needed, use thread-local bundles
import threading

_thread_local = threading.local()

def get_bundle():
    if not hasattr(_thread_local, 'bundle'):
        _thread_local.bundle = FluentBundle("en")
        _thread_local.bundle.add_resource(ftl_source)
    return _thread_local.bundle

# See examples/thread_safety.py for complete patterns
```

---

## Advanced Usage

### Loading FTL from Files

**Pattern**:

```python
from pathlib import Path

def load_locale(locale_code: str, resource_name: str) -> FluentBundle:
    """Load FTL resource from locale directory.

    Directory structure:
        locale/
        ├── en/
        │   ├── main.ftl
        │   └── errors.ftl
        ├── lv/
        │   ├── main.ftl
        │   └── errors.ftl
        └── pl/
            ├── main.ftl
            └── errors.ftl
    """
    bundle = FluentBundle(locale_code)

    ftl_path = Path(f"locale/{locale_code}/{resource_name}.ftl")

    if ftl_path.exists():
        bundle.add_resource(ftl_path.read_text(encoding="utf-8"))
    else:
        # Fallback to English
        fallback_path = Path(f"locale/en/{resource_name}.ftl")
        if fallback_path.exists():
            bundle.add_resource(fallback_path.read_text(encoding="utf-8"))

    return bundle

# Usage
bundle = load_locale("lv_LV", "main")
```

---

### FluentParserV1 - Direct Parser Access

For advanced use cases requiring direct parser control or custom AST processing pipelines.

**Import**:
```python
from ftllexbuffer import FluentParserV1
```

**Constructor**:
```python
parser = FluentParserV1()
```

**Method**: `parse(source: str) -> Resource`

Parse FTL source to AST without creating a FluentBundle.

**Parameters**:
- **`source`** (str): FTL source code

**Returns**:
- **`Resource`**: AST root node

**Raises**:
- **`FluentSyntaxError`**: On critical parse errors

**Use Cases**:
- Building custom FTL tooling (linters, formatters, analyzers)
- AST transformation pipelines
- Static analysis tools
- Code generation from FTL files

**Example - Parse and Analyze**:

```python
from ftllexbuffer import FluentParserV1, Message

parser = FluentParserV1()
resource = parser.parse("""
hello = Hello, World!
welcome = Welcome, { $name }!
""")

# Count messages
message_count = sum(1 for entry in resource.entries if isinstance(entry, Message))
print(f"Found {message_count} messages")
# Output: Found 2 messages
```

**Example - Custom Linter**:

```python
from ftllexbuffer import FluentParserV1, ASTVisitor, VariableReference

class VariableCollector(ASTVisitor):
    def __init__(self):
        self.variables = set()

    def visit_VariableReference(self, node):
        self.variables.add(node.id.name)
        return super().visit_VariableReference(node)

parser = FluentParserV1()
resource = parser.parse(ftl_source)

collector = VariableCollector()
collector.visit(resource)

print(f"Variables used: {collector.variables}")
```

**Note**: Most applications should use `parse_ftl()` convenience function instead of FluentParserV1 directly. The parser class is primarily for tooling and advanced use cases.

**See Also**:
- [parse_ftl()](#parse_ftl) - Convenience function wrapper
- [ASTVisitor](#astvisitor) - AST traversal pattern
- [AST Node Types](#ast-node-types) - Complete AST reference

---

## Common Workflows

### CI/CD Pipeline: Validate All FTL Files

Validate FTL syntax in your CI pipeline to catch errors before deployment:

```python
#!/usr/bin/env python3
"""Validate all FTL files in CI/CD pipeline."""
import sys
from pathlib import Path
from ftllexbuffer import FluentBundle

def validate_ftl_directory(locale_dir: Path) -> bool:
    """Validate all .ftl files in directory.

    Returns:
        True if all files valid, False if errors found
    """
    bundle = FluentBundle("en", use_isolating=False)  # Locale doesn't matter for syntax validation
    errors_found = False

    for ftl_file in locale_dir.rglob("*.ftl"):
        source = ftl_file.read_text(encoding="utf-8")
        result = bundle.validate_resource(source)

        if not result.is_valid:
            print(f"[FAIL] {ftl_file}: {result.error_count} error(s)")
            for error in result.errors:
                location = f"line {error.line}" if error.line else "unknown"
                print(f"  {location}: {error.message[:80]}")
            errors_found = True
        else:
            print(f"[OK] {ftl_file}")

    return not errors_found

if __name__ == "__main__":
    locale_dir = Path("locale")
    success = validate_ftl_directory(locale_dir)
    sys.exit(0 if success else 1)
```

**GitHub Actions Integration**:

```yaml
# .github/workflows/validate-ftl.yml
name: Validate FTL Files
on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - run: pip install ftllexbuffer
      - run: python scripts/validate_ftl.py
```

---

### Flask Integration

Integrate FTLLexBuffer with Flask for web applications:

```python
from flask import Flask, g, request
from ftllexbuffer import FluentLocalization, PathResourceLoader

app = Flask(__name__)

# Initialize at startup
def get_l10n() -> FluentLocalization:
    """Get localization instance (cached per request)."""
    if 'l10n' not in g:
        loader = PathResourceLoader('locales/{locale}')
        g.l10n = FluentLocalization(
            ['en', 'es', 'fr'],
            ['ui.ftl', 'errors.ftl'],
            loader
        )
    return g.l10n

def _(message_id: str, **args) -> str:
    """Translation helper function."""
    l10n = get_l10n()
    result, errors = l10n.format_value(message_id, args)

    # Log errors in development
    if errors and app.debug:
        app.logger.warning(f"Translation error for '{message_id}': {errors}")

    return result

@app.route('/')
def index():
    return _(request.accept_languages.best_match(['en', 'es', 'fr']) or 'welcome')

if __name__ == '__main__':
    app.run()
```

---

### Django Integration

Use FTLLexBuffer in Django views:

```python
# myapp/l10n.py
from django.conf import settings
from ftllexbuffer import FluentLocalization, PathResourceLoader

_l10n_cache = {}

def get_localization(language_code: str) -> FluentLocalization:
    """Get or create localization instance for language."""
    if language_code not in _l10n_cache:
        loader = PathResourceLoader(settings.LOCALE_PATHS[0] / '{locale}')
        _l10n_cache[language_code] = FluentLocalization(
            [language_code, settings.LANGUAGE_CODE],  # Fallback to default
            ['django.ftl'],
            loader
        )
    return _l10n_cache[language_code]

def ftl(request, message_id: str, **args) -> str:
    """Format FTL message for current request language."""
    l10n = get_localization(request.LANGUAGE_CODE)
    result, errors = l10n.format_value(message_id, args)
    return result

# myapp/views.py
from django.shortcuts import render
from .l10n import ftl

def index(request):
    context = {
        'welcome': ftl(request, 'welcome', name=request.user.username)
    }
    return render(request, 'index.html', context)
```

---

### Type-Safe Message Wrappers

Generate type-safe wrappers using introspection:

```python
"""Generate type-safe Python wrappers for FTL messages."""
from ftllexbuffer import parse_ftl, introspect_message
from pathlib import Path

def generate_message_class(ftl_file: Path) -> str:
    """Generate Python class with typed methods for each message."""
    source = ftl_file.read_text(encoding="utf-8")
    resource = parse_ftl(source)

    lines = ['"""Auto-generated message wrappers."""', '', 'from ftllexbuffer import FluentBundle', '']
    lines.append('class Messages:')
    lines.append('    def __init__(self, bundle: FluentBundle):')
    lines.append('        self._bundle = bundle')
    lines.append('')

    for entry in resource.entries:
        if not hasattr(entry, 'id'):
            continue

        info = introspect_message(entry)
        vars_list = ', '.join(f'{var}: str' for var in sorted(info.get_variable_names()))

        lines.append(f'    def {entry.id.name.replace("-", "_")}(self, {vars_list}) -> str:')
        lines.append(f'        """Format {entry.id.name} message."""')
        lines.append(f'        result, _ = self._bundle.format_pattern("{entry.id.name}", {{')

        for var in sorted(info.get_variable_names()):
            lines.append(f'            "{var}": {var},')

        lines.append('        })')
        lines.append('        return result')
        lines.append('')

    return '\n'.join(lines)

# Usage:
code = generate_message_class(Path('locale/en/messages.ftl'))
Path('myapp/messages.py').write_text(code)
```

---

### Building Translation Tools

Create a tool to find unused messages:

```python
"""Find unused FTL messages in codebase."""
import ast
from pathlib import Path
from ftllexbuffer import parse_ftl

def extract_message_ids_from_ftl(ftl_file: Path) -> set[str]:
    """Extract all message IDs from FTL file."""
    source = ftl_file.read_text(encoding="utf-8")
    resource = parse_ftl(source)
    return {entry.id.name for entry in resource.entries if hasattr(entry, 'id')}

def extract_message_calls_from_python(py_file: Path) -> set[str]:
    """Extract all format_pattern() calls from Python file."""
    source = py_file.read_text(encoding="utf-8")
    tree = ast.parse(source)

    calls = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == 'format_pattern' and node.args:
                    if isinstance(node.args[0], ast.Constant):
                        calls.add(node.args[0].value)
    return calls

def find_unused_messages(locale_dir: Path, source_dir: Path) -> set[str]:
    """Find messages defined but never used."""
    # Collect all message IDs
    defined_messages = set()
    for ftl_file in locale_dir.rglob("*.ftl"):
        defined_messages.update(extract_message_ids_from_ftl(ftl_file))

    # Collect all used message IDs
    used_messages = set()
    for py_file in source_dir.rglob("*.py"):
        used_messages.update(extract_message_calls_from_python(py_file))

    return defined_messages - used_messages

# Usage:
unused = find_unused_messages(Path("locale/en"), Path("src"))
print(f"Unused messages: {unused}")
```

---

## Migrating from Mozilla python-fluent

FTLLexBuffer is **API-compatible** with Mozilla's `python-fluent` reference implementation, making migration straightforward.

### Import Changes

```python
# Mozilla python-fluent
from fluent.runtime import FluentBundle, FluentLocalization, FluentResource
from fluent.runtime.types import FluentError

# FTLLexBuffer
from ftllexbuffer import FluentBundle, FluentLocalization, Resource
from ftllexbuffer import FluentError
```

### API Compatibility Matrix

| Feature | python-fluent | FTLLexBuffer | Notes |
|---------|---------------|--------------|-------|
| **FluentBundle** | ✓ | ✓ | Identical interface |
| `bundle.format_pattern()` | ✓ | ✓ | Same signature and return type |
| `bundle.add_resource()` | ✓ | ✓ | Accepts FTL source string |
| **FluentLocalization** | ✓ | ✓ | Same constructor and methods |
| `l10n.format_value()` | ✓ | ✓ | Identical behavior |
| Error tuple returns | ✓ | ✓ | Both return `(value, list[FluentError])` |
| **Additional in FTLLexBuffer** | — | ✓ | See below |
| `bundle.validate_resource()` | ✗ | ✓ | FTL linting/validation |
| `bundle.format_value()` | ✗ | ✓ | Simpler API (alias for format_pattern) |
| `bundle.introspect_message()` | ✗ | ✓ | Message metadata extraction |
| `bundle.get_message_variables()` | ✗ | ✓ | Variable name extraction |
| Top-level imports | ✗ | ✓ | `from ftllexbuffer import Message, Term, etc.` |
| Type safety | Partial | **mypy --strict** | Full type coverage |

### Migration Example

**Before (python-fluent)**:
```python
from fluent.runtime import FluentBundle, FluentResource

ftl_string = """
hello = Hello, { $name }!
"""

bundle = FluentBundle(["en-US"])
resource = FluentResource(ftl_string)
bundle.add_resource(resource)

value, errors = bundle.format_pattern("hello", {"name": "World"})
```

**After (FTLLexBuffer)**:
```python
from ftllexbuffer import FluentBundle

ftl_string = """
hello = Hello, { $name }!
"""

bundle = FluentBundle("en-US")  # Single locale string, not list
bundle.add_resource(ftl_string)  # Direct string, no FluentResource wrapper

value, errors = bundle.format_pattern("hello", {"name": "World"})
```

### Key Differences

1. **Locale Parameter**: FTLLexBuffer takes single locale string, not list
   ```python
   # python-fluent
   bundle = FluentBundle(["en-US"])

   # FTLLexBuffer
   bundle = FluentBundle("en-US")
   ```

2. **Resource Loading**: FTLLexBuffer accepts FTL source directly
   ```python
   # python-fluent
   resource = FluentResource(ftl_string)
   bundle.add_resource(resource)

   # FTLLexBuffer
   bundle.add_resource(ftl_string)  # No wrapper needed
   ```

3. **Import Paths**: Different package structure
   ```python
   # python-fluent
   from fluent.runtime import FluentBundle
   from fluent.syntax import ast

   # FTLLexBuffer
   from ftllexbuffer import FluentBundle, Message, Term, Resource
   ```

### What Stays the Same

- Return types: `(str, list[FluentError])`
- Error handling: Never raises, always returns errors in list
- FluentLocalization fallback behavior
- FTL syntax and semantics
- Built-in functions: NUMBER, DATETIME

### Migration Checklist

- [ ] Update imports from `fluent.runtime` → `ftllexbuffer`
- [ ] Change `FluentBundle(["locale"])` → `FluentBundle("locale")`
- [ ] Remove `FluentResource` wrapper, pass FTL strings directly
- [ ] Update type annotations if using mypy
- [ ] Consider using new FTLLexBuffer features:
  - `validate_resource()` for CI/CD validation
  - `introspect_message()` for message metadata
  - `format_value()` for simpler API
- [ ] Test thoroughly (behavior should be identical)

---

## FluentLocalization

Multi-locale message formatting with automatic fallback chains.

**Thread Safety**: FluentLocalization instances have the same thread safety characteristics as FluentBundle - **NOT thread-safe** for writes (`add_resource()`), but safe for concurrent reads (`format_value()`, `has_message()`, `get_bundles()`) once resources are loaded.

**Recommended Pattern**: Load all locale resources during startup, then share the FluentLocalization instance across request handlers/threads for read-only formatting operations.

### Constructor

```python
FluentLocalization(
    locales: Iterable[LocaleCode],
    resource_ids: Iterable[ResourceId] | None = None,
    resource_loader: ResourceLoader | None = None,
    *,
    use_isolating: bool = True,
    enable_cache: bool = False,
    cache_size: int = 1000
)
```

**Parameters**:

- **`locales`** (Iterable[LocaleCode]): Locale codes in fallback priority order (first = preferred)
  - Example: `['lv', 'en']` tries Latvian first, falls back to English
  - At least one locale required
  - Type alias: `LocaleCode = str` (locale identifiers like "en", "lv_LV")

- **`resource_ids`** (Iterable[ResourceId], optional): FTL file identifiers to load automatically
  - Example: `['ui.ftl', 'errors.ftl']`
  - Requires `resource_loader` parameter
  - Type alias: `ResourceId = str` (resource identifiers like "main.ftl")

- **`resource_loader`** (ResourceLoader, optional): Loader for fetching FTL resources from disk/network
  - See [PathResourceLoader](#pathresourceloader) and [ResourceLoader Protocol](#resourceloader-protocol)
  - Required if `resource_ids` provided

- **`use_isolating`** (bool, default=True): Wrap interpolated values in Unicode bidi isolation marks

- **`enable_cache`** (bool, default=False): Enable format caching for all bundles (50x speedup)
  - Cache provides 50x performance improvement on repeated format calls
  - Applied to all locale bundles in the fallback chain
  - Automatically invalidated when resources change

- **`cache_size`** (int, default=1000): Maximum cache entries per bundle when caching enabled
  - Controls memory usage of format cache
  - Uses LRU eviction policy when limit reached

**Raises**:

- **`ValueError`**: If `locales` is empty (at least one locale required)
- **`ValueError`**: If `resource_ids` provided but `resource_loader` is None

**Example - Direct resource provision**:

```python
from ftllexbuffer import FluentLocalization

# Create localization with fallback chain: Latvian → English
l10n = FluentLocalization(['lv', 'en'])

# Add Latvian translations (incomplete)
l10n.add_resource('lv', """
welcome = Sveiki, { $name }!
cart = Grozs
""")

# Add English translations (complete)
l10n.add_resource('en', """
welcome = Hello, { $name }!
cart = Cart
payment-success = Payment successful!
""")

# Format messages with fallback
result, errors = l10n.format_value('welcome', {'name': 'Anna'})
# → ('Sveiki, Anna!', [])  # Found in Latvian

result, errors = l10n.format_value('payment-success')
# → ('Payment successful!', [])  # Falls back to English
```

**Example - Disk-based resources**:

```python
from ftllexbuffer import FluentLocalization, PathResourceLoader

# Create loader pointing to locale directory structure
loader = PathResourceLoader('locales/{locale}')

# Auto-load ui.ftl and errors.ftl for each locale
l10n = FluentLocalization(['lv', 'en'], ['ui.ftl', 'errors.ftl'], loader)

# Loads:
#   locales/lv/ui.ftl → Latvian bundle
#   locales/lv/errors.ftl → Latvian bundle
#   locales/en/ui.ftl → English bundle
#   locales/en/errors.ftl → English bundle

result, errors = l10n.format_value('welcome', {'name': 'Anna'})
```

**Example - Enable caching for performance**:

```python
from ftllexbuffer import FluentLocalization, PathResourceLoader

# Enable format caching for 50x speedup on repeated calls
loader = PathResourceLoader('locales/{locale}')
l10n = FluentLocalization(
    ['lv', 'en'],
    ['ui.ftl'],
    loader,
    enable_cache=True,    # Enable caching
    cache_size=1000       # Max 1000 entries per bundle
)

# First call - cache miss, formats message
result, _ = l10n.format_value('welcome', {'name': 'Anna'})

# Second call - cache hit, 50x faster
result, _ = l10n.format_value('welcome', {'name': 'Anna'})

# Cache applied to all bundles in fallback chain
# Automatically invalidated on add_resource() or add_function()
```

---

### Methods

#### add_resource

```python
add_resource(locale: LocaleCode, ftl_source: FTLSource) -> None
```

Add FTL resource to specific locale bundle (for dynamic loading).

**Parameters**:

- **`locale`** (LocaleCode): Locale code (must be in fallback chain)
- **`ftl_source`** (FTLSource): FTL source code

**Raises**:

- **`ValueError`**: If locale not in fallback chain

**Example**:

```python
l10n = FluentLocalization(['lv', 'en'])

# Add resources dynamically
l10n.add_resource('lv', 'hello = Sveiki!')
l10n.add_resource('en', 'hello = Hello!')
```

---

#### format_value

```python
format_value(message_id: MessageId, args: dict[str, object] | None = None) -> tuple[str, list[FluentError]]
```

Format message with automatic locale fallback.

**Parameters**:

- **`message_id`** (str): Message identifier
- **`args`** (dict, optional): Variable arguments for interpolation

**Returns**:

- **`tuple[str, list[FluentError]]`**: Tuple of (formatted_value, errors)
  - If message found: Returns formatted result from first bundle containing message
  - If not found in any locale: Returns `({message_id}, [FluentReferenceError])`
  - errors: List of FluentError exceptions (empty list if successful)

**Fallback Behavior**:

- Tries each locale in priority order
- Returns first successful match
- Never raises exceptions - errors collected in list

**Example**:

```python
l10n = FluentLocalization(['lv', 'en'])
l10n.add_resource('lv', 'home = Mājas')
l10n.add_resource('en', 'home = Home\nabout = About')

# Found in Latvian
result, errors = l10n.format_value('home')
# → ('Mājas', [])

# Not in Latvian, falls back to English
result, errors = l10n.format_value('about')
# → ('About', [])

# Not in any locale
result, errors = l10n.format_value('missing')
# → ('{missing}', [FluentReferenceError(...)])

# Proper error handling in production
import logging
logger = logging.getLogger(__name__)

result, errors = l10n.format_value('payment-error', {'reason': 'Invalid card'})
if errors:
    # Log translation errors
    for error in errors:
        logger.warning(f"Translation error for 'payment-error': {error}")
    # Optionally: report to error tracking service (Sentry, etc.)
    # sentry_sdk.capture_exception(errors[0])
print(result)  # Still displays fallback even with errors
```

**Best Practice**: Always check `errors` in production code and log/report translation issues. The `result` is always usable (fallback on error), but errors indicate missing translations or configuration problems.

---

#### has_message

```python
has_message(message_id: str) -> bool
```

Check if message exists in any locale.

**Parameters**:

- **`message_id`** (str): Message identifier

**Returns**:

- (bool): True if message exists in at least one locale

**Example**:

```python
if l10n.has_message('premium-feature'):
    result, _ = l10n.format_value('premium-feature')
    print(result)
else:
    print("Feature not available")
```

---

#### get_bundles

```python
get_bundles() -> Generator[FluentBundle]
```

Lazy generator yielding bundles in fallback order.

**Returns**:

- Generator yielding FluentBundle instances in locale priority order

**Important - Lazy Evaluation**:

Each call to `get_bundles()` creates a **new generator instance**. Generators are consumed after iteration, so if you need to iterate multiple times over the bundles, convert to a list:

```python
# BAD - Second iteration gets empty generator
for bundle in l10n.get_bundles():
    pass  # First iteration consumes generator
for bundle in l10n.get_bundles():
    pass  # This creates a NEW generator (works, but inefficient)

# GOOD - Convert to list for multiple iterations
bundles = list(l10n.get_bundles())
for bundle in bundles:
    # First pass
    pass
for bundle in bundles:
    # Second pass - reuses same list
    pass
```

**Performance Note**: Creating the generator is lightweight - it doesn't load resources until iteration. However, if you're iterating multiple times, converting to a list once is more efficient than calling `get_bundles()` repeatedly.

**Use Cases**:

- Advanced introspection
- Direct bundle access
- Checking which locale provides a message

**Example**:

```python
for bundle in l10n.get_bundles():
    print(f"Locale: {bundle.locale}")
    if bundle.has_message('welcome'):
        print(f"  Has 'welcome' message")
```

---

### Properties

#### locales

```python
locales: tuple[str, ...]
```

Immutable tuple of locale codes in fallback priority order.

**Example**:

```python
l10n = FluentLocalization(['lv', 'en', 'lt'])
print(l10n.locales)  # → ('lv', 'en', 'lt')
```

---

#### cache_enabled

```python
cache_enabled: bool
```

Whether format caching is enabled for all bundles (read-only).

**Example**:

```python
l10n = FluentLocalization(['lv', 'en'], enable_cache=True)
print(l10n.cache_enabled)  # True

l10n_no_cache = FluentLocalization(['lv', 'en'])
print(l10n_no_cache.cache_enabled)  # False
```

---

#### cache_size

```python
cache_size: int
```

Maximum cache size per bundle (read-only). Returns 0 if caching is disabled.

**Example**:

```python
l10n = FluentLocalization(['lv', 'en'], enable_cache=True, cache_size=500)
print(l10n.cache_size)  # 500 (per bundle, not total)

l10n_no_cache = FluentLocalization(['lv', 'en'])
print(l10n_no_cache.cache_size)  # 0
```

**Note**: Returns configured size **per bundle**, not total across all bundles. With 3 locales and cache_size=500, total cache capacity is 1500 entries.

---

## PathResourceLoader

File system resource loader using path templates.

### Constructor

```python
PathResourceLoader(base_path: str)
```

**Parameters**:

- **`base_path`** (str): Path template with `{locale}` placeholder
  - Example: `"locales/{locale}"` → `"locales/en"`, `"locales/lv"`

**Example**:

```python
from ftllexbuffer import PathResourceLoader

loader = PathResourceLoader("locales/{locale}")

# Load FTL file
ftl_source = loader.load("en", "main.ftl")
# Loads from: locales/en/main.ftl
```

---

### Methods

#### load

```python
load(locale: str, resource_id: str) -> str
```

Load FTL file from disk.

**Parameters**:

- **`locale`** (str): Locale code to substitute in path template
- **`resource_id`** (str): FTL filename (e.g., `'main.ftl'`)

**Returns**:

- (str): FTL source code (UTF-8 decoded)

**Raises**:

- **`FileNotFoundError`**: If file doesn't exist
- **`OSError`**: If file cannot be read

---

## ResourceLoader Protocol

Protocol for custom resource loaders (dependency inversion).

ResourceLoader is a **Protocol** (structural typing), not an ABC. This means you don't need to inherit from it - any class with a matching `load()` method signature automatically satisfies the protocol.

### Protocol Definition

```python
from typing import Protocol

class ResourceLoader(Protocol):
    """Protocol for loading FTL resources for specific locales.

    This is a Protocol (structural typing) rather than ABC to allow
    maximum flexibility for users implementing custom loaders.
    """

    def load(self, locale: str, resource_id: str) -> str:
        """Load FTL resource for given locale.

        Args:
            locale: Locale code (e.g., 'en', 'lv')
            resource_id: Resource identifier (e.g., 'main.ftl')

        Returns:
            FTL source code as string

        Raises:
            FileNotFoundError: If resource doesn't exist for this locale
            OSError: If file cannot be read
        """
```

**Key Points**:
- **Structural typing**: Any class with `load(locale: str, resource_id: str) -> str` satisfies the protocol
- **No inheritance required**: Don't need to inherit from ResourceLoader
- **Flexibility**: Implementations can load from disk, database, cache, HTTP, etc.

**Example - Custom in-memory loader**:

```python
class InMemoryLoader:
    """Load FTL from memory (database, cache, etc.)."""

    def __init__(self) -> None:
        self.resources: dict[tuple[str, str], str] = {}

    def add(self, locale: str, resource_id: str, ftl_source: str) -> None:
        self.resources[(locale, resource_id)] = ftl_source

    def load(self, locale: str, resource_id: str) -> str:
        key = (locale, resource_id)
        if key not in self.resources:
            raise FileNotFoundError(f"Resource not found: {locale}/{resource_id}")
        return self.resources[key]

# Usage
loader = InMemoryLoader()
loader.add('en', 'main.ftl', 'hello = Hello!')
loader.add('lv', 'main.ftl', 'hello = Sveiki!')

l10n = FluentLocalization(['lv', 'en'], ['main.ftl'], loader)
```

---

### Testing Patterns

**Pattern**: Using `ValidationResult` for CI/CD:

```python
import pytest
from pathlib import Path

def test_all_ftl_files_valid():
    """CI test: All FTL files must have valid syntax."""
    bundle = FluentBundle("en", use_isolating=False)

    for ftl_file in Path("locale").rglob("*.ftl"):
        result = bundle.validate_resource(ftl_file.read_text())

        assert result.is_valid, (
            f"{ftl_file} has {result.error_count} syntax errors:\n"
            + "\n".join(
                f"line {err.line}: {err.message[:80]}" if err.line
                else err.message[:80]
                for err in result.errors
            )
        )

def test_message_coverage():
    """Ensure all locales have required messages."""
    required_messages = {"welcome", "goodbye", "error-generic"}

    for locale in ["en", "lv", "pl"]:
        bundle = FluentBundle(locale)
        bundle.add_resource(Path(f"locale/{locale}/main.ftl").read_text())

        missing = required_messages - set(bundle.get_message_ids())
        assert not missing, f"{locale} missing: {missing}"
```

---

## AST Manipulation

### parse_ftl()

Parse FTL source text into an Abstract Syntax Tree (AST).

**Signature**:

```python
def parse_ftl(source: str) -> Resource
```

**Parameters**:
- **`source`** (str): FTL source text to parse

**Returns**: `Resource` - Root AST node containing all parsed entries

**Example**:

```python
from ftllexbuffer import parse_ftl

ftl_source = """
# Welcome messages
welcome = Hello, { $name }!
goodbye = Goodbye!
"""

resource = parse_ftl(ftl_source)

print(f"Parsed {len(resource.entries)} entries")
# Output: Parsed 2 entries

# Iterate over entries
for entry in resource.entries:
    if hasattr(entry, 'id'):
        print(f"Message: {entry.id.name}")
# Output:
# Message: welcome
# Message: goodbye
```

**Use Cases**:
- Building FTL linters and validators
- Creating FTL formatters and pretty-printers
- Analyzing FTL files for unused messages
- Extracting translatable strings

**Performance Note**: For parsing many files, consider using `FluentParserV1` directly to reuse a single parser instance. See [FluentParserV1 API](#fluentparserV1) for details.

---

### serialize_ftl()

Serialize an AST back into FTL source text.

**Signature**:

```python
def serialize_ftl(resource: Resource) -> str
```

**Parameters**:
- **`resource`** (Resource): AST root node to serialize

**Returns**: str - FTL source text

**Important - Comment Preservation Behavior**:
Comments ARE parsed into Comment AST nodes and ARE preserved during parse → serialize roundtrips when working with the AST directly. However, `FluentBundle.add_resource()` does NOT store Comment nodes at runtime (memory optimization).

**Comments ARE preserved in AST workflows**:
```python
# parse_ftl() → serialize_ftl() preserves comments
original = """
# This is a comment
welcome = Hello!
"""

resource = parse_ftl(original)
serialized = serialize_ftl(resource)
print(serialized)
# Output:
# # This is a comment
# welcome = Hello!
# (comment is preserved)
```

**Comments are NOT stored by FluentBundle**:
```python
# FluentBundle.add_resource() drops comments (runtime optimization)
bundle = FluentBundle("en")
bundle.add_resource("""
# This comment is not stored
welcome = Hello!
""")
# Comment is parsed but not retained in bundle's internal storage
```

**When to care**: Only use `parse_ftl()` / `serialize_ftl()` if you need to preserve comments (linters, formatters, refactoring tools). For runtime message formatting, `FluentBundle` is more efficient.

**Example**:

```python
from ftllexbuffer import parse_ftl, serialize_ftl

# Parse FTL
original = "welcome = Hello, { $name }!\n"
resource = parse_ftl(original)

# Serialize back
ftl_text = serialize_ftl(resource)
print(ftl_text)
# Output: welcome = Hello, { $name }!
```

**Roundtrip Property**:

```python
from ftllexbuffer import parse_ftl, serialize_ftl

ftl1 = "msg = Value\n"
resource = parse_ftl(ftl1)
ftl2 = serialize_ftl(resource)
resource2 = parse_ftl(ftl2)
ftl3 = serialize_ftl(resource2)

# Serialization converges (idempotent after first pass)
assert ftl2 == ftl3
```

**Use Cases**:
- Programmatically modifying FTL files
- Auto-formatting FTL source
- Migrating FTL syntax versions
- Code generation for FTL messages

---

### FluentParserV1

High-performance Fluent parser with reusable parser instances for batch processing.

**When to use FluentParserV1 directly:**
- Parsing hundreds/thousands of .ftl files (CI/CD pipelines, build tools)
- Performance-critical scenarios where parser instantiation overhead matters
- Batch validation of FTL resources
- Custom error handling requirements

**When to use parse_ftl() instead:**
- Single file parsing
- Simple scripts and prototypes
- When code simplicity matters more than performance

**Import:**
```python
# Top-level import
from ftllexbuffer import FluentParserV1

# Submodule import
from ftllexbuffer.syntax.parser import FluentParserV1
```

#### Constructor

```python
FluentParserV1()
```

Creates a new parser instance that can be reused across multiple parse operations.

**Parameters**: None

**Returns**: FluentParserV1 instance (reusable for multiple `.parse()` calls)

**Thread Safety**: Individual parser instances are **NOT thread-safe**. Create separate parser instances per thread if parsing concurrently. Parser instances are lightweight - creating one per thread has minimal overhead.

**Example:**
```python
from ftllexbuffer import FluentParserV1

# Create parser once
parser = FluentParserV1()

# Reuse for multiple files
for ftl_file in ftl_files:
    resource = parser.parse(ftl_file.read_text())
```

#### Methods

##### parse()

```python
def parse(self, source: str) -> Resource
```

Parse FTL source text into AST.

**Parameters:**
- **`source`** (str): FTL source code to parse

**Returns:** Resource - Root AST node containing all parsed entries

**Error Handling:**
- Parser uses error recovery - creates Junk nodes for unparseable content
- Never raises FluentSyntaxError for recoverable errors
- Returns valid Resource even if source contains syntax errors

**Example:**
```python
from ftllexbuffer import FluentParserV1

parser = FluentParserV1()

# Parse valid FTL
resource = parser.parse("hello = Hello, world!")
assert len(resource.entries) == 1

# Parse FTL with syntax errors (creates Junk nodes)
resource = parser.parse("invalid = { $")
assert len(resource.entries) == 1
assert isinstance(resource.entries[0], Junk)
```

#### Performance Benefits

**Single-file parsing (parse_ftl):**
```python
# Creates new parser instance each call
for i in range(1000):
    resource = parse_ftl(ftl_sources[i])  # ~1000 parser instantiations
```

**Batch parsing (FluentParserV1):**
```python
# Reuses single parser instance
parser = FluentParserV1()
for i in range(1000):
    resource = parser.parse(ftl_sources[i])  # 1 parser instantiation
```

**Benchmark results** (1000 files, 100 lines each):
- `parse_ftl()`: ~2.5 seconds
- `FluentParserV1().parse()`: ~1.8 seconds
- **Improvement**: ~28% faster for batch operations

#### Real-World Example: CI/CD Validation

```python
#!/usr/bin/env python3
"""Validate all FTL files in CI pipeline."""
import sys
from pathlib import Path
from ftllexbuffer import FluentParserV1
from ftllexbuffer import Junk

def validate_ftl_directory(locale_dir: Path) -> bool:
    """Validate all .ftl files, return True if all valid."""
    parser = FluentParserV1()  # Create once
    errors_found = False

    for ftl_file in locale_dir.rglob("*.ftl"):
        source = ftl_file.read_text(encoding="utf-8")
        resource = parser.parse(source)  # Reuse parser

        # Check for Junk entries (syntax errors)
        junk_entries = [e for e in resource.entries if isinstance(e, Junk)]
        if junk_entries:
            print(f"[FAIL] {ftl_file}: {len(junk_entries)} syntax error(s)")
            for junk in junk_entries:
                print(f"  {junk.content[:80]}")
            errors_found = True
        else:
            print(f"[OK] {ftl_file}")

    return not errors_found

if __name__ == "__main__":
    success = validate_ftl_directory(Path("locale"))
    sys.exit(0 if success else 1)
```

---

## AST Visitor Pattern

The AST visitor pattern allows you to traverse and transform FTL syntax trees programmatically.

**Import**:

```python
# Top-level imports
from ftllexbuffer import ASTVisitor, ASTTransformer
from ftllexbuffer import Message, Term, Pattern, Placeable, VariableReference, TextElement

# Submodule imports
from ftllexbuffer.syntax import ASTVisitor, ASTTransformer
from ftllexbuffer.syntax import Message, Term, Pattern, Placeable, VariableReference, TextElement
```

### ASTVisitor

Base class for read-only AST traversal.

**Signature**:

```python
class ASTVisitor:
    def visit(self, node: object) -> None:
        """Visit a node and dispatch to appropriate visitor method."""

    def visit_Message(self, node: Message) -> None:
        """Visit Message node."""

    def visit_Term(self, node: Term) -> None:
        """Visit Term node."""

    def visit_Pattern(self, node: Pattern) -> None:
        """Visit Pattern node."""

    def visit_VariableReference(self, node: VariableReference) -> None:
        """Visit VariableReference node."""

    def visit_FunctionReference(self, node: FunctionReference) -> None:
        """Visit FunctionReference node."""

    def visit_MessageReference(self, node: MessageReference) -> None:
        """Visit MessageReference node."""

    def visit_TermReference(self, node: TermReference) -> None:
        """Visit TermReference node."""

    # ... and other visit_* methods for each AST node type
```

**Example**:

```python
from ftllexbuffer import parse_ftl
from ftllexbuffer import ASTVisitor, VariableReference

class VariableCollector(ASTVisitor):
    """Collect all variable names used in FTL."""

    def __init__(self):
        self.variables = set()

    def visit_VariableReference(self, node: VariableReference):
        self.variables.add(node.id.name)
        return super().visit_VariableReference(node)

ftl_source = """
welcome = Hello, { $name }!
goodbye = Bye, { $name }!
"""

resource = parse_ftl(ftl_source)
collector = VariableCollector()
collector.visit(resource)

print(collector.variables)
# Output: {'name'}
```

**Use Cases**:
- Analyzing FTL files for linting
- Extracting metadata (variables, functions, references)
- Building IDE features (autocomplete, go-to-definition)
- Static analysis tools

**See Also**:
- [examples/ftl_linter.py](examples/ftl_linter.py) - Production linter using ASTVisitor
- [examples/ftl_transform.py](examples/ftl_transform.py) - AST transformations with ASTTransformer

---

### ASTTransformer

Base class for AST transformation (immutable transformations).

**Signature**:

```python
class ASTTransformer(ASTVisitor):
    def transform(self, resource: Resource) -> Resource:
        """Transform entire resource and return new resource."""

    def visit_Message(self, node: Message) -> Message | None:
        """Transform Message node. Return None to remove."""

    def visit_Term(self, node: Term) -> Term | None:
        """Transform Term node. Return None to remove."""

    def visit_Comment(self, node: Comment) -> Comment | None:
        """Transform Comment node. Return None to remove."""

    # ... and other visit_* methods that can return transformed nodes or None
```

**Example**:

```python
from ftllexbuffer import parse_ftl, serialize_ftl
from ftllexbuffer import ASTTransformer, Comment

class RemoveCommentsTransformer(ASTTransformer):
    """Remove all comments from FTL source."""

    def visit_Comment(self, node: Comment) -> None:
        return None  # Remove comments

ftl_source = """
# This is a comment
hello = Hello, World!
# Another comment
goodbye = Goodbye!
"""

resource = parse_ftl(ftl_source)
transformer = RemoveCommentsTransformer()
cleaned = transformer.transform(resource)

print(serialize_ftl(cleaned))
# Output:
# hello = Hello, World!
# goodbye = Goodbye!
```

**Example - Rename Variables**:

```python
from dataclasses import replace
from ftllexbuffer import parse_ftl, serialize_ftl
from ftllexbuffer import ASTTransformer, VariableReference, Identifier

class RenameVariablesTransformer(ASTTransformer):
    """Rename variables according to mapping."""

    def __init__(self, mapping: dict[str, str]):
        super().__init__()
        self.mapping = mapping

    def visit_VariableReference(self, node: VariableReference) -> VariableReference:
        if node.id.name in self.mapping:
            # Create new node with renamed variable (immutable)
            return replace(node, id=Identifier(name=self.mapping[node.id.name]))
        return node

ftl_source = """
greeting = Hello, { $userName }!
"""

resource = parse_ftl(ftl_source)
transformer = RenameVariablesTransformer({"userName": "user_name"})
renamed = transformer.transform(resource)

print(serialize_ftl(renamed))
# Output: greeting = Hello, { $user_name }!
```

**Use Cases**:
- Refactoring FTL files (rename variables, messages)
- Auto-formatting FTL source
- Removing obsolete elements
- Modernizing legacy FTL syntax

**See Also**: [examples/ftl_transform.py](examples/ftl_transform.py) for complete examples

---

## AST Node Types

Public AST node types available for inspection and manipulation.

**Import**:

All AST node types are available as **top-level imports**:

```python
# Top-level imports
from ftllexbuffer import (
    Resource, Message, Term, Comment, Junk, Attribute,
    Pattern, TextElement, Placeable,
    VariableReference, MessageReference, TermReference, FunctionReference,
    SelectExpression, Variant, NumberLiteral, StringLiteral,
    Identifier, CallArguments, NamedArgument, Span, Annotation,
    ASTVisitor, ASTTransformer,
)

# Submodule imports
from ftllexbuffer.syntax import (
    Resource, Message, Term, Attribute, Comment, Junk,
    Pattern, TextElement, Placeable,
)
from ftllexbuffer.syntax.ast import (
    VariableReference, MessageReference, TermReference, FunctionReference,
    SelectExpression, Variant, NumberLiteral, StringLiteral,
    Identifier, CallArguments, NamedArgument, Span, Annotation,
)
from ftllexbuffer.syntax.visitor import ASTVisitor, ASTTransformer
```

### Quick Reference Table

| Category | Node Type | Purpose | Key Fields |
|----------|-----------|---------|------------|
| **Entry Types** | `Resource` | Root AST node | `entries` (tuple) |
| | `Message` | Public translatable message | `id`, `value`, `attributes` |
| | `Term` | Private reusable message (-prefix) | `id`, `value`, `attributes` |
| | `Comment` | Comment line | `content` |
| | `Junk` | Parse error recovery | `content`, `annotations` |
| | `Attribute` | Message/term attribute (.prefix) | `id`, `value` |
| **Pattern** | `Pattern` | Text with placeables | `elements` (tuple) |
| | `TextElement` | Plain text | `value` |
| | `Placeable` | Expression in braces `{ }` | `expression` |
| **Expressions** | `VariableReference` | Variable `$name` | `id` |
| | `MessageReference` | Message reference | `id`, `attribute` |
| | `TermReference` | Term reference `-name` | `id`, `attribute` |
| | `FunctionReference` | Function call `FUNC()` | `id`, `arguments` |
| | `SelectExpression` | Selector `{ $x -> [a] ... }` | `selector`, `variants` |
| | `Variant` | Select variant `[key] value` | `key`, `value` |
| | `NumberLiteral` | Numeric literal `42` | `value` |
| | `StringLiteral` | String literal `"text"` | `value` |
| **Support** | `Identifier` | ID/name | `name` |
| | `CallArguments` | Function arguments | `positional`, `named` |
| | `NamedArgument` | Named arg `key: value` | `name`, `value` |
| | `Span` | Source location | `start`, `end` |
| | `Annotation` | Parser diagnostic | `code`, `message`, `arguments` |

**Use Cases**:
- **Linting**: Traverse AST to check for style violations
- **Transformation**: Refactor FTL files (rename, modernize)
- **Analysis**: Extract variables, validate references
- **IDE Features**: Autocomplete, go-to-definition, hover docs
- **Code Generation**: Generate type-safe wrappers from FTL

**Critical - Immutability Design**:

All AST nodes use **immutable tuples** (not lists) and are frozen dataclasses:

```python
@dataclass(frozen=True, slots=True)  # frozen=True prevents modification
class Message:
    attributes: tuple[Attribute, ...]  # Immutable tuple, not list
```

**Why tuples instead of lists?**
1. **Thread-safety**: AST can be shared across threads without locks
2. **Prevention of accidental mutations**: `msg.attributes.append()` fails at creation time
3. **Performance**: Tuples are faster and use less memory than lists
4. **Functional programming**: Transformations create new nodes via `dataclasses.replace()`

**Attempting to modify AST nodes raises FrozenInstanceError:**

```python
from ftllexbuffer import parse_ftl

resource = parse_ftl("msg = text")
msg = resource.entries[0]

# This will raise FrozenInstanceError
msg.id = Identifier(name="changed")  # ❌ Error: cannot assign to field 'id'

# This will raise AttributeError
msg.attributes.append(attr)  # ❌ Error: 'tuple' object has no attribute 'append'
```

**To modify AST, use ASTTransformer with dataclasses.replace():**

```python
from dataclasses import replace
from ftllexbuffer import ASTTransformer, Identifier

class RenameTransformer(ASTTransformer):
    def visit_Message(self, node: Message) -> Message:
        # Create new node with modified field (immutable transformation)
        return replace(node, id=Identifier(name="new-id"))
```

### Core Entry Types

**Resource** - Root AST node containing all entries

```python
@dataclass(frozen=True, slots=True)
class Resource:
    entries: tuple[Entry, ...]  # Immutable tuple of Message, Term, Comment, or Junk nodes
```

**Message** - Public translatable message

```python
@dataclass(frozen=True, slots=True)
class Message:
    id: Identifier        # Message ID (e.g., "welcome")
    value: Pattern | None # Message text pattern
    attributes: tuple[Attribute, ...]  # Immutable tuple of attributes (.tooltip, .aria-label, etc.)
```

**Term** - Private reusable message (prefixed with -)

```python
@dataclass(frozen=True, slots=True)
class Term:
    id: Identifier        # Term ID without - prefix (e.g., "brand-name")
    value: Pattern        # Term text pattern
    attributes: tuple[Attribute, ...]  # Immutable tuple of attributes
```

**Comment** - Comment line

```python
@dataclass(frozen=True, slots=True)
class Comment:
    content: str  # Comment text (without # prefix)
```

**Junk** - Parse error recovery node

```python
@dataclass(frozen=True, slots=True)
class Junk:
    content: str  # Source text that failed to parse
    annotations: tuple[Annotation, ...]  # Structured error information for tooling
    span: Span | None  # Source location of the error (optional)
```

Junk entries are created when the parser encounters syntax errors it cannot recover from.

**Understanding Junk Annotations**:

The `annotations` field provides structured diagnostic information for tooling. Each `Annotation` contains:
- `code`: Error code (e.g., `"expected-token"`, `"E0001"`)
- `message`: Human-readable error message
- `span`: Byte offset location of the error
- `arguments`: Additional context (optional)

**Example - Using Junk Annotations**:

```python
from ftllexbuffer import parse_ftl
from ftllexbuffer import Junk

ftl_source = """
valid = Hello
invalid = { $
another-valid = World
"""

resource = parse_ftl(ftl_source)

for entry in resource.entries:
    if isinstance(entry, Junk):
        print(f"Parse error in: {entry.content[:50]}...")

        # Iterate through annotations for detailed diagnostics
        for annotation in entry.annotations:
            print(f"  Error code: {annotation.code}")
            print(f"  Message: {annotation.message}")
            if annotation.span:
                print(f"  Location: bytes {annotation.span.start}-{annotation.span.end}")
```

**Use Cases for Annotations**:
- Building IDE error highlighting (show red squiggles at exact positions)
- Creating detailed lint reports with error codes
- Generating source maps for debugging
- Implementing custom error recovery strategies

The `span` field tracks byte offsets in the source for precise error reporting.

### Pattern Elements

**Pattern** - Sequence of text and placeables

```python
@dataclass(frozen=True, slots=True)
class Pattern:
    elements: tuple[PatternElement, ...]  # Immutable tuple of TextElement and Placeable
```

**TextElement** - Plain text

```python
@dataclass(frozen=True, slots=True)
class TextElement:
    value: str  # Text content
```

**Placeable** - Expression wrapped in braces { }

```python
@dataclass(frozen=True, slots=True)
class Placeable:
    expression: Expression  # Any expression type
```

### Expression Types

**VariableReference** - Variable placeholder ($var)

```python
@dataclass(frozen=True, slots=True)
class VariableReference:
    id: Identifier  # Variable name without $ prefix
```

**MessageReference** - Reference to another message

```python
@dataclass(frozen=True, slots=True)
class MessageReference:
    id: Identifier  # Message ID
    attribute: Identifier | None  # Optional attribute name
```

**TermReference** - Reference to a term (-term)

```python
@dataclass(frozen=True, slots=True)
class TermReference:
    id: Identifier  # Term ID without - prefix
    attribute: Identifier | None  # Optional attribute name
    arguments: CallArguments | None  # Optional parameterized arguments
```

**Note:** Terms can be parameterized per FTL spec. Example: `-brand(case: "nominative")` allows terms to vary by grammatical case, gender, or other parameters.

**Example:**
```python
from ftllexbuffer import parse_ftl

# Simple term reference
resource = parse_ftl("msg = { -brand }")
term_ref = resource.entries[0].value.elements[0].expression
print(term_ref.id.name)      # "brand"
print(term_ref.arguments)    # None

# Parameterized term reference
resource = parse_ftl("msg = { -brand(case: \"nominative\") }")
term_ref = resource.entries[0].value.elements[0].expression
print(term_ref.id.name)      # "brand"
print(term_ref.arguments.named[0].name.name)   # "case"
print(term_ref.arguments.named[0].value.value) # "nominative"

# Term reference with attribute
resource = parse_ftl("msg = { -brand.short }")
term_ref = resource.entries[0].value.elements[0].expression
print(term_ref.id.name)         # "brand"
print(term_ref.attribute.name)  # "short"
print(term_ref.arguments)       # None
```

**FunctionReference** - Function call

```python
@dataclass(frozen=True, slots=True)
class FunctionReference:
    id: Identifier  # Function name (e.g., "NUMBER", "DATETIME")
    arguments: CallArguments  # Positional and named arguments
```

**SelectExpression** - Conditional variants (plural forms, gender, etc.)

```python
@dataclass(frozen=True, slots=True)
class SelectExpression:
    selector: InlineExpression  # Expression to select on
    variants: tuple[Variant, ...]  # Immutable tuple of variants
```

**NumberLiteral** - Numeric value

```python
@dataclass(frozen=True, slots=True)
class NumberLiteral:
    value: int | float  # Parsed numeric value
    raw: str           # Original source text (for serialization)
```

**v0.9.0 Breaking Change**: `value` is now the parsed numeric value (int | float), not a string. Use `raw` for the original source text.

**Example:**
```python
from ftllexbuffer import parse_ftl

resource = parse_ftl("msg = { 42 }")
number_literal = resource.entries[0].value.elements[0].expression
print(number_literal.value)  # 42 (int)
print(number_literal.raw)    # "42" (str - original source)
print(type(number_literal.value))  # <class 'int'>

resource = parse_ftl("msg = { 3.14 }")
number_literal = resource.entries[0].value.elements[0].expression
print(number_literal.value)  # 3.14 (float)
print(number_literal.raw)    # "3.14" (str - original source)
print(type(number_literal.value))  # <class 'float'>
```

**StringLiteral** - Quoted string

```python
@dataclass(frozen=True, slots=True)
class StringLiteral:
    value: str  # String content (without quotes)
```

### Support Types

**Identifier** - Name identifier

```python
@dataclass(frozen=True, slots=True)
class Identifier:
    name: str  # Identifier name
```

**Attribute** - Message/term attribute

```python
@dataclass(frozen=True, slots=True)
class Attribute:
    id: Identifier  # Attribute name (e.g., "tooltip")
    value: Pattern  # Attribute value
```

**Variant** - Select expression variant

```python
@dataclass(frozen=True, slots=True)
class Variant:
    key: VariantKey  # Variant key (Identifier or NumberLiteral)
    value: Pattern   # Variant text
    default: bool = False  # True for default variant (marked with * in FTL)
    span: Span | None = None  # Source position tracking
```

**Note:** The `default` field identifies which variant is the fallback (marked with `*` in FTL syntax, e.g., `*[other]`). Only one variant per select expression should have `default=True`.

**Example:**
```python
from ftllexbuffer import parse_ftl

resource = parse_ftl("""
msg = { $count ->
    [one] one item
   *[other] { $count } items
}
""")

select_expr = resource.entries[0].value.elements[0].expression
for variant in select_expr.variants:
    print(f"Key: {variant.key.name}, Default: {variant.default}")
# Output:
# Key: one, Default: False
# Key: other, Default: True
```

**CallArguments** - Function arguments

```python
@dataclass(frozen=True, slots=True)
class CallArguments:
    positional: tuple[InlineExpression, ...]  # Immutable tuple of positional arguments
    named: tuple[NamedArgument, ...]  # Immutable tuple of named arguments
```

**Example:**
```python
from ftllexbuffer import parse_ftl

# Function with positional and named arguments
resource = parse_ftl("msg = { NUMBER($amount, minimumFractionDigits: 2) }")
message = resource.entries[0]
placeable = message.value.elements[0]
func_ref = placeable.expression

print(f"Function: {func_ref.id.name}")  # "NUMBER"
print(f"Positional args: {len(func_ref.arguments.positional)}")  # 1
print(f"Named args: {len(func_ref.arguments.named)}")  # 1

# Access positional argument
pos_arg = func_ref.arguments.positional[0]
print(f"Positional arg type: {type(pos_arg).__name__}")  # "VariableReference"
print(f"Variable name: {pos_arg.id.name}")  # "amount"

# Access named argument
named_arg = func_ref.arguments.named[0]
print(f"Named arg name: {named_arg.name.name}")  # "minimumFractionDigits"
print(f"Named arg value: {named_arg.value.value}")  # "2"

# Function with only named arguments
resource = parse_ftl('msg = { DATETIME($date, dateStyle: "short", timeStyle: "medium") }')
func_ref = resource.entries[0].value.elements[0].expression
print(f"Positional: {len(func_ref.arguments.positional)}")  # 1 ($date)
print(f"Named: {len(func_ref.arguments.named)}")  # 2 (dateStyle, timeStyle)

for named_arg in func_ref.arguments.named:
    print(f"  {named_arg.name.name} = {named_arg.value.value}")
# Output:
#   dateStyle = short
#   timeStyle = medium
```

**NamedArgument** - Named function argument

```python
@dataclass(frozen=True, slots=True)
class NamedArgument:
    name: Identifier  # Argument name
    value: InlineExpression  # Argument value
```

**Type Aliases**

**IMPORTANT**: Type aliases defined with Python 3.13's `type` keyword are for type annotations ONLY. They CANNOT be used with `isinstance()` at runtime.

These type aliases are defined in `ftllexbuffer.syntax.ast` and are primarily intended for type annotations rather than runtime isinstance checks.

**Import:**
```python
from ftllexbuffer import InlineExpression, VariantKey
```

**Definitions:**

```python
# InlineExpression - Expression that can appear inline (not select expressions)
type InlineExpression = (
    StringLiteral
    | NumberLiteral
    | FunctionReference
    | MessageReference
    | TermReference
    | VariableReference
    | Placeable
)

# VariantKey - Key for variant selection
type VariantKey = Identifier | NumberLiteral
```

**Runtime Type Checking:**

```python
# ❌ WRONG - TypeError: isinstance() arg 2 cannot be a parameterized generic
if isinstance(expr, InlineExpression):
    ...

# ✅ CORRECT - Use pattern matching for runtime checks
match expr:
    case StringLiteral() | NumberLiteral() | FunctionReference() | MessageReference() | TermReference() | VariableReference() | Placeable():
        # Handle inline expression
        ...
    case SelectExpression():
        # Handle select expression
        ...
```

**Why pattern matching?** Type aliases created with `type` keyword are NOT runtime classes. You cannot use them with `isinstance()`. Pattern matching provides exhaustive checking and better error messages.

**Reference**: See [PEP 695](https://peps.python.org/pep-0695/) for details on type aliases in Python 3.13+.

### Parser Support Types

These types are used for source position tracking and error diagnostics.

**Import**: Span and Annotation are available from both top-level and submodule imports:

```python
# Top-level import
from ftllexbuffer import Span, Annotation

# Submodule import
from ftllexbuffer.syntax import Span, Annotation
```

Use these types when building FTL tooling (linters, formatters, IDE plugins).

**Span** - Source position tracking (byte offsets)

Tracks byte offsets in source text for error reporting and tooling.

**Import:**
```python
from ftllexbuffer import Span
```

**Definition:**
```python
@dataclass(frozen=True, slots=True)
class Span:
    start: int  # Start byte offset (inclusive)
    end: int    # End byte offset (exclusive)
```

**Example:**
```python
from ftllexbuffer import Span

# Source: "hello = world"
# Message span: Span(start=0, end=13)
# Identifier "hello" span: Span(start=0, end=5)
span = Span(start=0, end=5)
```

**Annotation** - Parse error annotation with diagnostic information

Attached to Junk nodes to provide structured error information for tooling.

**Import:**
```python
from ftllexbuffer import Annotation
```

**Definition:**
```python
@dataclass(frozen=True, slots=True)
class Annotation:
    code: str                          # Error code (e.g., "E0001", "expected-token")
    message: str                       # Human-readable error message
    arguments: dict[str, str] | None   # Additional error context (optional)
    span: Span | None                  # Location of the error (optional)
```

**Example:**
```python
from ftllexbuffer import Annotation, Span

annotation = Annotation(
    code="expected-token",
    message="Expected '}' but found EOF",
    span=Span(start=10, end=10)
)
```

**Use Cases:**
- Building error-aware editors and IDEs
- Creating FTL linters with precise error locations
- Generating source maps for debugging
- Implementing code navigation features (go-to-definition)

**Cursor** - Immutable source position tracker (internal parser state)

```python
@dataclass(frozen=True, slots=True)
class Cursor:
    source: str     # Source text
    position: int   # Current byte position
    # Additional internal state...
```

**ParseError** - Parse error representation

```python
@dataclass(frozen=True, slots=True)
class ParseError:
    message: str    # Error message
    position: int   # Position where error occurred
```

**ParseResult[T]** - Type alias for parse results (Success or Failure)

```python
type ParseResult[T] = Result[T, ParseError]
```

**Example - Inspecting AST**:

```python
from ftllexbuffer import parse_ftl
from ftllexbuffer import Message, VariableReference, Placeable

ftl_source = """
welcome = Hello, { $name }!
"""

resource = parse_ftl(ftl_source)

# Inspect first entry
entry = resource.entries[0]
assert isinstance(entry, Message)
print(f"Message ID: {entry.id.name}")

# Inspect pattern elements
pattern = entry.value
assert pattern is not None
for element in pattern.elements:
    match element:
        case Placeable(expression=VariableReference(id=var_id)):
            print(f"Variable: ${var_id.name}")
        case _:
            pass
```

---

## AST Type Guards

FTLLexBuffer provides type guard methods for runtime type checking of AST nodes. These utilities use Python 3.13's `TypeIs` for type-safe narrowing, making them ideal for pattern matching and visitor implementations.

**v0.9.0**: Type guards are static methods on AST classes.

**Import AST Classes**:
```python
from ftllexbuffer import (
    Message,     # Message.guard()
    Term,        # Term.guard()
    Comment,     # Comment.guard()
    Junk,        # Junk.guard()
    Placeable,   # Placeable.guard()
    TextElement, # TextElement.guard()
    has_value,   # Helper function (not a class method)
)
```

**Why use type guards?** They provide both runtime checking AND type narrowing for mypy. After calling `Message.guard(entry)`, mypy knows `entry` is a `Message` type.

**v0.9.0 Breaking Change**: Type guards are now static methods on AST classes (e.g., `Message.guard()`) instead of standalone functions (e.g., `is_message()`).

### Understanding TypeIs Type Narrowing

Type guards in FTLLexBuffer use Python 3.13's `TypeIs` (PEP 727) to enable **type narrowing** - the ability for the type checker to understand that after a successful type guard check, the variable's type is refined to a more specific type.

**How TypeIs works**:

```python
from ftllexbuffer import parse_ftl, Message, Term

resource = parse_ftl("""
hello = Hello!
-brand = Acme Corp
""")

# Without type guard - entry has generic type
entry = resource.entries[0]
# Type: Message | Term | Comment | Junk (union type)
# entry.id.name  # Type error! Not all union members have 'id'

# With type guard - type is narrowed (v0.9.0: static method API)
if Message.guard(entry):
    # Inside this block, type checker knows entry is Message
    print(entry.id.name)  # No type error - Message has 'id'
    print(entry.value)    # No type error - Message has 'value'
elif Term.guard(entry):
    # Inside this block, type checker knows entry is Term
    print(entry.id.name)  # No type error - Term has 'id'
    print(entry.value)    # No type error - Term has 'value'
```

**Benefits**:
- **Type safety**: Catch errors at static analysis time
- **IDE support**: Autocomplete shows only available attributes after narrowing
- **Refactoring safety**: Type checker catches breaking changes
- **No runtime overhead**: TypeIs annotations are compile-time only

**Common pattern in visitors**:

```python
from ftllexbuffer import ASTVisitor, Message, Term

class MyVisitor(ASTVisitor):
    def visit_Resource(self, node):
        for entry in node.entries:
            # Type narrowing enables safe attribute access (v0.9.0: static methods)
            if Message.guard(entry):
                self.process_message(entry)  # entry: Message
            elif Term.guard(entry):
                self.process_term(entry)      # entry: Term

    def process_message(self, msg: Message) -> None:
        # Fully type-safe - mypy validates all attribute access
        print(f"Processing message: {msg.id.name}")

    def process_term(self, term: Term) -> None:
        print(f"Processing term: {term.id.name}")
```

### Available Type Guards

#### Message.guard()

```python
@staticmethod
def guard(entry: object) -> TypeIs[Message]:
```

Check if an AST entry is a `Message` node.

**Returns**: `True` if entry is a Message, `False` otherwise (with type narrowing)

**Example**:
```python
from ftllexbuffer import parse_ftl, Message

resource = parse_ftl("msg = value")
entry = resource.entries[0]

if Message.guard(entry):
    # Type-safe: mypy knows entry is Message
    print(f"Message ID: {entry.id.name}")  # No type error
```

#### Term.guard()

```python
@staticmethod
def guard(entry: object) -> TypeIs[Term]:
```

Check if an AST entry is a `Term` node (private message prefixed with `-`).

**Returns**: `True` if entry is a Term, `False` otherwise (with type narrowing)

**Example**:
```python
from ftllexbuffer import parse_ftl, Term

resource = parse_ftl("-brand = Firefox")
entry = resource.entries[0]

if Term.guard(entry):
    print(f"Term ID: {entry.id.name}")  # Type-safe
```

#### Comment.guard()

```python
@staticmethod
def guard(entry: object) -> TypeIs[Comment]:
```

Check if an AST entry is a `Comment` node.

**Returns**: `True` if entry is a Comment, `False` otherwise (with type narrowing)

#### Junk.guard()

```python
@staticmethod
def guard(entry: object) -> TypeIs[Junk]:
```

Check if an AST entry is a `Junk` node (parse error recovery).

**Returns**: `True` if entry is Junk, `False` otherwise (with type narrowing)

**Example**:
```python
from ftllexbuffer import parse_ftl, Junk

resource = parse_ftl("invalid = { $")  # Syntax error
entry = resource.entries[0]

if Junk.guard(entry):
    print(f"Parse error: {entry.content}")
    for annotation in entry.annotations:
        print(f"  Error: {annotation.message}")
```

#### Placeable.guard()

```python
@staticmethod
def guard(element: object) -> TypeIs[Placeable]:
```

Check if a pattern element is a `Placeable` node (expression in braces).

**Returns**: `True` if element is Placeable, `False` otherwise (with type narrowing)

**Example**:
```python
from ftllexbuffer import parse_ftl, Placeable

resource = parse_ftl("msg = Text { $var } more text")
message = resource.entries[0]

for element in message.value.elements:
    if Placeable.guard(element):
        print(f"Found placeable: {element.expression}")
```

#### TextElement.guard()

```python
@staticmethod
def guard(element: object) -> TypeIs[TextElement]:
```

Check if a pattern element is a `TextElement` node (plain text).

**Returns**: `True` if element is TextElement, `False` otherwise (with type narrowing)

#### has_value()

```python
def has_value(entry: object) -> TypeIs[Message | Term]:
```

Check if an entry has a value pattern (Message or Term).

**Returns**: `True` if entry is Message or Term, `False` otherwise (with type narrowing)

**Example**:
```python
from ftllexbuffer import parse_ftl
from ftllexbuffer import has_value

resource = parse_ftl("""
msg = value
# Comment
-term = term value
""")

for entry in resource.entries:
    if has_value(entry):
        # Type-safe: mypy knows entry is Message | Term
        print(f"Entry with value: {entry.id.name}")
```

### Usage Pattern: Visitor with Type Guards

Type guards are particularly useful in visitor patterns:

```python
from ftllexbuffer import parse_ftl, Message, Term, Junk

resource = parse_ftl(ftl_source)

# v0.9.0: Use static method API for type guards
for entry in resource.entries:
    if Message.guard(entry):
        print(f"Message: {entry.id.name}")
    elif Term.guard(entry):
        print(f"Term: {entry.id.name}")
    elif Junk.guard(entry):
        print(f"Parse error: {entry.content[:50]}...")
```

---

## Message Introspection

FTLLexBuffer provides comprehensive introspection APIs for analyzing FTL messages and extracting metadata about variables, functions, and references.

**Quick Navigation**:
- [`introspect_message()`](#introspect_message) - Full introspection (module-level function + bundle method)
- [`extract_variables()`](#extract_variables) - Extract variable names only (simplified API)
- [`MessageIntrospection`](#messageintrospection) - Introspection result dataclass
- [`VariableInfo`](#variableinfo), [`FunctionCallInfo`](#functioncallinfo), [`ReferenceInfo`](#referenceinfo) - Metadata types
- Bundle methods: [`bundle.get_message_variables()`](#get_message_variables), [`bundle.introspect_message()`](#introspect_message)

---

### introspect_message()

Get detailed information about a message's structure, including variables, function calls, and references.

**Important**: This function has two variants:
1. **Module-level function**: Takes Message AST node directly (this section)
2. **Bundle convenience method**: [`bundle.introspect_message(message_id)`](#introspect_message) - takes message ID string (see FluentBundle section)

**Signature (Module-Level Function)**:

```python
def introspect_message(message: Message) -> MessageIntrospection
```

**Parameters**:
- **`message`** (Message): Message AST node to introspect

**Returns**: `MessageIntrospection` - Structured information about the message

**Example (Module-Level)**:

```python
from ftllexbuffer import parse_ftl, introspect_message

ftl_source = """
welcome = Hello, { $name }! You have { NUMBER($count) } messages.
    .aria-label = Welcome message for { $name }
"""

resource = parse_ftl(ftl_source)
msg = resource.entries[0]  # Get Message AST node

info = introspect_message(msg)

print(f"Message ID: {info.message_id}")
# Output: Message ID: welcome

print(f"Variables: {info.get_variable_names()}")
# Output: Variables: frozenset({'name', 'count'})

print(f"Functions: {info.get_function_names()}")
# Output: Functions: frozenset({'NUMBER'})

print(f"Has selectors: {info.has_selectors}")
# Output: Has selectors: False
```

**Example (Bundle Convenience Method)**:

```python
from ftllexbuffer import FluentBundle

bundle = FluentBundle("en", use_isolating=False)
bundle.add_resource("""
welcome = Hello, { $name }! You have { NUMBER($count) } messages.
    .aria-label = Welcome message for { $name }
""")

# Use bundle's convenience method (takes message ID)
info = bundle.introspect_message("welcome")

print(f"Variables: {info.get_variable_names()}")
# Output: Variables: frozenset({'name', 'count'})
```

**Use Cases**:
- Validating that required variables are provided
- Building translation management tools
- Generating type-safe message wrappers
- Documentation generation

---

### extract_variables()

Extract all variable names from a message (simplified API).

**Signature**:

```python
def extract_variables(message: Message) -> frozenset[str]
```

**Parameters**:
- **`message`** (Message): Message AST node to analyze

**Returns**: `frozenset[str]` - Set of variable names (without $ prefix)

**Note**: This is a convenience function equivalent to `introspect_message(message).get_variable_names()`

**Example**:

```python
from ftllexbuffer import parse_ftl, extract_variables

ftl_source = """
user-greeting = Hello, { $firstName } { $lastName }!
    .title = Greeting for { $firstName }
"""

resource = parse_ftl(ftl_source)
msg = resource.entries[0]

variables = extract_variables(msg)

print(variables)
# Output: frozenset({'firstName', 'lastName'})

# Check if variable is required
if 'firstName' in variables:
    print("Message requires firstName variable")
```

**Convenience Alternative**:

For working with message IDs instead of AST nodes, use `bundle.get_message_variables()`:

```python
bundle = FluentBundle("en", use_isolating=False)
bundle.add_resource("""
user-greeting = Hello, { $firstName } { $lastName }!
""")

variables = bundle.get_message_variables("user-greeting")
print(variables)  # frozenset({'firstName', 'lastName'})
```

**Use Cases**:
- Validating translation files have required variables
- Generating function signatures for type-safe wrappers
- Building autocomplete for translation editors
- Static analysis of FTL files

---

## Introspection Data Types

### MessageIntrospection

Result of `introspect_message()` containing comprehensive message metadata.

**Attributes**:
- **`message_id`** (str): The message identifier
- **`variables`** (frozenset[VariableInfo]): All variable references in the message
- **`functions`** (frozenset[FunctionCallInfo]): All function calls in the message
- **`references`** (frozenset[ReferenceInfo]): All message/term references
- **`has_selectors`** (bool): Whether message uses select expressions

**Methods**:

- **`get_variable_names() -> frozenset[str]`**

  Get set of variable names.

  Returns frozen set of variable names without $ prefix.

  ```python
  info = bundle.introspect_message("welcome")
  vars = info.get_variable_names()  # frozenset({'name', 'count'})
  ```

- **`requires_variable(name: str) -> bool`**

  Check if message requires a specific variable.

  **Parameters**: `name` (str) - Variable name (without $ prefix)

  **Returns**: `True` if variable is used in the message

  ```python
  info = bundle.introspect_message("welcome")
  if info.requires_variable("name"):
      print("Message requires 'name' variable")
  ```

- **`get_function_names() -> frozenset[str]`**

  Get set of function names used in the message.

  Returns frozen set of function names (e.g., `{'NUMBER', 'DATETIME'}`).

  ```python
  info = bundle.introspect_message("price")
  funcs = info.get_function_names()  # frozenset({'NUMBER'})
  ```

**Example**:

```python
from ftllexbuffer import FluentBundle
from ftllexbuffer.introspection import introspect_message, extract_variables

bundle = FluentBundle("en", use_isolating=False)
bundle.add_resource("""
price = { NUMBER($amount, minimumFractionDigits: 2) } { $currency }
shipping = See { -brand-name } for details
""")

# Option 1: Use bundle convenience method 
info = bundle.introspect_message("price")

# Variables
for var in info.variables:
    print(f"Variable: ${var.name}")
# Output:
# Variable: $amount
# Variable: $currency

# Functions
for func in info.functions:
    print(f"Function: {func.name}()")
# Output: Function: NUMBER()

# References
info2 = bundle.introspect_message("shipping")
for ref in info2.references:
    print(f"Reference: {ref.kind} {ref.id}")
# Output: Reference: term brand-name

# Option 2: Direct module-level function (advanced - requires AST node)
message_node = bundle._messages["price"]
info3 = introspect_message(message_node)
```

---

### VariableInfo

Information about a variable reference in a message.

**Attributes**:
- **`name`** (str): Variable name (without $ prefix)
- **`context`** (str): Context where variable appears, one of:
  - `"pattern"` - In message pattern text (e.g., `Hello, { $name }!`)
  - `"selector"` - In select expression selector (e.g., `{ $count -> ...}`)
  - `"variant"` - In variant value (e.g., `[one] { $count } item`)
  - `"function_arg"` - As function argument (e.g., `NUMBER($amount)`)

**Example**:

```python
from ftllexbuffer import parse_ftl, introspect_message

ftl_source = """
welcome = Hello, { $name }!
    .aria-label = Greeting for { $name }
emails = { $count ->
    [one] You have { $count } email
   *[other] You have { $count } emails
}
"""

resource = parse_ftl(ftl_source)

# Introspect first message
msg1 = resource.entries[0]
info1 = introspect_message(msg1)

for var in info1.variables:
    print(f"${var.name} in context: {var.context}")
# Output:
# $name in context: pattern
# $name in context: pattern (from attribute)

# Introspect second message with selector
msg2 = resource.entries[1]
info2 = introspect_message(msg2)

for var in info2.variables:
    print(f"${var.name} in context: {var.context}")
# Output:
# $count in context: selector
# $count in context: variant
# $count in context: variant
```

---

### FunctionCallInfo

Information about a function call in a message.

**Attributes**:
- **`name`** (str): Name of the function (e.g., "NUMBER", "DATETIME")
- **`positional_args`** (tuple[str, ...]): Tuple of positional argument variable names
- **`named_args`** (frozenset[str]): Frozen set of named argument keys

**Example**:

```python
from ftllexbuffer import FluentBundle

bundle = FluentBundle("en", use_isolating=False)
bundle.add_resource("""
formatted = { NUMBER($value, minimumFractionDigits: 2, useGrouping: true) }
""")

info = bundle.introspect_message("formatted")

for func in info.functions:
    print(f"Function: {func.name}()")
    print(f"  Positional args: {func.positional_args}")
    print(f"  Named args: {func.named_args}")
# Output:
# Function: NUMBER()
#   Positional args: ('value',)
#   Named args: frozenset({'minimumFractionDigits', 'useGrouping'})
```

---

### ReferenceInfo

Information about a message or term reference.

**Attributes**:
- **`id`** (str): ID of referenced message/term
- **`kind`** (str): "message" or "term"
- **`attribute`** (str | None): Attribute name if accessing an attribute, None otherwise

**Example**:

```python
from ftllexbuffer import FluentBundle

bundle = FluentBundle("en", use_isolating=False)
bundle.add_resource("""
-brand-name = Acme Corp
about = Learn more about { -brand-name }
contact = { about } or call us
""")

info = bundle.introspect_message("about")
for ref in info.references:
    print(f"References {ref.kind}: {ref.id}")
# Output: References term: brand-name

info2 = bundle.introspect_message("contact")
for ref in info2.references:
    print(f"References {ref.kind}: {ref.id}")
# Output: References message: about
```

---

## Module Exports

### __all__

List of symbols exported from the `ftllexbuffer` module.

**Import Examples**:

```python
# Recommended: Explicit imports
from ftllexbuffer import FluentBundle, FluentLocalization, parse_ftl

# Discouraged: Wildcard import (includes all __all__ symbols)
from ftllexbuffer import *
```

**Exported Symbols**:

```python
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
    "FUNCTION_REGISTRY",
    "number_format",
    "datetime_format",

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

    # Module constants
    "__version__",
    "__fluent_spec_version__",
    "__spec_url__",
    "__recommended_encoding__",
]
```

**Note**: Prefer explicit imports over wildcard `import *` for better code clarity, editor autocomplete, and static analysis support.

---

## Module Constants

### __version__

Package version string (PEP 440 compliant).

**Value**: Auto-populated from package metadata via `importlib.metadata.version("ftllexbuffer")`

**Example**:

```python
import ftllexbuffer

print(f"FTLLexBuffer version: {ftllexbuffer.__version__}")
# Output: FTLLexBuffer version: 0.7.0
```

**Note**: In development mode (package not installed), `__version__` returns `"0.0.0+dev"`. Run `pip install -e .` to populate from `pyproject.toml`.

**Use Cases**:
- Version checking in dependency management
- Logging application startup information
- Debugging compatibility issues

---

### __fluent_spec_version__

FTL specification version implemented by this library.

**Value**: `"1.0"`

**Example**:

```python
import ftllexbuffer

print(f"Implements FTL {ftllexbuffer.__fluent_spec_version__}")
# Output: Implements FTL 1.0
```

---

### __recommended_encoding__

Recommended character encoding for FTL files.

**Value**: `"UTF-8"`

**Example**:

```python
import ftllexbuffer
from pathlib import Path

encoding = ftllexbuffer.__recommended_encoding__
ftl_content = Path("messages.ftl").read_text(encoding=encoding)
```

---

### __spec_url__

URL to the official FTL specification.

**Value**: `"https://github.com/projectfluent/fluent/blob/master/spec/fluent.ebnf"`

**Example**:

```python
import ftllexbuffer

print(f"Specification: {ftllexbuffer.__spec_url__}")
# Output: Specification: https://github.com/projectfluent/fluent/blob/master/spec/fluent.ebnf
```

---

## Type Annotations

FTLLexBuffer is fully type-annotated and passes `mypy --strict`.

**Import types**:

```python
from ftllexbuffer import FluentBundle, ValidationResult, FluentError
from ftllexbuffer import FluentBundle
```

**Type hints for custom code**:

```python
from typing import Any
from ftllexbuffer import FluentBundle

def format_message(bundle: FluentBundle, msg_id: str, **args: Any) -> str:
    """Type-safe wrapper for format_pattern."""
    return bundle.format_pattern(msg_id, args)
```

---

## Performance Notes

### Bundle Creation

- **Lightweight**: Bundle creation is fast (no CLDR data loading)
- **Recommendation**: Create once per locale, reuse across requests (e.g., store in app context)

### Resource Parsing

- **One-time cost**: `add_resource()` parses FTL text into AST (cached in memory)
- **Recommendation**: Load resources at startup, not per-request

### Message Formatting

- **Fast**: `format_pattern()` walks AST and interpolates variables (no re-parsing)
- **Caching available**: v0.6.0+ supports format caching with `enable_cache=True` (50x speedup)
- **Recommendation**: Enable caching for production web/mobile apps

### Format Caching (v0.6.0+)

**Overview:**
FTLLexBuffer supports optional LRU format caching for significant performance improvements. When enabled, formatted message results are cached by (message_id, args_hash), avoiding repeated AST walks and interpolation.

#### Performance Impact

**Cached vs Uncached:**
- **Uncached**: ~50μs per format call (AST walk + interpolation)
- **Cached hit**: ~1μs per format call (dictionary lookup)
- **Speedup**: **~50x faster** on repeated calls with same arguments

**When to Enable:**
- ✅ Web applications (repeated message formatting across requests)
- ✅ Desktop applications (UI labels formatted on every render)
- ✅ Mobile applications (memory-constrained but high format volume)
- ❌ CLI tools (one-time format calls, no benefit)
- ❌ Batch processing (each message formatted once with unique args)

#### Cache Size Recommendations

**Decision Matrix:**

| Application Type | Recommended cache_size | Memory Usage | Reasoning |
|-----------------|------------------------|--------------|-----------|
| **Web server** | 1000-5000 | ~200KB-1MB | High volume, repeated messages across requests |
| **Desktop app** | 500-1000 | ~100KB-200KB | Moderate volume, language switching |
| **Mobile app** | 100-500 | ~20KB-100KB | Memory-constrained, UI labels |
| **Embedded device** | 50-100 | ~10KB-20KB | Very memory-constrained |
| **CLI tool** | 0 (disabled) | 0 | One-time format calls, no benefit |

**Memory Cost Analysis:**
- **Per cache entry**: ~200 bytes (message_id + args_hash + formatted_result + metadata)
- **cache_size=100**: ~20 KB
- **cache_size=500**: ~100 KB
- **cache_size=1000**: ~200 KB
- **cache_size=5000**: ~1 MB

**Multi-locale Cost:**
Each bundle (locale) has its own cache. With 3 locales and `cache_size=1000`, total memory = 3 × 200KB = 600KB.

#### Cache Invalidation

**Automatic Invalidation:**
Cache is **fully cleared** on these operations:
- `add_resource()` - New or modified resource added
- `add_function()` - Custom function registered
- Bundle destruction

**NOT Invalidated:**
- ✅ Locale switching (each bundle has independent cache)
- ✅ Different arguments to same message (separate cache entries)
- ✅ `format_value()` vs `format_pattern()` (same cache key if message_id + args match)

**Cache Persistence:**
- Cache lifetime = bundle lifetime
- Use bundle pooling pattern to preserve cache across requests (see Framework Integration examples)

#### Configuration Examples

**Example 1: Web Application (High Performance)**
```python
from ftllexbuffer import FluentLocalization, PathResourceLoader

loader = PathResourceLoader('locales/{locale}')
l10n = FluentLocalization(
    ['lv', 'en', 'ru'],  # 3 locales
    ['ui.ftl', 'validation.ftl'],
    loader,
    enable_cache=True,  # Enable caching
    cache_size=5000      # 5000 entries × 3 locales = 15,000 total (3MB)
)

# Cache benefit: Repeated UI messages across thousands of requests
result, _ = l10n.format_value('common-button-save')  # Cached after first call
```

**Example 2: Mobile Application (Memory-Constrained)**
```python
l10n = FluentLocalization(
    ['en', 'es'],  # 2 locales
    ['app.ftl'],
    loader,
    enable_cache=True,
    cache_size=200  # 200 entries × 2 locales = 400 total (~80KB)
)

# Cache benefit: UI labels formatted on every screen render
```

**Example 3: CLI Tool (No Caching)**
```python
l10n = FluentLocalization(
    ['en'],
    ['cli.ftl'],
    loader,
    enable_cache=False  # Default - no caching overhead
)

# No cache benefit: Each message formatted once during tool execution
```

#### Cache Introspection (v0.6.0+)

**Monitor cache performance:**
```python
# FluentBundle API
bundle = FluentBundle('en', enable_cache=True, cache_size=1000)
stats = bundle.get_cache_stats()
print(f"Hits: {stats['hits']}, Misses: {stats['misses']}, Hit Rate: {stats['hit_rate']:.1%}")
print(f"Current Size: {stats['current_size']}/{stats['max_size']}")

# FluentLocalization API
l10n = FluentLocalization(['lv', 'en'], enable_cache=True)
all_stats = l10n.get_cache_stats()  # Returns dict[locale, stats]
for locale, stats in all_stats.items():
    print(f"{locale}: {stats['hit_rate']:.1%} hit rate")
```

**Interpretation:**
- **Hit rate < 50%**: Cache size may be too small or message/args too unique
- **Hit rate > 80%**: Cache is effective, consider keeping current size
- **Current size = max_size**: Cache is full, LRU eviction occurring
- **Hits = 0**: Caching disabled or no repeated calls

#### Best Practices

1. **Start with defaults**: `enable_cache=True, cache_size=1000` works for most apps
2. **Monitor in production**: Use `get_cache_stats()` to verify cache effectiveness
3. **Tune based on hit rate**: If hit rate < 50%, investigate message/args patterns
4. **Consider memory budget**: Mobile/embedded devices should use smaller cache_size
5. **Use ISO 8601 for dates**: Ensures consistent cache keys (parsing falls back to ISO format)
6. **Reuse bundles/localization**: Create once at startup, reuse across requests (framework integration patterns)

### Bidi Isolation Overhead

- **Minimal**: Adding FSI/PDI characters is O(1) per placeable
- **Disable if LTR-only**: Set `use_isolating=False` to skip character insertion

---

## Specification Compliance

FTLLexBuffer is **100% compliant** with the Fluent v1.0 specification.

**Implementation Scope:**
- ✅ All FTL v1.0 EBNF grammar rules
- ✅ CLDR plural rules for 30 world languages
- ✅ Unicode bidi isolation (FSI/PDI marks)
- ✅ Circular reference detection
- ✅ Error recovery with Junk nodes
- ✅ Source position tracking (Span/Annotation)

**Verification:**
- 2,131+ tests including spec conformance tests
- 95% code coverage with property-based testing
- Hypothesis-based fuzz testing for parser robustness

**Locale Support:**
- 30 built-in CLDR locales (top world languages)
- Graceful fallback for unsupported locales (simple one/other rules)
- Babel integration for NUMBER/DATETIME (600+ locales)

**Reference:** [Fluent Specification v1.0 EBNF](https://github.com/projectfluent/fluent/blob/master/spec/fluent.ebnf)

---

## Version History

See [CHANGELOG.md](CHANGELOG.md) for version-specific changes, migration guides, and upgrade notes.

---

## Further Reading

### FTLLexBuffer Documentation

- [README.md](README.md) - Getting started guide and quick reference
- [CHANGELOG.md](CHANGELOG.md) - Version history and migration guides
- [examples/](examples/) - Comprehensive usage examples
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines

### Fluent Localization System

- **[Fluent Specification v1.0 (EBNF Grammar)](https://github.com/projectfluent/fluent/blob/master/spec/fluent.ebnf)** - Official syntax specification implemented by FTLLexBuffer
- **[Fluent Syntax Guide](https://projectfluent.org/fluent/guide/)** - User-friendly tutorial for writing FTL files
- **[Project Fluent](https://projectfluent.org/)** - Official Fluent homepage with philosophy and ecosystem

### Unicode Standards

- **[CLDR Plural Rules](https://cldr.unicode.org/index/cldr-spec/plural-rules)** - Unicode plural categories used by FTLLexBuffer
- **[Unicode TR9 (Bidirectional Algorithm)](http://www.unicode.org/reports/tr9/)** - Bidi isolation explained (FSI/PDI marks)
- **[Unicode CLDR](https://cldr.unicode.org/)** - Common Locale Data Repository

### Localization Best Practices

- **[Mozilla L10n Style Guide](https://mozilla-l10n.github.io/localizer-documentation/l10n_resources/index.html)** - Localization guidelines
- **[OWASP i18n Security Cheat Sheet](https://cheatsheets.github.io/CheatSheetSeries/Internationalization_Cheat_Sheet.html)** - Security considerations
