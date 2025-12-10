"""Fluent runtime package.

Provides message resolution, built-in functions, and the FluentBundle API.
Depends on syntax package for parsing.

Python 3.13+.
"""

from ftllexbuffer.diagnostics import ValidationResult

from .bundle import FluentBundle
from .function_bridge import FunctionRegistry
from .functions import FUNCTION_REGISTRY, datetime_format, number_format
from .plural_rules import select_plural_category
from .resolver import FluentResolver

__all__ = [
    "FUNCTION_REGISTRY",
    "FluentBundle",
    "FluentResolver",
    "FunctionRegistry",
    "ValidationResult",
    "datetime_format",
    "number_format",
    "select_plural_category",
]
