<!--
RETRIEVAL_HINTS:
  keywords: [ftllexbuffer, fluent, localization, i18n, l10n, ftl, translation, plurals, babel, cldr, python]
  answers: [what is ftllexbuffer, how to install, quick start, fluent python, localization library]
  related: [docs/QUICK_REFERENCE.md, docs/DOC_00_Index.md, docs/PARSING_GUIDE.md, docs/TERMINOLOGY.md]
-->
# FTLLexBuffer

[![PyPI](https://img.shields.io/pypi/v/ftllexbuffer.svg)](https://pypi.org/project/ftllexbuffer/)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

![FTLLexBuffer Device (MK1), Early Victorian Design](images/FTLLexBuffer.png)

**Independent Python implementation of the Mozilla Fluent localization system.**

FTLLexBuffer implements [Project Fluent](https://projectfluent.org/) for Python, enabling natural-sounding translations with grammatical logic handled by translators, not developers. It provides bidirectional localization: format messages for display and parse localized input back to Python types.

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [The Fluent Difference](#the-fluent-difference)
- [Key Features](#key-features)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## Installation

```bash
pip install ftllexbuffer
```

**Requirements**: Python >= 3.13, Babel >= 2.17

---

## Quick Start

### Basic Message Formatting

```python
from ftllexbuffer import FluentBundle

bundle = FluentBundle("en_US")
bundle.add_resource("""
hello = Hello, World!
welcome = Welcome, { $name }!
""")

result, errors = bundle.format_pattern("hello")
print(result)  # "Hello, World!"

result, errors = bundle.format_pattern("welcome", {"name": "Alice"})
print(result)  # "Welcome, Alice!"
```

### Bidirectional Localization (Parse + Format)

```python
from decimal import Decimal
from ftllexbuffer import FluentBundle
from ftllexbuffer.parsing import parse_currency

# 1. PARSE: Locale-formatted user input -> Python types
result, errors = parse_currency("1.234,50 €", "de_DE")
if result is not None:
    amount, currency = result  # Decimal('1234.50'), 'EUR'

    # 2. CALCULATE: Standard Python math with Decimal precision
    total = amount * Decimal("1.19")  # Add 19% VAT

    # 3. FORMAT: Python types -> Locale-formatted output
    bundle = FluentBundle("en_US")
    bundle.add_resource('invoice = Total: { CURRENCY($amount, currency: "EUR") }')

    output, _ = bundle.format_pattern("invoice", {"amount": total})
    print(output)  # "Total: €1,469.06"
```

---

## The Fluent Difference

Traditional i18n forces developers to handle grammatical logic:

```python
# Developer must know grammar rules for every language
if count == 1:
    msg = "1 cup of coffee"
else:
    msg = f"{count} cups of coffee"
```

With Fluent, translators handle grammar in `.ftl` files:

```python
from ftllexbuffer import FluentBundle

bundle = FluentBundle("en_US")
bundle.add_resource("""
coffee-order = { $count ->
    [one] { $count } cup of coffee
   *[other] { $count } cups of coffee
}
""")

result, _ = bundle.format_pattern("coffee-order", {"count": 1})
print(result)  # "1 cup of coffee"

result, _ = bundle.format_pattern("coffee-order", {"count": 5})
print(result)  # "5 cups of coffee"
```

This separation enables correct translations for complex languages (Polish with 4 plural forms, Welsh with 6) without code changes.

---

## Key Features

- **Fluent 1.0 Compliant** - Full implementation of the [Fluent syntax](https://projectfluent.org/fluent/guide/), including select expressions, terms, attributes, and built-in functions.

- **Bidirectional Localization** - Format messages for output AND parse locale-formatted strings (numbers, dates, currencies) back to Python types.

- **Translator-Controlled Logic** - Pluralization, gender agreement, and grammatical cases live in `.ftl` files, keeping application code clean.

- **CLDR-Powered** - Uses Babel for Unicode CLDR compliance across 200+ locales with correct number, date, and currency formatting.

- **Robust Error Handling** - Never raises exceptions during formatting. Returns `(result, errors)` tuples for graceful degradation in production.

- **Full Introspection** - Extract variables, functions, and structure from messages for validation, tooling, and IDE integration.

- **Type-Safe** - Comprehensive type hints throughout. Works with mypy strict mode.

---

## Documentation

| Resource | Description |
|:---------|:------------|
| [Quick Reference](docs/QUICK_REFERENCE.md) | Copy-paste patterns for common tasks |
| [API Reference](docs/DOC_00_Index.md) | Complete class and function documentation |
| [Parsing Guide](docs/PARSING_GUIDE.md) | Locale-aware input parsing |
| [Terminology](docs/TERMINOLOGY.md) | Fluent/FTLLexBuffer concept definitions |
| [Examples](examples/) | Working code examples |

---

## Contributing

Contributions welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, testing, and pull request guidelines.

---

## License

MIT License - See [LICENSE](LICENSE).

Independent implementation of [Fluent Specification](https://github.com/projectfluent/fluent/blob/master/spec/fluent.ebnf) (Apache 2.0).

**Legal**: [PATENTS.md](PATENTS.md) | [NOTICE](NOTICE)
