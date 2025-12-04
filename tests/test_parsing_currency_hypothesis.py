"""Hypothesis-based property tests for currency parsing.

Focus on financial precision and edge cases.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from ftllexbuffer.parsing import parse_currency
from ftllexbuffer.parsing.currency import _CURRENCY_SYMBOL_MAP


class TestParseCurrencyHypothesis:
    """Property-based tests for parse_currency()."""

    @given(
        amount=st.decimals(
            min_value=Decimal("0.01"),
            max_value=Decimal("999999.99"),
            places=2,
        ),
        currency_symbol=st.sampled_from(["€", "$", "£", "¥", "₹", "₽", "₪", "₫", "₱"]),
    )
    @settings(max_examples=200)
    def test_parse_currency_roundtrip_financial_precision(
        self, amount: Decimal, currency_symbol: str
    ) -> None:
        """Roundtrip parsing preserves financial precision (critical for accounting)."""
        # Format: symbol + amount (no locale formatting for simplicity)
        currency_str = f"{currency_symbol}{amount}"

        result = parse_currency(currency_str, "en_US")
        assert result is not None

        parsed_amount, currency_code = result

        # Must preserve exact decimal value (no float rounding)
        assert parsed_amount == amount, f"Expected {amount}, got {parsed_amount}"
        assert isinstance(parsed_amount, Decimal), "Must return Decimal for precision"

        # Currency code must be valid
        assert len(currency_code) == 3
        assert currency_code.isupper()

    @given(
        currency_code=st.text(
            alphabet=st.characters(min_codepoint=65, max_codepoint=90),  # A-Z
            min_size=3,
            max_size=3,
        ),
    )
    @settings(max_examples=100)
    def test_parse_currency_iso_code_format(self, currency_code: str) -> None:
        """ISO 4217 currency codes (3 uppercase letters) should be recognized."""
        amount_str = f"{currency_code} 123.45"

        result = parse_currency(amount_str, "en_US")
        assert result is not None

        parsed_amount, parsed_code = result

        # Should preserve ISO code exactly
        assert parsed_code == currency_code
        assert parsed_amount == Decimal("123.45")

    @given(
        unknown_symbol=st.text(
            alphabet=st.characters(
                whitelist_categories=("So",),  # Other symbols
                blacklist_characters="€$£¥₹₽¢₡₦₧₨₩₪₫₱₴₵₸₺₼₾",
            ),
            min_size=1,
            max_size=1,
        ).filter(lambda x: x not in "€$£¥₹₽¢₡₦₧₨₩₪₫₱₴₵₸₺₼₾"),
    )
    @settings(max_examples=50)
    def test_parse_currency_unknown_symbol_strict_mode(self, unknown_symbol: str) -> None:
        """Unknown currency symbols should raise ValueError in strict mode."""
        # Lines 96-98 coverage - symbols not in regex pattern
        currency_str = f"{unknown_symbol}100.50"

        with pytest.raises(
            ValueError, match="No currency symbol or code found"
        ):
            parse_currency(currency_str, "en_US", strict=True)

    @given(
        unknown_symbol=st.text(
            alphabet=st.characters(
                whitelist_categories=("So",),
                blacklist_characters="€$£¥₹₽¢₡₦₧₨₩₪₫₱₴₵₸₺₼₾",
            ),
            min_size=1,
            max_size=1,
        ).filter(lambda x: x not in "€$£¥₹₽¢₡₦₧₨₩₪₫₱₴₵₸₺₼₾"),
    )
    @settings(max_examples=50)
    def test_parse_currency_unknown_symbol_non_strict(self, unknown_symbol: str) -> None:
        """Unknown currency symbols should return None in non-strict mode."""
        currency_str = f"{unknown_symbol}100.50"

        result = parse_currency(currency_str, "en_US", strict=False)
        assert result is None

    def test_parse_currency_symbol_in_regex_but_not_in_map(self) -> None:
        """Test defensive code path: symbol in regex but not in mapping."""
        # Lines 108-111 coverage - this tests internal consistency
        # In production, all symbols in regex are in _CURRENCY_SYMBOL_MAP
        # This test documents the defensive behavior if they diverge

        # The regex pattern is: ([€$£¥₹₽¢₡₦₧₨₩₪₫₱₴₵₸₺₼₾]|[A-Z]{3})
        # All these symbols ARE in the map, so this is defensive code

        # To exercise lines 108-111, we'd need to:
        # 1. Modify parse_currency to use a different regex
        # 2. Or mock _CURRENCY_SYMBOL_MAP
        # For now, verify all regex symbols are in the map (no divergence)

        regex_symbols = "€$£¥₹₽¢₡₦₧₨₩₪₫₱₴₵₸₺₼₾"
        for symbol in regex_symbols:
            assert (
                symbol in _CURRENCY_SYMBOL_MAP
            ), f"Symbol {symbol} in regex but not in map (defensive code would trigger)"

        # This documents that lines 108-111 are defensive code for maintainability

    @given(
        invalid_number=st.one_of(
            st.text(
                alphabet=st.characters(whitelist_categories=("L",)),  # Letters only
                min_size=1,
                max_size=10,
            ).filter(lambda x: x.upper() not in ("NAN", "INFINITY", "INF")),
            st.just("abc"),
            st.just("xyz123"),
            st.just("!@#"),
            st.just(""),
        ),
    )
    @settings(max_examples=50)
    def test_parse_currency_invalid_number_strict_mode(self, invalid_number: str) -> None:
        """Invalid numbers should raise ValueError in strict mode (NumberFormatError)."""
        # Lines 122-126 coverage
        # Note: Babel accepts NaN/Infinity/Inf (any case) as valid Decimal values
        currency_str = f"${invalid_number}"

        with pytest.raises(ValueError, match="Failed to parse amount"):
            parse_currency(currency_str, "en_US", strict=True)

    @given(
        invalid_number=st.one_of(
            st.text(
                alphabet=st.characters(whitelist_categories=("L",)),
                min_size=1,
                max_size=10,
            ).filter(lambda x: x.upper() not in ("NAN", "INFINITY", "INF")),
            st.just("abc"),
            st.just("xyz123"),
            st.just("!@#"),
            st.just(""),
        ),
    )
    @settings(max_examples=50)
    def test_parse_currency_invalid_number_non_strict(self, invalid_number: str) -> None:
        """Invalid numbers should return None in non-strict mode."""
        # Note: Babel accepts NaN/Infinity/Inf (any case) as valid Decimal values
        currency_str = f"${invalid_number}"

        result = parse_currency(currency_str, "en_US", strict=False)
        assert result is None

    @given(
        value=st.one_of(
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.lists(st.integers()),
            st.dictionaries(st.text(), st.integers()),
        ),
    )
    @settings(max_examples=50)
    def test_parse_currency_type_error_strict_mode(self, value: object) -> None:
        """Non-string types should raise ValueError in strict mode (TypeError path)."""
        # Lines 133-134, 136 coverage
        with pytest.raises(ValueError, match="Failed to parse currency"):
            parse_currency(value, "en_US", strict=True)

    @given(
        value=st.one_of(
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.lists(st.integers()),
        ),
    )
    @settings(max_examples=50)
    def test_parse_currency_type_error_non_strict(self, value: object) -> None:
        """Non-string types should return None in non-strict mode."""
        result = parse_currency(value, "en_US", strict=False)
        assert result is None

    @given(
        amount=st.decimals(
            min_value=Decimal("-999999.99"),
            max_value=Decimal("-0.01"),
            places=2,
        ),
    )
    @settings(max_examples=100)
    def test_parse_currency_negative_amounts(self, amount: Decimal) -> None:
        """Negative amounts should parse correctly (debt, refunds)."""
        currency_str = f"${amount}"

        result = parse_currency(currency_str, "en_US")
        assert result is not None

        parsed_amount, _ = result

        # Negative amounts are valid for accounting
        assert parsed_amount == amount
        assert parsed_amount < 0

    @given(
        amount=st.decimals(
            min_value=Decimal("0.001"),
            max_value=Decimal("0.999"),
            places=3,
        ),
    )
    @settings(max_examples=100)
    def test_parse_currency_fractional_amounts(self, amount: Decimal) -> None:
        """Sub-dollar amounts should preserve precision (critical for financial)."""
        currency_str = f"${amount}"

        result = parse_currency(currency_str, "en_US")
        assert result is not None

        parsed_amount, _ = result

        # Must preserve fractional precision
        assert parsed_amount == amount
        assert parsed_amount < Decimal("1.00")

    @given(
        locale=st.sampled_from(["en_US", "de_DE", "fr_FR", "ja_JP", "lv_LV", "pl_PL"]),
    )
    @settings(max_examples=50)
    def test_parse_currency_locale_independence(self, locale: str) -> None:
        """Currency parsing should work across locales."""
        # Use ISO code (universal)
        currency_str = "EUR 1234.56"

        result = parse_currency(currency_str, locale)
        assert result is not None

        parsed_amount, currency_code = result

        assert currency_code == "EUR"
        # Note: Babel parsing may interpret differently based on locale
        # Main check: doesn't crash and returns valid Decimal
        assert isinstance(parsed_amount, Decimal)

    @given(
        value=st.text(
            alphabet=st.characters(min_codepoint=32, max_codepoint=126),  # ASCII printable
            min_size=1,
            max_size=20,
        ).filter(
            lambda x: not any(
                symbol in x for symbol in "€$£¥₹₽¢₡₦₧₨₩₪₫₱₴₵₸₺₼₾"
            )
            and not any(
                x[i : i + 3].isupper() and x[i : i + 3].isalpha() for i in range(len(x) - 2)
            )
        ),
    )
    @settings(max_examples=100)
    def test_parse_currency_no_symbol_returns_none(self, value: str) -> None:
        """Strings without currency symbols/codes should return None in non-strict."""
        result = parse_currency(value, "en_US", strict=False)
        assert result is None

    @given(
        value=st.text(
            alphabet=st.characters(min_codepoint=32, max_codepoint=126),
            min_size=1,
            max_size=20,
        ).filter(
            lambda x: not any(
                symbol in x for symbol in "€$£¥₹₽¢₡₦₧₨₩₪₫₱₴₵₸₺₼₾"
            )
            and not any(
                x[i : i + 3].isupper() and x[i : i + 3].isalpha() for i in range(len(x) - 2)
            )
        ),
    )
    @settings(max_examples=100)
    def test_parse_currency_no_symbol_strict_raises(self, value: str) -> None:
        """Strings without currency symbols/codes should raise in strict mode."""
        with pytest.raises(ValueError, match="No currency symbol or code found"):
            parse_currency(value, "en_US", strict=True)


class TestCurrencyMetamorphicProperties:
    """Metamorphic properties for currency parsing."""

    @given(
        amount1=st.decimals(min_value=Decimal("0.01"), max_value=Decimal("999.99"), places=2),
        amount2=st.decimals(min_value=Decimal("0.01"), max_value=Decimal("999.99"), places=2),
        currency=st.sampled_from(["EUR", "USD", "GBP", "JPY"]),
    )
    @settings(max_examples=100)
    def test_parse_currency_comparison_property(
        self, amount1: Decimal, amount2: Decimal, currency: str
    ) -> None:
        """parse(format(a)) < parse(format(b)) iff a < b (ordering preserved)."""
        from ftllexbuffer.runtime.functions import currency_format

        formatted1 = currency_format(float(amount1), "en_US", currency=currency)
        formatted2 = currency_format(float(amount2), "en_US", currency=currency)

        result1 = parse_currency(formatted1, "en_US")
        result2 = parse_currency(formatted2, "en_US")

        assert result1 is not None
        assert result2 is not None

        parsed1, _ = result1
        parsed2, _ = result2

        # Ordering must be preserved
        if amount1 < amount2:
            assert parsed1 < parsed2
        elif amount1 > amount2:
            assert parsed1 > parsed2
        else:
            assert parsed1 == parsed2

    @given(
        amount=st.decimals(min_value=Decimal("0.01"), max_value=Decimal("999999.99"), places=2),
        locale1=st.sampled_from(["en_US", "de_DE", "lv_LV"]),
        locale2=st.sampled_from(["en_US", "de_DE", "lv_LV"]),
    )
    @settings(max_examples=100)
    def test_parse_currency_locale_format_independence(
        self, amount: Decimal, locale1: str, locale2: str
    ) -> None:
        """parse(format(x, L1), L1) == parse(format(x, L2), L2) for all locales."""
        from ftllexbuffer.runtime.functions import currency_format

        # Format in different locales
        formatted1 = currency_format(float(amount), locale1, currency="EUR")
        formatted2 = currency_format(float(amount), locale2, currency="EUR")

        # Parse with respective locales
        result1 = parse_currency(formatted1, locale1)
        result2 = parse_currency(formatted2, locale2)

        assert result1 is not None
        assert result2 is not None

        parsed1, code1 = result1
        parsed2, code2 = result2

        # Numeric value and currency code should be identical
        assert parsed1 == parsed2 == amount
        assert code1 == code2 == "EUR"

    @given(
        amount=st.decimals(min_value=Decimal("0.01"), max_value=Decimal("999.99"), places=2),
    )
    @settings(max_examples=100)
    def test_parse_currency_addition_homomorphism(self, amount: Decimal) -> None:
        """parse(format(a)) + parse(format(a)) == parse(format(2*a)) (within precision)."""
        from ftllexbuffer.runtime.functions import currency_format

        formatted1 = currency_format(float(amount), "en_US", currency="USD")
        formatted2 = currency_format(float(amount * 2), "en_US", currency="USD")

        result1 = parse_currency(formatted1, "en_US")
        result2 = parse_currency(formatted2, "en_US")

        assert result1 is not None
        assert result2 is not None

        parsed1, _ = result1
        parsed2, _ = result2

        # Addition property (within Decimal precision)
        assert parsed1 + parsed1 == parsed2
