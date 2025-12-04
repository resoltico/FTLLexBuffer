"""Tests for number parsing functions.

Validates parse_number() and parse_decimal() across multiple locales.
"""

from decimal import Decimal

import pytest

from ftllexbuffer.parsing import parse_decimal, parse_number


class TestParseNumber:
    """Test parse_number() function."""

    def test_parse_number_en_us(self) -> None:
        """Parse US English number format."""
        assert parse_number("1,234.5", "en_US") == 1234.5
        assert parse_number("1234.5", "en_US") == 1234.5
        assert parse_number("0.5", "en_US") == 0.5

    def test_parse_number_lv_lv(self) -> None:
        """Parse Latvian number format."""
        assert parse_number("1 234,5", "lv_LV") == 1234.5
        assert parse_number("1234,5", "lv_LV") == 1234.5
        assert parse_number("0,5", "lv_LV") == 0.5

    def test_parse_number_de_de(self) -> None:
        """Parse German number format."""
        assert parse_number("1.234,5", "de_DE") == 1234.5
        assert parse_number("1234,5", "de_DE") == 1234.5
        assert parse_number("0,5", "de_DE") == 0.5

    def test_parse_number_strict_mode(self) -> None:
        """Strict mode raises ValueError on invalid input."""
        with pytest.raises(ValueError, match="Failed to parse number"):
            parse_number("invalid", "en_US", strict=True)

    def test_parse_number_non_strict_mode(self) -> None:
        """Non-strict mode returns None on invalid input."""
        assert parse_number("invalid", "en_US", strict=False) is None
        assert parse_number("", "en_US", strict=False) is None


class TestParseDecimal:
    """Test parse_decimal() function."""

    def test_parse_decimal_en_us(self) -> None:
        """Parse US English decimal format."""
        assert parse_decimal("1,234.56", "en_US") == Decimal("1234.56")
        assert parse_decimal("0.01", "en_US") == Decimal("0.01")

    def test_parse_decimal_lv_lv(self) -> None:
        """Parse Latvian decimal format."""
        assert parse_decimal("1 234,56", "lv_LV") == Decimal("1234.56")
        assert parse_decimal("0,01", "lv_LV") == Decimal("0.01")

    def test_parse_decimal_de_de(self) -> None:
        """Parse German decimal format."""
        assert parse_decimal("1.234,56", "de_DE") == Decimal("1234.56")
        assert parse_decimal("0,01", "de_DE") == Decimal("0.01")

    def test_parse_decimal_financial_precision(self) -> None:
        """Decimal preserves financial precision."""
        amount = parse_decimal("100,50", "lv_LV")
        assert amount is not None
        vat = amount * Decimal("0.21")
        assert vat == Decimal("21.105")  # Exact, no float precision loss

    def test_parse_decimal_strict_mode(self) -> None:
        """Strict mode raises ValueError on invalid input."""
        with pytest.raises(ValueError, match="Failed to parse decimal"):
            parse_decimal("invalid", "en_US", strict=True)

    def test_parse_decimal_non_strict_mode(self) -> None:
        """Non-strict mode returns None on invalid input."""
        assert parse_decimal("invalid", "en_US", strict=False) is None


class TestRoundtrip:
    """Test format → parse → format roundtrip preservation."""

    def test_roundtrip_number_en_us(self) -> None:
        """Number roundtrip for US English."""
        from ftllexbuffer.runtime.functions import number_format

        original = 1234.5
        formatted = number_format(original, "en-US", use_grouping=True)
        parsed = parse_number(formatted, "en_US")
        assert parsed == original

    def test_roundtrip_number_lv_lv(self) -> None:
        """Number roundtrip for Latvian."""
        from ftllexbuffer.runtime.functions import number_format

        original = 1234.5
        formatted = number_format(original, "lv-LV", use_grouping=True)
        parsed = parse_number(formatted, "lv_LV")
        assert parsed == original

    def test_roundtrip_decimal_precision(self) -> None:
        """Decimal roundtrip preserves financial precision."""
        from ftllexbuffer.runtime.functions import number_format

        original = Decimal("1234.56")
        formatted = number_format(
            float(original), "lv-LV", minimum_fraction_digits=2, use_grouping=True
        )
        parsed = parse_decimal(formatted, "lv_LV")
        assert parsed == original
