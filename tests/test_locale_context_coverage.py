"""Coverage tests for LocaleContext edge cases and error paths.

Targets uncovered lines in locale_context.py:
- Unknown locale handling in __post_init__ (lines 77-78)
- Fallback to en_US in babel_locale (lines 97-100)
- Number formatting error paths (lines 175-176)
- Datetime formatting error paths (lines 257-258)
- Currency formatting error paths (lines 348-349)
"""

import logging
from datetime import UTC, datetime

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from ftllexbuffer.runtime.locale_context import LocaleContext


class TestLocaleContextUnknownLocale:
    """Test LocaleContext with unknown/invalid locales."""

    def test_unknown_locale_warns_on_init(self, caplog: pytest.LogCaptureFixture) -> None:
        """Unknown locale logs warning during initialization."""
        with caplog.at_level(logging.WARNING):
            _ = LocaleContext("xx_INVALID")

        # Should log warning about unknown locale
        assert any("Unknown locale" in record.message for record in caplog.records)
        assert any("xx_INVALID" in record.message for record in caplog.records)

    def test_unknown_locale_fallback_to_en_us(self, caplog: pytest.LogCaptureFixture) -> None:
        """Unknown locale falls back to en_US for formatting."""
        with caplog.at_level(logging.DEBUG):
            ctx = LocaleContext("xx_NONEXISTENT")
            # Access babel_locale to trigger fallback
            locale = ctx.babel_locale

        # Should fallback to en_US
        assert locale.language == "en"
        # Should log debug message about fallback
        assert any("Falling back to en_US" in record.message for record in caplog.records)

    def test_completely_invalid_locale_string(self, caplog: pytest.LogCaptureFixture) -> None:
        """Completely malformed locale string triggers fallback."""
        with caplog.at_level(logging.DEBUG):
            ctx = LocaleContext("!!!INVALID@@@")
            locale = ctx.babel_locale

        # Should still fallback gracefully
        assert locale.language == "en"

    @given(
        st.text(
            alphabet=st.characters(blacklist_categories=("Cs",)),  # type: ignore[arg-type]
            min_size=1,
            max_size=20,
        ).filter(lambda x: x not in ["en", "en_US", "en-US", "de", "de_DE", "lv", "lv_LV"])
    )
    @settings(max_examples=50)
    def test_arbitrary_locale_never_crashes(self, locale_str: str) -> None:
        """Any locale string should create context without crashing (Hypothesis)."""
        # Should never raise, might warn/debug log
        ctx = LocaleContext(locale_str)

        # Should be able to get babel_locale (might fallback)
        locale = ctx.babel_locale
        assert locale is not None

        # Should be able to format
        result = ctx.format_number(123.45)
        assert isinstance(result, str)


class TestNumberFormattingErrorPaths:
    """Test number formatting error paths."""

    def test_format_number_with_invalid_pattern_params(self) -> None:
        """Invalid fraction digits should trigger error path (lines 175-176)."""
        ctx = LocaleContext("en_US")

        # This hits the error path but may not log depending on Babel behavior
        result = ctx.format_number(123.45, minimum_fraction_digits=-1)

        # Should return some valid string (either formatted or fallback)
        assert isinstance(result, str)

    def test_format_number_value_error_path(
        self, caplog: pytest.LogCaptureFixture, monkeypatch
    ) -> None:
        """ValueError in format_number hits lines 175-176."""
        from babel import numbers as babel_numbers

        ctx = LocaleContext("en_US")

        original_format_decimal = babel_numbers.format_decimal

        def mock_format_decimal(*_args, **_kwargs):
            # Raise ValueError to hit the specific exception handler
            msg = "Invalid format pattern"
            raise ValueError(msg)

        monkeypatch.setattr(babel_numbers, "format_decimal", mock_format_decimal)

        with caplog.at_level(logging.DEBUG):
            result = ctx.format_number(123.45)

        # Should hit lines 175-176: log debug and return str(value)
        assert "123.45" in result
        assert any(
            "Number formatting failed (expected error)" in record.message
            for record in caplog.records
        )

        monkeypatch.setattr(babel_numbers, "format_decimal", original_format_decimal)

    @given(
        st.one_of(
            st.integers(min_value=-1000, max_value=-1),  # Negative fraction digits
            st.integers(min_value=1000, max_value=10000),  # Huge fraction digits
        )
    )
    @settings(max_examples=30)
    def test_format_number_extreme_fraction_digits(self, fraction_digits: int) -> None:
        """Extreme fraction digit values should not crash (Hypothesis)."""
        ctx = LocaleContext("en_US")

        # Should handle gracefully even with extreme values
        result = ctx.format_number(
            123.456,
            minimum_fraction_digits=max(0, fraction_digits),
            maximum_fraction_digits=max(0, abs(fraction_digits)),
        )
        assert isinstance(result, str)


