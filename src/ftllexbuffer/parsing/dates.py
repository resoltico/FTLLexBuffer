"""Date and datetime parsing functions with locale awareness.

v0.8.0 BREAKING CHANGE: API aligned with formatting functions.
- parse_date() returns tuple[date | None, list[FluentParseError]]
- parse_datetime() returns tuple[datetime | None, list[FluentParseError]]
- Removed `strict` parameter - functions NEVER raise, errors returned in list
- Consistent with format_*() "never raise" philosophy
- Fixed: Date pattern tokenizer replaces regex word boundary approach

Thread-safe. Uses Python 3.13 stdlib + Babel CLDR patterns.

Python 3.13+.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from babel import Locale, UnknownLocaleError

from ftllexbuffer.diagnostics import FluentParseError
from ftllexbuffer.diagnostics.templates import ErrorTemplate


def parse_date(
    value: str,
    locale_code: str,
) -> tuple[date | None, list[FluentParseError]]:
    """Parse locale-aware date string to date object.

    v0.8.0 BREAKING CHANGE: Returns tuple[date | None, list[FluentParseError]].
    No longer raises exceptions. Errors are returned in the list.
    The `strict` parameter has been removed.

    Only ISO 8601 and locale-specific CLDR patterns are supported.
    Ambiguous formats like "1/2/25" will ONLY match if locale CLDR pattern matches.

    Args:
        value: Date string (e.g., "28.01.25" for lv_LV, "2025-01-28" for ISO 8601)
        locale_code: BCP 47 locale identifier (e.g., "en_US", "lv_LV", "de_DE")

    Returns:
        Tuple of (result, errors):
        - result: Parsed date object, or None if parsing failed
        - errors: List of FluentParseError (empty on success)

    Examples:
        >>> result, errors = parse_date("2025-01-28", "en_US")  # ISO 8601
        >>> result
        datetime.date(2025, 1, 28)
        >>> errors
        []

        >>> result, errors = parse_date("1/28/25", "en_US")  # US locale format
        >>> result
        datetime.date(2025, 1, 28)

        >>> result, errors = parse_date("invalid", "en_US")
        >>> result is None
        True
        >>> len(errors)
        1

    Thread Safety:
        Thread-safe. Uses Babel + stdlib (no global state).
    """
    errors: list[FluentParseError] = []

    # Type check: value must be string (runtime defense for untyped callers)
    if not isinstance(value, str):
        diagnostic = ErrorTemplate.parse_date_failed(  # type: ignore[unreachable]
            str(value), locale_code, f"Expected string, got {type(value).__name__}"
        )
        errors.append(
            FluentParseError(
                diagnostic,
                input_value=str(value),
                locale_code=locale_code,
                parse_type="date",
            )
        )
        return (None, errors)

    # Try ISO 8601 first (fastest path)
    try:
        return (datetime.fromisoformat(value).date(), errors)
    except ValueError:
        pass

    # Try locale-specific CLDR patterns
    patterns = _get_date_patterns(locale_code)
    if not patterns:
        # Unknown locale
        diagnostic = ErrorTemplate.parse_locale_unknown(locale_code)
        errors.append(
            FluentParseError(
                diagnostic,
                input_value=value,
                locale_code=locale_code,
                parse_type="date",
            )
        )
        return (None, errors)

    for pattern in patterns:
        try:
            return (datetime.strptime(value, pattern).date(), errors)
        except ValueError:
            continue

    # All patterns failed
    diagnostic = ErrorTemplate.parse_date_failed(
        value, locale_code, "No matching date pattern found"
    )
    errors.append(
        FluentParseError(
            diagnostic,
            input_value=value,
            locale_code=locale_code,
            parse_type="date",
        )
    )
    return (None, errors)


def parse_datetime(
    value: str,
    locale_code: str,
    *,
    tzinfo: timezone | None = None,
) -> tuple[datetime | None, list[FluentParseError]]:
    """Parse locale-aware datetime string to datetime object.

    v0.8.0 BREAKING CHANGE: Returns tuple[datetime | None, list[FluentParseError]].
    No longer raises exceptions. Errors are returned in the list.
    The `strict` parameter has been removed.

    Only ISO 8601 and locale-specific CLDR patterns are supported.

    Args:
        value: DateTime string (e.g., "2025-01-28 14:30" for ISO 8601)
        locale_code: BCP 47 locale identifier (e.g., "en_US", "lv_LV", "de_DE")
        tzinfo: Timezone to assign if not in string (default: None - naive datetime)

    Returns:
        Tuple of (result, errors):
        - result: Parsed datetime object, or None if parsing failed
        - errors: List of FluentParseError (empty on success)

    Examples:
        >>> result, errors = parse_datetime("2025-01-28 14:30", "en_US")  # ISO 8601
        >>> result
        datetime.datetime(2025, 1, 28, 14, 30)
        >>> errors
        []

        >>> result, errors = parse_datetime("1/28/25 2:30 PM", "en_US")  # US locale
        >>> result
        datetime.datetime(2025, 1, 28, 14, 30)

        >>> result, errors = parse_datetime("invalid", "en_US")
        >>> result is None
        True
        >>> len(errors)
        1

    Thread Safety:
        Thread-safe. Uses Babel + stdlib (no global state).
    """
    errors: list[FluentParseError] = []

    # Type check: value must be string (runtime defense for untyped callers)
    if not isinstance(value, str):
        diagnostic = ErrorTemplate.parse_datetime_failed(  # type: ignore[unreachable]
            str(value), locale_code, f"Expected string, got {type(value).__name__}"
        )
        errors.append(
            FluentParseError(
                diagnostic,
                input_value=str(value),
                locale_code=locale_code,
                parse_type="datetime",
            )
        )
        return (None, errors)

    # Try ISO 8601 first (fastest path)
    try:
        parsed = datetime.fromisoformat(value)
        if tzinfo is not None and parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=tzinfo)
        return (parsed, errors)
    except (ValueError, TypeError):
        pass

    # Try locale-specific CLDR patterns
    patterns = _get_datetime_patterns(locale_code)
    if not patterns:
        # Unknown locale
        diagnostic = ErrorTemplate.parse_locale_unknown(locale_code)
        errors.append(
            FluentParseError(
                diagnostic,
                input_value=value,
                locale_code=locale_code,
                parse_type="datetime",
            )
        )
        return (None, errors)

    for pattern in patterns:
        try:
            parsed = datetime.strptime(value, pattern)
            if tzinfo is not None and parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=tzinfo)
            return (parsed, errors)
        except ValueError:
            continue

    # All patterns failed
    diagnostic = ErrorTemplate.parse_datetime_failed(
        value, locale_code, "No matching datetime pattern found"
    )
    errors.append(
        FluentParseError(
            diagnostic,
            input_value=value,
            locale_code=locale_code,
            parse_type="datetime",
        )
    )
    return (None, errors)


def _get_date_patterns(locale_code: str) -> list[str]:
    """Get strptime date patterns for locale.

    Uses ONLY Babel CLDR date format patterns specific to the locale.
    No fallback patterns to avoid ambiguous date interpretation.

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

    except (UnknownLocaleError, ValueError, RuntimeError):
        return []


