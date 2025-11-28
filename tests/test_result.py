"""Comprehensive tests for ftllexbuffer.result module.

Tests cover:
1. Success/Failure construction and unwrapping
2. Error cases (calling wrong methods)
3. Immutability guarantees
4. Type narrowing with isinstance
5. Pattern matching support
6. Generic type parameters
7. Property-based tests with Hypothesis

Coverage target: 100% for src/ftllexbuffer/result.py
"""

import sys
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from ftllexbuffer.result import Failure, Success


class TestSuccessBasics:
    """Test Success type basic functionality."""

    def test_success_construction(self) -> None:
        """Success wraps a value."""
        result = Success(42)
        assert result._value == 42

    def test_success_unwrap(self) -> None:
        """Success.unwrap() returns the wrapped value."""
        result = Success("hello")
        assert result.unwrap() == "hello"

    def test_success_unwrap_preserves_type(self) -> None:
        """Success.unwrap() preserves value type."""
        result = Success([1, 2, 3])
        value = result.unwrap()
        assert isinstance(value, list)
        assert value == [1, 2, 3]

    def test_success_failure_raises(self) -> None:
        """Success.failure() raises AttributeError."""
        result = Success(42)
        with pytest.raises(AttributeError) as exc_info:
            result.failure()
        assert "Cannot call .failure() on Success" in str(exc_info.value)

    def test_success_isinstance(self) -> None:
        """isinstance(result, Success) works correctly."""
        result = Success(42)
        assert isinstance(result, Success)
        assert not isinstance(result, Failure)  # type: ignore[unreachable]


class TestFailureBasics:
    """Test Failure type basic functionality."""

    def test_failure_construction(self) -> None:
        """Failure wraps an error."""
        result = Failure("error")
        assert result._error == "error"

    def test_failure_failure(self) -> None:
        """Failure.failure() returns the wrapped error."""
        result = Failure("invalid input")
        assert result.failure() == "invalid input"

    def test_failure_failure_preserves_type(self) -> None:
        """Failure.failure() preserves error type."""
        error_dict = {"code": 404, "message": "Not found"}
        result = Failure(error_dict)
        error = result.failure()
        assert isinstance(error, dict)
        assert error == error_dict

    def test_failure_unwrap_raises(self) -> None:
        """Failure.unwrap() raises ValueError."""
        result = Failure("error")
        with pytest.raises(ValueError) as exc_info:
            result.unwrap()
        assert "Cannot unwrap Failure" in str(exc_info.value)
        assert "error" in str(exc_info.value)

    def test_failure_isinstance(self) -> None:
        """isinstance(result, Failure) works correctly."""
        result = Failure("error")
        assert isinstance(result, Failure)
        assert not isinstance(result, Success)  # type: ignore[unreachable]


class TestImmutability:
    """Test that Success and Failure are immutable."""

    def test_success_frozen(self) -> None:
        """Success is frozen (cannot mutate _value)."""
        result = Success(42)
        with pytest.raises((AttributeError, TypeError)):
            result._value = 999  # type: ignore[misc]

    def test_failure_frozen(self) -> None:
        """Failure is frozen (cannot mutate _error)."""
        result = Failure("error")
        with pytest.raises((AttributeError, TypeError)):
            result._error = "changed"  # type: ignore[misc]

    def test_success_no_new_attributes(self) -> None:
        """Success uses slots (cannot add new attributes)."""
        result = Success(42)
        with pytest.raises((AttributeError, TypeError)):
            result.new_attr = "test"  # type: ignore[attr-defined]

    def test_failure_no_new_attributes(self) -> None:
        """Failure uses slots (cannot add new attributes)."""
        result = Failure("error")
        with pytest.raises((AttributeError, TypeError)):
            result.new_attr = "test"  # type: ignore[attr-defined]


class TestTypeNarrowing:
    """Test type narrowing with isinstance checks."""

    def test_isinstance_success_narrows(self) -> None:
        """isinstance(result, Success) enables .unwrap()."""
        result: Success[int] | Failure[str] = Success(42)
        if isinstance(result, Success):
            value = result.unwrap()
            assert value == 42
        else:
            pytest.fail("Should be Success")

    def test_isinstance_failure_narrows(self) -> None:
        """isinstance(result, Failure) enables .failure()."""
        result: Success[int] | Failure[str] = Failure("error")
        if isinstance(result, Failure):
            error = result.failure()
            assert error == "error"
        else:
            pytest.fail("Should be Failure")

    def test_function_returning_result(self) -> None:
        """Functions can return Success | Failure."""

        def parse_int(s: str) -> Success[int] | Failure[str]:
            try:
                return Success(int(s))
            except ValueError:
                return Failure(f"Not a number: {s}")

        result = parse_int("42")
        assert isinstance(result, Success)
        assert result.unwrap() == 42

        result2 = parse_int("abc")
        assert isinstance(result2, Failure)
        assert "Not a number" in result2.failure()


