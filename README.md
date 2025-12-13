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

**Mozilla Fluent Visualization System for Python.**

FTLLexBuffer is a library for the [Fluent](https://projectfluent.org/) localization system, targeting Python 3.13+. It provides functions for formatting translations and parsing localized data (numbers, dates, currencies).

---

## Table of Contents
- [Getting Started](#getting-started)
- [The Fluent Difference](#the-fluent-difference)
- [Key Features](#key-features)
- [Project Structure](#project-structure)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license--legal)

---

## Getting Started

FTLLexBuffer facilitates both the formatting of messages and the parsing of user input.

```python
from decimal import Decimal
from ftllexbuffer import FluentBundle
from ftllexbuffer.parsing import parse_currency

# 1. PARSE: Native localized input
# Note: Handles ambiguity (e.g., differentiates USD/CAD $)
amount, currency = parse_currency("1.234,50 €", "de_DE")
# -> Decimal('1234.50'), 'EUR'

# 2. CALCULATE: Standard Python math
# Uses Decimal for financial precision (no floating point errors)
total = amount * Decimal("1.20") # Add 20% Tax

# 3. FORMAT: Serialize back to localized string
bundle = FluentBundle("en_US")
bundle.add_resource("total = Total: { CURRENCY($num, currency: $curr) }")

print(bundle.format_pattern("total", {"num": total, "curr": currency}))
# -> "Total: $1,481.40"
```

---

## The Fluent Difference

Localization often requires logic for grammatical agreement (plurals, cases).

**The Traditional Way (Logic in Python)**

Developers often have to hardcode grammatical logic directly in their application code.

```python
# The developer manually handles pluralization logic
if coffee_count == 0:
    msg = "Out of coffee! Panic!"
elif coffee_count == 1:
    msg = "1 coffee left."
else:
    msg = f"{coffee_count} coffees left."
```

**The Fluent Way (Logic in FTL)**

With Fluent, the application code passes the data, and the translation file handles the logic. This keeps your Python code **clean and logic-free**.

```python
# The developer passes the data; no if/else statements
bundle.format_pattern("coffee-stock", {"count": coffee_count})
```

```ftl
# Grammar and logic live in the translation file
coffee-stock = { $count ->
    [0] Out of coffee! Panic!
    [one] One coffee left.
   *[other] { $count } coffees left.
}
```

---

## Key Features

FTLLexBuffer provides three core capabilities for handling localized data:

### 1. Translation Management
The core engine (`FluentBundle`) manages the lifecycle of translation resources.
*   **Logical Isolation**: Translators define logic in `.ftl` files.
*   **Runtime Resolution**: The engine resolves messages at runtime, providing robust fallback strings.

### 2. Output Formatting
Format complex strings with natural-sounding grammar using the Mozilla Fluent syntax.

### 3. Input Parsing
Parse localized strings back into Python objects for data processing.
*   **Ambiguity Detection**: Smartly handles ambiguous currency symbols (e.g., determining if `$` implies `USD` or `CAD` based on locale).
*   **Safety**: Uses a non-raising error pattern to ensure production stability.
*   **Data Types**: Wraps `Babel` to parse Numbers, Dates, and Currencies into standard Python types (`Decimal`, `date`).

---

## Project Structure

```text
ftllexbuffer/
├── diagnostics/      # Error definitions and templates
├── parsing/          # Locale-aware parsing (Babel wrapper)
├── runtime/          # Core message formatting engine
├── syntax/           # FTL parser and AST definitions
├── enums.py          # Type-safe constants
├── introspection.py  # Variable extraction tools
├── locale_utils.py   # BCP-47 localization helpers
└── localization.py   # High-level orchestration
```

---

## Documentation

| Guide | Description |
|:------|:------------|
| [Quick Reference](docs/QUICK_REFERENCE.md) | One-page reference for common tasks. |
| [API Reference](docs/DOC_00_Index.md) | Detailed class and function documentation. |
| [Parsing Guide](docs/PARSING_GUIDE.md) | Guide to locale-aware parsing functions. |
| [Examples](examples/) | Code examples for various use cases. |

---

## Installation

```bash
pip install ftllexbuffer
```

**Requirements**: Python 3.13+, Babel>=2.17.0

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on setting up your development environment, running tests, and submitting pull requests.

---

## License & Legal

MIT License - See [LICENSE](LICENSE).

Independent implementation of [Fluent Specification](https://github.com/projectfluent/fluent/blob/master/spec/fluent.ebnf) (Apache 2.0).

**Legal**: [PATENTS.md](PATENTS.md) (patent considerations) | [NOTICE](NOTICE) (attributions)