class TestDatetimeFormattingErrorPaths:
    """Test datetime formatting error paths."""

    def test_format_datetime_value_error_path(
        self, caplog: pytest.LogCaptureFixture, monkeypatch
    ) -> None:
        """ValueError in format_datetime hits lines 257-258."""
        from babel import dates as babel_dates

        ctx = LocaleContext("en_US")
        dt = datetime(2025, 1, 1, tzinfo=UTC)

        original_format_date = babel_dates.format_date

        def mock_format_date(*_args, **_kwargs):
            # Raise ValueError to hit the specific exception handler
            msg = "Invalid date format"
            raise ValueError(msg)

        monkeypatch.setattr(babel_dates, "format_date", mock_format_date)

        with caplog.at_level(logging.DEBUG):
            result = ctx.format_datetime(dt)

        # Should return ISO format as fallback (hit lines 257-258)
        assert "2025" in result
        assert any("DateTime formatting failed" in record.message for record in caplog.records)

        monkeypatch.setattr(babel_dates, "format_date", original_format_date)

    def test_format_datetime_with_invalid_iso_string(self) -> None:
        """Invalid ISO string should return error placeholder."""
        ctx = LocaleContext("en_US")

        result = ctx.format_datetime("not-a-valid-iso-string")

        # Should return error placeholder
        assert result == "{?DATETIME}"

    @given(
        st.text(min_size=1, max_size=50).filter(
            lambda s: not s.startswith(("19", "20", "21"))  # Avoid valid ISO dates
        )
    )
    @settings(max_examples=50)
    def test_format_datetime_arbitrary_strings(self, invalid_iso: str) -> None:
        """Arbitrary strings should return error placeholder (Hypothesis)."""
        ctx = LocaleContext("en_US")

        result = ctx.format_datetime(invalid_iso)

        # Should return error placeholder for invalid ISO strings
        assert result == "{?DATETIME}"


class TestCurrencyFormattingErrorPaths:
    """Test currency formatting error paths."""

    def test_format_currency_invalid_currency_code(self, caplog: pytest.LogCaptureFixture) -> None:
        """Invalid currency code should trigger error path."""
        ctx = LocaleContext("en_US")

        with caplog.at_level(logging.DEBUG):
            result = ctx.format_currency(123.45, currency="INVALID")

        # Should return fallback format
        assert "INVALID" in result
        assert "123.45" in result
        # Babel might handle gracefully, so we just ensure we got a valid string

    def test_format_currency_type_error_path(
        self, caplog: pytest.LogCaptureFixture, monkeypatch
    ) -> None:
        """TypeError in format_currency hits lines 348-349."""
        from babel import numbers as babel_numbers

        ctx = LocaleContext("en_US")

        original_format_currency = babel_numbers.format_currency

        def mock_format_currency(*_args, **_kwargs):
            # Raise TypeError to hit the specific exception handler
            msg = "Invalid type for currency formatting"
            raise TypeError(msg)

        monkeypatch.setattr(babel_numbers, "format_currency", mock_format_currency)

        with caplog.at_level(logging.DEBUG):
            result = ctx.format_currency(123.45, currency="EUR")

        # Should return fallback format (hit lines 348-349)
        assert "EUR" in result
        assert "123.45" in result
        # Should log debug message about formatting failure
        assert any(
            "Currency formatting failed (expected error)" in record.message
            for record in caplog.records
        )

        monkeypatch.setattr(babel_numbers, "format_currency", original_format_currency)

    @given(
        st.text(
            alphabet=st.characters(min_codepoint=65, max_codepoint=90),  # A-Z
            min_size=1,
            max_size=10,
        ).filter(lambda x: x not in ["USD", "EUR", "GBP", "JPY", "CHF"])
    )
    @settings(max_examples=50)
    def test_format_currency_arbitrary_codes(self, currency_code: str) -> None:
        """Arbitrary currency codes should not crash (Hypothesis)."""
        ctx = LocaleContext("en_US")

        # Most will be invalid and trigger fallback, some might be valid
        result = ctx.format_currency(99.99, currency=currency_code)

        # Should always return a string
        assert isinstance(result, str)
        # Should contain currency code and value
        assert currency_code in result or "99.99" in result or "99,99" in result


