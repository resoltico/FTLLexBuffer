"""Bi-Directional Localization Examples.

FTLLexBuffer v0.5.0+ provides full bi-directional localization:
- Format: data → display (FluentBundle + CURRENCY/NUMBER functions)
- Parse: display → data (parsing module)

This enables locale-aware forms, invoices, and financial applications.

Implementation:
- Number/currency parsing: Babel's parse_decimal() (CLDR-compliant)
- Date/datetime parsing: Python 3.13 stdlib (strptime, fromisoformat) with Babel CLDR patterns
- Zero external date libraries - pure Python 3.13 + Babel
- Thread-safe, fast ISO 8601 path, pattern fallback chains
"""

from decimal import Decimal

from ftllexbuffer import FluentBundle
from ftllexbuffer.parsing import parse_currency, parse_date, parse_decimal


def example_invoice_processing() -> None:
    """Invoice processing with bi-directional localization."""
    print("[Example 1] Invoice Processing (Latvian Locale)")
    print("-" * 60)

    # Create bundle for Latvian locale
    bundle = FluentBundle("lv_LV", use_isolating=False)
    bundle.add_resource(
        """
subtotal = Summa: { CURRENCY($amount, currency: "EUR") }
vat = PVN (21%): { CURRENCY($vat, currency: "EUR") }
total = Kopā: { CURRENCY($total, currency: "EUR") }
"""
    )

    # Parse user input (subtotal)
    user_input = "1 234,56"
    print(f"User input (subtotal): {user_input}")

    subtotal = parse_decimal(user_input, "lv_LV")
    assert subtotal is not None, "Failed to parse subtotal"
    print(f"Parsed to Decimal: {subtotal}")

    # Calculate VAT (financial precision with Decimal)
    vat_rate = Decimal("0.21")
    vat = subtotal * vat_rate
    total = subtotal + vat

    print("\nCalculations (Decimal precision):")
    print(f"  VAT (21%): {vat}")
    print(f"  Total: {total}")

    # Format for display
    subtotal_display, _ = bundle.format_pattern("subtotal", {"amount": float(subtotal)})
    vat_display, _ = bundle.format_pattern("vat", {"vat": float(vat)})
    total_display, _ = bundle.format_pattern("total", {"total": float(total)})

    print("\nFormatted for display (Latvian):")
    print(f"  {subtotal_display}")
    print(f"  {vat_display}")
    print(f"  {total_display}")

    # Roundtrip validation
    print("\nRoundtrip validation:")
    parsed_back = parse_decimal("1 234,56", "lv_LV")
    print(f"  Original: {subtotal}")
    print(f"  Parsed back: {parsed_back}")
    print(f"  Match: {subtotal == parsed_back}")


def example_form_validation() -> None:
    """Form input validation with locale-aware parsing."""
    print("\n[Example 2] Form Validation (German Locale)")
    print("-" * 60)

    bundle = FluentBundle("de_DE", use_isolating=False)
    bundle.add_resource('price = Preis: { CURRENCY($amount, currency: "EUR") }')

    # Simulate user input in German format
    user_inputs = [
        "123,45",  # Valid
        "1.234,56",  # Valid (with thousand separator)
        "invalid",  # Invalid
        "",  # Empty
    ]

    for user_input in user_inputs:
        print(f"\nUser input: '{user_input}'")

        # Validate and parse
        if not user_input.strip():
            print("  Error: Amount is required")
            continue

        try:
            amount = parse_decimal(user_input, "de_DE", strict=True)
            assert amount is not None, "Parse returned None"
            print(f"  Parsed: {amount}")

            # Range validation
            if amount <= 0:
                print("  Error: Amount must be positive")
                continue

            if amount > Decimal("1000000"):
                print("  Error: Amount exceeds maximum")
                continue

            # Format for display
            formatted, _ = bundle.format_pattern("price", {"amount": float(amount)})
            print(f"  Display: {formatted}")
            print("  Status: Valid")

        except ValueError as e:
            print(f"  Error: {e}")


