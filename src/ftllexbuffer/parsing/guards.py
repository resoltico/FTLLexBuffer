"""Type guard functions for parsing result type narrowing.

Provides TypeIs-based type guards for mypy to narrow parsing result types safely.
Particularly useful with mypy --strict for financial applications.

Python 3.13+ with TypeIs support (PEP 742).

Example:
    >>> from ftllexbuffer.parsing import parse_decimal
    >>> from ftllexbuffer.parsing.guards import is_valid_decimal
    >>> parsed = parse_decimal("1,234.56", "en_US")
    >>> if is_valid_decimal(parsed):
    ...     # mypy knows parsed is Decimal (not Decimal | None)
    ...     amount = parsed.quantize(Decimal("0.01"))
"""

from __future__ import annotations

import math
from datetime import date, datetime
from decimal import Decimal
from typing import TypeIs

__all__ = [
    "is_valid_currency",
    "is_valid_date",
    "is_valid_datetime",
    "is_valid_decimal",
    "is_valid_number",
]


def is_valid_decimal(value: Decimal | None) -> TypeIs[Decimal]:
    """Type guard: Check if parsed decimal is valid (not None, not NaN/Infinity).

    Validates that parse_decimal() result is safe for financial calculations.
    Rejects None, NaN, and Infinity values.

    Args:
        value: Result from parse_decimal()

    Returns:
        True if value is a finite Decimal, False otherwise

    Example:
        >>> from ftllexbuffer.parsing import parse_decimal
        >>> parsed = parse_decimal("1,234.56", "en_US")
        >>> if is_valid_decimal(parsed):
        ...     # Type-safe: mypy knows parsed is Decimal
        ...     total = parsed * Decimal("1.21")  # Add VAT
    """
    return value is not None and value.is_finite()


def is_valid_number(value: float | None) -> TypeIs[float]:
    """Type guard: Check if parsed number is valid (not None, not NaN/Infinity).

    Validates that parse_number() result is safe for calculations.
    Rejects None, NaN, and Infinity values.

    Args:
        value: Result from parse_number()

    Returns:
        True if value is a finite float, False otherwise

    Example:
        >>> from ftllexbuffer.parsing import parse_number
        >>> parsed = parse_number("1,234.56", "en_US")
        >>> if is_valid_number(parsed):
        ...     # Type-safe: mypy knows parsed is float
        ...     total = parsed * 1.21
    """
    return value is not None and math.isfinite(value)


def is_valid_currency(
    value: tuple[Decimal, str] | None,
) -> TypeIs[tuple[Decimal, str]]:
    """Type guard: Check if parsed currency is valid (not None, finite amount).

    Validates that parse_currency() result is safe for financial calculations.
    Rejects None and verifies amount is finite.

    Args:
        value: Result from parse_currency()

    Returns:
        True if value is (Decimal, str) with finite amount, False otherwise

    Example:
        >>> from ftllexbuffer.parsing import parse_currency
        >>> parsed = parse_currency("€1,234.56", "en_US")
        >>> if is_valid_currency(parsed):
        ...     # Type-safe: mypy knows parsed is tuple[Decimal, str]
        ...     amount, currency = parsed
        ...     total = amount * Decimal("1.21")
    """
    return value is not None and value[0].is_finite()


def is_valid_date(value: date | None) -> TypeIs[date]:
    """Type guard: Check if parsed date is valid (not None).

    Validates that parse_date() result is safe for use.

    Args:
        value: Result from parse_date()

    Returns:
        True if value is a date object, False otherwise

    Example:
        >>> from ftllexbuffer.parsing import parse_date
        >>> parsed = parse_date("2025-01-28", "en_US")
        >>> if is_valid_date(parsed):
        ...     # Type-safe: mypy knows parsed is date
        ...     year = parsed.year
    """
    return value is not None


def is_valid_datetime(value: datetime | None) -> TypeIs[datetime]:
    """Type guard: Check if parsed datetime is valid (not None).

    Validates that parse_datetime() result is safe for use.

    Args:
        value: Result from parse_datetime()

    Returns:
        True if value is a datetime object, False otherwise

    Example:
        >>> from ftllexbuffer.parsing import parse_datetime
        >>> parsed = parse_datetime("2025-01-28 14:30", "en_US")
        >>> if is_valid_datetime(parsed):
        ...     # Type-safe: mypy knows parsed is datetime
        ...     timestamp = parsed.timestamp()
    """
    return value is not None