class TestLocaleContextUnexpectedErrors:
    """Test handling of unexpected errors (coverage for broad exception handlers)."""

    def test_format_number_unexpected_error_path(
        self, caplog: pytest.LogCaptureFixture, monkeypatch
    ) -> None:
        """Unexpected error in format_number should log warning and return str(value)."""
        ctx = LocaleContext("en_US")

        # Monkey-patch babel_numbers.format_decimal to raise unexpected error
        from babel import numbers as babel_numbers

        original_format_decimal = babel_numbers.format_decimal

        def mock_format_decimal(*_args, **_kwargs):
            msg = "Unexpected platform error!"
            raise RuntimeError(msg)

        monkeypatch.setattr(babel_numbers, "format_decimal", mock_format_decimal)

        with caplog.at_level(logging.WARNING):
            result = ctx.format_number(123.45)

        # Should return str(value) as ultimate fallback
        assert "123.45" in result

        # Should log warning with exc_info
        assert any(
            "Unexpected error in format_number" in record.message
            for record in caplog.records
        )

        # Restore original
        monkeypatch.setattr(babel_numbers, "format_decimal", original_format_decimal)

    def test_format_datetime_unexpected_error_path(
        self, caplog: pytest.LogCaptureFixture, monkeypatch
    ) -> None:
        """Unexpected error in format_datetime should log warning and return ISO string."""
        ctx = LocaleContext("en_US")
        dt = datetime(2025, 1, 1, tzinfo=UTC)

        from babel import dates as babel_dates

        original_format_date = babel_dates.format_date

        def mock_format_date(*_args, **_kwargs):
            msg = "Unexpected platform error!"
            raise RuntimeError(msg)

        monkeypatch.setattr(babel_dates, "format_date", mock_format_date)

        with caplog.at_level(logging.WARNING):
            result = ctx.format_datetime(dt)

        # Should return ISO format as fallback
        assert "2025" in result

        # Should log warning
        assert any(
            "Unexpected error in format_datetime" in record.message
            for record in caplog.records
        )

        monkeypatch.setattr(babel_dates, "format_date", original_format_date)

    def test_format_currency_unexpected_error_path(
        self, caplog: pytest.LogCaptureFixture, monkeypatch
    ) -> None:
        """Unexpected error in format_currency should log warning and return fallback."""
        ctx = LocaleContext("en_US")

        from babel import numbers as babel_numbers

        original_format_currency = babel_numbers.format_currency

        def mock_format_currency(*_args, **_kwargs):
            msg = "Unexpected platform error!"
            raise RuntimeError(msg)

        monkeypatch.setattr(babel_numbers, "format_currency", mock_format_currency)

        with caplog.at_level(logging.WARNING):
            result = ctx.format_currency(123.45, currency="EUR")

        # Should return fallback format
        assert "EUR" in result
        assert "123.45" in result

        # Should log warning
        assert any(
            "Unexpected error in format_currency" in record.message
            for record in caplog.records
        )

        monkeypatch.setattr(babel_numbers, "format_currency", original_format_currency)
