# Parsing Guide - Bi-Directional Localization

FTLLexBuffer provides comprehensive **bi-directional localization**: both formatting (data → display) and parsing (display → data).

**v0.8.0 BREAKING CHANGE**: All parse functions now return `tuple[result, list[FluentParseError]]` instead of raising exceptions. See [Migration from v0.7.0](#migration-from-v07x).

## Table of Contents

1. [Quick Start](#quick-start)
2. [API Reference](#api-reference)
3. [Best Practices](#best-practices)
4. [Common Patterns](#common-patterns)
5. [Migration from Babel](#migration-from-babel)
6. [Migration from v0.7.x](#migration-from-v07x)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Basic Number Parsing (v0.8.0 API)

```python
from ftllexbuffer.parsing import parse_decimal
from ftllexbuffer.parsing.guards import is_valid_decimal

# Parse locale-formatted number (v0.8.0 tuple return)
result, errors = parse_decimal("1 234,56", "lv_LV")
if not errors and is_valid_decimal(result):
    amount = result  # Decimal('1234.56')

# Parse US format
result, errors = parse_decimal("1,234.56", "en_US")
if not errors:
    amount_us = result  # Decimal('1234.56')
```

### Bi-Directional Workflow (v0.8.0 API)

```python
from ftllexbuffer import FluentBundle
from ftllexbuffer.parsing import parse_decimal
from ftllexbuffer.parsing.guards import is_valid_decimal

# Create bundle
bundle = FluentBundle("lv_LV")
bundle.add_resource("price = { CURRENCY($amount, currency: 'EUR') }")

# Format for display
formatted, _ = bundle.format_pattern("price", {"amount": 1234.56})
# → "1 234,56 €"

# Parse user input back to data (v0.8.0 API)
user_input = "1 234,56"
result, errors = parse_decimal(user_input, "lv_LV")

if not errors and is_valid_decimal(result):
    # Roundtrip: format → parse → format preserves value
    assert float(result) == 1234.56
```

---

## API Reference

### parse_number()

Parse locale-formatted number string to `float`.

**v0.8.0**: Returns `tuple[float, list[FluentParseError]]`.

```python
from ftllexbuffer.parsing import parse_number
# has_parse_errors removed in v0.10.0 - use `if errors:` directly

# US English
result, errors = parse_number("1,234.5", "en_US")
# result → 1234.5, errors → []

# Latvian
result, errors = parse_number("1 234,5", "lv_LV")
# result → 1234.5, errors → []

# German
result, errors = parse_number("1.234,5", "de_DE")
# result → 1234.5, errors → []

# Error handling (v0.8.0)
result, errors = parse_number("invalid", "en_US")
if errors:
    print(f"Parse error: {errors[0]}")
    # result is 0.0 (default fallback)
```

**When to use**: Display values, UI elements, non-financial data

### parse_decimal()

Parse locale-formatted number string to `Decimal` (financial precision).

**v0.8.0**: Returns `tuple[Decimal, list[FluentParseError]]`.

```python
from decimal import Decimal
from ftllexbuffer.parsing import parse_decimal
from ftllexbuffer.parsing.guards import is_valid_decimal

# Financial precision - no float rounding errors
result, errors = parse_decimal("100,50", "lv_LV")
if not errors and is_valid_decimal(result):
    vat = result * Decimal("0.21")  # → Decimal('21.105') - exact!

# Float would lose precision
float_amount = 100.50
float_vat = float_amount * 0.21  # → 21.105000000000004 - precision loss!
```

**When to use**:
- Financial calculations (invoices, payments, VAT)
- Currency amounts
- Any calculation where precision matters

### parse_date()

Parse locale-formatted date string to `date` object.

**v0.8.0**: Returns `tuple[date | None, list[FluentParseError]]`.

```python
from ftllexbuffer.parsing import parse_date
from ftllexbuffer.parsing.guards import is_valid_date

# US format (MM/DD/YYYY)
result, errors = parse_date("1/28/2025", "en_US")
if not errors and is_valid_date(result):
    date_value = result  # date(2025, 1, 28)

# European format (DD.MM.YYYY)
result, errors = parse_date("28.01.2025", "lv_LV")
# result → date(2025, 1, 28)

# ISO 8601 (works everywhere)
result, errors = parse_date("2025-01-28", "en_US")
# result → date(2025, 1, 28)
```

**Implementation Details**:
- **Python 3.13 stdlib only** - Uses `datetime.strptime()` and `datetime.fromisoformat()` (no external date libraries)
- **Babel CLDR patterns** - Converts Babel date patterns to strptime format directives
  - Example conversions: `"M/d/yy"` → `"%m/%d/%y"`, `"dd.MM.yyyy"` → `"%d.%m.%Y"`
- **v0.8.0 Token-based converter** - Replaces fragile regex approach for pattern conversion
- **Fast path optimization** - ISO 8601 dates (`"2025-01-28"`) use native `fromisoformat()` for maximum speed
- **Safe pattern matching** - No ambiguous fallback patterns:
  1. ISO 8601 format (fastest, unambiguous, always works)
  2. Locale-specific CLDR patterns from Babel ONLY
  3. No generic fallback patterns (prevents misinterpretation)
- **Locale determines interpretation** - Day-first (EU) vs month-first (US) based on CLDR patterns
- **Thread-safe** - No global state, immutable pattern lists
- **Zero external dependencies** - Uses only Python 3.13 stdlib + Babel (already a dependency)

**Important**: Ambiguous dates like "1/2/25" will FAIL unless:
- Input matches locale's CLDR pattern (e.g., "1/2/25" only works for en_US, not lv_LV)
- Input uses ISO 8601 format "2025-01-02" (works everywhere, recommended)

### parse_datetime()

Parse locale-formatted datetime string to `datetime` object.

**v0.8.0**: Returns `tuple[datetime | None, list[FluentParseError]]`.

```python
from datetime import timezone
from ftllexbuffer.parsing import parse_datetime
from ftllexbuffer.parsing.guards import is_valid_datetime

# Parse datetime (v0.8.0 API)
result, errors = parse_datetime("1/28/2025 14:30", "en_US")
if not errors and is_valid_datetime(result):
    dt = result  # datetime(2025, 1, 28, 14, 30)

# With timezone
result, errors = parse_datetime("2025-01-28 14:30", "en_US", tzinfo=timezone.utc)
# result → datetime(2025, 1, 28, 14, 30, tzinfo=timezone.utc)
```

**Implementation Details**:
- Same implementation as `parse_date()` but with time components
- Uses Babel CLDR datetime patterns converted to strptime format
- Pattern conversion includes time directives: `"HH:mm:ss"` → `"%H:%M:%S"`
- Fast path for ISO 8601 datetime strings
- Thread-safe, no external dependencies beyond Babel

### parse_currency()

Parse locale-formatted currency string to `(Decimal, currency_code)` tuple.

**v0.8.0**: Returns `tuple[tuple[Decimal, str] | None, list[FluentParseError]]`.

```python
from ftllexbuffer.parsing import parse_currency
from ftllexbuffer.parsing.guards import is_valid_currency

# Unambiguous symbols - work without default_currency
result, errors = parse_currency("€100.50", "en_US")
if not errors and is_valid_currency(result):
    amount, currency = result  # (Decimal('100.50'), 'EUR')

# Latvian format
result, errors = parse_currency("1 234,56 €", "lv_LV")
# result → (Decimal('1234.56'), 'EUR')

# ISO codes - always unambiguous
result, errors = parse_currency("USD 1,234.56", "en_US")
# result → (Decimal('1234.56'), 'USD')

# Ambiguous symbols require explicit currency
result, errors = parse_currency("$100", "en_US", default_currency="USD")
# result → (Decimal('100'), 'USD')

result, errors = parse_currency("$100", "en_CA", default_currency="CAD")
# result → (Decimal('100'), 'CAD')

# Or infer from locale
result, errors = parse_currency("$100", "en_CA", infer_from_locale=True)
# result → (Decimal('100'), 'CAD')  # Inferred from Canadian locale

# Ambiguous symbols without default_currency return error (v0.8.0)
result, errors = parse_currency("$100", "en_US")
if errors:
    print(f"Ambiguous currency: {errors[0]}")
```

**Currency Symbol Handling**:
- **Ambiguous**: $ (USD/CAD/AUD/SGD/HKD/NZD/MXN), ¢, ₨, ₱, kr
- **Unambiguous**: € (EUR), £ (GBP), ¥ (JPY), ₹ (INR), ₽ (RUB), etc.
- **Always safe**: ISO codes (USD, CAD, EUR, etc.)

**Supported currencies**: All ISO 4217 codes plus major currency symbols (€, $, £, ¥, etc.)

---

## Best Practices

### 1. Always Use Same Locale

**CRITICAL**: Format and parse must use the **same locale** for roundtrip correctness.

```python
# CORRECT - Same locale
locale = "lv_LV"
formatted = bundle.format_value("price", {"amount": 1234.56})
result, errors = parse_decimal(formatted, locale)  # Same locale!

# WRONG - Different locales break roundtrip
formatted = bundle.format_value("price", {"amount": 1234.56})  # lv_LV
result, errors = parse_decimal(formatted, "en_US")  # Wrong locale!
# Result: errors will contain parse error
```

### 2. Check Errors in Production (v0.8.0)

```python
from ftllexbuffer.parsing import parse_decimal
from ftllexbuffer.parsing.guards import is_valid_decimal

# v0.8.0: Check errors list instead of try/except
result, errors = parse_decimal(user_input, locale)

if errors:
    show_error_to_user(f"Invalid amount: {errors[0]}")
    return

if not is_valid_decimal(result):
    show_error_to_user("Amount cannot be NaN or Infinity")
    return

# Safe to use result
process_payment(result)
```

### 3. Financial Precision - Always Use Decimal

```python
from decimal import Decimal
from ftllexbuffer.parsing import parse_decimal
from ftllexbuffer.parsing.guards import is_valid_decimal

# CORRECT - Decimal for financial data
result, errors = parse_decimal("100,50", "lv_LV")
if not errors and is_valid_decimal(result):
    vat = result * Decimal("0.21")  # → Decimal('21.105') - exact

# WRONG - Float loses precision
from ftllexbuffer.parsing import parse_number
result, _ = parse_number("100,50", "lv_LV")  # float
vat = result * 0.21  # → 21.105000000000004 - precision loss!
```

**Impact**: Float precision loss accumulates in calculations and causes rounding errors in financial reports.

**Note on Special Values**: Babel's `parse_decimal()` accepts `NaN`, `Infinity`, and `Inf` (case-insensitive) as valid Decimal values per IEEE 754 standard. Use `is_valid_decimal()` to reject these for financial data:

```python
from ftllexbuffer.parsing.guards import is_valid_decimal

result, errors = parse_decimal(user_input, locale)

if errors:
    raise ValueError(f"Parse error: {errors[0]}")

# Reject special values for financial data
if not is_valid_decimal(result):
    raise ValueError("Amount must be a finite number")
```

### 4. Validate Before Processing

```python
from ftllexbuffer.parsing import parse_decimal
from ftllexbuffer.parsing.guards import is_valid_decimal

def parse_user_amount(input_str: str, locale: str) -> Decimal | None:
    # Trim whitespace
    input_str = input_str.strip()

    # Check not empty
    if not input_str:
        return None

    # Parse (v0.8.0 API)
    result, errors = parse_decimal(input_str, locale)

    if errors or not is_valid_decimal(result):
        return None

    return result

# Usage
amount = parse_user_amount(user_input, "lv_LV")
if amount is None:
    show_error("Please enter a valid amount")
```

### 5. Roundtrip Validation

```python
from ftllexbuffer.parsing import parse_currency
from ftllexbuffer.runtime.functions import currency_format
from ftllexbuffer.parsing.guards import is_valid_currency

# Verify roundtrip in tests
def test_roundtrip():
    original = Decimal("1234.56")
    formatted = currency_format(float(original), "lv-LV", currency="EUR")
    result, errors = parse_currency(formatted, "lv_LV")

    assert not errors
    assert is_valid_currency(result)
    assert result[0] == original  # Roundtrip preserved!
```

---

## Common Patterns

### Invoice Processing (v0.8.0)

```python
from decimal import Decimal
from ftllexbuffer import FluentBundle
from ftllexbuffer.parsing import parse_decimal
from ftllexbuffer.parsing.guards import is_valid_decimal

bundle = FluentBundle("lv_LV")
bundle.add_resource("""
    subtotal = Summa: { CURRENCY($amount, currency: "EUR") }
    vat = PVN (21%): { CURRENCY($vat, currency: "EUR") }
    total = Kopa: { CURRENCY($total, currency: "EUR") }
""")

def process_invoice(user_input: str) -> dict | None:
    # Parse user input (subtotal) - v0.8.0 API
    result, errors = parse_decimal(user_input, "lv_LV")

    if errors or not is_valid_decimal(result):
        return None

    subtotal = result

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

### Form Input Validation (v0.8.0)

```python
from decimal import Decimal
from ftllexbuffer.parsing import parse_decimal
from ftllexbuffer.parsing.guards import is_valid_decimal

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

    if errors:
        return (None, f"Invalid amount format for {locale}")

    # Validate finite (not NaN/Infinity)
    if not is_valid_decimal(result):
        return (None, "Amount must be a finite number")

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

### Data Import from CSV (v0.8.0)

```python
from ftllexbuffer.parsing import parse_decimal, parse_date
from ftllexbuffer.parsing.guards import is_valid_date, is_valid_decimal

def import_transactions_csv(csv_path: str, locale: str) -> tuple[list[dict], list[str]]:
    """Import financial transactions from CSV."""
    import csv

    transactions = []
    import_errors = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            # Parse date (v0.8.0 API)
            date_result, date_errors = parse_date(row['date'], locale)
            if date_errors or not is_valid_date(date_result):
                import_errors.append(f"Row {row_num}: Invalid date '{row['date']}'")
                continue

            # Parse amount (v0.8.0 API)
            amount_result, amount_errors = parse_decimal(row['amount'], locale)
            if amount_errors or not is_valid_decimal(amount_result):
                import_errors.append(f"Row {row_num}: Invalid amount '{row['amount']}'")
                continue

            transactions.append({
                "date": date_result,
                "amount": amount_result,
                "description": row['description']
            })

    return transactions, import_errors

# Usage
transactions, errors = import_transactions_csv("export.csv", "lv_LV")
if errors:
    print(f"Import completed with {len(errors)} errors:")
    for error in errors:
        print(f"  - {error}")
```

---

## Migration from Babel

### Before (Babel only)

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

### After (FTLLexBuffer for both - v0.8.0)

```python
from ftllexbuffer import FluentBundle
from ftllexbuffer.parsing import parse_decimal
from ftllexbuffer.parsing.guards import is_valid_decimal

# Formatting: FTLLexBuffer
bundle = FluentBundle("lv_LV")
formatted = bundle.format_value("price", {"amount": 1234.56})

# Parsing: FTLLexBuffer (consistent API, v0.8.0)
user_input = "1 234,56"
result, errors = parse_decimal(user_input, "lv_LV")

if not errors and is_valid_decimal(result):
    parsed = result  # Same locale format!
```

**Benefits**:
- Single import source
- Consistent locale code format
- Symmetric API design (format ↔ parse)
- Better error handling with structured errors

---

## Migration from v0.7.x

### Breaking Changes in v0.8.0

1. **Tuple return type**: All parse functions now return `tuple[result, list[FluentParseError]]`
2. **No more exceptions**: Check `errors` list instead of catching `ValueError`
3. **`strict` parameter removed**: Functions NEVER raise - errors are always in the list
4. **Default values on error**:
   - `parse_number()` returns `0.0` on error
   - `parse_decimal()` returns `Decimal("0")` on error
   - `parse_date()` returns `None` on error
   - `parse_datetime()` returns `None` on error
   - `parse_currency()` returns `None` on error

### Migration Examples

```python
# OLD (v0.7.x): Exception-based error handling
try:
    amount = parse_decimal(user_input, locale)
except ValueError as e:
    show_error(f"Invalid: {e}")
    return

# NEW (v0.8.0): Tuple-based error handling
# has_parse_errors removed in v0.10.0 - use `if errors:` directly
result, errors = parse_decimal(user_input, locale)
if errors:
    show_error(f"Invalid: {errors[0]}")
    return
amount = result

# OLD (v0.7.x): Non-strict mode
amount = parse_decimal(user_input, locale, strict=False)
if amount is None:
    amount = Decimal("0")

# NEW (v0.8.0): Check errors list
result, errors = parse_decimal(user_input, locale)
if errors:
    result = Decimal("0")
amount = result

# NEW (v0.8.0): Using type guards for full safety
from ftllexbuffer.parsing.guards import is_valid_decimal

result, errors = parse_decimal(user_input, locale)
if not errors and is_valid_decimal(result):
    # mypy knows result is finite Decimal
    process_payment(result)
```

---

## Troubleshooting

### Parse Returns Errors (v0.8.0)

**Problem**: `parse_decimal()` returns non-empty errors list

**Common causes**:
1. **Wrong locale**: Make sure parsing locale matches formatting locale
2. **Invalid format**: Input doesn't match locale's number format
3. **Non-numeric input**: Input contains letters or unexpected characters

**Solution**:
```python
from ftllexbuffer.parsing import parse_decimal
# has_parse_errors removed in v0.10.0 - use `if errors:` directly

# Debug: Print the error details
result, errors = parse_decimal(user_input, locale)
if errors:
    print(f"Parse error: {errors[0]}")
    print(f"Input: '{user_input}'")
    print(f"Locale: {locale}")
    print(f"Error code: {errors[0].diagnostic_code}")
```

### Roundtrip Doesn't Preserve Value

**Problem**: format → parse → format changes the value

**Cause**: Different locales used for format and parse

**Solution**:
```python
from ftllexbuffer.parsing import parse_number
from ftllexbuffer.runtime.functions import number_format

# Correct: Same locale throughout
locale = "lv_LV"
formatted = number_format(1234.56, f"{locale.replace('_', '-')}")
result, errors = parse_number(formatted, locale)  # Same locale!

# Wrong: Different locales
formatted = number_format(1234.56, "lv-LV")
result, errors = parse_number(formatted, "en_US")  # Different locale!
```

### Float Precision Loss

**Problem**: Calculations give unexpected results like `21.105000000000004`

**Cause**: Using `float` instead of `Decimal` for financial data

**Solution**:
```python
from decimal import Decimal
from ftllexbuffer.parsing import parse_number, parse_decimal
# has_parse_errors removed in v0.10.0 - use `if errors:` directly

# Wrong: Float precision loss
result, _ = parse_number("100,50", "lv_LV")  # float
vat = result * 0.21  # 21.105000000000004

# Correct: Decimal precision
result, errors = parse_decimal("100,50", "lv_LV")
if not errors:
    vat = result * Decimal("0.21")  # Decimal('21.105') - exact!
```

### Special Values (NaN, Infinity) Accepted

**Problem**: `parse_decimal("NaN", locale)` succeeds instead of returning error

**Cause**: Babel's `parse_decimal()` accepts `NaN`, `Infinity`, and `Inf` (case-insensitive) as valid Decimal values per IEEE 754 standard

**Solution**:
```python
from ftllexbuffer.parsing import parse_decimal
from ftllexbuffer.parsing.guards import is_valid_decimal

result, errors = parse_decimal(user_input, locale)

if errors:
    raise ValueError(f"Parse failed: {errors[0]}")

# Reject NaN and Infinity for financial calculations
if not is_valid_decimal(result):
    raise ValueError("Amount must be a finite number")
```

**Background**: These special values are mathematically valid but typically inappropriate for financial calculations. Use `is_valid_decimal()` type guard to reject them.

### Date Parsing Ambiguity

**Problem**: `parse_date("01/02/2025")` - is this Jan 2 or Feb 1?

**Cause**: Ambiguous date format depends on locale

**Solution**:
```python
from ftllexbuffer.parsing import parse_date
from ftllexbuffer.parsing.guards import is_valid_date

# US: Interprets as month-first (Jan 2)
result, _ = parse_date("01/02/2025", "en_US")  # → date(2025, 1, 2)

# Europe: Interprets as day-first (Feb 1)
result, _ = parse_date("01/02/2025", "lv_LV")  # → date(2025, 2, 1)

# Recommendation: Use ISO 8601 (unambiguous)
result, errors = parse_date("2025-01-02", locale)  # Always Jan 2
```

---

## See Also

- [API.md](API.md) - Complete API reference
- [README.md](README.md) - Getting started
- [CHANGELOG.md](CHANGELOG.md) - v0.8.0 breaking changes
- [Babel Documentation](https://babel.pocoo.org/) - Number and date formatting patterns

---

**FTLLexBuffer v0.9.0** - Production-ready bi-directional localization