def _get_datetime_patterns(locale_code: str) -> list[str]:
    """Get strptime datetime patterns for locale.

    Uses ONLY Babel CLDR datetime format patterns specific to the locale.
    No fallback patterns to avoid ambiguous datetime interpretation.

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
            patterns.extend(
                [
                    f"{date_pat} %H:%M:%S",  # 24-hour with seconds
                    f"{date_pat} %H:%M",  # 24-hour without seconds
                    f"{date_pat} %I:%M:%S %p",  # 12-hour with seconds + AM/PM
                    f"{date_pat} %I:%M %p",  # 12-hour without seconds + AM/PM
                ]
            )

        return patterns

    except (UnknownLocaleError, ValueError, RuntimeError):
        return []


# ==============================================================================
# TOKEN-BASED BABEL-TO-STRPTIME CONVERTER (v0.8.0 - replaces regex approach)
# ==============================================================================

# Token mapping: Babel CLDR pattern -> Python strptime directive
_BABEL_TOKEN_MAP: dict[str, str] = {
    # Year
    "yyyy": "%Y",  # 4-digit year
    "yy": "%y",  # 2-digit year
    "y": "%Y",  # Year (default to 4-digit)
    # Month
    "MMMM": "%B",  # Full month name
    "MMM": "%b",  # Short month name
    "MM": "%m",  # 2-digit month
    "M": "%m",  # Month
    # Day
    "dd": "%d",  # 2-digit day
    "d": "%d",  # Day
    # Weekday
    "EEEE": "%A",  # Full weekday name
    "EEE": "%a",  # Short weekday name
    "E": "%a",  # Weekday
    # Hour
    "HH": "%H",  # 2-digit hour (0-23)
    "H": "%H",  # Hour (0-23)
    "hh": "%I",  # 2-digit hour (1-12)
    "h": "%I",  # Hour (1-12)
    # Minute
    "mm": "%M",  # 2-digit minute
    "m": "%M",  # Minute
    # Second
    "ss": "%S",  # 2-digit second
    "s": "%S",  # Second
    # AM/PM
    "a": "%p",  # AM/PM marker
}


def _tokenize_babel_pattern(pattern: str) -> list[str]:
    """Tokenize Babel CLDR pattern into individual tokens.

    v0.8.0: Token-based approach replaces regex word boundary approach.
    This correctly handles patterns like "d.MM.yyyy" where "d" is adjacent
    to punctuation without word boundaries.

    Args:
        pattern: Babel CLDR date pattern (e.g., "d.MM.yyyy")

    Returns:
        List of tokens (e.g., ["d", ".", "MM", ".", "yyyy"])
    """
    tokens: list[str] = []
    i = 0
    n = len(pattern)

    while i < n:
        char = pattern[i]

        # Check for quoted literal (single quotes in CLDR patterns)
        if char == "'":
            # Find closing quote
            j = i + 1
            while j < n and pattern[j] != "'":
                j += 1
            # Include content between quotes as literal
            if j > i + 1:
                tokens.append(pattern[i + 1 : j])
            i = j + 1
            continue

        # Check for pattern letter sequences (a-zA-Z)
        if char.isalpha():
            # Collect consecutive same letters (e.g., "yyyy", "MM", "dd")
            j = i + 1
            while j < n and pattern[j] == char:
                j += 1
            tokens.append(pattern[i:j])
            i = j
            continue

        # Everything else is a literal (punctuation, spaces, etc.)
        tokens.append(char)
        i += 1

    return tokens


def _babel_to_strptime(babel_pattern: str) -> str:
    """Convert Babel CLDR pattern to Python strptime format.

    v0.8.0: Token-based converter replaces regex approach.
    Fixes edge cases with word boundaries in patterns like "d.MM.yyyy".

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
    tokens = _tokenize_babel_pattern(babel_pattern)
    result_parts: list[str] = []

    for token in tokens:
        # Check if token is a Babel pattern token
        if token in _BABEL_TOKEN_MAP:
            result_parts.append(_BABEL_TOKEN_MAP[token])
        else:
            # Literal: pass through (punctuation, spaces, etc.)
            result_parts.append(token)

    return "".join(result_parts)
