"""Type guard functions for parsing result type narrowing.

v0.8.0 BREAKING CHANGE: Type guards updated for new tuple return types.
- All parse_* functions now return tuple[result, list[FluentParseError]]
- Type guards now check the result component of the tuple
- has_parse_errors() added to check error presence

Provides TypeIs-based type guards for mypy to narrow parsing result types safely.
Particularly useful with mypy --strict for financial applications.

Python 3.13+ with TypeIs support (PEP 742).

Example:
    >>> from ftllexbuffer.parsing import parse_decimal
    >>> from ftllexbuffer.parsing.guards import is_valid_decimal, has_parse_errors
    >>> result, errors = parse_decimal("1,234.56", "en_US")
    >>> if not has_parse_errors(errors) and is_valid_decimal(result):
    ...     # mypy knows result is Decimal (not Decimal)
    ...     amount = result.quantize(Decimal("0.01"))
"""

from __future__ import annotations

import math
from datetime import date, datetime
from decimal import Decimal
from typing import TypeIs

from ftllexbuffer.diagnostics import FluentParseError

__all__ = [
    "has_parse_errors",
    "is_valid_currency",
    "is_valid_date",
    "is_valid_datetime",
    "is_valid_decimal",
    "is_valid_number",
]


def has_parse_errors(errors: list[FluentParseError]) -> bool:
    """Check if parsing returned any errors.

    v0.8.0: New function for checking parse result errors.

    Args:
        errors: Error list from parse_* function result tuple

    Returns:
        True if errors list is non-empty, False otherwise

    Example:
        >>> result, errors = parse_number("invalid", "en_US")
        >>> if has_parse_errors(errors):
        ...     print(f"Parse failed: {errors[0]}")
    """
    return len(errors) > 0


def is_valid_decimal(value: Decimal) -> TypeIs[Decimal]:
    """Type guard: Check if parsed decimal is valid (not NaN/Infinity).

    v0.8.0: Updated for new API - validates Decimal from tuple result.
    Check has_parse_errors() first to ensure parsing succeeded.

    Validates that parse_decimal() result is safe for financial calculations.
    Rejects NaN and Infinity values.

    Args:
        value: Decimal from parse_decimal() result tuple

    Returns:
        True if value is a finite Decimal, False otherwise

    Example:
        >>> result, errors = parse_decimal("1,234.56", "en_US")
        >>> if not has_parse_errors(errors) and is_valid_decimal(result):
        ...     # Type-safe: mypy knows result is finite Decimal
        ...     total = result * Decimal("1.21")  # Add VAT
    """
    return value.is_finite()


def is_valid_number(value: float) -> TypeIs[float]:
    """Type guard: Check if parsed number is valid (not NaN/Infinity).

    v0.8.0: Updated for new API - validates float from tuple result.
    Check has_parse_errors() first to ensure parsing succeeded.

    Validates that parse_number() result is safe for calculations.
    Rejects NaN and Infinity values.

    Args:
        value: Float from parse_number() result tuple

    Returns:
        True if value is a finite float, False otherwise

    Example:
        >>> result, errors = parse_number("1,234.56", "en_US")
        >>> if not has_parse_errors(errors) and is_valid_number(result):
        ...     # Type-safe: mypy knows result is finite float
        ...     total = result * 1.21
    """
    return math.isfinite(value)


def is_valid_currency(
    value: tuple[Decimal, str] | None,
) -> TypeIs[tuple[Decimal, str]]:
    """Type guard: Check if parsed currency is valid (not None, finite amount).

    v0.8.0: Updated for new API - validates currency tuple from result.
    Check has_parse_errors() first to ensure parsing succeeded.

    Validates that parse_currency() result is safe for financial calculations.
    Rejects None and verifies amount is finite.

    Args:
        value: Currency tuple from parse_currency() result

    Returns:
        True if value is (Decimal, str) with finite amount, False otherwise

    Example:
        >>> result, errors = parse_currency("EUR1,234.56", "en_US")
        >>> if not has_parse_errors(errors) and is_valid_currency(result):
        ...     # Type-safe: mypy knows result is tuple[Decimal, str]
        ...     amount, currency = result
        ...     total = amount * Decimal("1.21")
    """
    return value is not None and value[0].is_finite()


def is_valid_date(value: date | None) -> TypeIs[date]:
    """Type guard: Check if parsed date is valid (not None).

    v0.8.0: Updated for new API - validates date from tuple result.
    Check has_parse_errors() first to ensure parsing succeeded.

    Args:
        value: Date from parse_date() result tuple

    Returns:
        True if value is a date object, False otherwise

    Example:
        >>> result, errors = parse_date("2025-01-28", "en_US")
        >>> if not has_parse_errors(errors) and is_valid_date(result):
        ...     # Type-safe: mypy knows result is date
        ...     year = result.year
    """
    return value is not None


def is_valid_datetime(value: datetime | None) -> TypeIs[datetime]:
    """Type guard: Check if parsed datetime is valid (not None).

    v0.8.0: Updated for new API - validates datetime from tuple result.
    Check has_parse_errors() first to ensure parsing succeeded.

    Args:
        value: Datetime from parse_datetime() result tuple

    Returns:
        True if value is a datetime object, False otherwise

    Example:
        >>> result, errors = parse_datetime("2025-01-28 14:30", "en_US")
        >>> if not has_parse_errors(errors) and is_valid_datetime(result):
        ...     # Type-safe: mypy knows result is datetime
        ...     timestamp = result.timestamp()
    """
    return value is not None
