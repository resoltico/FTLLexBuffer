# FTLLexBuffer Testing Documentation

This document describes the testing infrastructure for FTLLexBuffer.

---

## Table of Contents

1. [Testing Overview](#testing-overview)
2. [Scripts Reference](#scripts-reference)
3. [Daily Workflow](#daily-workflow)
4. [Property-Based Testing](#property-based-testing)
5. [Hypothesis Configuration](#hypothesis-configuration)
6. [Coverage Requirements](#coverage-requirements)
7. [Troubleshooting](#troubleshooting)

---

## Testing Overview

FTLLexBuffer uses comprehensive testing with a focus on correctness and reliability:

- **Property-based testing** with Hypothesis (100+ tests)
- **Comprehensive coverage** (95%+ required)
- **Performance regression tests** (baseline enforcement)
- **Spec conformance tests** (FTL 1.0 validation)
- **Type safety** (mypy strict mode)
- **Code quality** (ruff + pylint)

### Core Principles

1. **Correctness First** - Tests validate behavior, not implementation
2. **Property-Based** - Hypothesis generates hundreds of test cases automatically
3. **Regression Protection** - Failed examples are saved and replayed automatically
4. **Fast Feedback** - Local tests run in <30s, full CI in ~5-10 minutes
5. **Production Quality** - Strict standards prevent bugs from reaching users

---

## Scripts Reference

### [scripts/lint.sh](scripts/lint.sh) - Code Quality

**Purpose:** Run all linters and type checkers

**Usage:**
```bash
./scripts/lint.sh        # Check code quality
./scripts/lint.sh --fix  # Auto-fix where possible
./scripts/lint.sh --ci   # CI mode (strict)
```

**Checks:**
1. Ruff (linting + formatting)
2. Mypy (type checking - strict mode)
3. Pylint (static analysis - 10.00/10 target)

**Duration:** ~30-60 seconds

---

### [scripts/test.sh](scripts/test.sh) - Test Suite

**Purpose:** Run full test suite with coverage

**Usage:**
```bash
./scripts/test.sh          # Full suite with coverage
./scripts/test.sh --quick  # No coverage (faster)
./scripts/test.sh --ci     # CI mode
```

**What it does:**
1. Clears pytest cache
2. Runs all tests with Hypothesis property-based testing
3. Automatically replays saved examples from `.hypothesis/examples/`
4. Generates coverage report (95%+ threshold)
5. Shows **[ALERT]** if Hypothesis discovers a bug

**Important:** If you see `[ALERT] HYPOTHESIS DISCOVERED A BUG`, this is a REAL bug that needs investigation. The failing example is automatically saved for regression protection.

---

## Daily Workflow

### Standard Development

```bash
# 1. Write code
vim src/ftllexbuffer/parser.py

# 2. Run linter
./scripts/lint.sh

# 3. Run tests
./scripts/test.sh

# 4. Commit if all pass
git add . && git commit -m "Add feature"

# 5. Push
git push
```

---

## Property-Based Testing

### What is Property-Based Testing?

Instead of writing individual test cases, you write **properties** that should always be true:

```python
from hypothesis import given
from hypothesis import strategies as st

# Traditional test - checks ONE specific case
def test_parser_empty_string():
    result = parse("")
    assert result is not None

# Property-based test - checks HUNDREDS of cases automatically
@given(st.text())
def test_parser_handles_any_string(text):
    result = parse(text)
    # Property: parser should never crash
    assert result is not None
```

**Hypothesis automatically:**
- Generates hundreds of random inputs
- Finds edge cases you didn't think of
- Shrinks failures to minimal examples
- Saves failures for regression protection

### Real Example from FTLLexBuffer

```python
@given(ftl_message_text())
def test_parse_then_serialize_roundtrips(ftl_source):
    """Property: parse(serialize(parse(x))) == parse(x)"""
    ast1 = parse(ftl_source)
    serialized = serialize(ast1)
    ast2 = parse(serialized)
    assert ast1 == ast2  # Roundtrip property
```

This single test validates thousands of combinations automatically.

### When Hypothesis Finds a Bug

**Example scenario:**
```bash
$ ./scripts/test.sh
...
FAILED tests/test_parser.py::test_parser_handles_any_string
Falsifying example: test_parser_handles_any_string(
    text='\x00'
)
AssertionError: Parser crashed on null byte

[ALERT] HYPOTHESIS DISCOVERED A BUG
This example has been saved to .hypothesis/examples/
```

**What to do:**
1. Fix the bug in your code (handle null bytes)
2. Re-run `./scripts/test.sh` - saved example automatically replays
3. Optionally add `@example("\x00")` decorator to make it explicit

**Result:** Permanent regression protection - this example will replay on EVERY future test run.

---

## Hypothesis Configuration

### Automatic Profile Detection

Tests use different configurations based on environment:

| Environment | Profile | Max Examples | Behavior |
|-------------|---------|--------------|----------|
| Local development | `default` | 100 | Fast feedback, random seed |
| Extended testing (CI=true) | `ci` | 200 | Thorough, deterministic |

**Implementation:** [tests/conftest.py](tests/conftest.py) auto-detects via `CI=true` env var

### Running with Extended Test Profile

```bash
# Test with extended thoroughness (200 examples instead of 100)
export CI=true
pytest tests/
```

**Use when:** You want more thorough property-based testing before publishing

---

## Coverage Requirements

### Coverage Threshold

- **Required:** 95%+ (production-ready quality baseline)

**Rationale:** 95% threshold ensures production quality. All testing and quality checks are performed locally before committing.

---

## Troubleshooting

### Issue: Tests Pass Locally but Fail in CI

**Cause:** CI runs more examples (200 vs 100)

**Solution:**
```bash
# Run with CI profile locally
export CI=true
pytest tests/
```

### Issue: Hypothesis Discovers a Bug

**Symptom:** `[ALERT] HYPOTHESIS DISCOVERED A BUG` message

**This is GOOD:** You found a real bug before it reached production!

**Action:**
1. Look at the "Falsifying example" in output
2. Fix the bug in source code
3. Re-run tests - example replays automatically
4. (Optional) Add `@example()` decorator for documentation

### Issue: Coverage Too Low

**Check coverage (95% threshold):**
```bash
# View HTML coverage report
pytest --cov=src/ftllexbuffer --cov-report=html
open htmlcov/index.html
```

**CI (95% threshold):**
- Download coverage artifact from GitHub Actions
- Or run locally: `pytest --cov=... --cov-fail-under=95`

### Issue: Lint Errors

**Auto-fix where possible:**
```bash
./scripts/lint.sh --fix
```

**Manual fixes:**
- Ruff errors: Usually formatting - let ruff fix them
- Mypy errors: Type annotations missing or incorrect
- Pylint errors: Code quality issues

---

## Test Organization

### Directory Structure

```
tests/
├── conftest.py              # Pytest + Hypothesis configuration
├── .pylintrc                # Test-specific pylint config
├── mypy.ini                 # Test-specific mypy config
├── strategies.py            # Hypothesis strategy helpers
├── test_*.py                # Test modules (115 files)
└── helpers/                 # Test utilities
```

### Test File Naming

- `test_*.py` - Standard test modules
- Property-based tests use `@given()` decorator
- Spec conformance: `test_spec_conformance.py`
- Performance: `test_performance_regression.py`

### Test Markers

```python
@pytest.mark.property  # Property-based test
@pytest.mark.slow      # Slow-running test (use sparingly)
```

---

## Best Practices

### Writing Good Property Tests

**DO:**
- Test properties, not specific values
- Use broad input strategies (`st.text()`, `st.integers()`)
- Let Hypothesis find edge cases for you

**DON'T:**
- Test implementation details
- Use overly narrow strategies
- Duplicate example-based tests

### Example: Good vs Bad

**Bad (overly specific):**
```python
@given(st.integers(min_value=1, max_value=10))
def test_parser_small_numbers(n):
    parse(f"value = {n}")
```

**Good (broad property):**
```python
@given(st.integers())
def test_parser_any_integer(n):
    # Property: parser handles any integer
    result = parse(f"value = {n}")
    assert result.value == n
```

### Adding Explicit Examples

Use `@example()` for critical edge cases:

```python
@given(st.text())
@example("")           # Empty string
@example("\x00")       # Null byte
@example("日本語")     # Unicode
def test_parser_text(text):
    ...
```

---

**Remember:** Property-based testing finds bugs you didn't know existed. When Hypothesis discovers a failure, that's a success - you caught a bug before production!
