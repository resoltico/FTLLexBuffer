"""Date and datetime parsing functions with locale awareness.

Provides parse_date() and parse_datetime() for converting locale-formatted
date/time strings back to Python date/datetime objects.

Thread-safe. Uses Python 3.13 stdlib + Babel CLDR patterns.

Python 3.13+.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timezone

from babel import Locale


def parse_date(
    value: str,
    locale_code: str,
    *,
    strict: bool = True,
) -> date | None:
    """Parse locale-aware date string to date object.

    v0.7.0 BREAKING CHANGE: Removed ambiguous fallback patterns.
    Only ISO 8601 and locale-specific CLDR patterns are supported.
    Ambiguous formats like "1/2/25" will ONLY match if locale CLDR pattern matches.

    Args:
        value: Date string (e.g., "28.01.25" for lv_LV, "2025-01-28" for ISO 8601)
        locale_code: BCP 47 locale identifier (e.g., "en_US", "lv_LV", "de_DE")
        strict: Raise exception on parse failure (default: True)

    Returns:
        Parsed date object, or None if strict=False and parsing fails

    Raises:
        ValueError: If parsing fails and strict=True

    Examples:
        >>> parse_date("2025-01-28", "en_US")  # ISO 8601 - always works
        datetime.date(2025, 1, 28)
        >>> parse_date("1/28/25", "en_US")  # US locale format
        datetime.date(2025, 1, 28)
        >>> parse_date("28.01.25", "lv_LV")  # Latvian locale format
        datetime.date(2025, 1, 28)
        >>> parse_date("28.01.2025", "de_DE")  # German locale format
        datetime.date(2025, 1, 28)
        >>> parse_date("invalid", "en_US", strict=False)
        None

    Note:
        v0.7.0: No ambiguous fallback patterns. Use ISO 8601 (YYYY-MM-DD) for
        unambiguous, locale-independent dates.

    Thread Safety:
        Thread-safe. Uses Babel + stdlib (no global state).
    """
    # Try ISO 8601 first (fastest path)
    try:
        return datetime.fromisoformat(value).date()
    except (ValueError, TypeError):
        pass

    # Try locale-specific CLDR patterns
    try:
        patterns = _get_date_patterns(locale_code)
        for pattern in patterns:
            try:
                return datetime.strptime(value, pattern).date()
            except ValueError:
                continue

        # If all patterns fail, raise error
        if strict:
            msg = f"Failed to parse date '{value}' for locale '{locale_code}'"
            raise ValueError(msg)
        return None

    except (ValueError, TypeError) as e:
        if strict:
            msg = f"Failed to parse date '{value}' for locale '{locale_code}': {e}"
            raise ValueError(msg) from e
        return None


def parse_datetime(
    value: str,
    locale_code: str,
    *,
    strict: bool = True,
    tzinfo: timezone | None = None,
) -> datetime | None:
    """Parse locale-aware datetime string to datetime object.

    v0.7.0 BREAKING CHANGE: Removed ambiguous fallback patterns.
    Only ISO 8601 and locale-specific CLDR patterns are supported.

    Args:
        value: DateTime string (e.g., "2025-01-28 14:30" for ISO 8601)
        locale_code: BCP 47 locale identifier (e.g., "en_US", "lv_LV", "de_DE")
        strict: Raise exception on parse failure (default: True)
        tzinfo: Timezone to assign if not in string (default: None - naive datetime)

    Returns:
        Parsed datetime object, or None if strict=False and parsing fails

    Raises:
        ValueError: If parsing fails and strict=True

    Examples:
        >>> parse_datetime("2025-01-28 14:30", "en_US")  # ISO 8601 - always works
        datetime.datetime(2025, 1, 28, 14, 30)
        >>> parse_datetime("1/28/25 2:30 PM", "en_US")  # US locale format
        datetime.datetime(2025, 1, 28, 14, 30)
        >>> parse_datetime("28.01.25 14:30", "lv_LV")  # Latvian locale format
        datetime.datetime(2025, 1, 28, 14, 30)
        >>> parse_datetime("invalid", "en_US", strict=False)
        None

    Note:
        v0.7.0: No ambiguous fallback patterns. Use ISO 8601 (YYYY-MM-DD HH:MM:SS)
        for unambiguous, locale-independent datetimes.

    Thread Safety:
        Thread-safe. Uses Babel + stdlib (no global state).
    """
    # Try ISO 8601 first (fastest path)
    try:
        parsed = datetime.fromisoformat(value)
        if tzinfo is not None and parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=tzinfo)
        return parsed
    except (ValueError, TypeError):
        pass

    # Try locale-specific CLDR patterns
    try:
        patterns = _get_datetime_patterns(locale_code)
        for pattern in patterns:
            try:
                parsed = datetime.strptime(value, pattern)
                if tzinfo is not None and parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=tzinfo)
                return parsed
            except ValueError:
                continue

        # If all patterns fail, raise error
        if strict:
            msg = f"Failed to parse datetime '{value}' for locale '{locale_code}'"
            raise ValueError(msg)
        return None

    except (ValueError, TypeError) as e:
        if strict:
            msg = f"Failed to parse datetime '{value}' for locale '{locale_code}': {e}"
            raise ValueError(msg) from e
        return None


def _get_date_patterns(locale_code: str) -> list[str]:
    """Get strptime date patterns for locale.

    Uses ONLY Babel CLDR date format patterns specific to the locale.
    No fallback patterns to avoid ambiguous date interpretation.

    v0.7.0 BREAKING CHANGE: Removed ambiguous fallback patterns.
    Only ISO 8601 and locale-specific CLDR patterns are supported.
    Use ISO 8601 (YYYY-MM-DD) for unambiguous, locale-independent dates.

    Args:
        locale_code: BCP 47 locale identifier

    Returns:
        List of strptime patterns to try, in order of preference
        Empty list if locale parsing fails
    """
    try:
        # Parse locale (convert BCP-47 to POSIX: en-US -> en_US)
        normalized = locale_code.replace("-", "_")
        locale = Locale.parse(normalized)

        # Get CLDR date patterns
        patterns = []

        # Try short, medium, long formats
        for style in ["short", "medium", "long"]:
            try:
                babel_pattern = locale.date_formats[style].pattern
                strptime_pattern = _babel_to_strptime(babel_pattern)
                patterns.append(strptime_pattern)
            except (AttributeError, KeyError):
                pass

        return patterns

    except Exception:  # pylint: disable=broad-exception-caught
        # v0.7.0: If locale parsing fails, return empty list (no fallback patterns)
        return []


def _get_datetime_patterns(locale_code: str) -> list[str]:
    """Get strptime datetime patterns for locale.

    Uses ONLY Babel CLDR datetime format patterns specific to the locale.
    No fallback patterns to avoid ambiguous datetime interpretation.

    v0.7.0 BREAKING CHANGE: Removed ambiguous fallback patterns.
    Only ISO 8601 and locale-specific CLDR patterns are supported.

    Args:
        locale_code: BCP 47 locale identifier

    Returns:
        List of strptime patterns to try, in order of preference
        Empty list if locale parsing fails
    """
    try:
        # Parse locale (convert BCP-47 to POSIX: en-US -> en_US)
        normalized = locale_code.replace("-", "_")
        locale = Locale.parse(normalized)

        # Get CLDR datetime patterns
        patterns = []

        # Try short, medium formats with time
        for style in ["short", "medium"]:
            try:
                babel_pattern = locale.datetime_formats[style].pattern
                strptime_pattern = _babel_to_strptime(babel_pattern)
                patterns.append(strptime_pattern)
            except (AttributeError, KeyError):
                pass

        # Get date patterns and add time components for locale
        date_patterns = _get_date_patterns(locale_code)

        # Add datetime combinations using locale-specific date patterns
        for date_pat in date_patterns:
            patterns.extend([
                f"{date_pat} %H:%M:%S",      # 24-hour with seconds
                f"{date_pat} %H:%M",         # 24-hour without seconds
                f"{date_pat} %I:%M:%S %p",   # 12-hour with seconds + AM/PM
                f"{date_pat} %I:%M %p",      # 12-hour without seconds + AM/PM
            ])

        return patterns

    except Exception:  # pylint: disable=broad-exception-caught
        # v0.7.0: If locale parsing fails, return empty list (no fallback patterns)
        return []


def _babel_to_strptime(babel_pattern: str) -> str:
    """Convert Babel CLDR pattern to Python strptime format.

    Babel uses Unicode CLDR date pattern syntax, Python uses strptime directives.

    Babel Patterns:
        y, yy      = 2-digit year
        yyyy       = 4-digit year
        M, MM      = month (1-12)
        MMM        = short month name (Jan, Feb)
        MMMM       = full month name (January, February)
        d, dd      = day of month
        E, EEE     = short weekday (Mon)
        EEEE       = full weekday (Monday)
        H, HH      = hour 0-23
        h, hh      = hour 1-12
        m, mm      = minute
        s, ss      = second
        a          = AM/PM

    Python strptime:
        %y  = 2-digit year
        %Y  = 4-digit year
        %m  = month (01-12)
        %b  = short month name
        %B  = full month name
        %d  = day of month
        %a  = short weekday
        %A  = full weekday
        %H  = hour 0-23
        %I  = hour 1-12
        %M  = minute
        %S  = second
        %p  = AM/PM

    Args:
        babel_pattern: Babel CLDR date pattern

    Returns:
        Python strptime pattern
    """
    # Mapping: Babel pattern -> strptime directive
    # Process in order from longest to shortest to avoid partial matches
    replacements = [
        # Year
        ("yyyy", "%Y"),     # 4-digit year
        ("yy", "%y"),       # 2-digit year
        ("y", "%Y"),        # Year (default to 4-digit)

        # Month
        ("MMMM", "%B"),     # Full month name
        ("MMM", "%b"),      # Short month name
        ("MM", "%m"),       # 2-digit month
        ("M", "%m"),        # Month

        # Day
        ("dd", "%d"),       # 2-digit day
        ("d", "%d"),        # Day

        # Weekday
        ("EEEE", "%A"),     # Full weekday name
        ("EEE", "%a"),      # Short weekday name
        ("E", "%a"),        # Weekday

        # Hour
        ("HH", "%H"),       # 2-digit hour (0-23)
        ("H", "%H"),        # Hour (0-23)
        ("hh", "%I"),       # 2-digit hour (1-12)
        ("h", "%I"),        # Hour (1-12)

        # Minute
        ("mm", "%M"),       # 2-digit minute
        ("m", "%M"),        # Minute

        # Second
        ("ss", "%S"),       # 2-digit second
        ("s", "%S"),        # Second

        # AM/PM
        ("a", "%p"),        # AM/PM marker
    ]

    result = babel_pattern

    # Replace Babel patterns with strptime directives
    for babel_token, strptime_token in replacements:
        # Use negative lookbehind to avoid replacing tokens that are already
        # part of strptime directives (preceded by %)
        # e.g., don't replace 'M' in '%M' or 'm' in '%m'
        result = re.sub(
            rf"(?<!%)\b{re.escape(babel_token)}\b",
            strptime_token,
            result
        )

    return result
