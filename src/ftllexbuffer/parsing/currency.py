"""Currency parsing with locale awareness.

v0.8.0 BREAKING CHANGE: API aligned with formatting functions.
- parse_currency() returns tuple[tuple[Decimal, str] | None, list[FluentParseError]]
- Removed `strict` parameter - function NEVER raises, errors returned in list
- Consistent with format_*() "never raise" philosophy

Thread-safe. Uses Babel for currency symbol mapping and number parsing.

Python 3.13+.
"""

from __future__ import annotations

import re
from decimal import Decimal

from babel import Locale, UnknownLocaleError
from babel.numbers import NumberFormatError, parse_decimal

from ftllexbuffer.diagnostics import FluentParseError
from ftllexbuffer.diagnostics.templates import ErrorTemplate

# Ambiguous currency symbols shared by multiple currencies
# These symbols require explicit default_currency parameter
_AMBIGUOUS_SYMBOLS: set[str] = {
    "$",   # USD, CAD, AUD, SGD, HKD, NZD, MXN, etc.
    "kr",  # SEK, NOK, DKK, ISK (krona/krone)
}

# Currency symbol to ISO code mapping (for unambiguous symbols)
# Ambiguous symbols will require default_currency parameter
_CURRENCY_SYMBOL_MAP: dict[str, str] = {
    # Ambiguous symbols (default mappings - will fail without default_currency)
    "$": "USD",    # AMBIGUOUS: Also CAD, AUD, SGD, HKD, NZD, MXN

    # Unambiguous symbols
    "€": "EUR",
    "£": "GBP",
    "¥": "JPY",    # Also CNY, but typically means JPY
    "¢": "USD",    # US cents
    "₨": "INR",    # Rupee (also PKR, NPR, LKR)
    "₱": "PHP",    # Philippine peso (also CUP)
    "₹": "INR",    # Official Indian rupee symbol
    "₽": "RUB",
    "₡": "CRC",    # Costa Rican colon
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
    default_currency: str | None = None,
    infer_from_locale: bool = False,
) -> tuple[tuple[Decimal, str] | None, list[FluentParseError]]:
    """Parse locale-aware currency string to (amount, currency_code).

    v0.8.0 BREAKING CHANGE: Returns tuple[tuple[Decimal, str] | None, list[FluentParseError]].
    No longer raises exceptions. Errors are returned in the list.
    The `strict` parameter has been removed.

    Extracts both numeric value and currency code from formatted string.

    Ambiguous currency symbols ($, kr) require explicit default_currency
    or infer_from_locale=True. This prevents silent misidentification
    in multi-currency applications.

    Args:
        value: Currency string (e.g., "100,50 EUR" for lv_LV, "$100" with default_currency)
        locale_code: BCP 47 locale identifier
        default_currency: ISO 4217 code for ambiguous symbols (e.g., "CAD" for "$")
        infer_from_locale: Infer currency from locale if symbol is ambiguous

    Returns:
        Tuple of (result, errors):
        - result: Tuple of (amount, currency_code), or None if parsing failed
        - errors: List of FluentParseError (empty on success)

    Examples:
        >>> result, errors = parse_currency("EUR100.50", "en_US")  # Unambiguous symbol
        >>> result
        (Decimal('100.50'), 'EUR')
        >>> errors
        []

        >>> result, errors = parse_currency("100,50 EUR", "lv_LV")  # Unambiguous symbol
        >>> result
        (Decimal('100.50'), 'EUR')

        >>> result, errors = parse_currency("USD 1,234.56", "en_US")  # ISO code
        >>> result
        (Decimal('1234.56'), 'USD')

        >>> # Ambiguous symbols require explicit currency
        >>> result, errors = parse_currency("$100", "en_US", default_currency="USD")
        >>> result
        (Decimal('100'), 'USD')

        >>> result, errors = parse_currency("$100", "en_CA", default_currency="CAD")
        >>> result
        (Decimal('100'), 'CAD')

        >>> result, errors = parse_currency("$100", "en_CA", infer_from_locale=True)
        >>> result
        (Decimal('100'), 'CAD')

        >>> # Ambiguous symbols without default return error
        >>> result, errors = parse_currency("$100", "en_US")
        >>> result is None
        True
        >>> len(errors)
        1

    Note:
        Ambiguous symbols: $ (USD/CAD/AUD/etc), kr (SEK/NOK/DKK/ISK)
        Always use ISO codes (USD, CAD, EUR) for unambiguous parsing.

    Thread Safety:
        Thread-safe. Uses Babel (no global state).
    """
    errors: list[FluentParseError] = []

    # Type check: value must be string (runtime defense for untyped callers)
    if not isinstance(value, str):
        diagnostic = ErrorTemplate.parse_currency_failed(  # type: ignore[unreachable]
            str(value), locale_code, f"Expected string, got {type(value).__name__}"
        )
        errors.append(FluentParseError(
            diagnostic,
            input_value=str(value),
            locale_code=locale_code,
            parse_type="currency",
        ))
        return (None, errors)

    try:
        locale = Locale.parse(locale_code)
    except (UnknownLocaleError, ValueError):
        diagnostic = ErrorTemplate.parse_locale_unknown(locale_code)
        errors.append(FluentParseError(
            diagnostic,
            input_value=value,
            locale_code=locale_code,
            parse_type="currency",
        ))
        return (None, errors)

    # Extract currency symbol or code
    # Look for currency symbols or ISO codes (EUR, USD, etc.)
    currency_pattern = r"([€$£¥₹₽¢₡₦₧₨₩₪₫₱₴₵₸₺₼₾]|kr|[A-Z]{3})"
    match = re.search(currency_pattern, value)

    if not match:
        diagnostic = ErrorTemplate.parse_currency_failed(
            value, locale_code, "No currency symbol or code found"
        )
        errors.append(FluentParseError(
            diagnostic,
            input_value=value,
            locale_code=locale_code,
            parse_type="currency",
        ))
        return (None, errors)

    currency_str = match.group(1)

    # Map symbol to ISO code if it's a symbol
    if len(currency_str) <= 2:  # Symbol (1 char) or "kr" (2 chars)
        # Check if ambiguous
        if currency_str in _AMBIGUOUS_SYMBOLS:
            # Ambiguous symbols require explicit handling
            if default_currency:
                currency_code = default_currency
            elif infer_from_locale:
                inferred_currency = _LOCALE_TO_CURRENCY.get(locale_code)
                if inferred_currency is None:
                    diagnostic = ErrorTemplate.parse_currency_ambiguous(currency_str, value)
                    errors.append(FluentParseError(
                        diagnostic,
                        input_value=value,
                        locale_code=locale_code,
                        parse_type="currency",
                    ))
                    return (None, errors)
                currency_code = inferred_currency
            else:
                # No default provided - error for ambiguous symbol
                diagnostic = ErrorTemplate.parse_currency_ambiguous(currency_str, value)
                errors.append(FluentParseError(
                    diagnostic,
                    input_value=value,
                    locale_code=locale_code,
                    parse_type="currency",
                ))
                return (None, errors)
        else:
            # Unambiguous symbol - use mapping
            mapped_currency = _CURRENCY_SYMBOL_MAP.get(currency_str)
            if mapped_currency is None:
                diagnostic = ErrorTemplate.parse_currency_symbol_unknown(currency_str, value)
                errors.append(FluentParseError(
                    diagnostic,
                    input_value=value,
                    locale_code=locale_code,
                    parse_type="currency",
                ))
                return (None, errors)
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
        diagnostic = ErrorTemplate.parse_amount_invalid(number_str, value, str(e))
        errors.append(FluentParseError(
            diagnostic,
            input_value=value,
            locale_code=locale_code,
            parse_type="currency",
        ))
        return (None, errors)

    return ((amount, currency_code), errors)
