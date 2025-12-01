"""CLDR plural rules implementation for 30 languages.

Implements Unicode CLDR plural category selection for 30 locales.
Python 3.13+. No external dependencies for this module.

Supported locales (30 languages):
- English (en): one, other
- Mandarin Chinese (zh): other (no plurals)
- Hindi (hi): one, other
- Spanish (es): one, other
- French (fr): one, many, other
- Arabic (ar): zero, one, two, few, many, other (6 categories)
- Bengali (bn): one, other
- Portuguese (pt): one, many, other
- Russian (ru): one, few, many, other
- Japanese (ja): other (no plurals)
- German (de): one, other
- Javanese (jv): other (no plurals)
- Korean (ko): other (no plurals)
- Vietnamese (vi): other (no plurals)
- Telugu (te): one, other
- Turkish (tr): one, other
- Tamil (ta): one, other
- Marathi (mr): one, other
- Urdu (ur): one, other
- Italian (it): one, many, other
- Thai (th): other (no plurals)
- Gujarati (gu): one, other
- Polish (pl): one, few, many, other
- Ukrainian (uk): one, few, many, other
- Kannada (kn): one, other
- Odia (or): one, other
- Malayalam (ml): one, other
- Burmese (my): other (no plurals)
- Punjabi (pa): one, other
- Latvian (lv): zero, one, other

Reference: https://www.unicode.org/cldr/charts/47/supplemental/language_plural_rules.html

Architecture:
    Languages are grouped by rule complexity for maintainability:
    1. No-plural languages: zh, ja, jv, ko, vi, th, my → always "other"
    2. Simple-one languages: es, te, tr, ta, mr, ur, ml, or → n=1 → "one"
    3. Integer-one languages: en, de → i=1 and v=0 → "one"
    4. Zero-one languages: hi, bn, gu, kn → i=0 or n=1 → "one"
    5. Punjabi: pa → n=0..1 → "one"
    6. Slavic languages: ru, pl, uk → complex modulo rules
    7. Romance-many languages: fr, pt, it → millions rule
    8. Arabic: ar → 6 categories
    9. Latvian: lv → special rules

CLDR Operand Reference:
    n = absolute value of source number (integer and decimals)
    i = integer digits of n
    v = number of visible fraction digits (with trailing zeros)
    w = number of visible fraction digits (without trailing zeros)
    f = visible fraction digits (with trailing zeros)
    t = visible fraction digits (without trailing zeros)
    e = exponent of the source number (compact decimal exponent)
"""

from __future__ import annotations

# Languages with NO plural distinctions (always "other")
_NO_PLURAL_LANGUAGES = frozenset({"zh", "ja", "jv", "ko", "vi", "th", "my"})

# Languages with simple n=1 rule
_SIMPLE_ONE_LANGUAGES = frozenset({"es", "te", "tr", "ta", "mr", "ur", "ml", "or"})

# Languages with i=1 and v=0 rule (integer 1 only)
_INTEGER_ONE_LANGUAGES = frozenset({"en", "de"})

# Languages with i=0 or n=1 rule
_ZERO_ONE_LANGUAGES = frozenset({"hi", "bn", "gu", "kn"})

# Slavic languages with complex rules
_SLAVIC_LANGUAGES = frozenset({"ru", "pl", "uk"})

# Romance languages with "many" category (millions rule)
_ROMANCE_MANY_LANGUAGES = frozenset({"fr", "pt", "it"})


def select_plural_category(n: int | float, locale: str) -> str:
    """Select CLDR plural category for number.

    Args:
        n: Number to categorize
        locale: Locale code (e.g., "lv_LV", "en_US", "ar-SA")

    Returns:
        Plural category: "zero", "one", "two", "few", "many", or "other"

    Examples:
        >>> select_plural_category(0, "lv_LV")
        'zero'
        >>> select_plural_category(1, "en_US")
        'one'
        >>> select_plural_category(5, "ru_RU")
        'many'
        >>> select_plural_category(2, "ar_SA")
        'two'
        >>> select_plural_category(42, "ja_JP")
        'other'
    """
    # Extract language code: "lv_LV" → "lv", "en-US" → "en"
    lang = locale.replace("-", "_").split("_")[0].lower()

    # Route to appropriate rule group
    if lang in _NO_PLURAL_LANGUAGES:
        return "other"

    if lang in _SIMPLE_ONE_LANGUAGES:
        return _simple_one_rule(n)

    if lang in _INTEGER_ONE_LANGUAGES:
        return _integer_one_rule(n)

    if lang in _ZERO_ONE_LANGUAGES:
        return _zero_one_rule(n)

    if lang == "pa":
        return _punjabi_rule(n)

    if lang in _SLAVIC_LANGUAGES:
        return _slavic_rule(n, lang)

    if lang in _ROMANCE_MANY_LANGUAGES:
        return _romance_many_rule(n)

    if lang == "ar":
        return _arabic_rule(n)

    if lang == "lv":
        return _latvian_rule(n)

    # Fallback: simple one/other (most common pattern)
    return _simple_one_rule(n)


def _get_integer_part(n: int | float) -> int:
    """Get integer part of number (CLDR 'i' operand)."""
    return int(abs(n))


def _has_visible_decimals(n: int | float) -> bool:
    """Check if number has visible decimal digits (CLDR v > 0)."""
    if isinstance(n, int):
        return False
    return n != int(n)


