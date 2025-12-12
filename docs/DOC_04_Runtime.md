---
spec_version: AFAD-v1
project_version: 0.11.1
context: RUNTIME
last_updated: 2025-12-12T00:00:00Z
maintainer: claude-opus-4-5
---

# Runtime Reference

---

## `number_format`

### Signature
```python
def number_format(
    value: int | float,
    locale_code: str = "en-US",
    *,
    minimum_fraction_digits: int = 0,
    maximum_fraction_digits: int = 3,
    use_grouping: bool = True,
    pattern: str | None = None,
) -> str:
```

### Contract
| Parameter | Type | Req | Description |
|:----------|:-----|:----|:------------|
| `value` | `int \| float` | Y | Number to format. |
| `locale_code` | `str` | N | BCP 47 locale code. |
| `minimum_fraction_digits` | `int` | N | Minimum decimal places. |
| `maximum_fraction_digits` | `int` | N | Maximum decimal places. |
| `use_grouping` | `bool` | N | Use thousands separator. |
| `pattern` | `str \| None` | N | Custom Babel number pattern. |

### Constraints
- Return: Formatted number string.
- Raises: Never. Returns str(value) on error.
- State: None.
- Thread: Safe.

---

## `datetime_format`

### Signature
```python
def datetime_format(
    value: datetime | str,
    locale_code: str = "en-US",
    *,
    date_style: Literal["short", "medium", "long", "full"] = "medium",
    time_style: Literal["short", "medium", "long", "full"] | None = None,
    pattern: str | None = None,
) -> str:
```

### Contract
| Parameter | Type | Req | Description |
|:----------|:-----|:----|:------------|
| `value` | `datetime \| str` | Y | Datetime or ISO string. |
| `locale_code` | `str` | N | BCP 47 locale code. |
| `date_style` | `Literal[...]` | N | Date format style. |
| `time_style` | `Literal[...] \| None` | N | Time format style. |
| `pattern` | `str \| None` | N | Custom Babel datetime pattern. |

### Constraints
- Return: Formatted datetime string.
- Raises: Never. Returns ISO format on error.
- State: None.
- Thread: Safe.

---

## `currency_format`

### Signature
```python
def currency_format(
    value: int | float,
    locale_code: str = "en-US",
    *,
    currency: str,
    currency_display: Literal["symbol", "code", "name"] = "symbol",
) -> str:
```

### Contract
| Parameter | Type | Req | Description |
|:----------|:-----|:----|:------------|
| `value` | `int \| float` | Y | Monetary amount. |
| `locale_code` | `str` | N | BCP 47 locale code. |
| `currency` | `str` | Y | ISO 4217 currency code. |
| `currency_display` | `Literal[...]` | N | Display style. |

### Constraints
- Return: Formatted currency string.
- Raises: Never. Returns "{currency} {value}" on error.
- State: None.
- Thread: Safe.

---

## `FunctionRegistry`

### Signature
```python
class FunctionRegistry:
    def __init__(self) -> None: ...
    def register(
        self,
        func: Callable[..., str],
        *,
        ftl_name: str | None = None
    ) -> None: ...
    def get(self, name: str) -> Callable[..., str] | None: ...
    def copy(self) -> FunctionRegistry: ...
```

### Contract
| Parameter | Type | Req | Description |
|:----------|:-----|:----|:------------|

### Constraints
- Return: Registry instance.
- State: Mutable registry dict.
- Thread: Unsafe for concurrent register().

---

## `FunctionRegistry.register`

### Signature
```python
def register(
    self,
    func: Callable[..., str],
    *,
    ftl_name: str | None = None
) -> None:
```

### Contract
| Parameter | Type | Req | Description |
|:----------|:-----|:----|:------------|
| `func` | `Callable[..., str]` | Y | Function to register. |
| `ftl_name` | `str \| None` | N | FTL name override. |

### Constraints
- Return: None.
- Raises: None.
- State: Mutates registry.
- Thread: Unsafe.

---

## `FUNCTION_REGISTRY`

### Signature
```python
FUNCTION_REGISTRY: FunctionRegistry
```

### Contract
| Parameter | Type | Req | Description |
|:----------|:-----|:----|:------------|

### Constraints
- Module-level singleton with built-in functions.
- Contains: NUMBER, DATETIME, CURRENCY.
- State: Pre-populated at import.

---

## `select_plural_category`

### Signature
```python
def select_plural_category(n: int | float, locale: str) -> str:
```

### Contract
| Parameter | Type | Req | Description |
|:----------|:-----|:----|:------------|
| `n` | `int \| float` | Y | Number to categorize. |
| `locale` | `str` | Y | BCP 47 locale code. |

### Constraints
- Return: CLDR plural category (zero, one, two, few, many, other).
- Raises: Never. Returns "one" or "other" on invalid locale.
- State: None.
- Thread: Safe.

---

## FTL Function Name Mapping

| FTL Name | Python Function | Parameter Mapping |
|:---------|:----------------|:------------------|
| `NUMBER` | `number_format` | minimumFractionDigits -> minimum_fraction_digits |
| `DATETIME` | `datetime_format` | dateStyle -> date_style, timeStyle -> time_style |
| `CURRENCY` | `currency_format` | currencyDisplay -> currency_display |

---

## Custom Function Protocol

### Signature
```python
def CUSTOM_FUNCTION(
    positional_arg: FluentValue,
    *,
    keyword_arg: str = "default",
) -> str:
```

### Contract
| Parameter | Type | Req | Description |
|:----------|:-----|:----|:------------|
| First positional | `FluentValue` | Y | Primary input value. |
| Keyword args | `str` | N | Named options. |

### Constraints
- Return: Must return str.
- Raises: Should not raise. Return fallback on error.
- State: Should be stateless.
- Thread: Should be safe.

---
