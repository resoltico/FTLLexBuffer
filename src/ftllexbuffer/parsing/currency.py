"""Currency parsing with locale awareness.

Provides parse_currency() for extracting both numeric value and currency code
from locale-formatted currency strings.

Thread-safe. Uses Babel for currency symbol mapping and number parsing.

Python 3.13+.
"""

from __future__ import annotations

import re
from decimal import Decimal

from babel import Locale
from babel.numbers import NumberFormatError, parse_decimal

# Currency symbol to ISO code mapping
# Extended mapping for common currency symbols
_CURRENCY_SYMBOL_MAP: dict[str, str] = {
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
    "¥": "JPY",
    "₹": "INR",
    "₽": "RUB",
    "¢": "USD",  # Cents (US)
    "₡": "CRC",  # Costa Rican colón
    "₦": "NGN",  # Nigerian naira
    "₧": "ESP",  # Spanish peseta (historical)
    "₨": "INR",  # Rupee variants
    "₩": "KRW",  # South Korean won
    "₪": "ILS",  # Israeli new shekel
    "₫": "VND",  # Vietnamese dong
    "₱": "PHP",  # Philippine peso
    "₴": "UAH",  # Ukrainian hryvnia
    "₵": "GHS",  # Ghanaian cedi
    "₸": "KZT",  # Kazakhstani tenge
    "₺": "TRY",  # Turkish lira
    "₼": "AZN",  # Azerbaijani manat
    "₾": "GEL",  # Georgian lari
}


def parse_currency(
    value: str,
    locale_code: str,
    *,
    strict: bool = True,
) -> tuple[Decimal, str] | None:
    """Parse locale-aware currency string to (amount, currency_code).

    Extracts both numeric value and currency code from formatted string.

    Args:
        value: Currency string (e.g., "100,50 €" for lv_LV)
        locale_code: BCP 47 locale identifier
        strict: Raise exception on parse failure (default: True)

    Returns:
        Tuple of (amount, currency_code) where:
        - amount: Decimal for precision
        - currency_code: ISO 4217 code (e.g., "EUR", "USD")
        Or None if strict=False and parsing fails

    Raises:
        ValueError: If parsing fails and strict=True

    Examples:
        >>> parse_currency("€100.50", "en_US")
        (Decimal('100.50'), 'EUR')
        >>> parse_currency("100,50 €", "lv_LV")
        (Decimal('100.50'), 'EUR')
        >>> parse_currency("$1,234.56", "en_US")
        (Decimal('1234.56'), 'USD')
        >>> parse_currency("¥12,345", "ja_JP")
        (Decimal('12345'), 'JPY')
        >>> parse_currency("USD 1,234.56", "en_US")
        (Decimal('1234.56'), 'USD')
        >>> parse_currency("invalid", "en_US", strict=False)
        None

    Thread Safety:
        Thread-safe. Uses Babel (no global state).
    """
    try:
        locale = Locale.parse(locale_code)

        # Extract currency symbol or code
        # Look for currency symbols (€, $, etc.) or ISO codes (EUR, USD, etc.)
        currency_pattern = r"([€$£¥₹₽¢₡₦₧₨₩₪₫₱₴₵₸₺₼₾]|[A-Z]{3})"
        match = re.search(currency_pattern, value)

        if not match:
            if strict:
                msg = f"No currency symbol or code found in '{value}'"
                raise ValueError(msg)
            return None

        currency_str = match.group(1)

        # Map symbol to ISO code if it's a symbol
        if len(currency_str) == 1:
            # It's a symbol
            currency_code = _CURRENCY_SYMBOL_MAP.get(currency_str)
            if currency_code is None:
                if strict:
                    msg = f"Unknown currency symbol '{currency_str}' in '{value}'"
                    raise ValueError(msg)
                return None
        else:
            # It's already an ISO code
            currency_code = currency_str

        # Remove currency symbol/code to extract number
        number_str = value.replace(currency_str, "").strip()

        # Parse number using Babel
        try:
            amount = parse_decimal(number_str, locale=locale)
        except NumberFormatError as e:
            if strict:
                msg = f"Failed to parse amount '{number_str}' from '{value}': {e}"
                raise ValueError(msg) from e
            return None

        return (amount, currency_code)

    except (ValueError, TypeError) as e:
        if strict:
            if not isinstance(e, ValueError):
                msg = f"Failed to parse currency '{value}' for locale '{locale_code}': {e}"
                raise ValueError(msg) from e
            raise
        return None
