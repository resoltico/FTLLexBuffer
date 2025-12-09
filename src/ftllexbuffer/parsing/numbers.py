"""Number parsing functions with locale awareness.

v0.8.0 BREAKING CHANGE: API aligned with formatting functions.
- parse_number() returns tuple[float, list[FluentParseError]]
- parse_decimal() returns tuple[Decimal, list[FluentParseError]]
- Removed `strict` parameter - functions NEVER raise, errors returned in list
- Consistent with format_*() "never raise" philosophy

Thread-safe. Uses Babel for CLDR-compliant parsing.

Python 3.13+.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from babel import Locale, UnknownLocaleError
from babel.numbers import NumberFormatError
from babel.numbers import parse_decimal as babel_parse_decimal

from ftllexbuffer.diagnostics import FluentParseError
from ftllexbuffer.diagnostics.templates import ErrorTemplate


def parse_number(
    value: str,
    locale_code: str,
) -> tuple[float | None, list[FluentParseError]]:
    """Parse locale-aware number string to float.

    v0.8.0 BREAKING CHANGE: Returns tuple instead of raising exceptions.
    v0.9.0 BREAKING CHANGE: Returns None on failure instead of 0.0 sentinel.

    Args:
        value: Number string (e.g., "1 234,56" for lv_LV)
        locale_code: BCP 47 locale identifier

    Returns:
        Tuple of (result, errors):
        - result: Parsed float, or None if parsing failed
        - errors: List of FluentParseError (empty on success)

    Examples:
        >>> result, errors = parse_number("1,234.5", "en_US")
        >>> result
        1234.5
        >>> errors
        []

        >>> result, errors = parse_number("1 234,5", "lv_LV")
        >>> result
        1234.5

        >>> result, errors = parse_number("invalid", "en_US")
        >>> result
        None
        >>> len(errors)
        1
        >>> errors[0].parse_type
        'number'

    Thread Safety:
        Thread-safe. Uses Babel (no global state).
    """
    errors: list[FluentParseError] = []

    try:
        # v0.9.0: Normalize locale format (en-US → en_US) for Babel
        normalized_locale = locale_code.replace("-", "_")
        locale = Locale.parse(normalized_locale)
    except (UnknownLocaleError, ValueError):
        diagnostic = ErrorTemplate.parse_locale_unknown(locale_code)
        errors.append(
            FluentParseError(
                diagnostic,
                input_value=value,
                locale_code=locale_code,
                parse_type="number",
            )
        )
        return (None, errors)

    try:
        parsed = babel_parse_decimal(value, locale=locale)
        return (float(parsed), errors)
    except (NumberFormatError, InvalidOperation, ValueError, AttributeError, TypeError) as e:
        diagnostic = ErrorTemplate.parse_number_failed(value, locale_code, str(e))
        errors.append(
            FluentParseError(
                diagnostic,
                input_value=value,
                locale_code=locale_code,
                parse_type="number",
            )
        )
        return (None, errors)


def parse_decimal(
    value: str,
    locale_code: str,
) -> tuple[Decimal | None, list[FluentParseError]]:
    """Parse locale-aware number string to Decimal (financial precision).

    v0.8.0 BREAKING CHANGE: Returns tuple instead of raising exceptions.
    v0.9.0 BREAKING CHANGE: Returns None on failure instead of Decimal("0") sentinel.

    Use this for financial calculations where float precision loss
    would cause rounding errors.

    Args:
        value: Number string (e.g., "1 234,56" for lv_LV)
        locale_code: BCP 47 locale identifier

    Returns:
        Tuple of (result, errors):
        - result: Parsed Decimal, or None if parsing failed
        - errors: List of FluentParseError (empty on success)

    Examples:
        >>> result, errors = parse_decimal("1,234.56", "en_US")
        >>> result
        Decimal('1234.56')
        >>> errors
        []

        >>> result, errors = parse_decimal("1 234,56", "lv_LV")
        >>> result
        Decimal('1234.56')

        >>> result, errors = parse_decimal("invalid", "en_US")
        >>> result
        None
        >>> len(errors)
        1

    Financial Use Cases:
        # VAT calculations (no float precision loss)
        >>> amount, errors = parse_decimal("100,50", "lv_LV")
        >>> if amount is not None:
        ...     vat = amount * Decimal("0.21")
        ...     print(vat)
        21.105

    Thread Safety:
        Thread-safe. Uses Babel (no global state).
    """
    errors: list[FluentParseError] = []

    try:
        # v0.9.0: Normalize locale format (en-US → en_US) for Babel
        normalized_locale = locale_code.replace("-", "_")
        locale = Locale.parse(normalized_locale)
    except (UnknownLocaleError, ValueError):
        diagnostic = ErrorTemplate.parse_locale_unknown(locale_code)
        errors.append(
            FluentParseError(
                diagnostic,
                input_value=value,
                locale_code=locale_code,
                parse_type="decimal",
            )
        )
        return (None, errors)

    try:
        return (babel_parse_decimal(value, locale=locale), errors)
    except (NumberFormatError, InvalidOperation, ValueError, AttributeError, TypeError) as e:
        diagnostic = ErrorTemplate.parse_decimal_failed(value, locale_code, str(e))
        errors.append(
            FluentParseError(
                diagnostic,
                input_value=value,
                locale_code=locale_code,
                parse_type="decimal",
            )
        )
        return (None, errors)
