<!--
RETRIEVAL_HINTS:
  keywords: [ftllexbuffer, fluent, localization, i18n, l10n, ftl, translation, plurals, babel, cldr]
  answers: [what is ftllexbuffer, how to install, quick start, getting started, fluent python]
  related: [docs/QUICK_REFERENCE.md, docs/DOC_00_Index.md, docs/PARSING_GUIDE.md, docs/TERMINOLOGY.md]
-->
# FTLLexBuffer

[![PyPI](https://img.shields.io/pypi/v/ftllexbuffer.svg)](https://pypi.org/project/ftllexbuffer/)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

![FTLLexBuffer Device (MK1), Early Victorian Design](images/FTLLexBuffer.png)

**Fluent-based localization for Python** - asymmetric grammar, bi-directional parsing, 200+ locales.

FTLLexBuffer implements Mozilla's [Fluent](https://projectfluent.org/) localization system for Python 3.13+. Unlike traditional gettext-style translation where all languages must follow the source message structure, Fluent enables **asymmetric localization**: each language can restructure messages to fit its native grammar. Arabic uses 6 plural forms, Latvian has a zero category, Polish distinguishes "few" from "many" - all without changing your application code.

FTLLexBuffer extends the Fluent v1.0 specification with **bi-directional localization** (parse locale-formatted strings back to Python types), **CURRENCY formatting**, **message introspection**, and **full type safety** (`mypy --strict` compatible).

---

## Quick Links

| Getting Started | Documentation | Development |
|:----------------|:--------------|:------------|
| [Quick Reference](docs/QUICK_REFERENCE.md) | [API Reference](docs/DOC_00_Index.md) | [Testing Guide](TESTING.md) |
| [Examples](examples/) | [Parsing Guide](docs/PARSING_GUIDE.md) | [Contributing](CONTRIBUTING.md) |
| | [Type Hints Guide](docs/TYPE_HINTS_GUIDE.md) | [Changelog](CHANGELOG.md) |
| | [Terminology](docs/TERMINOLOGY.md) | |
| | [Migration Guide](docs/MIGRATION.md) | |

---

## Installation

```bash
pip install ftllexbuffer
```

**Requirements**: Python 3.13+, Babel>=2.17.0

---

## Key Features

- **Fluent v1.0 specification compliance** - Asymmetric localization, select expressions, terms, attributes
- **Bi-directional localization** - Parse locale-formatted numbers, dates, currencies back to Python types
- **200+ locale plural rules** - Full Unicode CLDR compliance via Babel
- **Type safety** - `mypy --strict` compatible with PEP 695 generics
- **Production-ready** - Never raises exceptions, graceful fallbacks, optional LRU caching

---

## Why Fluent?

Traditional localization forces all translations to follow the source language structure:

```po
# gettext: Translators fill blanks, can't restructure
msgid "You have %d file"
msgid_plural "You have %d files"
msgstr[0] "Masz %d plik"      # Polish must follow English structure
msgstr[1] "Masz %d pliki"
msgstr[2] "Masz %d plików"
```

Fluent lets each language use its native grammar:

```ftl
# Fluent: Each language defines its own structure
# English (2 forms)
files = { $count ->
    [one] one file
   *[other] { $count } files
}

# Arabic (6 forms including dual)
files = { $count ->
    [zero] no files
    [one] one file
    [two] two files
    [few] { $count } files
    [many] { $count } files
   *[other] { $count } files
}
```

**Additional Fluent capabilities**: Gender agreement, message references, terms (brand names), attributes (tooltips, aria-labels).

---

## Python Localization Solutions Comparison

| Feature | **FTLLexBuffer** | fluent.runtime | gettext (stdlib) | Babel |
|---------|------------------|----------------|------------------|-------|
| **Grammar Approach** | **Asymmetric** | **Asymmetric** | Symmetric | Symmetric |
| **Bi-directional Parsing** | **Yes** | No | No | **Yes** |
| **Plural Forms** | CLDR (200+) | CLDR | CLDR | CLDR (600+) |
| **Type Safety** | **mypy --strict** | Partial | No | Partial |
| **Python Version** | 3.13+ | 3.6+ | All | 3.8+ |
| **Dependencies** | Babel only | Multiple | None | pytz |

**Recommendation**:
- **Need asymmetric grammar** (natural translations): FTLLexBuffer, fluent.runtime
- **Need bi-directional parsing** (forms, invoices): FTLLexBuffer, Babel
- **Legacy/maximum compatibility**: gettext

---

## License & Legal

MIT License - See [LICENSE](LICENSE).

Independent implementation of [Fluent Specification](https://github.com/projectfluent/fluent/blob/master/spec/fluent.ebnf) (Apache 2.0).

**Legal**: [PATENTS.md](PATENTS.md) (patent considerations) | [NOTICE](NOTICE) (attributions)
