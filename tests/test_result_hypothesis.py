"""Hypothesis property-based tests for Result[T, E] monad.

Tests Success/Failure construction, unwrap/failure properties, immutability,
and type safety. Complements test_result.py with property-based testing.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from ftllexbuffer.result import Failure, Success

# ============================================================================
# HYPOTHESIS STRATEGIES
# ============================================================================


# Strategy for success values - keep reasonable collection bounds for performance
success_values = st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),  # No max_size - let Hypothesis decide
    st.booleans(),
    st.none(),
    st.lists(st.integers(), max_size=20),  # Keep bound for memory
    st.dictionaries(st.text(), st.integers(), max_size=10),  # Keep bound for memory
)

# Strategy for error values - keep reasonable collection bounds for performance
error_values = st.one_of(
    st.text(min_size=1),  # No max_size
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.lists(st.text(), max_size=10),  # Keep bound for memory
)


# ============================================================================
# PROPERTY TESTS - SUCCESS CONSTRUCTION
# ============================================================================


class TestSuccessProperties:
    """Test Success[T] construction and behavior properties."""

    @given(value=success_values)
    @settings(max_examples=200)
    def test_success_unwrap_returns_value(self, value) -> None:
        """PROPERTY: Success(x).unwrap() == x."""
        success = Success(value)
        assert success.unwrap() == value

    @given(value=success_values)
    @settings(max_examples=200)
    def test_success_failure_raises_attribute_error(self, value) -> None:
        """PROPERTY: Success(x).failure() raises AttributeError."""
        success = Success(value)
        with pytest.raises(AttributeError, match=r"Cannot call .failure\(\) on Success"):
            success.failure()

    @given(value=success_values)
    @settings(max_examples=200)
    def test_success_isinstance_check(self, value) -> None:
        """PROPERTY: Success(x) is instance of Success."""
        success = Success(value)
        assert isinstance(success, Success)
        assert not isinstance(success, Failure)  # type: ignore[unreachable]

    @given(value=success_values)
    @settings(max_examples=200)
    def test_success_equality_reflexive(self, value) -> None:
        """PROPERTY: Success(x) == Success(x) (reflexive)."""
        success = Success(value)
        assert success == success  # noqa: PLR0124  # pylint: disable=comparison-with-itself

    @given(value=success_values)
    @settings(max_examples=100)
    def test_success_equality_symmetric(self, value) -> None:
        """PROPERTY: Success(x) == Success(x) (symmetric)."""
        success1 = Success(value)
        success2 = Success(value)
        assert success1 == success2
        assert success2 == success1

    @given(value1=success_values, value2=success_values)
    @settings(max_examples=100)
    def test_success_different_values_not_equal(self, value1, value2) -> None:
        """PROPERTY: Success(x) != Success(y) when x != y."""
        if value1 != value2:
            success1 = Success(value1)
            success2 = Success(value2)
            assert success1 != success2


# ============================================================================
# PROPERTY TESTS - FAILURE CONSTRUCTION
# ============================================================================


class TestFailureProperties:
    """Test Failure[E] construction and behavior properties."""

    @given(error=error_values)
    @settings(max_examples=200)
    def test_failure_failure_returns_error(self, error) -> None:
        """PROPERTY: Failure(e).failure() == e."""
        failure = Failure(error)
        assert failure.failure() == error

    @given(error=error_values)
    @settings(max_examples=200)
    def test_failure_unwrap_raises_value_error(self, error) -> None:
        """PROPERTY: Failure(e).unwrap() raises ValueError."""
        failure = Failure(error)
        with pytest.raises(ValueError, match="Cannot unwrap Failure"):
            failure.unwrap()

    @given(error=error_values)
    @settings(max_examples=200)
    def test_failure_isinstance_check(self, error) -> None:
        """PROPERTY: Failure(e) is instance of Failure."""
        failure = Failure(error)
        assert isinstance(failure, Failure)
        assert not isinstance(failure, Success)  # type: ignore[unreachable]

    @given(error=error_values)
    @settings(max_examples=200)
    def test_failure_equality_reflexive(self, error) -> None:
        """PROPERTY: Failure(e) == Failure(e) (reflexive)."""
        failure = Failure(error)
        assert failure == failure  # noqa: PLR0124  # pylint: disable=comparison-with-itself

    @given(error=error_values)
    @settings(max_examples=100)
    def test_failure_equality_symmetric(self, error) -> None:
        """PROPERTY: Failure(e) == Failure(e) (symmetric)."""
        failure1 = Failure(error)
        failure2 = Failure(error)
        assert failure1 == failure2
        assert failure2 == failure1

    @given(error1=error_values, error2=error_values)
    @settings(max_examples=100)
    def test_failure_different_errors_not_equal(self, error1, error2) -> None:
        """PROPERTY: Failure(e1) != Failure(e2) when e1 != e2."""
        if error1 != error2:
            failure1 = Failure(error1)
            failure2 = Failure(error2)
            assert failure1 != failure2


# ============================================================================
# PROPERTY TESTS - SUCCESS VS FAILURE
# ============================================================================


class TestSuccessFailureInteraction:
    """Test properties of Success vs Failure interaction."""

    @given(value=success_values, error=error_values)
    @settings(max_examples=100)
    def test_success_not_equal_to_failure(self, value, error) -> None:
        """PROPERTY: Success(x) != Failure(e) always."""
        success = Success(value)
        failure = Failure(error)
        assert success != failure  # type: ignore[comparison-overlap]
        assert failure != success  # type: ignore[comparison-overlap]

    @given(value=success_values, error=error_values)
    @settings(max_examples=100)
    def test_isinstance_distinguishes_types(self, value, error) -> None:
        """PROPERTY: isinstance() correctly distinguishes Success from Failure."""
        success = Success(value)
        failure = Failure(error)

        assert isinstance(success, Success)
        assert not isinstance(success, Failure)  # type: ignore[unreachable]
        assert isinstance(failure, Failure)
        assert not isinstance(failure, Success)  # type: ignore[unreachable]


# ============================================================================
# PROPERTY TESTS - IMMUTABILITY
# ============================================================================


class TestImmutabilityProperties:
    """Test immutability (frozen=True) properties."""

    @given(value=success_values)
    @settings(max_examples=100)
    def test_success_immutable(self, value) -> None:
        """PROPERTY: Success is immutable (frozen=True)."""
        success = Success(value)

        # Attempt to modify _value should fail
        with pytest.raises(AttributeError):
            success._value = "modified"  # type: ignore[misc]

    @given(error=error_values)
    @settings(max_examples=100)
    def test_failure_immutable(self, error) -> None:
        """PROPERTY: Failure is immutable (frozen=True)."""
        failure = Failure(error)

        # Attempt to modify _error should fail
        with pytest.raises(AttributeError):
            failure._error = "modified"  # type: ignore[misc]

    @given(value=success_values)
    @settings(max_examples=100)
    def test_success_no_new_attributes(self, value) -> None:
        """PROPERTY: Cannot add new attributes to Success (slots=True)."""
        success = Success(value)

        # Attempt to add new attribute should fail
        with pytest.raises((AttributeError, TypeError)):
            success.new_attr = "value"  # type: ignore[attr-defined]

    @given(error=error_values)
    @settings(max_examples=100)
    def test_failure_no_new_attributes(self, error) -> None:
        """PROPERTY: Cannot add new attributes to Failure (slots=True)."""
        failure = Failure(error)

        # Attempt to add new attribute should fail
        with pytest.raises((AttributeError, TypeError)):
            failure.new_attr = "value"  # type: ignore[attr-defined]


# ============================================================================
# PROPERTY TESTS - IDEMPOTENCE
# ============================================================================


class TestIdempotenceProperties:
    """Test idempotent operations on Result types."""

    @given(value=success_values)
    @settings(max_examples=100)
    def test_success_unwrap_idempotent(self, value) -> None:
        """PROPERTY: Multiple unwrap() calls return same value."""
        success = Success(value)

        result1 = success.unwrap()
        result2 = success.unwrap()
        result3 = success.unwrap()

        assert result1 == result2 == result3

    @given(error=error_values)
    @settings(max_examples=100)
    def test_failure_failure_idempotent(self, error) -> None:
        """PROPERTY: Multiple failure() calls return same error."""
        failure = Failure(error)

        result1 = failure.failure()
        result2 = failure.failure()
        result3 = failure.failure()

        assert result1 == result2 == result3

    @given(value=success_values)
    @settings(max_examples=100)
    def test_success_isinstance_idempotent(self, value) -> None:
        """PROPERTY: Multiple isinstance() checks return same result."""
        success = Success(value)

        check1 = isinstance(success, Success)
        check2 = isinstance(success, Success)
        check3 = isinstance(success, Success)

        assert check1 == check2 == check3
        assert check1 is True

    @given(error=error_values)
    @settings(max_examples=100)
    def test_failure_isinstance_idempotent(self, error) -> None:
        """PROPERTY: Multiple isinstance() checks return same result."""
        failure = Failure(error)

        check1 = isinstance(failure, Failure)
        check2 = isinstance(failure, Failure)
        check3 = isinstance(failure, Failure)

        assert check1 == check2 == check3
        assert check1 is True


# ============================================================================
# PROPERTY TESTS - ROBUSTNESS
# ============================================================================


class TestRobustnessProperties:
    """Test Result robustness with edge cases."""

    @given(value=st.none())
    @settings(max_examples=50)
    def test_success_with_none_value(self, value) -> None:
        """ROBUSTNESS: Success(None) is valid."""
        success = Success(value)
        assert success.unwrap() is None

    @given(value=st.integers(min_value=-1000000, max_value=1000000))
    @settings(max_examples=100)
    def test_success_with_large_integers(self, value: int) -> None:
        """ROBUSTNESS: Success handles large integers."""
        success = Success(value)
        assert success.unwrap() == value

    @given(value=st.text(min_size=0, max_size=1000))
    @settings(max_examples=100)
    def test_success_with_long_strings(self, value: str) -> None:
        """ROBUSTNESS: Success handles long strings."""
        success = Success(value)
        assert success.unwrap() == value

    @given(value=st.lists(st.integers(), min_size=0, max_size=100))
    @settings(max_examples=50)
    def test_success_with_lists(self, value: list) -> None:
        """ROBUSTNESS: Success handles lists."""
        success = Success(value)
        assert success.unwrap() == value

    @given(value=st.dictionaries(st.text(max_size=10), st.integers(), max_size=20))
    @settings(max_examples=50)
    def test_success_with_dicts(self, value: dict) -> None:
        """ROBUSTNESS: Success handles dictionaries."""
        success = Success(value)
        assert success.unwrap() == value


# ============================================================================
# PROPERTY TESTS - HASHING
# ============================================================================


class TestHashingProperties:
    """Test hashability properties for use in sets/dicts."""

    @given(value=st.integers())
    @settings(max_examples=100)
    def test_success_hash_consistency(self, value: int) -> None:
        """PROPERTY: hash(Success(x)) is consistent across calls."""
        success = Success(value)

        hash1 = hash(success)
        hash2 = hash(success)
        hash3 = hash(success)

        assert hash1 == hash2 == hash3

    @given(error=st.text(min_size=1, max_size=100))
    @settings(max_examples=100)
    def test_failure_hash_consistency(self, error: str) -> None:
        """PROPERTY: hash(Failure(e)) is consistent across calls."""
        failure = Failure(error)

        hash1 = hash(failure)
        hash2 = hash(failure)
        hash3 = hash(failure)

        assert hash1 == hash2 == hash3

    @given(values=st.lists(st.integers(), min_size=2, max_size=10, unique=True))
    @settings(max_examples=50)
    def test_success_usable_in_set(self, values: list[int]) -> None:
        """PROPERTY: Success instances can be used in sets."""
        success_set = {Success(v) for v in values}

        assert len(success_set) == len(values)

    @given(errors=st.lists(st.text(min_size=1, max_size=20), min_size=2, max_size=10, unique=True))
    @settings(max_examples=50)
    def test_failure_usable_in_set(self, errors: list[str]) -> None:
        """PROPERTY: Failure instances can be used in sets."""
        failure_set = {Failure(e) for e in errors}

        assert len(failure_set) == len(errors)
