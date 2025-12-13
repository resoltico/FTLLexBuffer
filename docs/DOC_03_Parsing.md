---
spec_version: AFAD-v1
project_version: 0.12.0
context: PARSING
last_updated: 2025-12-13T00:00:00Z
maintainer: claude-opus-4-5
---

# Parsing Reference

---

## `parse_ftl`

### Signature
```python
def parse_ftl(source: str) -> Resource:
```

### Contract
| Parameter | Type | Req | Description |
|:----------|:-----|:----|:------------|
| `source` | `str` | Y | FTL source code. |

### Constraints
- Return: Resource AST containing parsed entries.
- Raises: `FluentSyntaxError` on critical parse error.
- State: None.
- Thread: Safe.

---

## `serialize_ftl`

### Signature
```python
def serialize_ftl(resource: Resource) -> str:
```

### Contract
| Parameter | Type | Req | Description |
|:----------|:-----|:----|:------------|
| `resource` | `Resource` | Y | Resource AST node. |

### Constraints
- Return: FTL source string.
- Raises: None.
- State: None.
- Thread: Safe.

---

## `FluentParserV1`

### Signature
```python
class FluentParserV1:
    def __init__(self) -> None: ...
    def parse(self, source: str) -> Resource: ...
```

### Contract
| Parameter | Type | Req | Description |
|:----------|:-----|:----|:------------|

### Constraints
- Return: Parser instance.
- State: Stateless after initialization.
- Thread: Safe for concurrent parse() calls.

---

## `parse_number`

### Signature
```python
def parse_number(
    value: str,
    locale_code: str,
) -> tuple[float | None, tuple[FluentParseError, ...]]:
```

### Contract
| Parameter | Type | Req | Description |
|:----------|:-----|:----|:------------|
| `value` | `str` | Y | Locale-formatted number string. |
| `locale_code` | `str` | Y | BCP 47 locale identifier. |

### Constraints
- Return: Tuple of (float or None, errors).
- Raises: Never.
- State: None.
- Thread: Safe.

---

## `parse_decimal`

### Signature
```python
def parse_decimal(
    value: str,
    locale_code: str,
) -> tuple[Decimal | None, tuple[FluentParseError, ...]]:
```

### Contract
| Parameter | Type | Req | Description |
|:----------|:-----|:----|:------------|
| `value` | `str` | Y | Locale-formatted number string. |
| `locale_code` | `str` | Y | BCP 47 locale identifier. |

### Constraints
- Return: Tuple of (Decimal or None, errors).
- Raises: Never.
- State: None.
- Thread: Safe.

---

## `parse_date`

### Signature
```python
def parse_date(
    value: str,
    locale_code: str,
) -> tuple[date | None, tuple[FluentParseError, ...]]:
```

### Contract
| Parameter | Type | Req | Description |
|:----------|:-----|:----|:------------|
| `value` | `str` | Y | Locale-formatted date string. |
| `locale_code` | `str` | Y | BCP 47 locale identifier. |

### Constraints
- Return: Tuple of (date or None, errors).
- Raises: Never.
- State: None.
- Thread: Safe.

---

## `parse_datetime`

### Signature
```python
def parse_datetime(
    value: str,
    locale_code: str,
    *,
    tzinfo: timezone | None = None,
) -> tuple[datetime | None, tuple[FluentParseError, ...]]:
```

### Contract
| Parameter | Type | Req | Description |
|:----------|:-----|:----|:------------|
| `value` | `str` | Y | Locale-formatted datetime string. |
| `locale_code` | `str` | Y | BCP 47 locale identifier. |
| `tzinfo` | `timezone \| None` | N | Timezone to assign. |

### Constraints
- Return: Tuple of (datetime or None, errors).
- Raises: Never.
- State: None.
- Thread: Safe.

---

## `parse_currency`

### Signature
```python
def parse_currency(
    value: str,
    locale_code: str,
) -> tuple[tuple[Decimal, str] | None, tuple[FluentParseError, ...]]:
```

### Contract
| Parameter | Type | Req | Description |
|:----------|:-----|:----|:------------|
| `value` | `str` | Y | Currency string with amount and symbol. |
| `locale_code` | `str` | Y | BCP 47 locale identifier. |

### Constraints
- Return: Tuple of ((amount, currency_code) or None, errors).
- Raises: Never.
- State: None.
- Thread: Safe.

---

## `is_valid_number`

### Signature
```python
def is_valid_number(value: float) -> TypeIs[float]:
```

### Contract
| Parameter | Type | Req | Description |
|:----------|:-----|:----|:------------|
| `value` | `float` | Y | Float to validate. |

### Constraints
- Return: True if finite float.
- Raises: None.
- State: None.

---

## `is_valid_decimal`

### Signature
```python
def is_valid_decimal(value: Decimal) -> TypeIs[Decimal]:
```

### Contract
| Parameter | Type | Req | Description |
|:----------|:-----|:----|:------------|
| `value` | `Decimal` | Y | Decimal to validate. |

### Constraints
- Return: True if finite Decimal.
- Raises: None.
- State: None.

---

## `is_valid_date`

### Signature
```python
def is_valid_date(value: date | None) -> TypeIs[date]:
```

### Contract
| Parameter | Type | Req | Description |
|:----------|:-----|:----|:------------|
| `value` | `date \| None` | Y | Date to validate. |

### Constraints
- Return: True if not None.
- Raises: None.
- State: None.

---

## `is_valid_datetime`

### Signature
```python
def is_valid_datetime(value: datetime | None) -> TypeIs[datetime]:
```

### Contract
| Parameter | Type | Req | Description |
|:----------|:-----|:----|:------------|
| `value` | `datetime \| None` | Y | Datetime to validate. |

### Constraints
- Return: True if not None.
- Raises: None.
- State: None.

---

## `is_valid_currency`

### Signature
```python
def is_valid_currency(
    value: tuple[Decimal, str] | None,
) -> TypeIs[tuple[Decimal, str]]:
```

### Contract
| Parameter | Type | Req | Description |
|:----------|:-----|:----|:------------|
| `value` | `tuple[Decimal, str] \| None` | Y | Currency tuple to validate. |

### Constraints
- Return: True if not None and amount is finite.
- Raises: None.
- State: None.

---
