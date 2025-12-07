# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
