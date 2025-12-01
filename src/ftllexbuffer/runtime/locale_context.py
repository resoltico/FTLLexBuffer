"""Locale context for thread-safe, bundle-scoped formatting.

This module provides locale-aware formatting without global state mutation.
Uses Babel for CLDR-compliant number, date, and currency formatting.

Architecture:
    - LocaleContext: Immutable locale configuration container
    - Formatters use Babel (thread-safe, CLDR-based)
    - No dependency on Python's locale module (avoids global state)
    - Each FluentBundle owns its LocaleContext (locale isolation)

Design Principles:
    - Explicit over implicit (locale always visible)
    - Immutable by default (frozen dataclass)
    - Thread-safe (no shared mutable state)
    - CLDR-compliant (matches Intl.NumberFormat semantics)

Python 3.13+. Uses Babel for i18n.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from babel import Locale, UnknownLocaleError  # pylint: disable=import-error
from babel import dates as babel_dates  # pylint: disable=import-error
from babel import numbers as babel_numbers  # pylint: disable=import-error

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LocaleContext:
    """Immutable locale configuration for formatting operations.

    Provides thread-safe, locale-specific formatting for numbers, dates, and currency
    without mutating global state. Each FluentBundle owns its LocaleContext.

    Args:
        locale_code: BCP 47 locale identifier (e.g., 'en-US', 'lv-LV', 'de-DE')

    Examples:
        >>> ctx_en = LocaleContext('en-US')
        >>> ctx_en.format_number(1234.5, use_grouping=True)
        '1,234.5'

        >>> ctx_lv = LocaleContext('lv-LV')
        >>> ctx_lv.format_number(1234.5, use_grouping=True)
        '1 234,5'

    Thread Safety:
        LocaleContext is immutable and thread-safe. Multiple threads can
        share the same instance without synchronization.

    Babel vs locale module:
        - Babel: Thread-safe, CLDR-based, 600+ locales
        - locale: Thread-unsafe, platform-dependent, requires setlocale()
    """

    locale_code: str

    def __post_init__(self) -> None:
        """Validate locale code on initialization.

        Raises:
            UnknownLocaleError: If locale_code is not recognized by CLDR.
        """
        # Validate locale exists in CLDR
        try:
            # Convert BCP-47 'en-US' to Babel's POSIX format 'en_US'
            # BCP-47 uses hyphens, Babel/POSIX uses underscores
            normalized = self.locale_code.replace("-", "_")
            Locale.parse(normalized)
        except (UnknownLocaleError, ValueError) as e:
            logger.warning("Unknown locale '%s': %s", self.locale_code, e)
            # Don't raise - allow fallback to default formatting
            # Fluent spec: "Functions MUST return str, never raise"

    @property
    def babel_locale(self) -> Locale:
        """Get Babel Locale object for this context.

        Returns:
            Babel Locale instance (cached by Babel internally)

        Note:
            Babel.Locale.parse() caches parsed locales, so repeated
            calls are cheap.
        """
        try:
            # Convert BCP-47 'en-US' to Babel's POSIX format 'en_US'
            normalized = self.locale_code.replace("-", "_")
            return Locale.parse(normalized)
        except (UnknownLocaleError, ValueError):
            # Fallback to English (US) if locale unknown
            logger.debug("Falling back to en_US for unknown locale: %s", self.locale_code)
            return Locale.parse("en_US")

    def format_number(
        self,
        value: int | float,
        *,
        minimum_fraction_digits: int = 0,
        maximum_fraction_digits: int = 3,
        use_grouping: bool = True,
    ) -> str:
        """Format number with locale-specific separators.

        Implements Fluent NUMBER function semantics using Babel.

        Args:
            value: Number to format
            minimum_fraction_digits: Minimum decimal places (default: 0)
            maximum_fraction_digits: Maximum decimal places (default: 3)
            use_grouping: Use thousands separator (default: True)

        Returns:
            Formatted number string according to locale rules

        Examples:
            >>> ctx = LocaleContext('en-US')
            >>> ctx.format_number(1234.5)
            '1,234.5'

            >>> ctx = LocaleContext('de-DE')
            >>> ctx.format_number(1234.5)
            '1.234,5'

            >>> ctx = LocaleContext('lv-LV')
            >>> ctx.format_number(1234.5)
            '1 234,5'

        CLDR Compliance:
            Uses Babel's format_decimal() which implements CLDR rules.
            Matches Intl.NumberFormat behavior in JavaScript.
        """
        try:
            # Build format pattern
            # '#,##0' = integer with grouping
            # '#,##0.0##' = 1-3 decimal places with grouping
            # '0.00' = exactly 2 decimal places, no grouping

            # Integer part
            integer_part = "#,##0" if use_grouping else "0"

            # Decimal part
            if maximum_fraction_digits == 0:
                # No decimals - round to integer
                value = round(value)
                pattern = integer_part
            elif minimum_fraction_digits == maximum_fraction_digits:
                # Fixed decimals (e.g., '0.00' for exactly 2)
                decimal_part = "0" * minimum_fraction_digits
                pattern = f"{integer_part}.{decimal_part}"
            else:
                # Variable decimals (e.g., '0.0##' for 1-3)
                required = "0" * minimum_fraction_digits
                optional = "#" * (maximum_fraction_digits - minimum_fraction_digits)
                pattern = f"{integer_part}.{required}{optional}"

            # Format using Babel
            return str(
                babel_numbers.format_decimal(
                    value,
                    format=pattern,
                    locale=self.babel_locale,
                )
            )

        except (ValueError, TypeError) as e:
            # Expected: invalid format pattern or non-numeric value
            logger.debug("Number formatting failed (expected error): %s", e)
            return str(value)
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Unexpected: platform-specific errors
            # i18n MUST NOT crash application - graceful degradation required
            logger.warning(
                "Unexpected error in format_number(%s, locale=%s): %s",
                value,
                self.locale_code,
                e,
                exc_info=True,
            )
            return str(value)

    def format_datetime(
        self,
        value: datetime | str,
        *,
        date_style: Literal["short", "medium", "long", "full"] = "medium",
        time_style: Literal["short", "medium", "long", "full"] | None = None,
    ) -> str:
        """Format datetime with locale-specific formatting.

        Implements Fluent DATETIME function semantics using Babel.

        Args:
            value: datetime object or ISO string
            date_style: Date format style (default: "medium")
            time_style: Time format style (default: None - date only)

        Returns:
            Formatted datetime string according to locale rules

        Examples:
            >>> from datetime import datetime, UTC
            >>> ctx = LocaleContext('en-US')
            >>> dt = datetime(2025, 10, 27, 14, 30, tzinfo=UTC)
            >>> ctx.format_datetime(dt, date_style='short')
            '10/27/25'

            >>> ctx = LocaleContext('de-DE')
            >>> ctx.format_datetime(dt, date_style='short')
            '27.10.25'

        CLDR Compliance:
            Uses Babel's format_datetime() which implements CLDR rules.
            Matches Intl.DateTimeFormat behavior in JavaScript.
        """
        # Type narrowing: convert str to datetime
        dt_value: datetime

        if isinstance(value, str):
            try:
                dt_value = datetime.fromisoformat(value)
            except ValueError:
                # Invalid datetime string - return Fluent error placeholder
                return "{?DATETIME}"
        else:
            dt_value = value

        try:
            # Map Fluent styles to Babel format strings
            if time_style:
                # Both date and time
                return str(
                    babel_dates.format_datetime(
                        dt_value,
                        format=f"{date_style}",  # Babel accepts 'short', 'medium', etc.
                        locale=self.babel_locale,
                    )
                )
            # Date only
            return str(
                babel_dates.format_date(
                    dt_value,
                    format=date_style,
                    locale=self.babel_locale,
                )
            )

        except (ValueError, OverflowError) as e:
            # Expected: year out of range, invalid datetime
            logger.debug("DateTime formatting failed: %s", e)
            return dt_value.isoformat()
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Unexpected: platform-specific errors
            logger.warning(
                "Unexpected error in format_datetime(%s, locale=%s): %s",
                dt_value,
                self.locale_code,
                e,
                exc_info=True,
            )
            return dt_value.isoformat()

    def format_currency(
        self,
        value: int | float,
        *,
        currency: str,
        currency_display: Literal["symbol", "code", "name"] = "symbol",
    ) -> str:
        """Format currency with locale-specific rules.

        Implements Fluent CURRENCY function semantics using Babel.

        Args:
            value: Monetary amount
            currency: ISO 4217 currency code (EUR, USD, JPY, BHD, etc.)
            currency_display: Display style for currency
                - "symbol": Use currency symbol (€, $, ¥)
                - "code": Use currency code (EUR, USD, JPY)
                - "name": Use currency name (euros, dollars, yen)

        Returns:
            Formatted currency string according to locale rules

        Examples:
            >>> ctx = LocaleContext('en-US')
            >>> ctx.format_currency(123.45, currency='EUR')
            '€123.45'

            >>> ctx = LocaleContext('lv-LV')
            >>> ctx.format_currency(123.45, currency='EUR')
            '123,45 €'

            >>> ctx = LocaleContext('ja-JP')
            >>> ctx.format_currency(12345, currency='JPY')
            '¥12,345'

            >>> ctx = LocaleContext('ar-BH')
            >>> ctx.format_currency(123.456, currency='BHD')
            '123.456 د.ب.'

        CLDR Compliance:
            Uses Babel's format_currency() which implements CLDR rules.
            Matches Intl.NumberFormat with style: 'currency'.
            Automatically applies currency-specific decimal places:
            - JPY: 0 decimals
            - BHD, KWD, OMR: 3 decimals
            - Most others: 2 decimals
        """
        try:
            # Map currency_display to Babel's format_type parameter
            # Babel format_type must be Literal["name", "standard", "accounting"]
            if currency_display == "name":
                format_type: Literal["name", "standard", "accounting"] = "name"
            else:
                # Both "symbol" and "code" use "standard" format_type
                format_type = "standard"

            # For "code" display, we need custom format pattern
            # Babel uses ¤ for symbol, ¤¤ for code, ¤¤¤ for name
            format_pattern: str | None = None
            if currency_display == "code":
                # Force code display with ¤¤ pattern
                format_pattern = "¤¤ #,##0.00"

            # Babel's format_currency() automatically uses currency-specific
            # decimal places from CLDR (0 for JPY, 3 for BHD, 2 for most)
            return str(
                babel_numbers.format_currency(
                    value,
                    currency,
                    locale=self.babel_locale,
                    currency_digits=True,  # Use CLDR currency-specific decimals
                    format_type=format_type,
                    format=format_pattern,  # Custom pattern for code display
                )
            )

        except (ValueError, TypeError) as e:
            # Expected: invalid currency code or non-numeric value
            logger.debug("Currency formatting failed (expected error): %s", e)
            return f"{currency} {value}"
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Unexpected: platform-specific errors
            logger.warning(
                "Unexpected error in format_currency(%s, %s, locale=%s): %s",
                value,
                currency,
                self.locale_code,
                e,
                exc_info=True,
            )
            return f"{currency} {value}"