def _simple_one_rule(n: int | float) -> str:
    """Simple n=1 rule: one if n equals 1, else other.

    Used by: Spanish, Telugu, Turkish, Tamil, Marathi, Urdu, Malayalam, Odia
    """
    return "one" if n == 1 else "other"


def _integer_one_rule(n: int | float) -> str:
    """Integer-one rule: one if i=1 and v=0 (integer 1 only).

    Used by: English, German

    CLDR: one → i = 1 and v = 0
    """
    i = _get_integer_part(n)
    v = _has_visible_decimals(n)
    return "one" if i == 1 and not v else "other"


def _zero_one_rule(n: int | float) -> str:
    """Zero-one rule: one if i=0 or n=1.

    Used by: Hindi, Bengali, Gujarati, Kannada

    CLDR: one → i = 0 or n = 1
    """
    i = _get_integer_part(n)
    return "one" if i == 0 or n == 1 else "other"


def _punjabi_rule(n: int | float) -> str:
    """Punjabi rule: one if n is 0 or 1.

    CLDR: one → n = 0..1
    """
    return "one" if n in (0, 1) else "other"


def _slavic_rule(n: int | float, _lang: str) -> str:
    """Slavic plural rules (Russian, Polish, Ukrainian).

    All use 4 categories: one, few, many, other

    CLDR rules:
    - one: v = 0 and i % 10 = 1 and i % 100 != 11
    - few: v = 0 and i % 10 = 2..4 and i % 100 != 12..14
    - many: v = 0 and (i % 10 = 0 or i % 10 = 5..9 or i % 100 = 11..14)
    - other: fractions and remaining cases
    """
    # Fractions use "other"
    if _has_visible_decimals(n):
        return "other"

    i = _get_integer_part(n)
    i_mod_10 = i % 10
    i_mod_100 = i % 100

    # "one" category
    if i_mod_10 == 1 and i_mod_100 != 11:
        return "one"

    # "few" category (2-4 ending, excluding 12-14)
    if 2 <= i_mod_10 <= 4 and not 12 <= i_mod_100 <= 14:
        return "few"

    # "many" category
    if i_mod_10 == 0 or 5 <= i_mod_10 <= 9 or 11 <= i_mod_100 <= 14:
        return "many"

    # All other cases (including Polish i=1, which is caught by line 211-212)
    return "other"


def _romance_many_rule(n: int | float) -> str:
    """Romance language rule with "many" category (French, Portuguese, Italian).

    CLDR rules:
    - one: i = 0..1 (for fr, pt) or i = 1 and v = 0 (for it)
    - many: compact notation for millions (e != 0..5) - simplified here
    - other: everything else

    Note: The "many" category in CLDR applies to compact notation
    (e.g., "1 million") which is rarely used in Fluent. We simplify
    to check for exact multiples of 1,000,000 with no decimals.
    """
    i = _get_integer_part(n)
    v = _has_visible_decimals(n)

    # one: i = 0 or 1 (covers 0, 0.x, 1, 1.x)
    if i in (0, 1):
        return "one"

    # many: exact millions (simplified CLDR rule)
    # Full CLDR: e = 0 and i != 0 and i % 1000000 = 0 and v = 0 or e != 0..5
    if not v and i != 0 and i % 1_000_000 == 0:
        return "many"

    return "other"


def _arabic_rule(n: int | float) -> str:
    """Arabic plural rules (6 categories - most complex).

    CLDR rules:
    - zero: n = 0
    - one: n = 1
    - two: n = 2
    - few: n % 100 = 3..10
    - many: n % 100 = 11..99
    - other: everything else (including fractions)
    """
    # Handle fractions
    if _has_visible_decimals(n):
        return "other"

    i = _get_integer_part(n)

    if i == 0:
        return "zero"
    if i == 1:
        return "one"
    if i == 2:
        return "two"

    i_mod_100 = i % 100
    if 3 <= i_mod_100 <= 10:
        return "few"
    if 11 <= i_mod_100 <= 99:
        return "many"

    return "other"


def _latvian_rule(n: int | float) -> str:
    """Latvian plural rules (3 categories).

    CLDR rules:
    - zero: n % 10 = 0 or n % 100 = 11..19
    - one: n % 10 = 1 and n % 100 != 11
    - other: everything else

    Examples:
    - zero: 0, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 30, 100, 1000
    - one: 1, 21, 31, 41, 51, 61, 71, 81, 101, 1001
    - other: 2, 3, 4, 5, 6, 7, 8, 9, 22, 23, 102, 1002
    """
    # Fractions use "other"
    if _has_visible_decimals(n):
        return "other"

    i = _get_integer_part(n)
    i_mod_10 = i % 10
    i_mod_100 = i % 100

    # "zero" category
    if i_mod_10 == 0 or 11 <= i_mod_100 <= 19:
        return "zero"

    # "one" category
    if i_mod_10 == 1 and i_mod_100 != 11:
        return "one"

    return "other"


# Exported for documentation and testing
SUPPORTED_LOCALES: frozenset[str] = frozenset({
    "en", "zh", "hi", "es", "fr", "ar", "bn", "pt", "ru", "ja",
    "de", "jv", "ko", "vi", "te", "tr", "ta", "mr", "ur", "it",
    "th", "gu", "pl", "uk", "kn", "or", "ml", "my", "pa", "lv",
})