def example_currency_parsing() -> None:
    """Currency parsing with automatic symbol detection."""
    print("\n[Example 3] Currency Parsing (Multiple Locales)")
    print("-" * 60)

    test_cases = [
        ("€123.45", "en_US"),
        ("1 234,56 €", "lv_LV"),
        ("1.234,56 €", "de_DE"),
        ("USD 1,234.56", "en_US"),
        ("£99.99", "en_GB"),
        ("¥12,345", "ja_JP"),
    ]

    for user_input, locale in test_cases:
        print(f"\nInput: {user_input:15} | Locale: {locale}")

        result = parse_currency(user_input, locale)
        if result is not None:
            amount, currency = result
            print(f"  Amount: {amount:12} | Currency: {currency}")

            # Format back in same locale
            bundle = FluentBundle(locale, use_isolating=False)
            bundle.add_resource("formatted = { CURRENCY($amount, currency: $curr) }")

            # Create select expression for dynamic currency
            ftl_source = """
formatted = { $curr ->
    [EUR] { CURRENCY($amount, currency: "EUR") }
    [USD] { CURRENCY($amount, currency: "USD") }
    [GBP] { CURRENCY($amount, currency: "GBP") }
    [JPY] { CURRENCY($amount, currency: "JPY") }
   *[other] { $amount } { $curr }
}
"""
            bundle.add_resource(ftl_source)
            formatted, _ = bundle.format_pattern(
                "formatted", {"amount": float(amount), "curr": currency}
            )
            print(f"  Formatted: {formatted}")
        else:
            print("  Error: Could not parse currency")


def example_date_parsing() -> None:
    """Date parsing with locale-aware format detection."""
    print("\n[Example 4] Date Parsing (US vs European)")
    print("-" * 60)

    # Same date string, different interpretations
    date_string = "01/02/2025"

    # US format (month-first)
    us_date = parse_date(date_string, "en_US")
    print(f"Input: {date_string}")
    print(f"  US format (MM/DD/YYYY): {us_date}  # January 2, 2025")

    # European format (day-first)
    eu_date = parse_date(date_string, "lv_LV")
    print(f"  EU format (DD/MM/YYYY): {eu_date}  # February 1, 2025")

    # ISO 8601 (unambiguous)
    iso_string = "2025-01-02"
    iso_date = parse_date(iso_string, "en_US")
    print(f"\nISO 8601: {iso_string}")
    print(f"  Always unambiguous: {iso_date}  # January 2, 2025")


def example_roundtrip_validation() -> None:
    """Roundtrip validation: format → parse → format."""
    print("\n[Example 5] Roundtrip Validation")
    print("-" * 60)

    locales = ["en_US", "lv_LV", "de_DE", "ja_JP"]
    original_value = Decimal("1234.56")

    print(f"Original value: {original_value}\n")

    for locale in locales:
        bundle = FluentBundle(locale, use_isolating=False)
        bundle.add_resource('price = { CURRENCY($amount, currency: "EUR") }')

        # Format → Parse → Format
        formatted1, _ = bundle.format_pattern("price", {"amount": float(original_value)})
        parsed = parse_currency(formatted1, locale)
        if parsed is not None:
            parsed_amount, parsed_currency = parsed
            formatted2, _ = bundle.format_pattern("price", {"amount": float(parsed_amount)})

            print(f"Locale: {locale}")
            print(f"  Format 1:  {formatted1}")
            print(f"  Parsed:    {parsed_amount} {parsed_currency}")
            print(f"  Format 2:  {formatted2}")
            print(f"  Preserved: {parsed_amount == original_value}")
        else:
            print(f"Locale: {locale} - Parse failed")


def example_csv_import() -> None:
    """CSV data import with locale-aware parsing."""
    print("\n[Example 6] CSV Import (Latvian Locale)")
    print("-" * 60)

    # Simulated CSV data (Latvian format)
    csv_data = [
        ("2025-01-15", "Prece A", "123,45"),
        ("2025-01-16", "Prece B", "1 234,56"),
        ("2025-01-17", "Prece C", "invalid"),  # Error
    ]

    locale = "lv_LV"
    transactions = []
    errors = []

    print(f"Importing transactions (locale: {locale}):\n")

    for row_num, (date_str, description, amount_str) in enumerate(csv_data, start=2):
        print(f"Row {row_num}: {date_str} | {description} | {amount_str}")

        # Parse date (ISO format - unambiguous)
        date = parse_date(date_str, locale, strict=False)
        if date is None:
            error_msg = f"Row {row_num}: Invalid date '{date_str}'"
            errors.append(error_msg)
            print(f"  Error: {error_msg}")
            continue

        # Parse amount (Latvian format)
        amount = parse_decimal(amount_str, locale, strict=False)
        if amount is None:
            error_msg = f"Row {row_num}: Invalid amount '{amount_str}'"
            errors.append(error_msg)
            print(f"  Error: {error_msg}")
            continue

        transactions.append({"date": date, "description": description, "amount": amount})
        print(f"  Imported: {date} | {description} | {amount}")

    print("\nImport summary:")
    print(f"  Successful: {len(transactions)}")
    print(f"  Errors: {len(errors)}")


if __name__ == "__main__":
    print("=" * 60)
    print("Bi-Directional Localization Examples")
    print("FTLLexBuffer v0.5.0+")
    print("=" * 60)

    example_invoice_processing()
    example_form_validation()
    example_currency_parsing()
    example_date_parsing()
    example_roundtrip_validation()
    example_csv_import()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)
