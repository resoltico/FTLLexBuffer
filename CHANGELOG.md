# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
    - **Zero external date libraries**: Pure Python 3.13 + Babel (already a dependency)
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
  - **100% transparency**: Cached results identical to non-cached (property-based tested)
  - **100% coverage**: All cache paths tested including concurrency and edge cases

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

- **172 new tests** for v0.5.0 features (total: 3122 tests passing, 96.6%+ coverage)
  - **Parsing tests** (99 tests):
    - `tests/test_parsing_numbers.py` (14 tests) - Number/decimal parsing with roundtrip validation
    - `tests/test_parsing_dates.py` (10 tests) - Date/datetime parsing with timezone support
    - `tests/test_parsing_currency.py` (9 tests) - Currency parsing with symbol detection
    - `tests/test_parsing_numbers_hypothesis.py` (16 tests) - **NEW: Property-based number parsing tests**
      - **Roundtrip precision preservation**: format → parse maintains exact float/Decimal value across 200 examples per test
      - **Type invariants**: Always returns float (parse_number) or Decimal (parse_decimal), never mixed types
      - **Negative amounts and fractional precision**: Tests edge cases with sub-dollar amounts and negative values
      - **Cross-locale consistency**: Parsing works identically across en_US, de_DE, fr_FR, lv_LV, pl_PL, ja_JP
      - **Metamorphic properties**: Order independence (parse order doesn't matter), idempotence (parse(parse(x)) == parse(x)), stability (repeated parse operations converge)
      - **Type error handling**: **Discovered AttributeError/TypeError bug** - Babel crashes on non-string inputs (integers, lists, dicts)
      - **Generates 2800+ test cases** from property specifications (100-200 examples per property)
    - `tests/test_serialization_hypothesis.py` (11 tests) - **NEW: Property-based FTL serialization tests**
      - **Roundtrip idempotence**: parse → serialize → parse → serialize stabilizes after first cycle
      - **Structure preservation**: Message count, IDs, and attributes preserved through roundtrip
      - **Never crashes property**: serialize_ftl() never raises on any parsed Resource
      - **Unicode content handling**: Non-ASCII text (Latin-1 Supplement) survives roundtrip
      - **Multiline patterns**: Messages with 1-20 continuation lines maintain structure
      - **Whitespace normalization**: Roundtrip may normalize whitespace but preserves semantic content
      - **FTL syntax constraints**: Filters special characters (`{`, `[`, `*`, etc.) that have semantic meaning in FTL
      - **Generates 1500+ test cases** from property specifications (20-200 examples per property)
    - `tests/test_parsing_currency_hypothesis.py` (17 tests) - **ENHANCED: Added 3 metamorphic property tests**
      - **Financial precision preservation**: Decimal roundtrip (format → parse → format) with no float rounding
      - **ISO 4217 currency code recognition**: All 3-letter uppercase codes accepted (EUR, USD, GBP, JPY, etc.)
      - **Unknown symbol error handling**: Tests both strict mode (ValueError) and non-strict mode (None)
      - **Invalid number detection**: Filters out Babel's special IEEE 754 values (NaN, Infinity, Inf)
      - **NEW: Comparison property**: parse(format(a)) < parse(format(b)) iff a < b (ordering preserved through roundtrip)
      - **NEW: Locale format independence**: parse(format(x, L1), L1) == parse(format(x, L2), L2) for all locales
      - **NEW: Addition homomorphism**: parse(format(a)) + parse(format(a)) == parse(format(2*a)) within Decimal precision
      - **Type error handling**: Non-string inputs (integers, floats, lists, dicts) handled gracefully
      - **Negative amounts**: Debt/refunds with correct sign preservation
      - **Fractional amounts**: Sub-dollar precision (0.001-0.999) with exact Decimal preservation
      - **Cross-locale consistency**: Currency parsing works across multiple locales (en_US, de_DE, fr_FR, ja_JP, lv_LV, pl_PL)
      - **Defensive code validation**: Verifies regex pattern symbols match currency symbol map (lines 108-111)
      - **Generates 2000+ test cases** from property specifications (50-200 examples per property)
    - `tests/test_parsing_dates_hypothesis.py` (22 tests) - **Property-based date/datetime parsing tests**
      - **ISO 8601 format reliability**: 200 examples per test across all date/datetime combinations (2000-2099)
      - **Locale independence**: ISO dates parse identically in en_US, de_DE, fr_FR, lv_LV, pl_PL, ja_JP
      - **US format (month-first)**: M/D/YYYY parsing with correct month/day interpretation
      - **European format (day-first)**: D.M.YYYY parsing with correct day/month interpretation
      - **Type error handling**: **Discovered and fixed critical TypeError bug** in ISO fast path (lines 58, 121)
      - **Timezone assignment**: Tests both ISO path (line 118-120) and strptime path (line 131) with tzinfo parameter
      - **Invalid locale fallback**: Defensive exception handling for missing CLDR data (lines 174-179, 223-230)
      - **Financial reporting date formats**: ISO, US, EU formats all tested across 100 date combinations
      - **Minimal locale data**: Tests locales with incomplete CLDR data ("root", "und", "en_001", "en_150")
      - **24-hour time format**: 100 examples testing hour:minute combinations (0-23:0-59)
      - **Generates 3800+ test cases** from property specifications (50-200 examples per property)
  - **Caching tests** (26 tests):
    - `tests/test_cache_basic.py` (14 tests) - Cache hit/miss, LRU eviction, stats, invalidation
    - `tests/test_cache_concurrency.py` (6 tests) - Thread safety, race conditions, concurrent mutations
    - `tests/test_cache_properties.py` (6 tests with Hypothesis) - Cache transparency, isolation, LRU properties
  - **API completeness tests** (10 tests):
    - `tests/test_localization_api_completeness.py` (10 tests) - FluentLocalization new methods
  - **Rich diagnostics tests** (18 tests):
    - `tests/test_rich_diagnostics.py` (18 tests) - Enhanced error objects, diagnostic codes, error formatting
  - **Custom patterns tests** (19 tests):
    - `tests/test_custom_patterns.py` (19 tests) - NUMBER/DATETIME pattern support, regulatory formats

### Performance

- **Caching speedup**: Up to 50x faster for repeated format_pattern() calls with same arguments
  - Example: Rendering 1000 messages with same locale/args goes from 100ms to 2ms
  - Benefit scales with message complexity (functions, plurals, references)
  - Zero overhead when caching disabled (default behavior unchanged)

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
- Read [PARSING.md](https://github.com/resoltico/ftllexbuffer/blob/main/PARSING.md) for best practices

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

- **Comprehensive property-based test suite** (121 new tests):
  - **FunctionRegistry introspection** (24 Hypothesis tests):
    - List/iteration/contains invariants
    - Copy isolation and function overwriting behavior
    - Empty registry edge cases
    - Large registry performance (100-1000 functions)
  - **Function metadata** (26 coverage tests):
    - Locale injection detection with malformed registries
    - Custom functions overriding built-in names
    - Metadata consistency validation
  - **Integration tests** (21 tests):
    - Built-in functions (NUMBER, DATETIME, CURRENCY) introspection
    - Financial validation workflows (VAT calculations, invoice totals)
    - Function discovery patterns for auto-documentation
  - **Plural rules** (28 Hypothesis tests):
    - CLDR compliance for English, Latvian, Slavic (Russian/Polish), Arabic
    - Financial use cases (invoice line items, VAT amounts, product quantities)
    - Metamorphic properties and edge cases
  - **Bundle operations** (22 Hypothesis tests):
    - Term attribute cycle detection
    - Source path error logging
    - Validation error handling
    - Currency/VAT formatting robustness

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

- **Contract testing framework** (358 new tests in `tests/test_function_locale_contracts.py`)
  - Verifies FluentBundle output matches direct function calls for all locale-dependent functions
  - Tests NUMBER(), DATETIME(), CURRENCY() across 30 locales with various parameters
  - **Would have caught CURRENCY locale bug immediately**
  - Prevents future locale injection regressions

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
- **tests/test_currency_function.py** (new) - Test suite for CURRENCY() function (50+ tests)
  - All 30 supported locales tested
  - Currency-specific decimal rules (JPY: 0, BHD: 3)
  - Symbol placement variations (en_US vs lv_LV vs de_DE)
  - All display modes (symbol, code, name)
  - Error handling (invalid currency codes, invalid values)
  - Property-based tests with Hypothesis (100+ examples)
- **tests/test_ast_edge_cases.py** (new) - Coverage tests targeting uncovered lines
  - Validator edge cases (duplicate selectors, invalid message/term references)
  - Visitor transformation edge cases
  - Resolver edge cases (boolean conversion, placeable resolution)
  - Plural rules edge cases (Polish pl i=1 case)
  - AST edge cases and parser error paths
- **tests/test_bundle_error_handling.py** (new) - Bundle error handling and edge cases
  - Term attribute validation during cycle detection
  - Junk entry logging with source_path context
  - Comment entry handling
  - Parse error reporting with source_path
  - Message validation warnings (missing values/attributes)
  - Term validation (duplicate IDs, undefined references)
- **tests/test_introspection_coverage.py** (new) - Introspection API coverage tests
  - Function calls with variable references in named arguments
  - TypeError handling for non-Message/Term introspection
  - Edge cases in variable extraction
- **tests/test_locale_context_coverage.py** (new) - LocaleContext error path coverage
  - Unknown locale handling with fallback to en_US
  - Number formatting error paths
  - Datetime formatting error paths
  - Currency formatting error paths
- **tests/test_visitor_coverage.py** (new) - Visitor and Transformer coverage tests
  - Term transformation
  - SelectExpression, Variant, FunctionReference transformations
  - MessageReference, TermReference, VariableReference transformations
  - CallArguments and NamedArgument transformations
  - Attribute transformations and edge cases
- **tests/test_miscellaneous_coverage.py**
  - Improved naming for miscellaneous edge case coverage
  - Tests for localization with non-PathResourceLoader
  - Polish plural rules validation
  - Boolean to string conversion in resolver
  - Placeable resolution edge cases
- **tests/test_locale_formatting_comprehensive.py** - Added CURRENCY tests
  - Integration tests for all 30 locales
  - Parameter handling tests
  - Locale-specific formatting validation

## [0.1.1] - 2025-11-28

### Added
- `FluentBundle.get_all_message_variables()` - Batch introspection API for extracting variables from all messages at once. Useful for CI/CD validation pipelines.
- Property-based testing examples in `examples/property_based_testing.py` - 7 examples demonstrating Hypothesis usage with FTLLexBuffer.
- Test suite for batch introspection (`tests/test_bundle_batch_introspection.py`) - 23 tests including property-based tests.

## [0.1.0] - 2025-11-28

Initial release.

[0.3.0]: https://github.com/resoltico/ftllexbuffer/releases/tag/v0.3.0
[0.2.0]: https://github.com/resoltico/ftllexbuffer/releases/tag/v0.2.0
[0.1.1]: https://github.com/resoltico/ftllexbuffer/releases/tag/v0.1.1
[0.1.0]: https://github.com/resoltico/ftllexbuffer/releases/tag/v0.1.0
