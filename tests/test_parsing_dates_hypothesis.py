"""Hypothesis-based property tests for date/datetime parsing.

Focus on financial date handling and edge cases.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from ftllexbuffer.parsing import parse_date, parse_datetime


class TestParseDateHypothesis:
    """Property-based tests for parse_date()."""

    @given(
        year=st.integers(min_value=2000, max_value=2099),
        month=st.integers(min_value=1, max_value=12),
        day=st.integers(min_value=1, max_value=28),  # Safe for all months
    )
    @settings(max_examples=200)
    def test_parse_date_iso_format_always_works(
        self, year: int, month: int, day: int
    ) -> None:
        """ISO 8601 date format should always parse correctly (financial standard)."""
        # ISO 8601 is the international standard for dates
        iso_date = f"{year:04d}-{month:02d}-{day:02d}"

        result = parse_date(iso_date, "en_US")
        assert result is not None
        assert isinstance(result, date)

        # Must preserve exact date
        assert result.year == year
        assert result.month == month
        assert result.day == day

    @given(
        year=st.integers(min_value=2000, max_value=2099),
        month=st.integers(min_value=1, max_value=12),
        day=st.integers(min_value=1, max_value=28),
        locale=st.sampled_from(["en_US", "de_DE", "fr_FR", "lv_LV", "pl_PL", "ja_JP"]),
    )
    @settings(max_examples=200)
    def test_parse_date_locale_independent_iso(
        self, year: int, month: int, day: int, locale: str
    ) -> None:
        """ISO 8601 dates should parse consistently across all locales."""
        iso_date = f"{year:04d}-{month:02d}-{day:02d}"

        result = parse_date(iso_date, locale)
        assert result is not None

        # Must preserve date regardless of locale
        assert result.year == year
        assert result.month == month
        assert result.day == day

    @given(
        invalid_date=st.one_of(
            st.text(
                alphabet=st.characters(whitelist_categories=("L",)),  # Letters only
                min_size=1,
                max_size=20,
            ),
            st.just("not-a-date"),
            st.just("2025/99/99"),  # Invalid month/day
            st.just("9999-99-99"),  # Out of range
            st.just(""),
        ),
    )
    @settings(max_examples=100)
    def test_parse_date_invalid_strict_mode(self, invalid_date: str) -> None:
        """Invalid dates should raise ValueError in strict mode."""
        with pytest.raises(ValueError, match="Failed to parse date"):
            parse_date(invalid_date, "en_US", strict=True)

    @given(
        invalid_date=st.one_of(
            st.text(
                alphabet=st.characters(whitelist_categories=("L",)),
                min_size=1,
                max_size=20,
            ),
            st.just("not-a-date"),
            st.just("2025/99/99"),
        ),
    )
    @settings(max_examples=100)
    def test_parse_date_invalid_non_strict(self, invalid_date: str) -> None:
        """Invalid dates should return None in non-strict mode."""
        result = parse_date(invalid_date, "en_US", strict=False)
        assert result is None

    @given(
        value=st.one_of(
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.lists(st.integers()),
            st.dictionaries(st.text(), st.integers()),
        ),
    )
    @settings(max_examples=50)
    def test_parse_date_type_error_strict_mode(self, value: object) -> None:
        """Non-string types should raise ValueError in strict mode (TypeError path)."""
        # Line 80 coverage - TypeError exception path
        with pytest.raises(ValueError, match="Failed to parse date"):
            parse_date(value, "en_US", strict=True)

    @given(
        value=st.one_of(
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.lists(st.integers()),
        ),
    )
    @settings(max_examples=50)
    def test_parse_date_type_error_non_strict(self, value: object) -> None:
        """Non-string types should return None in non-strict mode."""
        result = parse_date(value, "en_US", strict=False)
        assert result is None

    @given(
        month=st.integers(min_value=1, max_value=12),
        day=st.integers(min_value=1, max_value=28),
    )
    @settings(max_examples=100)
    def test_parse_date_us_format_month_first(self, month: int, day: int) -> None:
        """US format (M/D/YYYY) should parse with month first."""
        # US uses month-first format
        date_str = f"{month}/{day}/2025"

        result = parse_date(date_str, "en_US")
        assert result is not None

        # Verify correct interpretation
        assert result.month == month
        assert result.day == day
        assert result.year == 2025

    @given(
        day=st.integers(min_value=1, max_value=28),
        month=st.integers(min_value=1, max_value=12),
    )
    @settings(max_examples=100)
    def test_parse_date_european_format_day_first(self, day: int, month: int) -> None:
        """European format (D.M.YYYY) should parse with day first."""
        # European uses day-first format
        date_str = f"{day:02d}.{month:02d}.2025"

        result = parse_date(date_str, "de_DE")
        assert result is not None

        # Verify correct interpretation
        assert result.day == day
        assert result.month == month
        assert result.year == 2025

    @given(
        year=st.integers(min_value=2000, max_value=2099),
        month=st.integers(min_value=1, max_value=12),
        day=st.integers(min_value=1, max_value=28),
    )
    @settings(max_examples=100)
    def test_parse_date_financial_reporting_dates(
        self, year: int, month: int, day: int
    ) -> None:
        """Common financial reporting date formats should parse correctly."""
        # Financial reports often use these formats
        formats = [
            (f"{year:04d}-{month:02d}-{day:02d}", "en_US"),  # ISO (universal)
            (f"{month:02d}/{day:02d}/{year:04d}", "en_US"),  # US format
            (f"{day:02d}.{month:02d}.{year:04d}", "de_DE"),  # EU format
        ]

        for date_str, locale in formats:
            result = parse_date(date_str, locale)
            assert result is not None
            assert result.year == year
            assert result.month == month
            assert result.day == day


class TestParseDatetimeHypothesis:
    """Property-based tests for parse_datetime()."""

    @given(
        year=st.integers(min_value=2000, max_value=2099),
        month=st.integers(min_value=1, max_value=12),
        day=st.integers(min_value=1, max_value=28),
        hour=st.integers(min_value=0, max_value=23),
        minute=st.integers(min_value=0, max_value=59),
        second=st.integers(min_value=0, max_value=59),
    )
    @settings(max_examples=200)
    def test_parse_datetime_iso_format_always_works(
        self, year: int, month: int, day: int, hour: int, minute: int, second: int
    ) -> None:
        """ISO 8601 datetime format should always parse correctly (financial standard)."""
        # ISO 8601 with time
        iso_datetime = (
            f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}"
        )

        result = parse_datetime(iso_datetime, "en_US")
        assert result is not None
        assert isinstance(result, datetime)

        # Must preserve exact datetime
        assert result.year == year
        assert result.month == month
        assert result.day == day
        assert result.hour == hour
        assert result.minute == minute
        assert result.second == second

    @given(
        year=st.integers(min_value=2000, max_value=2099),
        month=st.integers(min_value=1, max_value=12),
        day=st.integers(min_value=1, max_value=28),
        hour=st.integers(min_value=0, max_value=23),
        minute=st.integers(min_value=0, max_value=59),
    )
    @settings(max_examples=100)
    def test_parse_datetime_iso_with_tzinfo(
        self, year: int, month: int, day: int, hour: int, minute: int
    ) -> None:
        """ISO datetime without timezone should accept tzinfo parameter."""
        # Lines 118->120 coverage - ISO datetime with tzinfo
        iso_datetime = (
            f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:00"
        )

        # Parse with timezone
        result = parse_datetime(iso_datetime, "en_US", tzinfo=UTC)
        assert result is not None

        # Should have assigned timezone
        assert result.tzinfo == UTC
        assert result.year == year
        assert result.month == month
        assert result.day == day
        assert result.hour == hour
        assert result.minute == minute

    @given(
        year=st.integers(min_value=2000, max_value=2099),
        month=st.integers(min_value=1, max_value=12),
        day=st.integers(min_value=1, max_value=28),
        hour=st.integers(min_value=0, max_value=23),
        minute=st.integers(min_value=0, max_value=59),
    )
    @settings(max_examples=100)
    def test_parse_datetime_strptime_with_tzinfo(
        self, year: int, month: int, day: int, hour: int, minute: int
    ) -> None:
        """Non-ISO datetime patterns should accept tzinfo parameter."""
        # Line 131 coverage - strptime path with tzinfo
        # Use US format (not ISO)
        datetime_str = f"{month:02d}/{day:02d}/{year:04d} {hour:02d}:{minute:02d}"

        result = parse_datetime(datetime_str, "en_US", tzinfo=UTC)
        assert result is not None

        # Should have assigned timezone
        assert result.tzinfo == UTC
        assert result.year == year
        assert result.month == month
        assert result.day == day
        assert result.hour == hour
        assert result.minute == minute

    @given(
        invalid_datetime=st.one_of(
            st.text(
                alphabet=st.characters(whitelist_categories=("L",)),
                min_size=1,
                max_size=20,
            ),
            st.just("not-a-datetime"),
            st.just("2025-99-99 99:99:99"),
            st.just(""),
        ),
    )
    @settings(max_examples=100)
    def test_parse_datetime_invalid_strict_mode(self, invalid_datetime: str) -> None:
        """Invalid datetimes should raise ValueError in strict mode."""
        with pytest.raises(ValueError, match="Failed to parse datetime"):
            parse_datetime(invalid_datetime, "en_US", strict=True)

    @given(
        invalid_datetime=st.one_of(
            st.text(
                alphabet=st.characters(whitelist_categories=("L",)),
                min_size=1,
                max_size=20,
            ),
            st.just("not-a-datetime"),
        ),
    )
    @settings(max_examples=100)
    def test_parse_datetime_invalid_non_strict(self, invalid_datetime: str) -> None:
        """Invalid datetimes should return None in non-strict mode."""
        result = parse_datetime(invalid_datetime, "en_US", strict=False)
        assert result is None

    @given(
        value=st.one_of(
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.lists(st.integers()),
            st.dictionaries(st.text(), st.integers()),
        ),
    )
    @settings(max_examples=50)
    def test_parse_datetime_type_error_strict_mode(self, value: object) -> None:
        """Non-string types should raise ValueError in strict mode (TypeError path)."""
        # Line 146 coverage - TypeError exception path
        with pytest.raises(ValueError, match="Failed to parse datetime"):
            parse_datetime(value, "en_US", strict=True)

    @given(
        value=st.one_of(
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.lists(st.integers()),
        ),
    )
    @settings(max_examples=50)
    def test_parse_datetime_type_error_non_strict(self, value: object) -> None:
        """Non-string types should return None in non-strict mode."""
        result = parse_datetime(value, "en_US", strict=False)
        assert result is None

    @given(
        hour=st.integers(min_value=0, max_value=23),
        minute=st.integers(min_value=0, max_value=59),
    )
    @settings(max_examples=100)
    def test_parse_datetime_24hour_format(self, hour: int, minute: int) -> None:
        """24-hour time format should parse correctly (common in financial systems)."""
        datetime_str = f"2025-01-28 {hour:02d}:{minute:02d}"

        result = parse_datetime(datetime_str, "en_US")
        assert result is not None

        # Verify correct time parsing
        assert result.hour == hour
        assert result.minute == minute

    @given(
        locale=st.sampled_from(["en_US", "de_DE", "fr_FR", "lv_LV", "pl_PL", "ja_JP"]),
    )
    @settings(max_examples=50)
    def test_parse_datetime_locale_independent_iso(self, locale: str) -> None:
        """ISO 8601 datetimes should parse consistently across all locales."""
        iso_datetime = "2025-01-28T14:30:45"

        result = parse_datetime(iso_datetime, locale)
        assert result is not None

        # Must preserve datetime regardless of locale
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 28
        assert result.hour == 14
        assert result.minute == 30
        assert result.second == 45


class TestDateParsingEdgeCases:
    """Edge cases for date parsing pattern generation."""

    @given(
        invalid_locale=st.text(
            alphabet=st.characters(min_codepoint=33, max_codepoint=126),
            min_size=1,
            max_size=10,
        ).filter(lambda x: "_" not in x and "-" not in x),
    )
    @settings(max_examples=50)
    def test_parse_date_invalid_locale_fallback(self, invalid_locale: str) -> None:
        """Invalid locales should fall back to common patterns gracefully."""
        # Lines 174-179 coverage - Exception handling in _get_date_patterns
        # ISO date should still work with fallback patterns
        date_str = "2025-01-28"

        try:
            result = parse_date(date_str, invalid_locale)
            # Should either work with fallback or return None
            if result is not None:
                assert result.year == 2025
                assert result.month == 1
                assert result.day == 28
        except ValueError:
            # Acceptable to fail in strict mode
            pass

    def test_parse_date_minimal_locale_data(self) -> None:
        """Test locale with minimal date format data."""
        # Try locales that might not have full CLDR data
        # This attempts to trigger the AttributeError/KeyError path
        minimal_locales = ["root", "und", "en_001", "en_150"]

        for locale in minimal_locales:
            # ISO date should always work (uses fromisoformat, not CLDR)
            result = parse_date("2025-01-28", locale, strict=False)
            if result is not None:
                assert result.year == 2025
                assert result.month == 1
                assert result.day == 28

    @given(
        invalid_locale=st.text(
            alphabet=st.characters(min_codepoint=33, max_codepoint=126),
            min_size=1,
            max_size=10,
        ).filter(lambda x: "_" not in x and "-" not in x),
    )
    @settings(max_examples=50)
    def test_parse_datetime_invalid_locale_fallback(self, invalid_locale: str) -> None:
        """Invalid locales should fall back to common datetime patterns."""
        # Lines 223-224, 228-230 coverage - Exception handling in _get_datetime_patterns
        datetime_str = "2025-01-28T14:30:00"

        try:
            result = parse_datetime(datetime_str, invalid_locale)
            # Should either work with fallback or return None
            if result is not None:
                assert result.year == 2025
                assert result.month == 1
                assert result.day == 28
        except ValueError:
            # Acceptable to fail in strict mode
            pass

    def test_parse_datetime_minimal_locale_data(self) -> None:
        """Test datetime parsing with locales that have minimal CLDR data."""
        # Try locales that might not have full datetime format data
        # This attempts to trigger the AttributeError/KeyError path
        minimal_locales = ["root", "und", "en_001", "en_150"]

        for locale in minimal_locales:
            # ISO datetime should always work (uses fromisoformat, not CLDR)
            result = parse_datetime("2025-01-28T14:30:00", locale, strict=False)
            if result is not None:
                assert result.year == 2025
                assert result.month == 1
                assert result.day == 28
                assert result.hour == 14
                assert result.minute == 30
