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

    Args:
        value: Date string (e.g., "28.01.25" for lv_LV short format)
        locale_code: BCP 47 locale identifier (used for locale-specific patterns)
        strict: Raise exception on parse failure (default: True)

    Returns:
        Parsed date object, or None if strict=False and parsing fails

    Raises:
        ValueError: If parsing fails and strict=True

    Examples:
        >>> parse_date("1/28/25", "en_US")
        datetime.date(2025, 1, 28)
        >>> parse_date("28.01.25", "lv_LV")
        datetime.date(2025, 1, 28)
        >>> parse_date("28.01.2025", "de_DE")
        datetime.date(2025, 1, 28)
        >>> parse_date("invalid", "en_US", strict=False)
        None

    Note:
        Uses Babel CLDR date patterns with Python 3.13 strptime.
        Tries locale-specific patterns first, then common fallbacks.

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

    Args:
        value: DateTime string
        locale_code: BCP 47 locale identifier (used for locale-specific patterns)
        strict: Raise exception on parse failure (default: True)
        tzinfo: Timezone to assign if not in string (default: None - naive datetime)

    Returns:
        Parsed datetime object, or None if strict=False and parsing fails

    Raises:
        ValueError: If parsing fails and strict=True

    Examples:
        >>> parse_datetime("1/28/25 14:30", "en_US")
        datetime.datetime(2025, 1, 28, 14, 30)
        >>> parse_datetime("28.01.25 14:30", "lv_LV")
        datetime.datetime(2025, 1, 28, 14, 30)
        >>> parse_datetime("invalid", "en_US", strict=False)
        None

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

    Uses Babel CLDR date format patterns and converts them to strptime format.

    Args:
        locale_code: BCP 47 locale identifier

    Returns:
        List of strptime patterns to try, in order of preference
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

    except Exception:  # pylint: disable=broad-exception-caught
        # Fallback to common patterns if locale parsing fails
        patterns = []

    # Add common fallback patterns
    patterns.extend([
        "%m/%d/%Y",      # US: 1/28/2025
        "%m/%d/%y",      # US short: 1/28/25
        "%d.%m.%Y",      # EU: 28.01.2025
        "%d.%m.%y",      # EU short: 28.01.25
        "%d/%m/%Y",      # EU slash: 28/01/2025
        "%d/%m/%y",      # EU slash short: 28/01/25
        "%Y-%m-%d",      # ISO: 2025-01-28
        "%d-%m-%Y",      # ISO-like: 28-01-2025
        "%b %d, %Y",     # Jan 28, 2025
        "%d %b %Y",      # 28 Jan 2025
        "%B %d, %Y",     # January 28, 2025
        "%d %B %Y",      # 28 January 2025
    ])

    return patterns


def _get_datetime_patterns(locale_code: str) -> list[str]:
    """Get strptime datetime patterns for locale.

    Uses Babel CLDR datetime format patterns and converts them to strptime format.

    Args:
        locale_code: BCP 47 locale identifier

    Returns:
        List of strptime patterns to try, in order of preference
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

    except Exception:  # pylint: disable=broad-exception-caught
        # Fallback to common patterns if locale parsing fails
        patterns = []

    # Get date patterns and add time components
    date_patterns = _get_date_patterns(locale_code)

    # Add datetime combinations
    for date_pat in date_patterns[:5]:  # Use first 5 date patterns
        patterns.extend([
            f"{date_pat} %H:%M:%S",  # 28.01.2025 14:30:45
            f"{date_pat} %H:%M",     # 28.01.2025 14:30
            f"{date_pat} %I:%M:%S %p",  # 1/28/2025 02:30:45 PM
            f"{date_pat} %I:%M %p",     # 1/28/2025 02:30 PM
        ])

    # Add common fallback patterns
    patterns.extend([
        "%Y-%m-%d %H:%M:%S",    # ISO: 2025-01-28 14:30:45
        "%Y-%m-%d %H:%M",       # ISO: 2025-01-28 14:30
        "%m/%d/%Y %H:%M:%S",    # US: 1/28/2025 14:30:45
        "%m/%d/%Y %H:%M",       # US: 1/28/2025 14:30
        "%d.%m.%Y %H:%M:%S",    # EU: 28.01.2025 14:30:45
        "%d.%m.%Y %H:%M",       # EU: 28.01.2025 14:30
    ])

    return patterns


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
