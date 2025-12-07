"""Hypothesis property-based tests for parsing type guards.

Tests type guard correctness, type narrowing properties, and edge cases.
Ensures 100% coverage of parsing/guards.py.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

from hypothesis import given, settings
from hypothesis import strategies as st

from ftllexbuffer.parsing.guards import (
    is_valid_currency,
    is_valid_date,
    is_valid_datetime,
    is_valid_decimal,
    is_valid_number,
)

# ============================================================================
# HYPOTHESIS STRATEGIES
# ============================================================================


# Strategy for Decimal values
decimals = st.decimals(allow_nan=True, allow_infinity=True, places=2)

# Strategy for floats
floats = st.floats(allow_nan=True, allow_infinity=True)

# Strategy for currency tuples
currency_tuples = st.tuples(
    st.decimals(allow_nan=True, allow_infinity=True, places=2),
    st.from_regex(r"[A-Z]{3}", fullmatch=True),
)


# ============================================================================
# PROPERTY TESTS - is_valid_decimal
# ============================================================================


class TestValidDecimalGuard:
    """Test is_valid_decimal() type guard properties."""

    @given(value=st.decimals(allow_nan=False, allow_infinity=False))
    @settings(max_examples=200)
    def test_finite_decimal_returns_true(self, value: Decimal) -> None:
        """PROPERTY: Finite Decimal values return True."""
        assert is_valid_decimal(value) is True

    @given(value=st.none())
    @settings(max_examples=50)
    def test_none_returns_false(self, value: None) -> None:
        """PROPERTY: None returns False."""
        assert is_valid_decimal(value) is False

    @given(value=st.just(Decimal("NaN")))
    @settings(max_examples=50)
    def test_nan_returns_false(self, value: Decimal) -> None:
        """PROPERTY: NaN Decimal returns False (line 52)."""
        assert value.is_nan()
        assert is_valid_decimal(value) is False

    @given(value=st.just(Decimal("Infinity")))
    @settings(max_examples=50)
    def test_positive_infinity_returns_false(self, value: Decimal) -> None:
        """PROPERTY: Positive infinity Decimal returns False (line 52)."""
        assert value.is_infinite()
        assert is_valid_decimal(value) is False

    @given(value=st.just(Decimal("-Infinity")))
    @settings(max_examples=50)
    def test_negative_infinity_returns_false(self, value: Decimal) -> None:
        """PROPERTY: Negative infinity Decimal returns False (line 52)."""
        assert value.is_infinite()
        assert is_valid_decimal(value) is False


# ============================================================================
# PROPERTY TESTS - is_valid_number
# ============================================================================


class TestValidNumberGuard:
    """Test is_valid_number() type guard properties."""

    @given(value=st.floats(allow_nan=False, allow_infinity=False))
    @settings(max_examples=200)
    def test_finite_float_returns_true(self, value: float) -> None:
        """PROPERTY: Finite float values return True."""
        assert is_valid_number(value) is True

    @given(value=st.none())
    @settings(max_examples=50)
    def test_none_returns_false(self, value: None) -> None:
        """PROPERTY: None returns False."""
        assert is_valid_number(value) is False

    @given(value=st.just(float("nan")))
    @settings(max_examples=50)
    def test_nan_returns_false(self, value: float) -> None:
        """PROPERTY: NaN float returns False (line 74)."""
        assert is_valid_number(value) is False

    @given(value=st.just(float("inf")))
    @settings(max_examples=50)
    def test_positive_infinity_returns_false(self, value: float) -> None:
        """PROPERTY: Positive infinity float returns False (line 74)."""
        assert is_valid_number(value) is False

    @given(value=st.just(float("-inf")))
    @settings(max_examples=50)
    def test_negative_infinity_returns_false(self, value: float) -> None:
        """PROPERTY: Negative infinity float returns False (line 74)."""
        assert is_valid_number(value) is False


# ============================================================================
# PROPERTY TESTS - is_valid_currency
# ============================================================================


class TestValidCurrencyGuard:
    """Test is_valid_currency() type guard properties."""

    @given(
        amount=st.decimals(allow_nan=False, allow_infinity=False, places=2),
        currency=st.from_regex(r"[A-Z]{3}", fullmatch=True),
    )
    @settings(max_examples=200)
    def test_valid_currency_tuple_returns_true(
        self, amount: Decimal, currency: str
    ) -> None:
        """PROPERTY: Valid (Decimal, str) tuple returns True (line 99)."""
        value = (amount, currency)
        assert is_valid_currency(value) is True

    @given(value=st.none())
    @settings(max_examples=50)
    def test_none_returns_false(self, value: None) -> None:
        """PROPERTY: None returns False."""
        assert is_valid_currency(value) is False

    @given(currency=st.from_regex(r"[A-Z]{3}", fullmatch=True))
    @settings(max_examples=50)
    def test_nan_amount_returns_false(self, currency: str) -> None:
        """PROPERTY: NaN amount returns False (line 99)."""
        value = (Decimal("NaN"), currency)
        assert is_valid_currency(value) is False

    @given(currency=st.from_regex(r"[A-Z]{3}", fullmatch=True))
    @settings(max_examples=50)
    def test_infinite_amount_returns_false(self, currency: str) -> None:
        """PROPERTY: Infinite amount returns False (line 99)."""
        value = (Decimal("Infinity"), currency)
        assert is_valid_currency(value) is False


# ============================================================================
# PROPERTY TESTS - is_valid_date
# ============================================================================


class TestValidDateGuard:
    """Test is_valid_date() type guard properties."""

    @given(
        year=st.integers(min_value=1900, max_value=2100),
        month=st.integers(min_value=1, max_value=12),
        day=st.integers(min_value=1, max_value=28),
    )
    @settings(max_examples=200)
    def test_valid_date_returns_true(self, year: int, month: int, day: int) -> None:
        """PROPERTY: Valid date objects return True (line 120)."""
        value = date(year, month, day)
        assert is_valid_date(value) is True

    @given(value=st.none())
    @settings(max_examples=50)
    def test_none_returns_false(self, value: None) -> None:
        """PROPERTY: None returns False (line 120)."""
        assert is_valid_date(value) is False


# ============================================================================
# PROPERTY TESTS - is_valid_datetime
# ============================================================================


class TestValidDatetimeGuard:
    """Test is_valid_datetime() type guard properties."""

    @given(
        year=st.integers(min_value=1900, max_value=2100),
        month=st.integers(min_value=1, max_value=12),
        day=st.integers(min_value=1, max_value=28),
        hour=st.integers(min_value=0, max_value=23),
        minute=st.integers(min_value=0, max_value=59),
    )
    @settings(max_examples=200)
    def test_valid_datetime_returns_true(
        self, year: int, month: int, day: int, hour: int, minute: int
    ) -> None:
        """PROPERTY: Valid datetime objects return True (line 141)."""
        value = datetime(year, month, day, hour, minute, tzinfo=UTC)
        assert is_valid_datetime(value) is True

    @given(value=st.none())
    @settings(max_examples=50)
    def test_none_returns_false(self, value: None) -> None:
        """PROPERTY: None returns False (line 141)."""
        assert is_valid_datetime(value) is False


# ============================================================================
# PROPERTY TESTS - TYPE NARROWING INTEGRATION
# ============================================================================


class TestTypeNarrowingIntegration:
    """Test type guard integration with actual parsing functions."""

    @given(
        amount=st.decimals(
            min_value=Decimal("0.01"), max_value=Decimal("9999.99"), places=2
        ),
        currency=st.from_regex(r"[A-Z]{3}", fullmatch=True),
    )
    @settings(max_examples=100)
    def test_currency_type_narrowing(self, amount: Decimal, currency: str) -> None:
        """PROPERTY: Type guard correctly narrows currency result type."""
        from ftllexbuffer.parsing import parse_currency  # noqa: PLC0415

        currency_str = f"{currency} {amount}"
        parsed = parse_currency(currency_str, "en_US")

        if is_valid_currency(parsed):
            # After type narrowing, mypy knows parsed is tuple[Decimal, str]
            parsed_amount, parsed_currency = parsed
            assert isinstance(parsed_amount, Decimal)
            assert isinstance(parsed_currency, str)
            assert parsed_amount.is_finite()

    @given(
        year=st.integers(min_value=2000, max_value=2068),
        month=st.integers(min_value=1, max_value=12),
        day=st.integers(min_value=1, max_value=28),
    )
    @settings(max_examples=100)
    def test_date_type_narrowing(self, year: int, month: int, day: int) -> None:
        """PROPERTY: Type guard correctly narrows date result type."""
        from ftllexbuffer.parsing import parse_date  # noqa: PLC0415

        date_str = f"{year:04d}-{month:02d}-{day:02d}"
        parsed = parse_date(date_str, "en_US")

        if is_valid_date(parsed):
            # After type narrowing, mypy knows parsed is date
            assert isinstance(parsed, date)
            assert parsed.year == year

    @given(
        year=st.integers(min_value=2000, max_value=2068),
        month=st.integers(min_value=1, max_value=12),
        day=st.integers(min_value=1, max_value=28),
        hour=st.integers(min_value=0, max_value=23),
        minute=st.integers(min_value=0, max_value=59),
    )
    @settings(max_examples=100)
    def test_datetime_type_narrowing(
        self, year: int, month: int, day: int, hour: int, minute: int
    ) -> None:
        """PROPERTY: Type guard correctly narrows datetime result type."""
        from ftllexbuffer.parsing import parse_datetime  # noqa: PLC0415

        datetime_str = f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:00"
        parsed = parse_datetime(datetime_str, "en_US")

        if is_valid_datetime(parsed):
            # After type narrowing, mypy knows parsed is datetime
            assert isinstance(parsed, datetime)
            assert parsed.year == year
