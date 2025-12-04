"""Hypothesis-based property tests for number parsing.

Focus on precision, locale independence, and roundtrip properties.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from ftllexbuffer.parsing import parse_decimal, parse_number


class TestParseNumberHypothesis:
    """Property-based tests for parse_number()."""

    @given(
        value=st.floats(
            min_value=-999999.99,
            max_value=999999.99,
            allow_nan=False,
            allow_infinity=False,
        ),
    )
    @settings(max_examples=200)
    def test_parse_number_always_returns_float(self, value: float) -> None:
        """parse_number always returns float type."""
        # Format then parse
        from ftllexbuffer.runtime.functions import number_format

        formatted = number_format(value, "en_US")
        result = parse_number(formatted, "en_US")

        assert result is not None
        assert isinstance(result, float)

    @given(
        value=st.floats(
            min_value=-999999.99,
            max_value=999999.99,
            allow_nan=False,
            allow_infinity=False,
        ),
        locale=st.sampled_from(["en_US", "de_DE", "fr_FR", "lv_LV", "pl_PL", "ja_JP"]),
    )
    @settings(max_examples=200)
    def test_parse_number_roundtrip_preserves_value(
        self, value: float, locale: str
    ) -> None:
        """Roundtrip (format → parse → format) preserves numeric value within float precision."""
        from ftllexbuffer.runtime.functions import number_format

        # Format → parse → compare
        formatted = number_format(value, locale)
        parsed = parse_number(formatted, locale)

        assert parsed is not None
        # Float precision: allow small rounding error
        assert abs(parsed - value) < 0.01

    @given(
        invalid_input=st.one_of(
            st.text(
                alphabet=st.characters(whitelist_categories=("L",)),
                min_size=1,
                max_size=20,
            ).filter(lambda x: x.upper() not in ("NAN", "INFINITY", "INF")),
            st.just("abc"),
            st.just("xyz123"),
            st.just("!@#$%"),
            st.just(""),
        ),
    )
    @settings(max_examples=100)
    def test_parse_number_invalid_strict_mode(self, invalid_input: str) -> None:
        """Invalid numbers raise ValueError in strict mode."""
        # Note: Babel accepts NaN/Infinity/Inf
        with pytest.raises(ValueError, match="Failed to parse number"):
            parse_number(invalid_input, "en_US", strict=True)

    @given(
        invalid_input=st.one_of(
            st.text(alphabet=st.characters(whitelist_categories=("L",)), min_size=1).filter(
                lambda x: x.upper() not in ("NAN", "INFINITY", "INF")
            ),
            st.just("invalid"),
        ),
    )
    @settings(max_examples=100)
    def test_parse_number_invalid_non_strict(self, invalid_input: str) -> None:
        """Invalid numbers return None in non-strict mode."""
        result = parse_number(invalid_input, "en_US", strict=False)
        assert result is None

    @given(
        value=st.one_of(
            st.integers(),
            st.lists(st.integers()),
            st.dictionaries(st.text(), st.integers()),
        ),
    )
    @settings(max_examples=50)
    def test_parse_number_type_error_strict(self, value: object) -> None:
        """Non-string types raise ValueError in strict mode."""
        with pytest.raises(ValueError, match="Failed to parse number"):
            parse_number(value, "en_US", strict=True)

    @given(
        value=st.one_of(
            st.integers(),
            st.lists(st.integers()),
        ),
    )
    @settings(max_examples=50)
    def test_parse_number_type_error_non_strict(self, value: object) -> None:
        """Non-string types return None in non-strict mode."""
        result = parse_number(value, "en_US", strict=False)
        assert result is None


class TestParseDecimalHypothesis:
    """Property-based tests for parse_decimal()."""

    @given(
        value=st.decimals(
            min_value=Decimal("-999999.99"),
            max_value=Decimal("999999.99"),
            places=2,
        ),
    )
    @settings(max_examples=200)
    def test_parse_decimal_always_returns_decimal(self, value: Decimal) -> None:
        """parse_decimal always returns Decimal type."""
        from ftllexbuffer.runtime.functions import number_format

        formatted = number_format(float(value), "en_US")
        result = parse_decimal(formatted, "en_US")

        assert result is not None
        assert isinstance(result, Decimal)

    @given(
        value=st.decimals(
            min_value=Decimal("0.01"),
            max_value=Decimal("999999.99"),
            places=2,
        ),
        locale=st.sampled_from(["en_US", "de_DE", "fr_FR", "lv_LV", "pl_PL", "ja_JP"]),
    )
    @settings(max_examples=200)
    def test_parse_decimal_roundtrip_exact_precision(
        self, value: Decimal, locale: str
    ) -> None:
        """Roundtrip preserves exact Decimal precision (critical for financial)."""
        from ftllexbuffer.runtime.functions import number_format

        # Format → parse → compare
        formatted = number_format(float(value), locale, minimum_fraction_digits=2)
        parsed = parse_decimal(formatted, locale)

        assert parsed is not None
        # Decimal must preserve exact value
        assert parsed == value

    @given(
        value=st.decimals(
            min_value=Decimal("-999999.99"),
            max_value=Decimal("-0.01"),
            places=2,
        ),
    )
    @settings(max_examples=100)
    def test_parse_decimal_negative_amounts(self, value: Decimal) -> None:
        """Negative decimals parse correctly."""
        from ftllexbuffer.runtime.functions import number_format

        formatted = number_format(float(value), "en_US", minimum_fraction_digits=2)
        parsed = parse_decimal(formatted, "en_US")

        assert parsed is not None
        assert parsed == value
        assert parsed < 0

    @given(
        value=st.decimals(
            min_value=Decimal("0.001"),
            max_value=Decimal("0.999"),
            places=3,
        ),
    )
    @settings(max_examples=100)
    def test_parse_decimal_fractional_precision(self, value: Decimal) -> None:
        """Sub-unit decimals preserve fractional precision."""
        from ftllexbuffer.runtime.functions import number_format

        formatted = number_format(float(value), "en_US", minimum_fraction_digits=3)
        parsed = parse_decimal(formatted, "en_US")

        assert parsed is not None
        assert parsed == value
        assert parsed < Decimal("1.00")

    @given(
        invalid_input=st.one_of(
            st.text(
                alphabet=st.characters(whitelist_categories=("L",)),
                min_size=1,
                max_size=20,
            ).filter(lambda x: x.upper() not in ("NAN", "INFINITY", "INF")),
            st.just("abc"),
            st.just("not-a-number"),
            st.just(""),
        ),
    )
    @settings(max_examples=100)
    def test_parse_decimal_invalid_strict_mode(self, invalid_input: str) -> None:
        """Invalid decimals raise ValueError in strict mode."""
        with pytest.raises(ValueError, match="Failed to parse decimal"):
            parse_decimal(invalid_input, "en_US", strict=True)

    @given(
        invalid_input=st.one_of(
            st.text(alphabet=st.characters(whitelist_categories=("L",)), min_size=1).filter(
                lambda x: x.upper() not in ("NAN", "INFINITY", "INF")
            ),
            st.just("invalid"),
        ),
    )
    @settings(max_examples=100)
    def test_parse_decimal_invalid_non_strict(self, invalid_input: str) -> None:
        """Invalid decimals return None in non-strict mode."""
        result = parse_decimal(invalid_input, "en_US", strict=False)
        assert result is None

    @given(
        locale=st.sampled_from(["en_US", "de_DE", "fr_FR", "lv_LV", "pl_PL", "ja_JP"]),
        value=st.decimals(
            min_value=Decimal("100.00"),
            max_value=Decimal("999999.99"),
            places=2,
        ),
    )
    @settings(max_examples=100)
    def test_parse_decimal_locale_independence_for_large_numbers(
        self, locale: str, value: Decimal
    ) -> None:
        """Large numbers with grouping parse correctly across locales."""
        from ftllexbuffer.runtime.functions import number_format

        formatted = number_format(
            float(value), locale, use_grouping=True, minimum_fraction_digits=2
        )
        parsed = parse_decimal(formatted, locale)

        assert parsed is not None
        # Should handle grouping separators correctly
        assert parsed == value


class TestParsingMetamorphicProperties:
    """Metamorphic properties for number parsing."""

    @given(
        value=st.decimals(
            min_value=Decimal("0.01"),
            max_value=Decimal("9999.99"),
            places=2,
        ),
    )
    @settings(max_examples=100)
    def test_parse_order_independence(self, value: Decimal) -> None:
        """Parsing result independent of intermediate formatting steps."""
        from ftllexbuffer.runtime.functions import number_format

        # Path 1: Direct format → parse
        formatted1 = number_format(float(value), "en_US", minimum_fraction_digits=2)
        parsed1 = parse_decimal(formatted1, "en_US")

        # Path 2: Format with grouping → parse
        formatted2 = number_format(
            float(value), "en_US", use_grouping=True, minimum_fraction_digits=2
        )
        parsed2 = parse_decimal(formatted2, "en_US")

        # Both paths should yield same numeric value
        assert parsed1 == parsed2 == value

    @given(
        value=st.decimals(
            min_value=Decimal("0.01"),
            max_value=Decimal("9999.99"),
            places=2,
        ),
    )
    @settings(max_examples=100)
    def test_parse_idempotence(self, value: Decimal) -> None:
        """Parsing formatted value multiple times yields same result."""
        from ftllexbuffer.runtime.functions import number_format

        formatted = number_format(float(value), "en_US", minimum_fraction_digits=2)

        # Parse multiple times
        parsed1 = parse_decimal(formatted, "en_US")
        parsed2 = parse_decimal(formatted, "en_US")
        parsed3 = parse_decimal(formatted, "en_US")

        # All results identical
        assert parsed1 == parsed2 == parsed3 == value

    @given(
        value=st.decimals(
            min_value=Decimal("1.00"),
            max_value=Decimal("999.99"),
            places=2,
        ),
    )
    @settings(max_examples=100)
    def test_parse_format_parse_stability(self, value: Decimal) -> None:
        """parse(format(parse(format(x)))) == parse(format(x))."""
        from ftllexbuffer.runtime.functions import number_format

        # First cycle
        formatted1 = number_format(float(value), "en_US", minimum_fraction_digits=2)
        parsed1 = parse_decimal(formatted1, "en_US")

        # Second cycle
        assert parsed1 is not None
        formatted2 = number_format(float(parsed1), "en_US", minimum_fraction_digits=2)
        parsed2 = parse_decimal(formatted2, "en_US")

        # Should stabilize
        assert parsed1 == parsed2
