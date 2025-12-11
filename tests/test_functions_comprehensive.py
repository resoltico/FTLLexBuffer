"""Comprehensive property-based tests for runtime.functions module.

Tests error handling and fallback behavior for NUMBER, DATETIME, and CURRENCY functions.

"""

from datetime import UTC, datetime
from unittest.mock import patch

from hypothesis import given
from hypothesis import strategies as st

from ftllexbuffer.runtime.functions import (
    FUNCTION_REGISTRY,
    currency_format,
    datetime_format,
    number_format,
)
from ftllexbuffer.runtime.locale_context import LocaleValidationError


class TestNumberFormatErrorHandling:
    """Tests for number_format error handling and fallback behavior."""

    def test_number_format_with_locale_validation_error(self) -> None:
        """Verify number_format handles LocaleValidationError gracefully (lines 98-102)."""
        # Mock LocaleContext.create to return LocaleValidationError
        error = LocaleValidationError(
            locale_code="invalid-locale",
            error_message="Test error",
        )

        with patch("ftllexbuffer.runtime.functions.LocaleContext.create", return_value=error):
            result = number_format(1234.5, "invalid-locale")
            # Should return string representation of value as fallback
            assert result == "1234.5"

    @given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))
    def test_number_format_error_fallback_preserves_value(self, value: float) -> None:
        """Property: Error fallback returns str(value) for any finite float."""
        error = LocaleValidationError(
            locale_code="bad-locale",
            error_message="Mocked error",
        )

        with patch("ftllexbuffer.runtime.functions.LocaleContext.create", return_value=error):
            result = number_format(value, "bad-locale")
            assert result == str(value)

    def test_number_format_error_fallback_with_pattern(self) -> None:
        """Verify error fallback ignores pattern parameter."""
        error = LocaleValidationError(
            locale_code="xx-INVALID",
            error_message="Invalid locale format",
        )

        with patch("ftllexbuffer.runtime.functions.LocaleContext.create", return_value=error):
            result = number_format(
                42.0,
                "xx-INVALID",
                pattern="#,##0.00",
                minimum_fraction_digits=2,
            )
            # Should return simple str() fallback
            assert result == "42.0"

    def test_number_format_success_case_basic(self) -> None:
        """Verify number_format works correctly in success case."""
        result = number_format(1234.5, "en-US", minimum_fraction_digits=2)
        # Should format with locale-specific formatting
        assert "1" in result
        assert "234" in result

    def test_number_format_success_with_grouping(self) -> None:
        """Verify number_format with grouping enabled."""
        result = number_format(1000000, "en-US", use_grouping=True)
        # Should have thousands separators
        assert "," in result or " " in result


class TestDatetimeFormatErrorHandling:
    """Tests for datetime_format error handling and fallback behavior."""

    def test_datetime_format_with_locale_validation_error_datetime_input(self) -> None:
        """Verify datetime_format handles LocaleValidationError with datetime input."""
        dt = datetime(2025, 10, 27, 14, 30, tzinfo=UTC)
        error = LocaleValidationError(
            locale_code="invalid-locale",
            error_message="Test error",
        )

        with patch("ftllexbuffer.runtime.functions.LocaleContext.create", return_value=error):
            result = datetime_format(dt, "invalid-locale")
            # Should return ISO format as fallback
            assert result == dt.isoformat()
            assert "2025-10-27" in result
            assert "14:30" in result

    def test_datetime_format_with_locale_validation_error_string_input(self) -> None:
        """Verify datetime_format handles LocaleValidationError with string input (line 175)."""
        dt_string = "2025-10-27T14:30:00+00:00"
        error = LocaleValidationError(
            locale_code="bad-locale",
            error_message="Test error",
        )

        with patch("ftllexbuffer.runtime.functions.LocaleContext.create", return_value=error):
            result = datetime_format(dt_string, "bad-locale")
            # Should return str() of input as fallback
            assert result == dt_string

    @given(st.datetimes(timezones=st.just(UTC)))
    def test_datetime_format_error_fallback_returns_isoformat(self, dt: datetime) -> None:
        """Property: Error fallback returns dt.isoformat() for datetime inputs."""
        error = LocaleValidationError(
            locale_code="xx-XX",
            error_message="Mocked error",
        )

        with patch("ftllexbuffer.runtime.functions.LocaleContext.create", return_value=error):
            result = datetime_format(dt, "xx-XX")
            assert result == dt.isoformat()

    def test_datetime_format_error_fallback_with_pattern(self) -> None:
        """Verify error fallback ignores pattern parameter."""
        dt = datetime(2025, 10, 27, tzinfo=UTC)
        error = LocaleValidationError(
            locale_code="invalid",
            error_message="Invalid",
        )

        with patch("ftllexbuffer.runtime.functions.LocaleContext.create", return_value=error):
            result = datetime_format(dt, "invalid", pattern="yyyy-MM-dd")
            # Should return ISO format fallback, ignoring pattern
            assert result == dt.isoformat()
            assert "2025-10-27" in result

    def test_datetime_format_success_case_basic(self) -> None:
        """Verify datetime_format works correctly in success case."""
        dt = datetime(2025, 10, 27, tzinfo=UTC)
        result = datetime_format(dt, "en-US", date_style="short")
        # Should format with locale-specific formatting
        assert "10" in result
        assert "27" in result

    def test_datetime_format_success_with_time_style(self) -> None:
        """Verify datetime_format with both date and time styles."""
        dt = datetime(2025, 10, 27, 14, 30, tzinfo=UTC)
        result = datetime_format(dt, "en-US", date_style="medium", time_style="short")
        # Should include both date and time
        assert len(result) > 0


