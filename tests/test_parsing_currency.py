"""Tests for currency parsing functions.

v0.8.0: Updated for new tuple return type API.
- parse_currency() returns tuple[tuple[Decimal, str] | None, list[FluentParseError]]
- Removed strict parameter - functions never raise, errors in list

Validates parse_currency() across multiple locales and currency formats.
"""

from decimal import Decimal

from ftllexbuffer.parsing import parse_currency


class TestParseCurrency:
    """Test parse_currency() function."""

    def test_parse_currency_eur_symbol(self) -> None:
        """Parse EUR with € symbol."""
        result, errors = parse_currency("€100.50", "en_US")
        assert not errors
        assert result is not None
        amount, code = result
        assert amount == Decimal("100.50")
        assert code == "EUR"

        result, errors = parse_currency("100,50 €", "lv_LV")
        assert not errors
        assert result is not None
        amount, code = result
        assert amount == Decimal("100.50")
        assert code == "EUR"

    def test_parse_currency_usd_symbol(self) -> None:
        """Parse USD with $ symbol (v0.7.0: requires default_currency)."""
        result, errors = parse_currency("$1,234.56", "en_US", default_currency="USD")

        assert not errors
        assert result is not None

        amount, code = result
        assert amount == Decimal("1234.56")
        assert code == "USD"

    def test_parse_currency_gbp_symbol(self) -> None:
        """Parse GBP with £ symbol."""
        result, errors = parse_currency("£999.99", "en_GB")

        assert not errors
        assert result is not None

        amount, code = result
        assert amount == Decimal("999.99")
        assert code == "GBP"

    def test_parse_currency_jpy_symbol(self) -> None:
        """Parse JPY with ¥ symbol (no decimals)."""
        result, errors = parse_currency("¥12,345", "ja_JP")

        assert not errors
        assert result is not None

        amount, code = result
        assert amount == Decimal("12345")
        assert code == "JPY"

    def test_parse_currency_iso_code(self) -> None:
        """Parse currency with ISO code instead of symbol."""
        result, errors = parse_currency("USD 1,234.56", "en_US")

        assert not errors
        assert result is not None

        amount, code = result
        assert amount == Decimal("1234.56")
        assert code == "USD"

        result, errors = parse_currency("EUR 1.234,56", "de_DE")


        assert not errors
        assert result is not None


        amount, code = result
        assert amount == Decimal("1234.56")
        assert code == "EUR"

    def test_parse_currency_no_symbol_returns_error(self) -> None:
        """No currency symbol returns error in list (v0.8.0 - no exceptions)."""
        result, errors = parse_currency("1,234.56", "en_US")
        assert len(errors) > 0
        assert result is None

    def test_parse_currency_invalid_returns_error(self) -> None:
        """Invalid input returns error in list (v0.8.0 - no exceptions)."""
        result, errors = parse_currency("invalid", "en_US")
        assert len(errors) > 0
        assert result is None


class TestRoundtripCurrency:
    """Test format -> parse -> format roundtrip for currency."""

    def test_roundtrip_currency_en_us(self) -> None:
        """Currency roundtrip for US English."""
        from ftllexbuffer.runtime.functions import currency_format

        original_amount = Decimal("1234.56")
        formatted = currency_format(
            float(original_amount), "en-US", currency="USD", currency_display="symbol"
        )
        # v0.7.0: $ is ambiguous - specify default_currency for roundtrip
        result, errors = parse_currency(formatted, "en_US", default_currency="USD")

        assert not errors
        assert result is not None

        parsed_amount, parsed_currency = result

        assert parsed_amount == original_amount
        assert parsed_currency == "USD"

    def test_roundtrip_currency_lv_lv(self) -> None:
        """Currency roundtrip for Latvian."""
        from ftllexbuffer.runtime.functions import currency_format

        original_amount = Decimal("1234.56")
        formatted = currency_format(
            float(original_amount), "lv-LV", currency="EUR", currency_display="symbol"
        )
        result, errors = parse_currency(formatted, "lv_LV")

        assert not errors
        assert result is not None

        parsed_amount, parsed_currency = result

        assert parsed_amount == original_amount
        assert parsed_currency == "EUR"
