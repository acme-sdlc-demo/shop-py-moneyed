# Codebase Map

## Overview

py-moneyed is a Python library that provides `Money` and `Currency` types for
shop, billing and financial code. All public symbols are re-exported from the
top-level `moneyed` package.

## Key modules

| Path | Purpose |
|------|---------|
| `src/moneyed/classes.py` | Core `Money` and `Currency` classes, all ISO 4217 currency constants, `get_currency`, `add_currency`, helper functions [cite: src/moneyed/classes.py] |
| `src/moneyed/l10n.py` | Locale-aware `format_money` using Babel [cite: src/moneyed/l10n.py] |
| `src/moneyed/utils.py` | Internal utilities (`cached_property`) [cite: src/moneyed/utils.py] |
| `src/moneyed/__init__.py` | Re-exports everything from `classes` via `from .classes import *` [cite: src/moneyed/__init__.py] |

## Money arithmetic and allocation

`Money` stores an immutable `Decimal` amount and a `Currency`.  Standard
arithmetic operators (`+`, `-`, `*`, `/`, `%`) are defined with currency
matching and deprecation warnings for `float` operands.
[cite: src/moneyed/classes.py]

`Money.allocate(ratios: list[int]) -> list[Money]` splits an amount into parts
without losing a minor unit: each part is floored to the currency's minor unit,
then remaining minor units are distributed one-at-a-time to the earliest parts
in order, guaranteeing `sum(parts) == original`.  Raises `ValueError` for
empty, negative, or zero-sum ratio lists. [cite: src/moneyed/classes.py]

## Tests

| Path | Covers |
|------|--------|
| `tests/test_allocate.py` | `Money.allocate` — all six acceptance criteria plus edge cases [cite: tests/test_allocate.py] |

## Connections

### Provides

- `moneyed` (library): `Money`, `Currency` and ISO 4217 constants; paths: `src/moneyed/**` [cite: src/moneyed/__init__.py]
- `Money.allocate` (interface): lossless ratio-based allocation of a `Money` amount; paths: `src/moneyed/classes.py` [cite: src/moneyed/classes.py]

### Uses

(none — no other Projects in the Vertical registry)
