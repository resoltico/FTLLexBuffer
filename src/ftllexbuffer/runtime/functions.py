"""Fluent built-in functions with Python-native APIs.

Implements NUMBER and DATETIME functions with locale-aware formatting.
Uses snake_case parameters (PEP 8) with FTL camelCase bridge.

Architecture:
    - Python functions use snake_case (PEP 8 compliant)
    - FunctionRegistry bridges to FTL camelCase
    - FTL files still use camelCase syntax
    - No N802/N803 violations!
    - Locale-aware via LocaleContext (thread-safe, CLDR-based)

Example:
    # Python API (snake_case):
    number_format(1234.5, "en-US", minimum_fraction_digits=2)

    # FTL file (camelCase):
    price = { $amount NUMBER(minimumFractionDigits: 2) }

    # Bridge handles the conversion automatically!

Python 3.13+. Uses Babel for i18n.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Literal

from .function_bridge import FunctionRegistry
from .locale_context import LocaleContext

logger = logging.getLogger(__name__)


def number_format(
    value: int | float,
    locale_code: str = "en-US",
    *,
    minimum_fraction_digits: int = 0,
    maximum_fraction_digits: int = 3,
    use_grouping: bool = True,
) -> str:
    """Format number with locale-specific separators.

    Python-native API with snake_case parameters. FunctionRegistry bridges
    to FTL camelCase (minimumFractionDigits → minimum_fraction_digits).

    Args:
        value: Number to format
        locale_code: BCP 47 locale identifier (e.g., 'en-US', 'de-DE')
        minimum_fraction_digits: Minimum decimal places (default: 0)
        maximum_fraction_digits: Maximum decimal places (default: 3)
        use_grouping: Use thousands separator (default: True)

    Returns:
        Formatted number string

    Examples:
        >>> number_format(1234.5, "en-US")
        '1,234.5'
        >>> number_format(1234.5, "de-DE")
        '1.234,5'
        >>> number_format(1234.5, "lv-LV")
        '1 234,5'
        >>> number_format(42, "en-US", minimum_fraction_digits=2)
        '42.00'

    FTL Usage:
        price = { $amount NUMBER(minimumFractionDigits: 2) }

    Thread Safety:
        Thread-safe. Uses Babel (no global locale state mutation).

    CLDR Compliance:
        Implements CLDR formatting rules via Babel.
        Matches Intl.NumberFormat semantics.
    """
    # Delegate to LocaleContext (immutable, thread-safe)
    ctx = LocaleContext(locale_code)
    return ctx.format_number(
        value,
        minimum_fraction_digits=minimum_fraction_digits,
        maximum_fraction_digits=maximum_fraction_digits,
        use_grouping=use_grouping,
    )


def datetime_format(
    value: datetime | str,
    locale_code: str = "en-US",
    *,
    date_style: Literal["short", "medium", "long", "full"] = "medium",
    time_style: Literal["short", "medium", "long", "full"] | None = None,
) -> str:
    """Format datetime with locale-specific formatting.

    Python-native API with snake_case parameters. FunctionRegistry bridges
    to FTL camelCase (dateStyle → date_style, timeStyle → time_style).

    Args:
        value: datetime object or ISO string
        locale_code: BCP 47 locale identifier (e.g., 'en-US', 'de-DE')
        date_style: Date format style (default: "medium")
        time_style: Time format style (default: None - date only)

    Returns:
        Formatted datetime string

    Examples:
        >>> from datetime import datetime, UTC
        >>> dt = datetime(2025, 10, 27, tzinfo=UTC)
        >>> datetime_format(dt, "en-US", date_style="short")
        '10/27/25'
        >>> datetime_format(dt, "de-DE", date_style="short")
        '27.10.25'
        >>> dt_with_time = datetime(2025, 10, 27, 14, 30, tzinfo=UTC)
        >>> datetime_format(dt_with_time, "en-US", date_style="medium", time_style="short")
        'Oct 27, 2025, 2:30 PM'

    FTL Usage:
        today = { $date DATETIME(dateStyle: "short") }
        timestamp = { $time DATETIME(dateStyle: "medium", timeStyle: "short") }

    Thread Safety:
        Thread-safe. Uses Babel (no global locale state mutation).

    CLDR Compliance:
        Implements CLDR formatting rules via Babel.
        Matches Intl.DateTimeFormat semantics.
    """
    # Delegate to LocaleContext (immutable, thread-safe)
    ctx = LocaleContext(locale_code)
    return ctx.format_datetime(
        value,
        date_style=date_style,
        time_style=time_style,
    )


# Create function registry and register built-in functions
FUNCTION_REGISTRY = FunctionRegistry()

# Register NUMBER function with camelCase parameter mapping
FUNCTION_REGISTRY.register(number_format, ftl_name="NUMBER")

# Register DATETIME function with camelCase parameter mapping
FUNCTION_REGISTRY.register(datetime_format, ftl_name="DATETIME")
