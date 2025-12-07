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

# Ambiguous currency symbols shared by multiple currencies
# These symbols require explicit default_currency parameter
_AMBIGUOUS_SYMBOLS: set[str] = {
    "$",   # USD, CAD, AUD, SGD, HKD, NZD, MXN, etc.
    "¢",   # USD, CAD cents variants
    "₨",   # INR, PKR, NPR, LKR (rupee variants)
    "₱",   # PHP, CUP (peso variants)
    "kr",  # SEK, NOK, DKK, ISK (krona/krone)
}

# Currency symbol to ISO code mapping (for unambiguous symbols)
# Ambiguous symbols will require default_currency parameter
_CURRENCY_SYMBOL_MAP: dict[str, str] = {
    # Ambiguous symbols (default mappings - will raise error without default_currency)
    "$": "USD",    # AMBIGUOUS: Also CAD, AUD, SGD, HKD, NZD, MXN
    "¢": "USD",    # AMBIGUOUS: Also CAD (cents)
    "₨": "INR",    # AMBIGUOUS: Also PKR, NPR, LKR (rupees)
    "₱": "PHP",    # AMBIGUOUS: Also CUP (pesos)

    # Unambiguous symbols
    "€": "EUR",
    "£": "GBP",
    "¥": "JPY",    # Also CNY, but ¥ typically means JPY
    "₹": "INR",    # Official Indian rupee symbol
    "₽": "RUB",
    "₡": "CRC",    # Costa Rican colón
    "₦": "NGN",    # Nigerian naira
    "₧": "ESP",    # Spanish peseta (historical)
    "₩": "KRW",    # South Korean won
    "₪": "ILS",    # Israeli new shekel
    "₫": "VND",    # Vietnamese dong
    "₴": "UAH",    # Ukrainian hryvnia
    "₵": "GHS",    # Ghanaian cedi
    "₸": "KZT",    # Kazakhstani tenge
    "₺": "TRY",    # Turkish lira
    "₼": "AZN",    # Azerbaijani manat
    "₾": "GEL",    # Georgian lari
}

# Locale to default currency mapping (for infer_from_locale=True)
_LOCALE_TO_CURRENCY: dict[str, str] = {
    "en_US": "USD",
    "en_CA": "CAD",
    "en_AU": "AUD",
    "en_NZ": "NZD",
    "en_SG": "SGD",
    "en_HK": "HKD",
    "en_GB": "GBP",
    "de_DE": "EUR",
    "fr_FR": "EUR",
    "es_ES": "EUR",
    "it_IT": "EUR",
    "nl_NL": "EUR",
    "pt_PT": "EUR",
    "lv_LV": "EUR",
    "ja_JP": "JPY",
    "zh_CN": "CNY",
    "zh_TW": "TWD",
    "ko_KR": "KRW",
    "ru_RU": "RUB",
    "in_IN": "INR",
    "pl_PL": "PLN",
    "mx_MX": "MXN",
}


def parse_currency(
    value: str,
    locale_code: str,
    *,
    strict: bool = True,
    default_currency: str | None = None,
    infer_from_locale: bool = False,
) -> tuple[Decimal, str] | None:
    """Parse locale-aware currency string to (amount, currency_code).

    Extracts both numeric value and currency code from formatted string.

    v0.7.0 BREAKING CHANGE: Ambiguous currency symbols ($, ¢, ₨, ₱, kr) now
    require explicit default_currency or infer_from_locale=True. This prevents
    silent misidentification in multi-currency applications.

    Args:
        value: Currency string (e.g., "100,50 €" for lv_LV, "$100" with default_currency)
        locale_code: BCP 47 locale identifier
        strict: Raise exception on parse failure (default: True)
        default_currency: ISO 4217 code for ambiguous symbols (e.g., "CAD" for "$")
        infer_from_locale: Infer currency from locale if symbol is ambiguous

    Returns:
        Tuple of (amount, currency_code) where:
        - amount: Decimal for precision
        - currency_code: ISO 4217 code (e.g., "EUR", "USD")
        Or None if strict=False and parsing fails

    Raises:
        ValueError: If parsing fails, ambiguous symbol without default, or strict=True

    Examples:
        >>> parse_currency("€100.50", "en_US")  # Unambiguous symbol
        (Decimal('100.50'), 'EUR')
        >>> parse_currency("100,50 €", "lv_LV")  # Unambiguous symbol
        (Decimal('100.50'), 'EUR')
        >>> parse_currency("USD 1,234.56", "en_US")  # ISO code - always unambiguous
        (Decimal('1234.56'), 'USD')

        >>> # v0.7.0 BREAKING: Ambiguous symbols require explicit currency
        >>> parse_currency("$100", "en_US", default_currency="USD")
        (Decimal('100'), 'USD')
        >>> parse_currency("$100", "en_CA", default_currency="CAD")
        (Decimal('100'), 'CAD')
        >>> parse_currency("$100", "en_CA", infer_from_locale=True)
        (Decimal('100'), 'CAD')

        >>> # v0.7.0 BREAKING: Ambiguous symbols without default raise error
        >>> parse_currency("$100", "en_US")  # Raises ValueError
        ValueError: Ambiguous currency symbol '$' - use default_currency or ISO code

    Note:
        Ambiguous symbols: $ (USD/CAD/AUD/etc), ¢, ₨, ₱, kr
        Always use ISO codes (USD, CAD, EUR) for unambiguous parsing.

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
            # It's a symbol - check if ambiguous
            if currency_str in _AMBIGUOUS_SYMBOLS:
                # v0.7.0 BREAKING: Ambiguous symbols require explicit handling
                if default_currency:
                    currency_code = default_currency
                elif infer_from_locale:
                    inferred_currency = _LOCALE_TO_CURRENCY.get(locale_code)
                    if inferred_currency is None:
                        if strict:
                            msg = (
                                f"Ambiguous currency symbol '{currency_str}' and "
                                f"no currency mapping for locale '{locale_code}'. "
                                f"Use default_currency parameter or ISO code (USD, CAD, EUR)"
                            )
                            raise ValueError(msg)
                        return None
                    currency_code = inferred_currency
                else:
                    # No default provided - raise error for ambiguous symbol
                    if strict:
                        msg = (
                            f"Ambiguous currency symbol '{currency_str}' in '{value}'. "
                            f"Symbol '{currency_str}' is used by multiple currencies. "
                            f"Specify default_currency parameter, use infer_from_locale=True, "
                            f"or use ISO code (USD, CAD, EUR) for unambiguous parsing."
                        )
                        raise ValueError(msg)
                    return None
            else:
                # Unambiguous symbol - use mapping
                mapped_currency = _CURRENCY_SYMBOL_MAP.get(currency_str)
                if mapped_currency is None:
                    if strict:
                        msg = f"Unknown currency symbol '{currency_str}' in '{value}'"
                        raise ValueError(msg)
                    return None
                currency_code = mapped_currency
        else:
            # It's already an ISO code - always unambiguous
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
