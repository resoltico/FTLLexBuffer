"""Bi-directional localization: Parse locale-aware display strings back to Python types.

v0.8.0 BREAKING CHANGE: All parsing functions now return tuple[result, list[FluentParseError]].
- Functions NEVER raise exceptions - errors are returned in the list
- Removed `strict` parameter from all functions
- Consistent with format_*() "never raise" philosophy

This module provides the inverse operations to ftllexbuffer.runtime.functions:
- Formatting: Python data -> locale-aware display string
- Parsing: Locale-aware display string -> Python data

All parsing functions are thread-safe and use Babel for CLDR-compliant parsing.

Public API:
    Parsing Functions (v0.8.0 - new return types):
        parse_number - Returns tuple[float, list[FluentParseError]]
        parse_decimal - Returns tuple[Decimal, list[FluentParseError]]
        parse_date - Returns tuple[date | None, list[FluentParseError]]
        parse_datetime - Returns tuple[datetime | None, list[FluentParseError]]
        parse_currency - Returns tuple[tuple[Decimal, str] | None, list[FluentParseError]]

    Type Guards (v0.8.0 - updated for new API):
        has_parse_errors - Check if error list is non-empty
        is_valid_decimal - TypeIs guard for finite Decimal
        is_valid_number - TypeIs guard for finite float
        is_valid_currency - TypeIs guard for tuple[Decimal, str] (not None)
        is_valid_date - TypeIs guard for date (not None)
        is_valid_datetime - TypeIs guard for datetime (not None)

Example:
    >>> from ftllexbuffer.parsing import parse_decimal, has_parse_errors, is_valid_decimal
    >>> result, errors = parse_decimal("1 234,56", "lv_LV")
    >>> if not has_parse_errors(errors) and is_valid_decimal(result):
    ...     # mypy knows result is finite Decimal
    ...     total = result.quantize(Decimal("0.01"))

Python 3.13+. Uses Babel CLDR patterns + stdlib for all parsing.
"""

from __future__ import annotations

from .currency import parse_currency
from .dates import parse_date, parse_datetime
from .guards import (
    has_parse_errors,
    is_valid_currency,
    is_valid_date,
    is_valid_datetime,
    is_valid_decimal,
    is_valid_number,
)
from .numbers import parse_decimal, parse_number

__all__ = [
    # Type guards (v0.8.0 - updated)
    "has_parse_errors",
    "is_valid_currency",
    "is_valid_date",
    "is_valid_datetime",
    "is_valid_decimal",
    "is_valid_number",
    # Parsing functions (v0.8.0 - new return types)
    "parse_currency",
    "parse_date",
    "parse_datetime",
    "parse_decimal",
    "parse_number",
]