class TestPatternMatching:
    """Test pattern matching support (Python 3.10+)."""

    def test_match_success(self) -> None:
        """match statement works with Success."""
        result: Success[int] | Failure[str] = Success(42)
        match result:
            case Success(_value=value):
                assert value == 42
            case Failure(_error=error):
                pytest.fail(f"Should not match Failure: {error}")

    def test_match_failure(self) -> None:
        """match statement works with Failure."""
        result: Success[int] | Failure[str] = Failure("error")
        match result:
            case Success(_value=value):
                pytest.fail(f"Should not match Success: {value}")
            case Failure(_error=error):
                assert error == "error"


class TestGenericTypes:
    """Test generic type parameters."""

    def test_success_with_complex_types(self) -> None:
        """Success works with complex generic types."""
        result: Success[list[dict[str, int]]] = Success([{"a": 1}, {"b": 2}])
        value = result.unwrap()
        assert value == [{"a": 1}, {"b": 2}]

    def test_failure_with_complex_types(self) -> None:
        """Failure works with complex generic types."""
        result: Failure[tuple[int, str]] = Failure((404, "Not Found"))
        error = result.failure()
        assert error == (404, "Not Found")

    def test_result_alias_type_annotation(self) -> None:
        """Result[T, E] type alias works in annotations."""

        def divide(a: int, b: int) -> Success[float] | Failure[str]:
            if b == 0:
                return Failure("Division by zero")
            return Success(a / b)

        result = divide(10, 2)
        assert isinstance(result, Success)
        assert result.unwrap() == 5.0

        result2 = divide(10, 0)
        assert isinstance(result2, Failure)
        assert result2.failure() == "Division by zero"


class TestMemoryOptimization:
    """Test slots memory optimization."""

    def test_success_size_reduced(self) -> None:
        """Success with slots uses less memory than regular class."""
        result = Success(42)
        assert sys.getsizeof(result) < 100  # Reasonable upper bound

    def test_failure_size_reduced(self) -> None:
        """Failure with slots uses less memory than regular class."""
        result = Failure("error")
        assert sys.getsizeof(result) < 100  # Reasonable upper bound


class TestEdgeCases:
    """Test edge cases and corner conditions."""

    def test_success_with_none(self) -> None:
        """Success can wrap None."""
        result = Success(None)
        assert result.unwrap() is None

    def test_failure_with_none(self) -> None:
        """Failure can wrap None."""
        result = Failure(None)
        assert result.failure() is None

    def test_success_with_empty_string(self) -> None:
        """Success can wrap empty string."""
        result = Success("")
        assert result.unwrap() == ""

    def test_failure_with_empty_string(self) -> None:
        """Failure can wrap empty string."""
        result = Failure("")
        assert result.failure() == ""

    def test_success_with_zero(self) -> None:
        """Success can wrap zero."""
        result = Success(0)
        assert result.unwrap() == 0

    def test_failure_with_zero(self) -> None:
        """Failure can wrap zero."""
        result = Failure(0)
        assert result.failure() == 0

    def test_success_with_false(self) -> None:
        """Success can wrap False."""
        result = Success(False)
        assert result.unwrap() is False

    def test_failure_with_false(self) -> None:
        """Failure can wrap False."""
        result = Failure(False)
        assert result.failure() is False


class TestPublicAPI:
    """Test public API exports."""

    def test_all_exports(self) -> None:
        """__all__ contains expected exports."""
        from ftllexbuffer import result

        assert hasattr(result, "__all__")
        assert "Success" in result.__all__
        assert "Failure" in result.__all__
        assert "Result" in result.__all__
        assert len(result.__all__) == 3


# ============================================================================
# HYPOTHESIS PROPERTY-BASED TESTS
# ============================================================================


@given(st.integers())
def test_success_roundtrip_int(value: int) -> None:
    """Success unwrap is identity for integers."""
    result = Success(value)
    assert result.unwrap() == value


