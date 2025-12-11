"""Comprehensive coverage tests for runtime/locale_context.py.

Targets remaining uncovered lines:
- Line 54: LocaleValidationError.__str__()
- Lines 164-165: LocaleContext.create_or_raise() ValueError path
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from ftllexbuffer.runtime.locale_context import LocaleContext, LocaleValidationError

# ============================================================================
# LINE 54: LocaleValidationError.__str__()
# ============================================================================


class TestLocaleValidationErrorString:
    """Test LocaleValidationError.__str__() (line 54)."""

    def test_locale_validation_error_str(self) -> None:
        """Verify LocaleValidationError.__str__() formats correctly (line 54)."""
        error = LocaleValidationError(
            locale_code="invalid-locale",
            error_message="Test error message",
        )

        # Call __str__ method (line 54)
        result = str(error)

        assert "Invalid locale 'invalid-locale'" in result
        assert "Test error message" in result

    def test_locale_validation_error_str_with_special_chars(self) -> None:
        """Test LocaleValidationError.__str__() with special characters."""
        error = LocaleValidationError(
            locale_code="zh-Hans-CN",
            error_message="Contains special: <>[]{}",
        )

        result = str(error)

        assert "zh-Hans-CN" in result
        assert "special: <>[]" in result

    def test_locale_validation_error_str_empty_message(self) -> None:
        """Test LocaleValidationError.__str__() with empty error message."""
        error = LocaleValidationError(
            locale_code="test",
            error_message="",
        )

        result = str(error)

        assert "Invalid locale 'test'" in result


# ============================================================================
# LINES 164-165: LocaleContext.create_or_raise() ValueError Path
# ============================================================================


class TestLocaleContextCreateOrRaiseErrorPath:
    """Test LocaleContext.create_or_raise() error handling (lines 164-165)."""

    def test_create_or_raise_with_validation_error(self) -> None:
        """Test create_or_raise() raises ValueError when create() returns error (lines 164-165).

        Since LocaleContext.create() always returns LocaleContext (it fallsback to en_US),
        we need to mock it to return LocaleValidationError.
        """
        # Create a mock validation error
        mock_error = LocaleValidationError(
            locale_code="mock-invalid",
            error_message="Mocked validation error for testing",
        )

        # Mock LocaleContext.create to return LocaleValidationError
        with (
            patch.object(LocaleContext, "create", return_value=mock_error),
            pytest.raises(ValueError, match=r"Invalid locale 'mock-invalid'") as exc_info,
        ):
            LocaleContext.create_or_raise("mock-invalid")

        # Verify the ValueError message contains the error details (line 165)
        assert "Invalid locale 'mock-invalid'" in str(exc_info.value)
        assert "Mocked validation error" in str(exc_info.value)

    def test_create_or_raise_with_different_error_messages(self) -> None:
        """Test create_or_raise() with various error messages."""
        test_cases = [
            ("bad-locale", "Parse error"),
            ("xyz", "Unknown locale identifier"),
            ("", "Empty locale code"),
        ]

        for locale_code, error_msg in test_cases:
            mock_error = LocaleValidationError(
                locale_code=locale_code,
                error_message=error_msg,
            )

            with (
                patch.object(LocaleContext, "create", return_value=mock_error),
                pytest.raises(ValueError, match=r"Invalid locale") as exc_info,
            ):
                LocaleContext.create_or_raise(locale_code)

            # Check assertions outside the raises block
            assert locale_code in str(exc_info.value)
            assert error_msg in str(exc_info.value)

    def test_create_or_raise_success_path_returns_context(self) -> None:
        """Verify create_or_raise() returns LocaleContext on success."""
        # This tests the normal path where LocaleContext is returned
        ctx = LocaleContext.create_or_raise("en_US")

        assert isinstance(ctx, LocaleContext)
        assert ctx.locale_code == "en_US"


# ============================================================================
# Integration Tests
# ============================================================================


class TestLocaleValidationErrorIntegration:
    """Integration tests for LocaleValidationError with create_or_raise()."""

    def test_error_str_called_in_create_or_raise(self) -> None:
        """Verify __str__ is called when create_or_raise() raises ValueError."""
        mock_error = LocaleValidationError(
            locale_code="test-locale",
            error_message="Integration test error",
        )

        # Mock create() to return error
        with (
            patch.object(LocaleContext, "create", return_value=mock_error),
            pytest.raises(ValueError, match=r"Invalid locale 'test-locale'") as exc_info,
        ):
            LocaleContext.create_or_raise("test-locale")

        # The error message should be the result of str(mock_error)
        error_message = str(exc_info.value)
        # This confirms line 54 was executed via line 165: raise ValueError(str(err))
        assert "Invalid locale 'test-locale'" in error_message
        assert "Integration test error" in error_message

    def test_locale_validation_error_repr(self) -> None:
        """Test LocaleValidationError can be represented properly."""
        error = LocaleValidationError(
            locale_code="repr-test",
            error_message="Test repr",
        )

        # Verify repr works (uses default dataclass repr)
        repr_str = repr(error)
        assert "LocaleValidationError" in repr_str
        assert "repr-test" in repr_str
        assert "Test repr" in repr_str

    def test_locale_validation_error_equality(self) -> None:
        """Test LocaleValidationError equality comparison."""
        error1 = LocaleValidationError(
            locale_code="test",
            error_message="Same",
        )
        error2 = LocaleValidationError(
            locale_code="test",
            error_message="Same",
        )
        error3 = LocaleValidationError(
            locale_code="different",
            error_message="Same",
        )

        # Dataclass should provide __eq__
        assert error1 == error2
        assert error1 != error3
