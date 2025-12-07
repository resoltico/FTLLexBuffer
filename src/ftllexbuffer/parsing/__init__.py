"""Bi-directional localization: Parse locale-aware display strings back to Python types.

This module provides the inverse operations to ftllexbuffer.runtime.functions:
- Formatting: Python data → locale-aware display string
- Parsing: Locale-aware display string → Python data

All parsing functions are thread-safe and use Babel for CLDR-compliant parsing.

Public API:
    Parsing Functions:
        parse_number - Parse locale-aware number to float
        parse_decimal - Parse locale-aware number to Decimal (financial precision)
        parse_date - Parse locale-aware date string to date object
        parse_datetime - Parse locale-aware datetime string to datetime object
        parse_currency - Parse locale-aware currency string to (Decimal, currency_code)

    Type Guards (v0.7.0+):
        is_valid_decimal - TypeIs guard for Decimal | None → Decimal
        is_valid_number - TypeIs guard for float | None → float
        is_valid_currency - TypeIs guard for tuple | None → tuple[Decimal, str]
        is_valid_date - TypeIs guard for date | None → date
        is_valid_datetime - TypeIs guard for datetime | None → datetime

Example:
    >>> from ftllexbuffer.parsing import parse_decimal, is_valid_decimal
    >>> amount = parse_decimal("1 234,56", "lv_LV")
    >>> if is_valid_decimal(amount):
    ...     # mypy knows amount is Decimal (not Decimal | None)
    ...     total = amount.quantize(Decimal("0.01"))

Python 3.13+. Uses Babel CLDR patterns + stdlib for all parsing.
"""

from __future__ import annotations

from .currency import parse_currency
from .dates import parse_date, parse_datetime
from .guards import (
    is_valid_currency,
    is_valid_date,
    is_valid_datetime,
    is_valid_decimal,
    is_valid_number,
)
from .numbers import parse_decimal, parse_number

__all__ = [
    # Type guards (v0.7.0+)
    "is_valid_currency",
    "is_valid_date",
    "is_valid_datetime",
    "is_valid_decimal",
    "is_valid_number",
    # Parsing functions
    "parse_currency",
    "parse_date",
    "parse_datetime",
    "parse_decimal",
    "parse_number",
]
