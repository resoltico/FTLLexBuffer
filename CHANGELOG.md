# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2025-12-02

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
