# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
