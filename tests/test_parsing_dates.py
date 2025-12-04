"""Tests for date and datetime parsing functions.

Validates parse_date() and parse_datetime() across multiple locales.
"""

from datetime import UTC, date, datetime

import pytest

from ftllexbuffer.parsing import parse_date, parse_datetime


class TestParseDate:
    """Test parse_date() function."""

    def test_parse_date_us_format(self) -> None:
        """Parse US date format (MM/DD/YYYY)."""
        result = parse_date("1/28/2025", "en_US")
        assert result == date(2025, 1, 28)

    def test_parse_date_european_format(self) -> None:
        """Parse European date format (DD.MM.YYYY)."""
        result = parse_date("28.01.2025", "lv_LV")
        assert result == date(2025, 1, 28)

        result = parse_date("28.01.2025", "de_DE")
        assert result == date(2025, 1, 28)

    def test_parse_date_iso_format(self) -> None:
        """Parse ISO 8601 date format."""
        result = parse_date("2025-01-28", "en_US")
        assert result == date(2025, 1, 28)

    def test_parse_date_strict_mode(self) -> None:
        """Strict mode raises ValueError on invalid input."""
        with pytest.raises(ValueError, match="Failed to parse date"):
            parse_date("invalid", "en_US", strict=True)

    def test_parse_date_non_strict_mode(self) -> None:
        """Non-strict mode returns None on invalid input."""
        assert parse_date("invalid", "en_US", strict=False) is None


class TestParseDatetime:
    """Test parse_datetime() function."""

    def test_parse_datetime_us_format(self) -> None:
        """Parse US datetime format."""
        result = parse_datetime("1/28/2025 14:30", "en_US")
        assert result == datetime(2025, 1, 28, 14, 30)

    def test_parse_datetime_european_format(self) -> None:
        """Parse European datetime format."""
        result = parse_datetime("28.01.2025 14:30", "lv_LV")
        assert result == datetime(2025, 1, 28, 14, 30)

    def test_parse_datetime_with_timezone(self) -> None:
        """Parse datetime and apply timezone."""
        result = parse_datetime("2025-01-28 14:30", "en_US", tzinfo=UTC)
        assert result == datetime(2025, 1, 28, 14, 30, tzinfo=UTC)

    def test_parse_datetime_strict_mode(self) -> None:
        """Strict mode raises ValueError on invalid input."""
        with pytest.raises(ValueError, match="Failed to parse datetime"):
            parse_datetime("invalid", "en_US", strict=True)

    def test_parse_datetime_non_strict_mode(self) -> None:
        """Non-strict mode returns None on invalid input."""
        assert parse_datetime("invalid", "en_US", strict=False) is None
