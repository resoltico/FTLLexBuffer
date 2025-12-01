# FTLLexBuffer

[![PyPI](https://img.shields.io/pypi/v/ftllexbuffer.svg)](https://pypi.org/project/ftllexbuffer/)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Python 3.13+ implementation of the Fluent Localization System v1.0 specification.

> **Legal:** Licensed under MIT. Independent implementation of Apache 2.0-licensed FTL Specification. See [PATENTS.md](https://github.com/resoltico/ftllexbuffer/blob/main/PATENTS.md) for patent considerations and [NOTICE](https://github.com/resoltico/ftllexbuffer/blob/main/NOTICE) for attributions.

## Quick Links

**Getting Started**:
- [Quick Start](#quick-start) - Get started in 5 minutes
- [Quick Reference](https://github.com/resoltico/ftllexbuffer/blob/main/QUICK_REFERENCE.md) - One-page cheat sheet for common tasks
- [Examples](https://github.com/resoltico/ftllexbuffer/tree/main/examples) - Real-world usage patterns

**Documentation**:
- [API Reference](https://github.com/resoltico/ftllexbuffer/blob/main/API.md) - Complete API documentation
- [Type Hints Guide](https://github.com/resoltico/ftllexbuffer/blob/main/TYPE_HINTS.md) - Python 3.13+ type safety patterns
- [Terminology](https://github.com/resoltico/ftllexbuffer/blob/main/TERMINOLOGY.md) - Standard terminology reference
- [Migration Guide](https://github.com/resoltico/ftllexbuffer/blob/main/MIGRATION.md) - Migrating from fluent.runtime

**Development**:
- [Testing Guide](https://github.com/resoltico/ftllexbuffer/blob/main/TESTING.md) - Quality assurance and testing strategies
- [Contributing](https://github.com/resoltico/ftllexbuffer/blob/main/CONTRIBUTING.md) - Development guidelines

**Key Features**:
- Full Fluent v1.0 specification compliance
- 30 locale plural rules (CLDR-compliant)
- Zero runtime dependencies (except Babel for formatting)

---

## What is Fluent & Why Use It?

**Terminology:** "Fluent" is the localization system; ".ftl files" use the FTL file format; the language syntax is called "Fluent syntax".

### The Problem with Traditional i18n

Traditional localization often hands translators a single, opaque string with numbered placeholders. That works for trivial phrases, but quickly breaks when languages require different word order, grammatical inflection (case, gender), or multiple plural categories. The usual workarounds — forcing translators to guess placeholder positions, adding many near-duplicate strings, or entangling business logic with formatting — create brittle, hard-to-maintain code and unnatural translations.

FTLLexBuffer solves this by exposing the lexical building blocks of a message: named tokens (not anonymous %s slots), conditional/variant sections (plural/gender branches), and the ability to reorder tokens in the translation. Translators keep full control of how words and tokens combine in their language, and developers keep application logic simple and correct.

**gettext/PO files**, for example, require all translations to follow the source message structure, and translators can only fill in blanks, not restructure messages for natural phrasing:

```po
# English source defines the structure
msgid "You have %d file"
msgid_plural "You have %d files"

# Polish must follow same structure, can't restructure
msgstr[0] "Masz %d plik"
msgstr[1] "Masz %d pliki"
msgstr[2] "Masz %d plików"
msgstr[3] "Masz %d pliku"
```

### The Fluent Solution: Asymmetric Localization

**Each language uses its native grammar**, no compromises:

```ftl
# English (2 plural forms)
files = { $count ->
    [one] one file
   *[other] { $count } files
}

# Polish (4 plural forms)
files = { $count ->
    [one] { $count } plik
    [few] { $count } pliki
    [many] { $count } plików
   *[other] { $count } pliku
}

# Latvian (3 plural forms including zero!)
files = { $count ->
    [zero] { $count } failu
    [one] { $count } fails
   *[other] { $count } faili
}

# Arabic (6 plural forms including dual!)
files = { $count ->
    [zero] لا ملفات
    [one] ملف واحد
    [two] ملفان
    [few] { $count } ملفات
    [many] { $count } ملفًا
   *[other] { $count } ملف
}
```

**Additional Fluent Advantages**:

- **Gender agreement**: Different message variants per grammatical gender
- **Message references**: Reuse translations for consistency
- **Select expressions**: Arbitrary conditionals beyond plurals
- **Terms**: Shared vocabulary/glossary (brand names, product names)

### What FTLLexBuffer Does

**FTLLexBuffer is a Fluent parser + runtime** - it reads `.ftl` files and formats messages:

```python
from ftllexbuffer import FluentBundle

# Note: use_isolating=False for clean example output
# Production code should use default use_isolating=True
bundle = FluentBundle("lv_LV", use_isolating=False)
bundle.add_resource("""
files = { $count ->
    [zero] { $count } failu
    [one] { $count } fails
   *[other] { $count } faili
}
""")

result, errors = bundle.format_pattern("files", {"count": 0})
print(result)  # "0 failu"

result, errors = bundle.format_pattern("files", {"count": 1})
print(result)  # "1 fails"

result, errors = bundle.format_pattern("files", {"count": 21})
print(result)  # "21 fails"

result, errors = bundle.format_pattern("files", {"count": 5})
print(result)  # "5 faili"
```

**What it does NOT do** (pair with other tools):

- Translation management (use Pontoon/Crowdin/Weblate)
- Translator UI/CAT tools
- Machine translation
- Translation memory

**Think of it as**: It’s the translator who doesn’t just change words — it rearranges them so the sentence actually fits your language’s grammar.

---

## Terminology

Understanding FTLLexBuffer's terminology ensures clear communication in code and documentation.

**See [TERMINOLOGY.md](https://github.com/resoltico/ftllexbuffer/blob/main/TERMINOLOGY.md) for complete reference.**

Quick reference for common terms:

| Term | Meaning | Usage |
|------|---------|-------|
| **Fluent** | The localization system and specification | "Fluent supports asymmetric localization" |
| **FTL** / **.ftl files** | The file format (Fluent Translation List) | "Save translations in .ftl files" |
| **Fluent syntax** | The language syntax used in .ftl files | "Learn Fluent syntax at projectfluent.org" |
| **Message** | A translatable unit with an ID | `hello = Hello, World!` |
| **Message ID** | The identifier for a message | In prose: "message ID", in code: `message_id` |
| **Term** | A reusable translation (prefixed with `-`) | `-brand-name = Acme Corp` |
| **Pattern** | The text content of a message or term | `Hello, { $name }!` is a pattern |
| **Placeable** | An expression wrapped in `{ }` braces | `{ $name }` and `{ NUMBER($count) }` |
| **Resource** | **Context-dependent** - has THREE meanings: | See below |

### Resource - Three Meanings

**CRITICAL:** "Resource" has **three distinct meanings** in FTLLexBuffer. Always clarify context:

1. **FTL Resource (AST)**
   The parsed AST root node returned by `parse_ftl()`.
   **Type:** `Resource` class
   **Usage:** `resource = parse_ftl(ftl_source)` → `resource.entries` contains all messages/terms
   **Context:** AST manipulation, linting, transformation

2. **FTL source**
   The string content passed to `add_resource(source: str)`.
   **Type:** `str`
   **Usage:** `bundle.add_resource(ftl_source)` → parses the FTL source
   **Context:** Loading translations at runtime

3. **Resource loader**
   System for loading .ftl files from disk/network.
   **Types:** `PathResourceLoader`, `ResourceLoader` protocol
   **Usage:** `loader = PathResourceLoader("locales/{locale}")` → `loader.load("en", "main.ftl")`
   **Context:** Multi-locale applications with file-based translations

**Examples Clarifying Context:**

```python
# Context 1: FTL Resource (AST)
from ftllexbuffer import parse_ftl, Resource
resource: Resource = parse_ftl(ftl_source)  # AST root node
for entry in resource.entries:  # Traverse AST
    print(entry)

# Context 2: FTL source text
from ftllexbuffer import FluentBundle
bundle = FluentBundle("en")
bundle.add_resource(ftl_source)  # ftl_source is a string

# Context 3: Resource loader
from ftllexbuffer import PathResourceLoader, FluentLocalization
loader = PathResourceLoader("locales/{locale}")
l10n = FluentLocalization(['lv', 'en'], ['main.ftl'], loader)
```

**Best Practice:** When discussing "resource", specify which meaning:
- "the Resource AST node"
- "the FTL source"
- "the PathResourceLoader instance"

---

## Requirements

- Python 3.13 and later. The codebase leverages Python 3.13+ features including `type` keyword type aliases (PEP 695) and `TypeIs` type guards (PEP 742).
- Runtime dependencies:
  - `Babel>=2.17.0` (CLDR-compliant i18n formatting)

**Legal Note:** FTLLexBuffer is licensed under MIT. For patent considerations and licensing details, see [PATENTS.md](https://github.com/resoltico/ftllexbuffer/blob/main/PATENTS.md) and [NOTICE](https://github.com/resoltico/ftllexbuffer/blob/main/NOTICE).

## Installation

```bash
pip install ftllexbuffer
```

## Quick Start

```python
from ftllexbuffer import FluentBundle

# Create bundle for locale
# Note: Examples use use_isolating=False for clean output
# Production code should use default use_isolating=True
bundle = FluentBundle("en_US", use_isolating=False)

# Load translations
bundle.add_resource("""
greeting = Hello, { $name }!
emails = You have { $count ->
    [one] one email
   *[other] { $count } emails
}.
""")

# Format messages with proper error handling (PRODUCTION PATTERN)
result, errors = bundle.format_pattern("greeting", {"name": "Alice"})
if errors:
    for error in errors:
        # In production: use logger.warning() instead of print()
        print(f"Translation error: {error}")
print(result)  # "Hello, Alice!"

# For brevity in examples, we use underscore to ignore errors
# (Only do this in examples/tests - not production!)
result, _ = bundle.format_pattern("emails", {"count": 3})
print(result)  # "You have 3 emails."
```

**Alternative: Using `format_value()` for simpler API**

When you don't need attribute access, use `format_value()` instead:

```python
# format_value() - simpler when no attributes needed
result, errors = bundle.format_value("greeting", {"name": "Alice"})

# format_pattern() - use when accessing attributes
result, errors = bundle.format_pattern("button", attribute="tooltip")
```

---

**CRITICAL - Documentation Convention**: The example above uses `use_isolating=False` **for demonstration purposes only**. This creates cleaner terminal output in examples, but it is **UNSAFE for production**.

**Production Applications MUST Use Default Settings**:

```python
# ✓ CORRECT - Production code (RTL-safe, handles Arabic/Hebrew correctly)
bundle = FluentBundle("en_US")  # use_isolating=True (default)

# ❌ WRONG - Only for docs/tests (breaks RTL languages)
bundle = FluentBundle("en_US", use_isolating=False)
```

**Why This Matters**: By default (`use_isolating=True`), interpolated values are wrapped in invisible Unicode bidi isolation marks (FSI U+2068 and PDI U+2069). These marks prevent text corruption when mixing left-to-right text (English, Spanish) with right-to-left text (Arabic, Hebrew, Persian, Urdu). **Never disable bidi isolation in production** unless you are absolutely certain your application will never support RTL languages.

---

**Note on Error Handling**: All formatting methods return `(result, errors)` tuples. The `result` is always usable (fallback on error), and `errors` is a list of `FluentError` instances. **Critical**: `format_pattern()` **NEVER raises exceptions** - all errors are collected in the `errors` list. This is by design for graceful degradation in production. **In production code, always check the errors list** and log/report translation issues. Quick Start examples ignore errors for brevity.

---

## Thread Safety

**IMPORTANT**: `FluentBundle` is **NOT thread-safe** for write operations (`add_resource()`, `add_function()`). However, **concurrent reads ARE safe** (`format_pattern()`, `format_value()`, `has_message()`).

**Safe patterns for multi-threaded applications**:

1. **Recommended**: Load all resources during startup (single-threaded initialization)
   ```python
   # Startup phase (single-threaded)
   bundle = FluentBundle("en_US")
   bundle.add_resource(ftl_source)
   bundle.add_function("CUSTOM", my_function)

   # Runtime (multi-threaded) - safe for concurrent reads
   # Multiple threads can call format_pattern() simultaneously
   ```

2. **Alternative**: Use thread-local bundles if dynamic loading required
   ```python
   import threading

   _thread_local = threading.local()

   def get_bundle():
       if not hasattr(_thread_local, 'bundle'):
           _thread_local.bundle = FluentBundle("en_US")
           _thread_local.bundle.add_resource(ftl_source)
       return _thread_local.bundle
   ```

3. **See**: [examples/thread_safety.py](https://github.com/resoltico/ftllexbuffer/blob/main/examples/thread_safety.py) for complete patterns

---

**Next Steps**:
- See [API.md](https://github.com/resoltico/ftllexbuffer/blob/main/API.md) for complete API reference documentation
- Explore [examples/](https://github.com/resoltico/ftllexbuffer/tree/main/examples) for real-world usage patterns and advanced features
- Read [TESTING.md](https://github.com/resoltico/ftllexbuffer/blob/main/TESTING.md) for testing strategies and quality assurance

## Fluent Syntax

### Messages

```ftl
simple = Text value
variable = Hello, { $name }!
multiline = First line
    Second line
```

### Attributes

```ftl
button = Click here
    .tooltip = Click to submit
    .aria-label = Submit button
```

Access attributes:

```python
result, errors = bundle.format_pattern("button", attribute="tooltip")
print(result)  # "Click to submit"
```

### Select Expressions

```ftl
emails = { $count ->
    [one] one email
   *[other] { $count } emails
}

status = { $online ->
    [true] Online
   *[false] Offline
}
```

### Terms

```ftl
-brand = Firefox
about = About { -brand }
```

### Functions

```ftl
price = { NUMBER($amount, minimumFractionDigits: 2) }
date = { DATETIME($timestamp, dateStyle: "short") }
```

## Multi-Locale Fallback

For applications supporting multiple locales with fallback chains, use `FluentLocalization`:

```python
from ftllexbuffer import FluentLocalization

# Create localization with fallback: Latvian → English
l10n = FluentLocalization(['lv', 'en'])

# Add Latvian translations (incomplete)
l10n.add_resource('lv', """
welcome = Laipni lūdzam, { $name }!
cart = Grozs
""")

# Add English translations (complete)
l10n.add_resource('en', """
welcome = Welcome, { $name }!
cart = Cart
checkout = Checkout
""")

# Format with automatic fallback
result, errors = l10n.format_value('welcome', {'name': 'Anna'})
print(result)  # "Laipni lūdzam, Anna!" (from Latvian)

result, errors = l10n.format_value('checkout')
print(result)  # "Checkout" (falls back to English)
```

**Loading from disk**:

```python
from ftllexbuffer import FluentLocalization, PathResourceLoader

# Directory structure:
#   locales/lv/ui.ftl
#   locales/en/ui.ftl

loader = PathResourceLoader('locales/{locale}')
l10n = FluentLocalization(['lv', 'en'], ['ui.ftl'], loader)

result, errors = l10n.format_value('welcome')
```

See [API.md - FluentLocalization](https://github.com/resoltico/ftllexbuffer/blob/main/API.md#fluentlocalization) for complete documentation.

---

## Type Annotations

FTLLexBuffer is **fully type-safe** with `mypy --strict` compliance. Use provided type aliases for better IDE autocomplete and type checking:

```python
from ftllexbuffer import FluentBundle, MessageId, LocaleCode, FTLSource

def format_message(bundle: FluentBundle, msg_id: MessageId) -> str:
    """Format a message with error logging."""
    result, errors = bundle.format_value(msg_id)
    if errors:
        # errors is list[FluentError] - fully typed
        for error in errors:
            print(f"Translation error: {error}")
    return result

def create_localized_bundle(locale: LocaleCode, ftl_source: FTLSource) -> FluentBundle:
    """Create and populate a bundle for the given locale."""
    bundle = FluentBundle(locale)
    bundle.add_resource(ftl_source)
    return bundle
```

**Available type aliases**:
- `MessageId` - Message identifiers (type alias for `str`)
- `LocaleCode` - Locale codes like "en_US", "lv_LV" (type alias for `str`)
- `ResourceId` - Resource identifiers like "main.ftl" (type alias for `str`)
- `FTLSource` - FTL source strings (type alias for `str`)

**Note**: These are Python 3.13 `type` keyword aliases for documentation purposes. At runtime, they're just `str`, but they improve code readability and IDE support.

---

## Choosing the Right API

### Use FluentBundle when:

- ✅ Your app only supports one locale
- ✅ Locale is determined at startup and never changes
- ✅ You want maximum simplicity and direct control
- ✅ You're building a library that accepts locale as parameter

**Example**: Single-language application, microservice with fixed locale

### Use FluentLocalization when:

- ✅ Your app supports multiple locales
- ✅ Users can switch languages at runtime
- ✅ You need automatic fallback chains (e.g., `lv → en`)
- ✅ You load resources from disk with structured directory layout

**Example**: Web application, desktop app with language preferences, SaaS with multi-region support

### Can you mix them?

Yes! `FluentLocalization` uses `FluentBundle` internally. You can:
- Use `l10n.get_bundles()` to access individual bundles for advanced operations
- Use `FluentBundle` for unit testing specific locales
- Use `FluentLocalization` in production for fallback support

---

## API Reference

**Complete documentation**: See [API.md](https://github.com/resoltico/ftllexbuffer/blob/main/API.md) for comprehensive reference.

### FluentBundle

```python
FluentBundle(locale: str, *, use_isolating: bool = True)
```

Main API for Fluent message formatting.

**Parameters:**
- `locale` (str): Locale code (e.g., "en_US", "lv_LV", "de_DE", "pl_PL")

**Methods:**

- `add_resource(source: str) -> None`

  Parse and load FTL source into bundle.

  **Raises:** `FluentSyntaxError` on critical parse errors.

  **Note:** Non-critical syntax errors become Junk entries and are logged.

- `format_pattern(message_id: str, args: dict[str, Any] | None = None, *, attribute: str | None = None) -> tuple[str, list[FluentError]]`

  Format message to string with error reporting (Mozilla python-fluent aligned API).

  **Parameters:**
  - `message_id` (str): Message identifier
  - `args` (dict, optional): Variable arguments for interpolation
  - `attribute` (str, optional): Attribute name to access

  **Returns:** Tuple of `(formatted_string, errors)`
  - `formatted_string`: Best-effort formatted output (never empty)
  - `errors`: List of FluentError instances encountered during resolution

  **Note:** This method NEVER raises exceptions. All errors are collected and returned in the errors list.

  **Examples:**
  ```python
  result, errors = bundle.format_pattern("hello")
  assert result == "Hello, world!"
  assert errors == []

  result, errors = bundle.format_pattern("welcome", {"name": "Anna"})
  assert result == "Welcome, Anna!"

  result, errors = bundle.format_pattern("button", attribute="tooltip")
  assert result == "Click to submit"
  ```

- `format_value(message_id: str, args: dict[str, Any] | None = None) -> tuple[str, list[FluentError]]`

  Format message to string (alias for format_pattern without attribute access).

  Provides API consistency with FluentLocalization.format_value() for users who don't need attribute access.

  **Parameters:**
  - `message_id` (str): Message identifier
  - `args` (dict, optional): Variable arguments for interpolation

  **Returns:** Tuple of `(formatted_string, errors)`

  **Note:** This is an alias for `format_pattern(message_id, args, attribute=None)`.

- `has_message(message_id: str) -> bool`

  Check if message exists in bundle.

  **Parameters:**
  - `message_id` (str): Message identifier

  **Returns:** True if message exists

- `get_message_ids() -> list[str]`

  Get all message IDs in bundle.

  **Returns:** List of message identifiers

- `get_message_variables(message_id: str) -> frozenset[str]`

  Get all variables required by a message.

  **Parameters:**
  - `message_id` (str): Message identifier

  **Returns:** Frozen set of variable names (without $ prefix)

  **Example:**
  ```python
  bundle.add_resource("welcome = Hello, { $firstName } { $lastName }!")
  variables = bundle.get_message_variables("welcome")
  print(variables)  # frozenset({'firstName', 'lastName'})
  ```

- `introspect_message(message_id: str) -> MessageIntrospection`

  Get comprehensive metadata about a message.

  **Parameters:**
  - `message_id` (str): Message identifier

  **Returns:** `MessageIntrospection` with variables, functions, and references

  **Note:** This is a convenience method that looks up the message by ID. For working with AST nodes directly, use the module-level `introspect_message(message: Message)` function.

  **Example:**
  ```python
  bundle.add_resource("price = { NUMBER($amount, minimumFractionDigits: 2) }")
  info = bundle.introspect_message("price")
  print(info.get_variable_names())  # frozenset({'amount'})
  print(info.get_function_names())  # frozenset({'NUMBER'})
  ```

- `add_function(name: str, func: Callable) -> None`

  Register custom function.

  **Parameters:**
  - `name` (str): Function name (UPPERCASE by convention)
  - `func` (Callable): Function implementation

  **Example:**
  ```python
  def UPPER(value: str) -> str:
      return value.upper()

  bundle = FluentBundle("en_US")
  bundle.add_function("UPPER", UPPER)
  bundle.add_resource("msg = { UPPER($text) }")
  result, errors = bundle.format_pattern("msg", {"text": "hello"})
  print(result)  # "HELLO"
  ```

- `validate_resource(source: str) -> ValidationResult`

  Validate FTL resource without adding to bundle.

  Use this to check FTL files in CI/tooling before deployment.

  **Parameters:**
  - `source` (str): FTL source

  **Returns:** `ValidationResult` with parse errors and warnings

  **Example:**
  ```python
  result = bundle.validate_resource(ftl_source)
  if not result.is_valid:
      for error in result.errors:
          print(f"Error: {error.content}")
  ```

### FluentLocalization

Multi-locale message formatting with automatic fallback chains.

```python
FluentLocalization(
    locales: Iterable[str],
    resource_ids: Iterable[str] | None = None,
    resource_loader: ResourceLoader | None = None,
    *,
    use_isolating: bool = True
)
```

**Parameters:**
- `locales` (Iterable[str]): Locale codes in fallback priority order (e.g., `['lv', 'en']`)
- `resource_ids` (Iterable[str], optional): FTL file identifiers to load automatically
- `resource_loader` (ResourceLoader, optional): Loader for fetching FTL resources
- `use_isolating` (bool, default=True): Wrap interpolated values in Unicode bidi isolation marks

**Methods:**

- `add_resource(locale: str, ftl_source: str) -> None`

  Add FTL resource to specific locale bundle.

  **Parameters:**
  - `locale` (str): Locale code (must be in fallback chain)
  - `ftl_source` (str): FTL source

- `format_value(message_id: str, args: dict[str, object] | None = None) -> tuple[str, list[FluentError]]`

  Format message with automatic locale fallback.

  **Parameters:**
  - `message_id` (str): Message identifier
  - `args` (dict, optional): Variable arguments for interpolation

  **Returns:** Tuple of `(formatted_value, errors)`

  **Example:**
  ```python
  l10n = FluentLocalization(['lv', 'en'])
  l10n.add_resource('lv', 'hello = Sveiki!')
  l10n.add_resource('en', 'hello = Hello!\ngoodbye = Goodbye!')

  result, errors = l10n.format_value('hello')
  # result → "Sveiki!" (from Latvian)

  result, errors = l10n.format_value('goodbye')
  # result → "Goodbye!" (falls back to English)
  ```

- `has_message(message_id: str) -> bool`

  Check if message exists in any locale.

- `get_bundles() -> Generator[FluentBundle]`

  Lazy generator yielding bundles in fallback order.

**Properties:**
- `locales` (tuple[str, ...]): Immutable tuple of locale codes in fallback priority order

**See Also:** [API.md - FluentLocalization](https://github.com/resoltico/ftllexbuffer/blob/main/API.md#fluentlocalization) for complete documentation.

---

### ValidationResult

Returned by `validate_resource()`.

**Properties:**
- `is_valid` (bool): True if no errors found
- `error_count` (int): Number of parse errors (Junk entries)
- `warning_count` (int): Number of warnings
- `errors` (list[Junk]): List of parse error entries
- `warnings` (list[str]): List of warning messages

### Built-in Functions

**NUMBER(value, options)**

Formats numeric values with locale-aware thousand separators and decimal points.

**Locale Behavior:**
- Uses Babel (CLDR-compliant) for formatting
- Automatically adapts to bundle's locale (`en-US` → "1,234.5", `de-DE` → "1.234,5")
- Thread-safe (no global locale state)

**Options:**
- `minimumFractionDigits` (int): Minimum decimal places (default: 0)
- `maximumFractionDigits` (int): Maximum decimal places (default: 3)
- `useGrouping` (bool): Use thousand separators (default: true)

**Example:**
```ftl
price = { NUMBER($amount, minimumFractionDigits: 2) }
```

**DATETIME(value, options)**

Formats datetime values with locale-specific patterns.

**Locale Behavior:**
- Uses Babel (CLDR-compliant) for formatting
- Automatically adapts date/time formats to locale
- Supports datetime objects or ISO 8601 strings

**Options:**
- `dateStyle`: "short" | "medium" | "long" | "full" (default: "medium")
- `timeStyle`: "short" | "medium" | "long" | "full" | null (default: null)

**Example:**
```ftl
date = { DATETIME($timestamp, dateStyle: "short") }
```

**CURRENCY(value, options)**

Formats monetary amounts with locale-specific currency symbols, placement, and precision.

**Locale Behavior:**
- Uses Babel (CLDR-compliant) for formatting
- Automatically positions currency symbol (before/after) based on locale
- Uses currency-specific decimal places (JPY: 0, BHD: 3, EUR/USD: 2)
- Handles spacing and grouping per locale conventions

**Options:**
- `currency` (required): ISO 4217 currency code (EUR, USD, JPY, BHD, etc.)
- `currencyDisplay`: "symbol" | "code" | "name" (default: "symbol")
  - `"symbol"`: Use currency symbol (€, $, ¥)
  - `"code"`: Use currency code (EUR, USD, JPY)
  - `"name"`: Use full currency name (euros, dollars, yen)

**Examples:**
```ftl
# Basic usage
price = { CURRENCY($amount, currency: "EUR") }

# Variable currency code
price = { CURRENCY($amount, currency: $code) }

# Display as code instead of symbol
price-code = { CURRENCY($amount, currency: "USD", currencyDisplay: "code") }
```

**Locale-Specific Formatting:**
```python
bundle_us = FluentBundle("en_US")
bundle_us.add_resource('price = { CURRENCY($amount, currency: "EUR") }')
result, _ = bundle_us.format_pattern("price", {"amount": 123.45})
# Result: "€123.45" (symbol before, period decimal)

bundle_lv = FluentBundle("lv_LV")
bundle_lv.add_resource('price = { CURRENCY($amount, currency: "EUR") }')
result, _ = bundle_lv.format_pattern("price", {"amount": 123.45})
# Result: "123,45 €" (symbol after with space, comma decimal)

bundle_jp = FluentBundle("ja_JP")
bundle_jp.add_resource('price = { CURRENCY($amount, currency: "JPY") }')
result, _ = bundle_jp.format_pattern("price", {"amount": 12345})
# Result: "¥12,345" (no decimals - JPY uses 0 decimal places)
```

### Exception Classes

All exceptions inherit from `FluentError`.

**FluentError**

Base exception for all Fluent errors.

**Attributes:**
- `diagnostic` (Diagnostic | None): Structured diagnostic information

**FluentSyntaxError**

FTL syntax error during parsing. Parser continues after syntax errors (robustness principle). Errors become Junk entries in AST.

**FluentReferenceError**

Unknown message or term reference. Raised when resolving a message that references a non-existent ID.

**FluentResolutionError**

Runtime error during message resolution (e.g., type mismatch, invalid function arguments).

**FluentCyclicReferenceError**

Cyclic reference detected (message references itself directly or indirectly). Returns formatted error message instead of raising exception.

**Example:**
```python
from ftllexbuffer import FluentBundle, FluentSyntaxError

bundle = FluentBundle("en_US")

# Syntax errors create Junk entries
bundle.add_resource("invalid = incomplete")  # Parses successfully (valid syntax)

# Missing message returns fallback + error in list
result, errors = bundle.format_pattern("missing")
# result → "{missing}", errors → [FluentReferenceError(...)]

# Circular reference returns fallback + error in list (never raises)
bundle.add_resource("a = { b }\nb = { a }")
result, errors = bundle.format_pattern("a")
# result → "{a}", errors → [FluentCyclicReferenceError(...)]
```

## Locale Support

### Built-in CLDR Plural Rules (30 Languages)

FTLLexBuffer ships with CLDR-compliant plural rules for 30 languages:

| Language | Code | Plural Categories | Notes |
|----------|------|-------------------|-------|
| English | en | one, other | Integer 1 only |
| Mandarin Chinese | zh | other | No plurals |
| Hindi | hi | one, other | 0 or 1 → one |
| Spanish | es | one, other | Simple n=1 |
| French | fr | one, many, other | Millions rule |
| Arabic | ar | zero, one, two, few, many, other | 6 categories |
| Bengali | bn | one, other | 0 or 1 → one |
| Portuguese | pt | one, many, other | Millions rule |
| Russian | ru | one, few, many, other | Slavic rules |
| Japanese | ja | other | No plurals |
| German | de | one, other | Integer 1 only |
| Javanese | jv | other | No plurals |
| Korean | ko | other | No plurals |
| Vietnamese | vi | other | No plurals |
| Telugu | te | one, other | Simple n=1 |
| Turkish | tr | one, other | Simple n=1 |
| Tamil | ta | one, other | Simple n=1 |
| Marathi | mr | one, other | Simple n=1 |
| Urdu | ur | one, other | Simple n=1 |
| Italian | it | one, many, other | Millions rule |
| Thai | th | other | No plurals |
| Gujarati | gu | one, other | 0 or 1 → one |
| Polish | pl | one, few, many, other | Slavic rules |
| Ukrainian | uk | one, few, many, other | Slavic rules |
| Kannada | kn | one, other | 0 or 1 → one |
| Odia | or | one, other | Simple n=1 |
| Malayalam | ml | one, other | Simple n=1 |
| Burmese | my | other | No plurals |
| Punjabi | pa | one, other | 0 or 1 → one |
| Latvian | lv | zero, one, other | Special rules |

**Number/Date Formatting**: Uses Babel for CLDR-compliant NUMBER() and DATETIME() functions.

**Technical note:** Locale codes use language prefix extraction. `"en_US"` → `"en"`, `"ar-SA"` → `"ar"`.

### Fallback Behavior

**Unsupported locales** fall back to simple one/other rules (English-style). Most languages work correctly with this fallback.

## Implementation

### Parser

- Recursive descent parser
- Immutable cursor design
- Source position tracking (Span)
- Error recovery via Junk nodes
- Comment preservation (#, ##, ###)

### Resolver

- Message/term resolution with scope tracking
- Circular reference detection
- Variable interpolation
- Function dispatch (built-in and custom)

### Type System

- Strict type checking (mypy --strict) in production code[^1]
- PEP 742 TypeIs guards for type narrowing
- Frozen dataclasses with __slots__ (memory efficiency)

[^1]: Production code (src/) maintains zero-compromise quality with `mypy --strict`. Test code (tests/) uses relaxed settings for test DSL idioms while maintaining 9/10 quality standard.

### AST Nodes

**Entry types:**
- `Message` - Public message
- `Term` - Private message (-prefix)
- `Comment` - Comment line (#, ##, ###)
- `Junk` - Parse error recovery

**Expression types:**
- `TextElement` - Plain text
- `Placeable` - Brace expression { }
- `VariableReference` - $variable
- `MessageReference` - message-id
- `TermReference` - -term-id
- `FunctionReference` - FUNCTION()
- `SelectExpression` - Conditional variants
- `NumberLiteral` - Numeric value
- `StringLiteral` - Quoted string

## Error Handling

### Parse Errors

Invalid FTL syntax creates Junk nodes. Parser continues after errors.

```python
bundle = FluentBundle("en_US")
result = bundle.validate_resource("invalid = { $")
print(result.error_count)  # 1
print(result.errors[0].content)  # "invalid = { $"
```

### Missing Messages

Missing message references raise `FluentReferenceError`.

```python
from ftllexbuffer import FluentReferenceError

result, errors = bundle.format_pattern("missing")
# result → "{missing}"  # Readable fallback
# errors → [FluentReferenceError('Message not found: missing')]

if errors:
    for error in errors:
        print(f"Translation error: {error}")
```

### Circular References

Circular references return fallback + error in list (never raise exception).

```python
bundle.add_resource("a = { b }\nb = { a }")
result, errors = bundle.format_pattern("a")
# result → "{a}"  # Readable fallback
# errors → [FluentCyclicReferenceError('Circular reference detected: a -> b -> a')]
```

## Python Localization Solutions Comparison

Comprehensive comparison of localization libraries available in the Python ecosystem (versions verified as of November 2025):

| Feature | **FTLLexBuffer** (0.1.0) | fluent.runtime (0.4.0) | fluent-compiler (1.1) | gettext (stdlib) | Babel (2.17.0) | PySide6 (6.x LGPL) | python-i18n (0.3.9) |
|---------|----------|----------------|-------------------|-----------------|----------------|---------------------|-------------------|
| **Format** | .ftl (FTL v1.0) | .ftl (FTL v1.0) | .ftl (FTL v1.0) | .po/.mo (gettext) | .po/.mo (gettext) | .ts/.qm (Qt XML) | .yml/.json |
| **File Type** | Human-readable text | Human-readable text | Human-readable text | Text (.po) + Compiled binary (.mo) | Text (.po) + Compiled binary (.mo) | XML (.ts) + Compiled binary (.qm) | Human-readable text |
| **Compilation Required** | No (runtime interpreter) | No (runtime interpreter) | **Yes** (FTL → Python bytecode) | **Yes** (msgfmt .po → .mo) | **Yes** (pybabel compile .po → .mo) | **Yes** (lrelease .ts → .qm) | No (YAML/JSON loaded at runtime) |
| **Compilation Benefits** | N/A | N/A | Faster (PyPy optimized) | Faster lookups, validation, smaller size | Faster lookups, smaller size | Extremely fast lookups, binary format | N/A |
| **Grammar Approach** | **Asymmetric** (each locale restructures freely) | **Asymmetric** (each locale restructures freely) | **Asymmetric** (each locale restructures freely) | **Symmetric** (all follow source structure) | **Symmetric** (all follow source structure) | **Symmetric** (all follow source structure) | **Symmetric** (all follow source structure) |
| **Plural Forms** | CLDR (30 languages) | CLDR (all languages via babel) | CLDR (all languages via babel) | CLDR (via GNU ngettext) | **CLDR (600+ locales)** | **CLDR (all locales)** | Rails-style (one/many/zero/few) |
| **Select Expressions** | Built-in (`{ $var -> ... }`) | Built-in | Built-in | Manual workarounds | Manual workarounds | Manual workarounds | Manual workarounds |
| **Context Support** | Terms (`-brand`), Attributes | Terms, Attributes | Terms, Attributes | **pgettext()** (Python 3.8+) | **pgettext()** | **QCoreApplication.translate()** with disambiguation | Namespaces |
| **Number Formatting** | Babel CLDR (NUMBER, CURRENCY functions) | Babel CLDR | Babel CLDR | Manual (use Babel separately) | **CLDR (format_number, format_currency)** | **Qt CLDR** | Manual |
| **Date Formatting** | Babel CLDR (DATETIME function) | Babel CLDR | Babel CLDR | Manual (use Babel separately) | **CLDR (format_datetime, format_date, format_time)** | **Qt CLDR** | Manual |
| **Bidi Isolation** | **Yes** (Unicode FSI/PDI marks) | **Yes** | **Yes** | No (manual \u2068/\u2069) | No (manual) | **Yes** (Qt handles RTL) | No |
| **Error Handling** | (value, errors) tuples | (value, errors) tuples | (value, errors) tuples | Fallback to msgid | Fallback to msgid | Fallback to source text | Fallback to key |
| **Message References** | **Yes** (message-id, -term) | **Yes** | **Yes** | No | No | No | No |
| **Python Version** | 3.13+ | 3.6+ | 3.7+ | All (stdlib) | 3.8+ | 3.9+ (via PyQt6/PySide6) | 3.6+ |
| **Dependencies** | Babel only | fluent.syntax, attrs, babel, pytz, typing-extensions | fluent.syntax, attrs, babel, pytz | None (stdlib) | pytz, setuptools | PyQt6 or PySide6 | PyYAML (optional) |
| **Type Safety** | **mypy --strict** compatible | Partial (uses attrs) | Partial | No type stubs | Partial type stubs | PyQt6-stubs available | No type stubs |
| **Validation API** | **validate_resource()** (CI/tooling) | No dedicated API | No dedicated API | msgfmt --check | msgfmt --check | Qt Linguist GUI | No validation |
| **Circular Reference Detection** | **Yes** (runtime) | **Yes** | **Yes** | N/A | N/A | N/A | N/A |
| **Use Cases** | Modern apps needing asymmetric grammar | Firefox, Thunderbird extensions | Django (django-ftl), performance-critical | Linux, GNOME, legacy Django | Flask, Pyramid, date/number formatting | PyQt/PySide GUI apps, also non-GUI | Simple YAML-based apps |
| **GUI-Specific** | No | No | No | No | No | **No** (works with QCoreApplication for non-GUI) | No |
| **Ecosystem Maturity** | New (2025) | Mozilla reference (2023) | Mature (django-ftl) | **Very mature** (1990s) | **Very mature** (2013+) | **Very mature** (Qt 6.x) | Low maintenance (2018) |
| **License** | MIT ([see PATENTS.md](https://github.com/resoltico/ftllexbuffer/blob/main/PATENTS.md)) | Apache 2.0 | Apache 2.0 | **Python (stdlib)** | BSD | **LGPL** (PySide6) | MIT |
| **Performance** | Interpreter (moderate) | Interpreter (moderate) | **Bytecode (very fast)** | Binary .mo (fast) | Binary .mo (fast) | **Binary .qm (very fast)** | YAML/JSON parse (slow) |
| **Translator Tools** | Pontoon, generic text editors | Pontoon, generic text editors | Pontoon, generic text editors | **Poedit, Lokalize, Weblate** | **Poedit, Lokalize, Weblate** | **Qt Linguist GUI** | Generic text editors |
| **Update Workflow** | Edit .ftl → reload | Edit .ftl → reload | Edit .ftl → **recompile** | Edit .po → **msgfmt** → restart | Edit .po → **pybabel compile** → restart | Edit .ts → **lrelease** → restart | Edit .yml/.json → reload |
| **Django Integration** | Manual | Manual | **django-ftl** package | **Built-in** (makemessages, compilemessages) | **django-babel** | Manual (via PyQt) | Manual |
| **Flask Integration** | Manual | Manual | Manual | **flask-babel** | **Flask-Babel** package | Manual | Manual |

### Key Observations

**Asymmetric vs. Symmetric Grammar:**
- **Asymmetric** (FTL-based): Translators restructure messages freely per language grammar. Example: Arabic uses 6 plural forms with completely different sentence structures than English.
- **Symmetric** (gettext, Babel, Qt, python-i18n): All translations follow source language structure. Translators fill in blanks but cannot restructure.

**Compilation Trade-offs:**
- **No compilation** (FTLLexBuffer, fluent.runtime, python-i18n): Faster development (edit → reload), but slower runtime.
- **Requires compilation** (fluent-compiler, gettext, Babel, Qt Linguist): Extra build step (edit → compile → restart), but faster runtime and validation at compile time.
  - **When compilation is good**: Production deployments (smaller files, faster lookups), CI validation (catch errors early).
  - **When compilation is bad**: Development iteration (extra step slows feedback loop).

**Qt Linguist for Python:**
- **Works for non-GUI apps**: QTranslator is text-based, not tied to GUI. Use QCoreApplication.translate() for non-QObject classes.
- **Compilation**: .ts (XML) → .qm (binary) via lrelease. Extremely fast lookups.
- **Python support**: Requires Qt 6.2+ (pyside6-lupdate extracts from .py files). Available via PyQt6 or PySide6.
- **Licensing critical difference**:
  - **PySide6** (LGPL): Free for commercial closed-source apps (must provide LGPL compliance for PySide6 itself)
  - **PyQt6** (GPL/Commercial): Must open-source your app (GPL) OR purchase commercial license
- **Trade-off**: Heavy dependency (entire Qt framework) for non-Qt apps. Best for existing PyQt/PySide projects.

**Babel's Role:**
- Primarily a **formatting library** (numbers, dates, currencies) with gettext .po/.mo support.
- Often used **alongside** gettext (extract/compile .po files) rather than replacing it.
- **Best for**: Flask/Pyramid apps needing CLDR formatting + gettext workflow.

**python-i18n:**
- **Simplest** solution (YAML/JSON key-value pairs, Rails-inspired API).
- **Limitations**: Rails-style plurals (one/many/zero/few, not full CLDR), no select expressions, low maintenance (inactive project).
- **Best for**: Small projects with basic translation needs.

### Recommendation Matrix

| Your Situation | Recommended Solution | Reason |
|----------------|---------------------|---------|
| New project, modern Python 3.13+, need asymmetric grammar | **FTLLexBuffer** | Clean API, mypy --strict, no compilation step |
| Django project, asymmetric grammar, performance-critical | **fluent-compiler** | django-ftl integration, bytecode speed |
| PyQt/PySide GUI application | **Qt Linguist** | Native Qt integration, fast binary .qm format |
| Flask/Pyramid web app, need CLDR formatting | **Babel + gettext** | Flask-Babel package, mature ecosystem |
| Legacy Django app, existing .po files | **gettext (Django built-in)** | Built-in makemessages/compilemessages |
| Small project, simple key-value translations | **python-i18n** | Minimal setup, YAML/JSON simplicity |
| Maximum ecosystem compatibility | **gettext (stdlib)** | Universal support (Poedit, Weblate, etc.) |
| Modern app targeting Firefox/Mozilla ecosystem | **fluent.runtime** | Reference implementation from projectfluent |

**Note**: All Fluent implementations (FTLLexBuffer, fluent.runtime, fluent-compiler) support FTL v1.0 specification and allow translators to restructure messages per language grammar, while gettext/Babel/Qt/python-i18n require all translations to follow source message structure.

## Specification Compliance

- Fluent Specification v1.0 EBNF grammar (all production rules)
- CLDR plural rules (30 locales - see [Locale Support](#locale-support) for complete list)
- Unicode bidi isolation (FSI/PDI marks)
- Comment preservation (#, ##, ###)
- Unicode escapes (\uXXXX, \UXXXXXX)
- Line endings (CRLF, LF, CR)
- Select expressions (all selector types: `$var`, `42`, `"str"`, `FUNC()`)
- Message validation (Pattern OR Attribute required)
- Source position tracking (Span/Annotation)
- Error recovery (Junk nodes)

**Reference**: [Fluent Specification (fluent.ebnf)](https://github.com/projectfluent/fluent/blob/master/spec/fluent.ebnf)

## License

MIT License - See [LICENSE](LICENSE) for details.

This library is an independent implementation of the [Fluent Specification](https://github.com/projectfluent/fluent/blob/master/spec/fluent.ebnf) (Copyright Mozilla Foundation and others, licensed under Apache License 2.0).

**Important:** This implementation is licensed separately under MIT. The Apache 2.0 license applies to the specification itself, not to this implementation code.

**Legal Documentation:**
- [LICENSE](https://github.com/resoltico/ftllexbuffer/blob/main/LICENSE) - MIT License text
- [PATENTS.md](https://github.com/resoltico/ftllexbuffer/blob/main/PATENTS.md) - Comprehensive patent considerations, risk assessment, and contributor guidelines
- [NOTICE](https://github.com/resoltico/ftllexbuffer/blob/main/NOTICE) - Full attribution, trademark usage, disclaimer of affiliation, and dependency licenses

For patent-related concerns or commercial use requiring explicit patent protection, consult [PATENTS.md](https://github.com/resoltico/ftllexbuffer/blob/main/PATENTS.md).
