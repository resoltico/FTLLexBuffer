"""Unified validation result for Fluent resource validation.

Consolidates all validation feedback from different stages:
- Parser-level: Syntax annotations from AST parsing
- Syntax-level: Structured validation errors
- Semantic-level: Structured validation warnings

Python 3.13+.
"""

from dataclasses import dataclass

from ftllexbuffer.syntax.ast import Annotation

__all__ = [
    "ValidationError",
    "ValidationResult",
    "ValidationWarning",
]


# ============================================================================
# VALIDATION ERROR & WARNING TYPES
# ============================================================================


@dataclass(frozen=True, slots=True)
class ValidationError:
    """Structured syntax error from FTL validation.

    Attributes:
        code: Error code (e.g., "parse-error", "malformed-entry")
        message: Human-readable error message
        content: The unparseable FTL content
        line: Line number where error occurred (1-indexed, optional)
        column: Column number where error occurred (1-indexed, optional)
    """

    code: str
    message: str
    content: str
    line: int | None = None
    column: int | None = None


@dataclass(frozen=True, slots=True)
class ValidationWarning:
    """Structured semantic warning from FTL validation.

    Attributes:
        code: Warning code (e.g., "duplicate-id", "undefined-reference")
        message: Human-readable warning message
        context: Additional context (e.g., the duplicate ID name)
    """

    code: str
    message: str
    context: str | None = None


# ============================================================================
# UNIFIED VALIDATION RESULT
# ============================================================================


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Unified validation result for all validation levels.

    Consolidates feedback from:
    - Parser: AST annotations (syntax errors, malformed tokens)
    - Syntax validator: Structural validation errors
    - Semantic validator: Semantic warnings (duplicates, references, etc.)

    Immutable result object for thread-safe validation feedback.

    Attributes:
        errors: Syntax/parse validation errors
        warnings: Semantic validation warnings
        annotations: Parser-level AST annotations

    Example:
        >>> result = ValidationResult.valid()
        >>> result.is_valid
        True
        >>> result.error_count
        0

        >>> # With errors
        >>> result = ValidationResult.invalid(
        ...     errors=(ValidationError(
        ...         code="parse-error",
        ...         message="Expected '=' but found EOF",
        ...         content="msg",
        ...         line=1,
        ...         column=4
        ...     ),)
        ... )
        >>> result.is_valid
        False
        >>> result.error_count
        1
    """

    errors: tuple[ValidationError, ...]
    warnings: tuple[ValidationWarning, ...]
    annotations: tuple[Annotation, ...]

    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors or annotations).

        Warnings do not affect validity - they're informational.

        Returns:
            True if no errors or annotations found
        """
        return len(self.errors) == 0 and len(self.annotations) == 0

    @property
    def error_count(self) -> int:
        """Get total number of errors (syntax + parser).

        Returns:
            Count of errors and annotations combined
        """
        return len(self.errors) + len(self.annotations)

    @property
    def warning_count(self) -> int:
        """Get number of semantic warnings.

        Returns:
            Count of warnings
        """
        return len(self.warnings)

    @staticmethod
    def valid() -> "ValidationResult":
        """Create a valid result with no errors, warnings, or annotations.

        Returns:
            ValidationResult with empty tuples for all fields
        """
        return ValidationResult(errors=(), warnings=(), annotations=())

    @staticmethod
    def invalid(
        errors: tuple[ValidationError, ...] = (),
        warnings: tuple[ValidationWarning, ...] = (),
        annotations: tuple[Annotation, ...] = (),
    ) -> "ValidationResult":
        """Create an invalid result with errors and/or annotations.

        Args:
            errors: Tuple of validation errors (default: empty)
            warnings: Tuple of validation warnings (default: empty)
            annotations: Tuple of parser annotations (default: empty)

        Returns:
            ValidationResult with provided errors/warnings/annotations
        """
        return ValidationResult(
            errors=errors, warnings=warnings, annotations=annotations
        )

    @staticmethod
    def from_annotations(annotations: tuple[Annotation, ...]) -> "ValidationResult":
        """Create result from parser-level annotations only.

        Convenience factory for semantic validator usage.

        Args:
            annotations: Tuple of AST annotations

        Returns:
            ValidationResult with annotations, empty errors/warnings
        """
        if annotations:
            return ValidationResult(errors=(), warnings=(), annotations=annotations)
        return ValidationResult.valid()