class TestCurrencyFormatErrorHandling:
    """Tests for currency_format error handling and fallback behavior."""

    def test_currency_format_with_locale_validation_error(self) -> None:
        """Verify currency_format handles LocaleValidationError gracefully (lines 236-240)."""
        error = LocaleValidationError(
            locale_code="invalid-locale",
            error_message="Test error",
        )

        with patch("ftllexbuffer.runtime.functions.LocaleContext.create", return_value=error):
            result = currency_format(123.45, "invalid-locale", currency="EUR")
            # Should return "{currency} {value}" as fallback
            assert result == "EUR 123.45"

    @given(
        st.floats(allow_nan=False, allow_infinity=False, min_value=0, max_value=1e10),
        st.sampled_from(["USD", "EUR", "GBP", "JPY", "CHF"]),
    )
    def test_currency_format_error_fallback_format(self, value: float, currency: str) -> None:
        """Property: Error fallback returns '{currency} {value}' format."""
        error = LocaleValidationError(
            locale_code="bad",
            error_message="Mocked",
        )

        with patch("ftllexbuffer.runtime.functions.LocaleContext.create", return_value=error):
            result = currency_format(value, "bad", currency=currency)
            assert result == f"{currency} {value}"
            assert currency in result
            assert str(value) in result

    def test_currency_format_error_fallback_ignores_display_style(self) -> None:
        """Verify error fallback ignores currency_display parameter."""
        error = LocaleValidationError(
            locale_code="xx-INVALID",
            error_message="Invalid",
        )

        with patch("ftllexbuffer.runtime.functions.LocaleContext.create", return_value=error):
            result = currency_format(
                100.0,
                "xx-INVALID",
                currency="EUR",
                currency_display="name",
            )
            # Should return simple "{currency} {value}" fallback
            assert result == "EUR 100.0"

    def test_currency_format_success_case_basic(self) -> None:
        """Verify currency_format works correctly in success case."""
        result = currency_format(123.45, "en-US", currency="USD")
        # Should format with currency symbol or code
        assert "123" in result

    def test_currency_format_success_with_symbol_display(self) -> None:
        """Verify currency_format with symbol display."""
        result = currency_format(100, "en-US", currency="EUR", currency_display="symbol")
        # Should include currency representation
        assert len(result) > 0


class TestFunctionRegistryIntegration:
    """Tests for FUNCTION_REGISTRY integration."""

    def test_function_registry_contains_number(self) -> None:
        """Verify FUNCTION_REGISTRY contains NUMBER function."""
        assert "NUMBER" in FUNCTION_REGISTRY
        assert FUNCTION_REGISTRY.has_function("NUMBER")

    def test_function_registry_contains_datetime(self) -> None:
        """Verify FUNCTION_REGISTRY contains DATETIME function."""
        assert "DATETIME" in FUNCTION_REGISTRY
        assert FUNCTION_REGISTRY.has_function("DATETIME")

    def test_function_registry_contains_currency(self) -> None:
        """Verify FUNCTION_REGISTRY contains CURRENCY function."""
        assert "CURRENCY" in FUNCTION_REGISTRY
        assert FUNCTION_REGISTRY.has_function("CURRENCY")

    def test_function_registry_count(self) -> None:
        """Verify FUNCTION_REGISTRY has exactly 3 built-in functions."""
        assert len(FUNCTION_REGISTRY) == 3

    def test_function_registry_list_functions(self) -> None:
        """Verify FUNCTION_REGISTRY.list_functions returns all built-ins."""
        functions = FUNCTION_REGISTRY.list_functions()
        assert "NUMBER" in functions
        assert "DATETIME" in functions
        assert "CURRENCY" in functions

    def test_number_function_signature_in_registry(self) -> None:
        """Verify NUMBER function has correct signature in registry."""
        sig = FUNCTION_REGISTRY.get_function_info("NUMBER")
        assert sig is not None
        assert sig.python_name == "number_format"
        assert sig.ftl_name == "NUMBER"
        # Should have camelCase parameter mappings
        assert "minimumFractionDigits" in sig.param_mapping
        assert "maximumFractionDigits" in sig.param_mapping
        assert "useGrouping" in sig.param_mapping

    def test_datetime_function_signature_in_registry(self) -> None:
        """Verify DATETIME function has correct signature in registry."""
        sig = FUNCTION_REGISTRY.get_function_info("DATETIME")
        assert sig is not None
        assert sig.python_name == "datetime_format"
        assert sig.ftl_name == "DATETIME"
        # Should have camelCase parameter mappings
        assert "dateStyle" in sig.param_mapping
        assert "timeStyle" in sig.param_mapping

    def test_currency_function_signature_in_registry(self) -> None:
        """Verify CURRENCY function has correct signature in registry."""
        sig = FUNCTION_REGISTRY.get_function_info("CURRENCY")
        assert sig is not None
        assert sig.python_name == "currency_format"
        assert sig.ftl_name == "CURRENCY"
        # Should have camelCase parameter mappings
        assert "currencyDisplay" in sig.param_mapping
