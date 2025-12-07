"""Tests for currency parsing functions.

Validates parse_currency() across multiple locales and currency formats.
"""

from decimal import Decimal

import pytest

from ftllexbuffer.parsing import parse_currency


class TestParseCurrency:
    """Test parse_currency() function."""

    def test_parse_currency_eur_symbol(self) -> None:
        """Parse EUR with € symbol."""
        result = parse_currency("€100.50", "en_US")
        assert result is not None
        amount, code = result
        assert amount == Decimal("100.50")
        assert code == "EUR"

        result = parse_currency("100,50 €", "lv_LV")
        assert result is not None
        amount, code = result
        assert amount == Decimal("100.50")
        assert code == "EUR"

    def test_parse_currency_usd_symbol(self) -> None:
        """Parse USD with $ symbol (v0.7.0: requires default_currency)."""
        result = parse_currency("$1,234.56", "en_US", default_currency="USD")

        assert result is not None

        amount, code = result
        assert amount == Decimal("1234.56")
        assert code == "USD"

    def test_parse_currency_gbp_symbol(self) -> None:
        """Parse GBP with £ symbol."""
        result = parse_currency("£999.99", "en_GB")

        assert result is not None

        amount, code = result
        assert amount == Decimal("999.99")
        assert code == "GBP"

    def test_parse_currency_jpy_symbol(self) -> None:
        """Parse JPY with ¥ symbol (no decimals)."""
        result = parse_currency("¥12,345", "ja_JP")

        assert result is not None

        amount, code = result
        assert amount == Decimal("12345")
        assert code == "JPY"

    def test_parse_currency_iso_code(self) -> None:
        """Parse currency with ISO code instead of symbol."""
        result = parse_currency("USD 1,234.56", "en_US")

        assert result is not None

        amount, code = result
        assert amount == Decimal("1234.56")
        assert code == "USD"

        result = parse_currency("EUR 1.234,56", "de_DE")


        assert result is not None


        amount, code = result
        assert amount == Decimal("1234.56")
        assert code == "EUR"

    def test_parse_currency_strict_mode_no_symbol(self) -> None:
        """Strict mode raises ValueError when no currency symbol found."""
        with pytest.raises(ValueError, match="No currency symbol or code found"):
            parse_currency("1,234.56", "en_US", strict=True)

    def test_parse_currency_non_strict_mode(self) -> None:
        """Non-strict mode returns None on invalid input."""
        assert parse_currency("invalid", "en_US", strict=False) is None
        assert parse_currency("1,234.56", "en_US", strict=False) is None


class TestRoundtripCurrency:
    """Test format → parse → format roundtrip for currency."""

    def test_roundtrip_currency_en_us(self) -> None:
        """Currency roundtrip for US English."""
        from ftllexbuffer.runtime.functions import currency_format

        original_amount = Decimal("1234.56")
        formatted = currency_format(
            float(original_amount), "en-US", currency="USD", currency_display="symbol"
        )
        # v0.7.0: $ is ambiguous - specify default_currency for roundtrip
        result = parse_currency(formatted, "en_US", default_currency="USD")

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
        result = parse_currency(formatted, "lv_LV")

        assert result is not None

        parsed_amount, parsed_currency = result

        assert parsed_amount == original_amount
        assert parsed_currency == "EUR"
