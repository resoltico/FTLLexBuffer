"""Type-safe Result[T, E] implementation for error handling.

This module provides a modern Python 3.13+ implementation of the Result monad
pattern for railway-oriented programming.

Architecture:
    - Success[T]: Wraps a successful result value
    - Failure[E]: Wraps an error value
    - Result type alias: Success[T] | Failure[E]

Features:
    - Immutable (frozen=True): Prevents accidental mutation
    - Memory-optimized (slots=True): Reduces memory overhead
    - Type-safe: Full mypy --strict compatibility
    - Pattern matching: Supports both isinstance() and match statement

Usage:
    def parse_number(s: str) -> Success[int] | Failure[str]:
        try:
            return Success(int(s))
        except ValueError:
            return Failure(f"Not a number: {s}")

    # isinstance pattern (used throughout parser.py)
    result = parse_number("42")
    if isinstance(result, Success):
        value = result.unwrap()
    elif isinstance(result, Failure):
        error = result.failure()

    # match statement pattern (modern alternative)
    match parse_number("42"):
        case Success(_value=value):
            print(f"Got: {value}")
        case Failure(_error=error):
            print(f"Error: {error}")
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Never


@dataclass(frozen=True, slots=True)
class Success[T]:
    """Success case containing a value.

    Represents a successful computation result. Immutable and memory-optimized.

    Attributes:
        _value: The success value (use .unwrap() to access)

    Methods:
        unwrap() -> T: Extract the success value
        failure() -> Never: Raises AttributeError (no failure on Success)
    """

    _value: T

    def unwrap(self) -> T:
        """Extract the success value.

        Returns:
            The wrapped success value

        Example:
            result = Success(42)
            value = result.unwrap()  # 42
        """
        return self._value

    def failure(self) -> Never:
        """Attempt to get failure value (always raises).

        Raises:
            AttributeError: Success has no failure value

        Note:
            This method exists for API compatibility with Failure.
            Always check isinstance() before calling.
        """
        msg = "Cannot call .failure() on Success - check isinstance(result, Failure) first"
        raise AttributeError(msg)


@dataclass(frozen=True, slots=True)
class Failure[E]:
    """Failure case containing an error.

    Represents a failed computation with an error value. Immutable and memory-optimized.

    Attributes:
        _error: The error value (use .failure() to access)

    Methods:
        failure() -> E: Extract the error value
        unwrap() -> Never: Raises ValueError (no value on Failure)
    """

    _error: E

    def failure(self) -> E:
        """Extract the error value.

        Returns:
            The wrapped error value

        Example:
            result = Failure("invalid input")
            error = result.failure()  # "invalid input"
        """
        return self._error

    def unwrap(self) -> Never:
        """Attempt to extract value (always raises).

        Raises:
            ValueError: Cannot unwrap Failure

        Note:
            This method exists for API compatibility with Success.
            Always check isinstance() before calling.
        """
        msg = f"Cannot unwrap Failure: {self._error}"
        raise ValueError(msg)


# Type alias for Result monad
# Usage: def parse(...) -> Success[T] | Failure[E]
type Result[T, E] = Success[T] | Failure[E]

# Public API
__all__ = ["Failure", "Result", "Success"]
