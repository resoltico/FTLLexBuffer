"""Bi-directional localization: Parse locale-aware display strings back to Python types.

This module provides the inverse operations to ftllexbuffer.runtime.functions:
- Formatting: Python data → locale-aware display string
- Parsing: Locale-aware display string → Python data

All parsing functions are thread-safe and use Babel for CLDR-compliant parsing.

Public API:
    parse_number - Parse locale-aware number to float
    parse_decimal - Parse locale-aware number to Decimal (financial precision)
    parse_date - Parse locale-aware date string to date object
    parse_datetime - Parse locale-aware datetime string to datetime object
    parse_currency - Parse locale-aware currency string to (Decimal, currency_code)

Example:
    >>> from ftllexbuffer.parsing import parse_decimal
    >>> amount = parse_decimal("1 234,56", "lv_LV")
    >>> amount
    Decimal('1234.56')

Python 3.13+. Uses Babel CLDR patterns + stdlib for all parsing.
"""

from __future__ import annotations

from .currency import parse_currency
from .dates import parse_date, parse_datetime
from .numbers import parse_decimal, parse_number

__all__ = [
    "parse_currency",
    "parse_date",
    "parse_datetime",
    "parse_decimal",
    "parse_number",
]