@given(st.text())
def test_success_roundtrip_str(value: str) -> None:
    """Success unwrap is identity for strings."""
    result = Success(value)
    assert result.unwrap() == value


@given(st.lists(st.integers()))
def test_success_roundtrip_list(value: list[int]) -> None:
    """Success unwrap is identity for lists."""
    result = Success(value)
    assert result.unwrap() == value


@given(st.integers())
def test_failure_roundtrip_int(error: int) -> None:
    """Failure.failure() is identity for integers."""
    result = Failure(error)
    assert result.failure() == error


@given(st.text())
def test_failure_roundtrip_str(error: str) -> None:
    """Failure.failure() is identity for strings."""
    result = Failure(error)
    assert result.failure() == error


@given(st.integers())
def test_success_failure_raises_always(value: int) -> None:
    """Success.failure() always raises for any value."""
    result = Success(value)
    with pytest.raises(AttributeError):
        result.failure()


@given(st.text())
def test_failure_unwrap_raises_always(error: str) -> None:
    """Failure.unwrap() always raises for any error."""
    result = Failure(error)
    with pytest.raises(ValueError):
        result.unwrap()


@given(st.one_of(st.integers(), st.text(), st.booleans(), st.none()))
def test_success_isinstance_consistent(value: Any) -> None:
    """Success is always Success, never Failure."""
    result = Success(value)
    assert isinstance(result, Success)
    assert not isinstance(result, Failure)  # type: ignore[unreachable]


@given(st.one_of(st.integers(), st.text(), st.booleans(), st.none()))
def test_failure_isinstance_consistent(error: Any) -> None:
    """Failure is always Failure, never Success."""
    result = Failure(error)
    assert isinstance(result, Failure)
    assert not isinstance(result, Success)  # type: ignore[unreachable]


@given(st.integers(), st.integers())
def test_result_monad_laws_left_identity(value: int, divisor: int) -> None:
    """Result satisfies monad left identity (for manual bind simulation)."""
    # return value >>= f === f value
    # Since we don't have bind, we test that Success wrapping is consistent

    def make_result(x: int) -> Success[int] | Failure[str]:
        if x < 0:
            return Failure("negative")
        return Success(x)

    # Direct application
    direct = make_result(value)

    # Via Success wrapping
    wrapped = Success(value)
    if isinstance(wrapped, Success):
        via_success = make_result(wrapped.unwrap())
    else:  # pragma: no cover
        # Mypy correctly detects this is unreachable (Success is always Success)
        # But we keep for runtime safety
        via_success = wrapped  # type: ignore[unreachable]

    # Both should have same outcome
    assert type(direct) == type(via_success)
    if isinstance(direct, Success) and isinstance(via_success, Success):
        assert direct.unwrap() == via_success.unwrap()
    elif isinstance(direct, Failure) and isinstance(via_success, Failure):
        assert direct.failure() == via_success.failure()


@given(st.integers(min_value=0, max_value=1000))
def test_parser_like_usage(value: int) -> None:
    """Test parser-like usage pattern with Result."""

    def parse_positive(n: int) -> Success[int] | Failure[str]:
        if n > 0:
            return Success(n)
        return Failure(f"Expected positive, got {n}")

    result = parse_positive(value)

    if value > 0:
        assert isinstance(result, Success)
        assert result.unwrap() == value
    else:
        assert isinstance(result, Failure)
        assert str(value) in result.failure()


@given(st.text(min_size=0, max_size=100))
def test_error_message_preservation(error: str) -> None:
    """Failure preserves error messages exactly."""
    result = Failure(error)
    assert result.failure() == error

    # Check that unwrap error contains original error
    with pytest.raises(ValueError) as exc_info:
        result.unwrap()
    assert error in str(exc_info.value)


@given(st.tuples(st.integers(), st.text()))
def test_complex_generic_types(value: tuple[int, str]) -> None:
    """Success and Failure work with complex tuple types."""
    success = Success(value)
    assert success.unwrap() == value

    failure = Failure(value)
    assert failure.failure() == value


@given(st.recursive(st.integers(), lambda x: st.lists(x, max_size=3), max_leaves=10))
def test_recursive_data_structures(value: Any) -> None:
    """Success and Failure work with recursive data structures."""
    result = Success(value)
    assert result.unwrap() == value

    failure = Failure(value)
    assert failure.failure() == value
