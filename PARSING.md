# Parsing Guide - Bi-Directional Localization

FTLLexBuffer provides comprehensive **bi-directional localization**: both formatting (data → display) and parsing (display → data).

## Table of Contents

1. [Quick Start](#quick-start)
2. [API Reference](#api-reference)
3. [Best Practices](#best-practices)
4. [Common Patterns](#common-patterns)
5. [Migration from Babel](#migration-from-babel)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Basic Number Parsing

```python
from ftllexbuffer.parsing import parse_decimal

# Parse locale-formatted number
amount = parse_decimal("1 234,56", "lv_LV")
# → Decimal('1234.56')

# Parse US format
amount_us = parse_decimal("1,234.56", "en_US")
# → Decimal('1234.56')
```

### Bi-Directional Workflow

```python
from ftllexbuffer import FluentBundle
from ftllexbuffer.parsing import parse_decimal

# Create bundle
bundle = FluentBundle("lv_LV")
bundle.add_resource("price = { CURRENCY($amount, currency: 'EUR') }")

# Format for display
formatted, _ = bundle.format_pattern("price", {"amount": 1234.56})
# → "1 234,56 €"

# Parse user input back to data
user_input = "1 234,56"
parsed = parse_decimal(user_input, "lv_LV")
# → Decimal('1234.56')

# Roundtrip: format → parse → format preserves value
assert float(parsed) == 1234.56
```

---

## API Reference

### parse_number()

Parse locale-formatted number string to `float`.

```python
from ftllexbuffer.parsing import parse_number

# US English
parse_number("1,234.5", "en_US")  # → 1234.5

# Latvian
parse_number("1 234,5", "lv_LV")  # → 1234.5

# German
parse_number("1.234,5", "de_DE")  # → 1234.5

# Non-strict mode (returns None on error)
parse_number("invalid", "en_US", strict=False)  # → None
```

**When to use**: Display values, UI elements, non-financial data

### parse_decimal()

Parse locale-formatted number string to `Decimal` (financial precision).

```python
from decimal import Decimal
from ftllexbuffer.parsing import parse_decimal

# Financial precision - no float rounding errors
amount = parse_decimal("100,50", "lv_LV")  # → Decimal('100.50')
vat = amount * Decimal("0.21")             # → Decimal('21.105') - exact!

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

```python
from ftllexbuffer.parsing import parse_date

# US format (MM/DD/YYYY)
parse_date("1/28/2025", "en_US")  # → date(2025, 1, 28)

# European format (DD.MM.YYYY)
parse_date("28.01.2025", "lv_LV")  # → date(2025, 1, 28)

# ISO 8601 (works everywhere)
parse_date("2025-01-28", "en_US")  # → date(2025, 1, 28)
```

**Implementation Details**:
- **Python 3.13 stdlib only** - Uses `datetime.strptime()` and `datetime.fromisoformat()` (no external date libraries)
- **Babel CLDR patterns** - Converts Babel date patterns to strptime format directives
  - Example conversions: `"M/d/yy"` → `"%m/%d/%y"`, `"dd.MM.yyyy"` → `"%d.%m.%Y"`
- **Fast path optimization** - ISO 8601 dates (`"2025-01-28"`) use native `fromisoformat()` for maximum speed
- **Pattern fallback chain**:
  1. ISO 8601 format (fastest, unambiguous)
  2. Locale-specific CLDR patterns from Babel
  3. Common formats (US: MM/DD/YYYY, EU: DD.MM.YYYY)
- **Locale determines interpretation** - Day-first (EU) vs month-first (US) for ambiguous dates
- **Thread-safe** - No global state, immutable pattern lists
- **Zero external dependencies** - Uses only Python 3.13 stdlib + Babel (already a dependency)

### parse_datetime()

Parse locale-formatted datetime string to `datetime` object.

```python
from datetime import timezone
from ftllexbuffer.parsing import parse_datetime

# Parse datetime
parse_datetime("1/28/2025 14:30", "en_US")
# → datetime(2025, 1, 28, 14, 30)

# With timezone
parse_datetime("2025-01-28 14:30", "en_US", tzinfo=timezone.utc)
# → datetime(2025, 1, 28, 14, 30, tzinfo=timezone.utc)
```

**Implementation Details**:
- Same implementation as `parse_date()` but with time components
- Uses Babel CLDR datetime patterns converted to strptime format
- Pattern conversion includes time directives: `"HH:mm:ss"` → `"%H:%M:%S"`
- Fast path for ISO 8601 datetime strings
- Thread-safe, no external dependencies beyond Babel

### parse_currency()

Parse locale-formatted currency string to `(Decimal, currency_code)` tuple.

```python
from ftllexbuffer.parsing import parse_currency

# Parse EUR with symbol
amount, currency = parse_currency("€100.50", "en_US")
# → (Decimal('100.50'), 'EUR')

# Parse with ISO code
amount, currency = parse_currency("USD 1,234.56", "en_US")
# → (Decimal('1234.56'), 'USD')

# Latvian format
amount, currency = parse_currency("1 234,56 €", "lv_LV")
# → (Decimal('1234.56'), 'EUR')
```

**Supported currencies**: All ISO 4217 codes plus major currency symbols (€, $, £, ¥, etc.)

---

## Best Practices

### 1. Always Use Same Locale

**CRITICAL**: Format and parse must use the **same locale** for roundtrip correctness.

```python
# ✅ CORRECT - Same locale
locale = "lv_LV"
formatted = bundle.format_value("price", {"amount": 1234.56})
parsed = parse_decimal(formatted, locale)  # Same locale!

# ❌ WRONG - Different locales break roundtrip
formatted = bundle.format_value("price", {"amount": 1234.56})  # lv_LV
parsed = parse_decimal(formatted, "en_US")  # ← WRONG LOCALE!
# Result: ValueError (can't parse "1 234,56" as US format)
```

### 2. Use Strict Mode in Production

```python
# ✅ Production: Strict mode catches errors immediately
try:
    amount = parse_decimal(user_input, locale, strict=True)
except ValueError as e:
    show_error_to_user(f"Invalid amount: {e}")
    return

# ❌ Don't silently ignore errors in production
amount = parse_decimal(user_input, locale, strict=False)
if amount is None:
    amount = Decimal("0.00")  # Dangerous: hides input errors!
```

**When to use `strict=False`**: Data import from unreliable sources, optional fields, legacy data migration

### 3. Financial Precision - Always Use Decimal

```python
# ✅ CORRECT - Decimal for financial data
from decimal import Decimal
amount = parse_decimal("100,50", "lv_LV")  # → Decimal('100.50')
vat = amount * Decimal("0.21")              # → Decimal('21.105') - exact

# ❌ WRONG - Float loses precision
amount = parse_number("100,50", "lv_LV")    # → 100.5 (float)
vat = amount * 0.21                         # → 21.105000000000004 - precision loss!
```

**Impact**: Float precision loss accumulates in calculations and causes rounding errors in financial reports.

**Note on Special Values**: Babel's `parse_decimal()` accepts `NaN`, `Infinity`, and `Inf` (case-insensitive) as valid Decimal values per IEEE 754 standard. These are legitimate mathematical values but may not be appropriate for financial calculations. Add validation if your application needs to reject these:

```python
from decimal import Decimal

amount = parse_decimal(user_input, locale, strict=True)

# Reject special values for financial data
if not amount.is_finite():
    raise ValueError("Amount must be a finite number")
```

### 4. Validate Before Parsing

```python
# ✅ Good: Validate input before parsing
def parse_user_amount(input_str: str, locale: str) -> Decimal | None:
    # Trim whitespace
    input_str = input_str.strip()

    # Check not empty
    if not input_str:
        return None

    # Parse
    try:
        return parse_decimal(input_str, locale, strict=True)
    except ValueError:
        return None

# Usage
amount = parse_user_amount(user_input, "lv_LV")
if amount is None:
    show_error("Please enter a valid amount")
```

### 5. Roundtrip Validation

```python
# ✅ Verify roundtrip in tests
def test_roundtrip():
    original = Decimal("1234.56")
    formatted = currency_format(float(original), "lv-LV", currency="EUR")
    parsed, _ = parse_currency(formatted, "lv_LV")
    assert parsed == original  # Roundtrip preserved!
```

---

## Common Patterns

### Invoice Processing

```python
from decimal import Decimal
from ftllexbuffer import FluentBundle
from ftllexbuffer.parsing import parse_decimal

bundle = FluentBundle("lv_LV")
bundle.add_resource("""
    subtotal = Summa: { CURRENCY($amount, currency: "EUR") }
    vat = PVN (21%): { CURRENCY($vat, currency: "EUR") }
    total = Kopā: { CURRENCY($total, currency: "EUR") }
""")

def process_invoice(user_input: str) -> dict:
    # Parse user input (subtotal)
    subtotal = parse_decimal(user_input, "lv_LV")

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
# display: {"subtotal": "Summa: 1 234,56 €", ...}
# data: {"subtotal": Decimal('1234.56'), ...}
```

### Form Input Validation

```python
from ftllexbuffer.parsing import parse_decimal

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

    # Parse
    try:
        amount = parse_decimal(input_value, locale, strict=True)
    except ValueError:
        return (None, f"Invalid amount format for {locale}")

    # Validate range
    if amount <= 0:
        return (None, "Amount must be positive")

    if amount > Decimal("1000000"):
        return (None, "Amount exceeds maximum (1,000,000)")

    return (amount, None)

# Usage in web form
amount, error = validate_amount_field(request.form['amount'], user_locale)
if error:
    flash(error, 'error')
    return redirect(url_for('form'))

# Amount is valid Decimal, use in calculations
process_payment(amount)
```

### Data Import from CSV

```python
from ftllexbuffer.parsing import parse_decimal, parse_date

def import_transactions_csv(csv_path: str, locale: str) -> list[dict]:
    """Import financial transactions from CSV."""
    import csv

    transactions = []
    errors = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            # Parse date (non-strict for legacy data)
            date = parse_date(row['date'], locale, strict=False)
            if date is None:
                errors.append(f"Row {row_num}: Invalid date '{row['date']}'")
                continue

            # Parse amount (non-strict for legacy data)
            amount = parse_decimal(row['amount'], locale, strict=False)
            if amount is None:
                errors.append(f"Row {row_num}: Invalid amount '{row['amount']}'")
                continue

            transactions.append({
                "date": date,
                "amount": amount,
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

### After (FTLLexBuffer for both)

```python
from ftllexbuffer import FluentBundle
from ftllexbuffer.parsing import parse_decimal

# Formatting: FTLLexBuffer
bundle = FluentBundle("lv_LV")
formatted = bundle.format_value("price", {"amount": 1234.56})

# Parsing: FTLLexBuffer (consistent API)
user_input = "1 234,56"
parsed = parse_decimal(user_input, "lv_LV")  # Same locale format!
```

**Benefits**:
- Single import source
- Consistent locale code format
- Symmetric API design (format ↔ parse)
- Better error messages

---

## Troubleshooting

### Parse Fails with ValueError

**Problem**: `parse_decimal()` raises `ValueError`

**Common causes**:
1. **Wrong locale**: Make sure parsing locale matches formatting locale
2. **Invalid format**: Input doesn't match locale's number format
3. **Non-numeric input**: Input contains letters or unexpected characters

**Solution**:
```python
# Debug: Print the error message
try:
    amount = parse_decimal(user_input, locale)
except ValueError as e:
    print(f"Parse error: {e}")
    print(f"Input: '{user_input}'")
    print(f"Locale: {locale}")
```

### Roundtrip Doesn't Preserve Value

**Problem**: format → parse → format changes the value

**Cause**: Different locales used for format and parse

**Solution**:
```python
# ✅ Correct: Same locale throughout
locale = "lv_LV"
formatted = number_format(1234.56, f"{locale.replace('_', '-')}")
parsed = parse_number(formatted, locale)  # Same locale!

# ❌ Wrong: Different locales
formatted = number_format(1234.56, "lv-LV")
parsed = parse_number(formatted, "en_US")  # ← Different locale!
```

### Float Precision Loss

**Problem**: Calculations give unexpected results like `21.105000000000004`

**Cause**: Using `float` instead of `Decimal` for financial data

**Solution**:
```python
# ❌ Wrong: Float precision loss
amount = parse_number("100,50", "lv_LV")  # float
vat = amount * 0.21  # 21.105000000000004

# ✅ Correct: Decimal precision
from decimal import Decimal
amount = parse_decimal("100,50", "lv_LV")  # Decimal
vat = amount * Decimal("0.21")  # Decimal('21.105') - exact!
```

### Special Values (NaN, Infinity) Accepted

**Problem**: `parse_decimal("NaN", locale)` or `parse_decimal("Infinity", locale)` succeeds instead of raising ValueError

**Cause**: Babel's `parse_decimal()` accepts `NaN`, `Infinity`, and `Inf` (case-insensitive) as valid Decimal values per IEEE 754 standard

**Solution**:
```python
# Add validation to reject special values for financial data
from decimal import Decimal

amount = parse_decimal(user_input, locale, strict=True)

# Reject NaN and Infinity for financial calculations
if not amount.is_finite():
    raise ValueError("Amount must be a finite number")
```

**Background**: These special values are mathematically valid but typically inappropriate for financial calculations. The property-based tests exclude them from "invalid number" test cases to reflect Babel's behavior.

### Date Parsing Ambiguity

**Problem**: `parse_date("01/02/2025")` - is this Jan 2 or Feb 1?

**Cause**: Ambiguous date format depends on locale

**Solution**:
```python
# US: Interprets as month-first (Jan 2)
parse_date("01/02/2025", "en_US")  # → date(2025, 1, 2)

# Europe: Interprets as day-first (Feb 1)
parse_date("01/02/2025", "lv_LV")  # → date(2025, 2, 1)

# Recommendation: Use ISO 8601 (unambiguous)
parse_date("2025-01-02", locale)  # Always Jan 2
```

---

## See Also

- [API.md](API.md) - Complete API reference
- [README.md](README.md) - Getting started
- [PLAN.md](PLAN.md) - v0.5.0 implementation plan
- [Babel Documentation](https://babel.pocoo.org/) - Number and date formatting patterns

---

**FTLLexBuffer v0.5.0** - Production-ready bi-directional localization
