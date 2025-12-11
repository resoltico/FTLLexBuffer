"""Fluent FTL parser module.

This module provides the main FluentParserV1 parser class and related
parsing utilities organized into focused submodules.

Module Organization (post-refactor):
- core.py: Main FluentParserV1 class and parse() entry point
- primitives.py: Basic parsers (identifiers, numbers, strings)
- whitespace.py: Whitespace handling and continuation detection
- patterns.py: Pattern and placeable parsing
- expressions.py: Expression parsing (select, inline, function calls)
- entries.py: Top-level entry parsing (messages, terms, attributes, comments)

Public API:
    FluentParserV1: Main parser class (backwards compatible re-export)
"""

from ftllexbuffer.syntax.parser.core import FluentParserV1

__all__ = ["FluentParserV1"]
