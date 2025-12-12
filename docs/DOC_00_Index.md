---
spec_version: AFAD-v1
project_version: 0.11.1
context: INDEX
last_updated: 2025-12-12T12:00:00Z
maintainer: claude-opus-4-5
retrieval_hints:
  keywords: [api reference, documentation, exports, imports, fluentbundle, fluentlocalization]
  answers: [api documentation, what classes available, how to import, module exports]
  related: [DOC_01_Core.md, DOC_02_Types.md, DOC_03_Parsing.md, DOC_04_Runtime.md, DOC_05_Errors.md]
---

# FTLLexBuffer API Reference Index

## Module Exports

### Root Exports (`from ftllexbuffer import ...`)
```python
from ftllexbuffer import (
    # Core API
    FluentBundle,
    FluentLocalization,
    parse_ftl,
    serialize_ftl,
    # Errors
    FluentError,
    FluentSyntaxError,
    FluentReferenceError,
    FluentResolutionError,
    # Metadata
    __version__,
    __fluent_spec_version__,
    __spec_url__,
    __recommended_encoding__,
)
```

### AST Types (`from ftllexbuffer.syntax.ast import ...`)
```python
from ftllexbuffer.syntax.ast import (
    Resource, Message, Term, Pattern, Attribute,
    Placeable, TextElement, Identifier, Junk, Comment,
    VariableReference, MessageReference, TermReference, FunctionReference,
    SelectExpression, Variant, NumberLiteral, StringLiteral,
    CallArguments, NamedArgument, Span, Annotation,
    InlineExpression, VariantKey,
)
```

### Errors & Validation (`from ftllexbuffer.diagnostics import ...`)
```python
from ftllexbuffer.diagnostics import (
    FluentError, FluentSyntaxError, FluentReferenceError,
    FluentResolutionError, FluentCyclicReferenceError,
    ValidationResult, ValidationError, ValidationWarning,
)
```

### Introspection (`from ftllexbuffer.introspection import ...`)
```python
from ftllexbuffer.introspection import (
    introspect_message, MessageIntrospection,
    extract_variables, extract_references,
)
```

### Visitor (`from ftllexbuffer.syntax.visitor import ...`)
```python
from ftllexbuffer.syntax.visitor import ASTVisitor
```

---

## File Routing Table

| Query Pattern | Target File | Domain |
|:--------------|:------------|:-------|
| FluentBundle, FluentLocalization, add_resource, format_pattern, format_value | [DOC_01_Core.md](DOC_01_Core.md) | Core API |
| Message, Term, Pattern, Resource, AST, Identifier, dataclass | [DOC_02_Types.md](DOC_02_Types.md) | AST Types |
| parse_ftl, parse_number, parse_decimal, parse_date, parse_currency | [DOC_03_Parsing.md](DOC_03_Parsing.md) | Parsing |
| NUMBER, DATETIME, CURRENCY, add_function, FunctionRegistry | [DOC_04_Runtime.md](DOC_04_Runtime.md) | Runtime |
| FluentError, FluentReferenceError, ValidationResult, diagnostic | [DOC_05_Errors.md](DOC_05_Errors.md) | Errors |

---

## Submodule Structure

```
ftllexbuffer/
  __init__.py              # Public API exports
  localization.py          # FluentLocalization, PathResourceLoader
  introspection.py         # MessageIntrospection, introspect_message
  syntax/
    __init__.py            # AST exports
    ast.py                 # AST node definitions
    parser.py              # FluentParserV1
    visitor.py             # ASTVisitor
  runtime/
    __init__.py            # Runtime exports
    bundle.py              # FluentBundle
    resolver.py            # FluentResolver
    functions.py           # Built-in functions, FunctionRegistry
  parsing/
    __init__.py            # Parsing API exports
    numbers.py             # parse_number, parse_decimal
    dates.py               # parse_date, parse_datetime
    currency.py            # parse_currency
    guards.py              # Type guards
  diagnostics/
    __init__.py            # Error exports
    errors.py              # FluentError hierarchy
    codes.py               # DiagnosticCode, Diagnostic
    validation.py          # ValidationResult
```

---

## Type Alias Quick Reference

| Alias | Definition | Location |
|:------|:-----------|:---------|
| `FluentValue` | `str \| int \| float \| bool \| Decimal \| datetime \| None` | localization.py |
| `MessageId` | `str` | localization.py |
| `LocaleCode` | `str` | localization.py |
| `ResourceId` | `str` | localization.py |
| `FTLSource` | `str` | localization.py |
| `InlineExpression` | Union of inline AST types | syntax/ast.py |
| `VariantKey` | `Identifier \| NumberLiteral` | syntax/ast.py |

---

## Cross-Reference: Non-Reference Documentation

| File | Purpose | Audience |
|:-----|:--------|:---------|
| [README.md](../README.md) | Entry point, installation, quick start | Humans |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Cheat sheet, common patterns | Humans |
| [PARSING_GUIDE.md](PARSING_GUIDE.md) | Bi-directional parsing tutorial | Humans |
| [TYPE_HINTS_GUIDE.md](TYPE_HINTS_GUIDE.md) | Python 3.13 type patterns | Humans |
| [TERMINOLOGY.md](TERMINOLOGY.md) | Glossary, disambiguation | Both |
| [MIGRATION.md](MIGRATION.md) | fluent.runtime migration guide | Humans |
| [CUSTOM_FUNCTIONS_GUIDE.md](CUSTOM_FUNCTIONS_GUIDE.md) | Custom function tutorial | Humans |

---
