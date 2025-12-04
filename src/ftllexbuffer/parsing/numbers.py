"""Number parsing functions with locale awareness.

Provides parse_number() and parse_decimal() for converting locale-formatted
number strings back to Python numeric types.

Thread-safe. Uses Babel for CLDR-compliant parsing.

Python 3.13+.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from babel import Locale
from babel.numbers import NumberFormatError
from babel.numbers import parse_decimal as babel_parse_decimal


def parse_number(
    value: str,
    locale_code: str,
    *,
    strict: bool = True,
) -> float | None:
    """Parse locale-aware number string to float.

    Args:
        value: Number string (e.g., "1 234,56" for lv_LV)
        locale_code: BCP 47 locale identifier
        strict: Raise exception on parse failure (default: True)

    Returns:
        Parsed number as float, or None if strict=False and parsing fails

    Raises:
        ValueError: If parsing fails and strict=True

    Examples:
        >>> parse_number("1,234.5", "en_US")
        1234.5
        >>> parse_number("1 234,5", "lv_LV")
        1234.5
        >>> parse_number("1.234,5", "de_DE")
        1234.5
        >>> parse_number("invalid", "en_US", strict=False)
        None

    Thread Safety:
        Thread-safe. Uses Babel (no global state).
    """
    try:
        locale = Locale.parse(locale_code)
        # Use parse_decimal internally, convert to float
        parsed = babel_parse_decimal(value, locale=locale)
        return float(parsed)
    except (NumberFormatError, InvalidOperation, ValueError, AttributeError, TypeError) as e:
        if strict:
            msg = f"Failed to parse number '{value}' for locale '{locale_code}': {e}"
            raise ValueError(msg) from e
        return None


def parse_decimal(
    value: str,
    locale_code: str,
    *,
    strict: bool = True,
) -> Decimal | None:
    """Parse locale-aware number string to Decimal (financial precision).

    Use this for financial calculations where float precision loss
    would cause rounding errors.

    Args:
        value: Number string (e.g., "1 234,56" for lv_LV)
        locale_code: BCP 47 locale identifier
        strict: Raise exception on parse failure (default: True)

    Returns:
        Parsed number as Decimal, or None if strict=False and parsing fails

    Raises:
        ValueError: If parsing fails and strict=True

    Examples:
        >>> parse_decimal("1,234.56", "en_US")
        Decimal('1234.56')
        >>> parse_decimal("1 234,56", "lv_LV")
        Decimal('1234.56')
        >>> parse_decimal("invalid", "en_US", strict=False)
        None

    Financial Use Cases:
        # VAT calculations (no float precision loss)
        >>> amount = parse_decimal("100,50", "lv_LV")
        >>> vat = amount * Decimal("0.21")
        >>> vat
        Decimal('21.105')

        # Invoice totals
        >>> total = parse_decimal("12 345,67", "lv_LV")
        >>> total
        Decimal('12345.67')

    Thread Safety:
        Thread-safe. Uses Babel (no global state).
    """
    try:
        locale = Locale.parse(locale_code)
        return babel_parse_decimal(value, locale=locale)
    except (NumberFormatError, InvalidOperation, ValueError, AttributeError, TypeError) as e:
        if strict:
            msg = f"Failed to parse decimal '{value}' for locale '{locale_code}': {e}"
            raise ValueError(msg) from e
        return None
