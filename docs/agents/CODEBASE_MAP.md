# CODEBASE_MAP — shop-py-moneyed

## Purpose

SHOP's fork of [py-moneyed](https://github.com/py-moneyed/py-moneyed). Provides the single
authoritative `Money` type (an amount together with its ISO 4217 currency), the full currency
registry with each currency's minor unit, and arithmetic, rounding and display-formatting that
every SHOP service uses for prices, totals, taxes and refunds. Forked in 2026 so SHOP can change
it under its own review process without waiting on upstream. Not published to PyPI; SHOP services
install from a git tag (`v<version>`). [cite: source:product-note@r1] [cite: source:how-we-release@r1]

## Solution layout

| Path | Purpose | Key dependencies |
|---|---|---|
| `src/moneyed/classes.py` | `Currency`, `Money`, `CURRENCIES` dict, `add_currency`, `get_currency`, `list_all_currencies`, `get_currencies_of_country`, error types | `babel`, `decimal`, `typing` |
| `src/moneyed/l10n.py` | `format_money` — thin wrapper over `babel.numbers.format_currency` for locale-aware display | `babel` |
| `src/moneyed/utils.py` | `cached_property` generic descriptor used for lazy `Currency` attributes | stdlib only |
| `src/moneyed/__init__.py` | Star-imports `classes.py`; everything in `classes.py` is part of the public API | `classes.py` |
| `tests/test_moneyed_classes.py` | Unit tests for `Currency` and `Money` | `pytest`, `moneyed` |
| `tests/test_l10n.py` | Unit tests for `format_money` | `pytest`, `moneyed.l10n` |
| `tests/test_money.yaml` | `pytest-mypy-plugins` type-checking cases for `Money` overloads | `pytest-mypy-plugins`, `mypy` |
| `setup.cfg` | Package metadata, `install_requires`, flake8/isort/pytest/mypy config | — |
| `pyproject.toml` | PEP 517 build-system declaration only | `setuptools`, `wheel` |
| `CHANGES.rst` | Changelog; must be updated before every release | — |
| `docs/conf.py` | Sphinx config; holds the second version string (must match `setup.cfg`) | — |

[cite: src/moneyed/classes.py] [cite: src/moneyed/l10n.py] [cite: src/moneyed/utils.py]
[cite: src/moneyed/__init__.py] [cite: setup.cfg] [cite: pyproject.toml]

## Key concepts

| Domain term | Type / symbol | File |
|---|---|---|
| **Money** | `Money` — `amount: Final[Decimal]` + `currency: Final[Currency]` | `src/moneyed/classes.py` |
| **Currency** | `Currency` — `code`, `numeric`, `sub_unit`, `name`, `countries` | `src/moneyed/classes.py` |
| **Minor unit** | `Currency.sub_unit: int` — e.g. 100 for EUR/USD, 1 for JPY, 1000 for BHD; never hard-coded as 2 | `src/moneyed/classes.py` |
| **Settlement amount** | Result of `Money.round(ndigits)` where `ndigits = log10(sub_unit)`; must use half-even — **known gap**: `round()` inherits ambient decimal context instead of enforcing `ROUND_HALF_EVEN` | `src/moneyed/classes.py` |
| **Display amount** | Result of `format_money(money, locale=…)` via Babel; never parsed back or used in arithmetic | `src/moneyed/l10n.py` |
| **Currency registry** | `CURRENCIES: dict[str, Currency]` and `CURRENCIES_BY_ISO: dict[str, Currency]`, populated at import time by `add_currency()` | `src/moneyed/classes.py` |
| **Currency mismatch** | Adding/subtracting/comparing `Money` of different currencies raises `TypeError` (planned: `CurrencyMismatchError(TypeError)` naming both codes) | `src/moneyed/classes.py` |
| **Percentage of Money** | `pct % money` (`__rmod__`) — returns unrounded `Money`; caller rounds to settlement separately | `src/moneyed/classes.py` |
| **Sub-unit integer** | `Money.get_amount_in_sub_unit() -> int` — truncates toward zero (known gap: should raise if amount has more precision than the minor unit allows) | `src/moneyed/classes.py` |

[cite: src/moneyed/classes.py] [cite: src/moneyed/l10n.py] [cite: source:transcript-run-a080ea35@r1]

## Where to change what

| Kind of change | Primary file(s) | Test file(s) |
|---|---|---|
| New arithmetic operation on `Money` | `src/moneyed/classes.py` (`Money` class) | `tests/test_moneyed_classes.py` (`TestMoney`) |
| New `Money` method with type overloads | `src/moneyed/classes.py` | `tests/test_money.yaml` (new case) + `tests/test_moneyed_classes.py` |
| Add a new ISO 4217 currency (e.g. XCG, ZWG) | `src/moneyed/classes.py` (currency list, reviewed change only) | `tests/test_moneyed_classes.py::test_all_babel_currencies` (re-enable after fix) |
| Change error type / message | `src/moneyed/classes.py` (exception class + raise sites) | `tests/test_moneyed_classes.py` (update `pytest.raises` calls) |
| Display formatting behaviour | `src/moneyed/l10n.py` | `tests/test_l10n.py` |
| Fix `Money.round()` to enforce half-even | `src/moneyed/classes.py` (`round` method) | `tests/test_moneyed_classes.py` (add rounding test) |
| Add `Money.discounted(percent)` (planned) | `src/moneyed/classes.py` | `tests/test_moneyed_classes.py` |
| Add `Money.allocate(ratios)` (planned) | `src/moneyed/classes.py` | `tests/test_moneyed_classes.py` |
| Changelog / version bump | `CHANGES.rst`, `setup.cfg` (`version =`), `docs/conf.py` (`release =`) | — (both version strings must match in the release commit) |

[cite: src/moneyed/classes.py] [cite: src/moneyed/l10n.py] [cite: tests/test_moneyed_classes.py]
[cite: tests/test_l10n.py] [cite: tests/test_money.yaml] [cite: source:how-we-release@r1]

## Build and test

All commands use the project venv at `project-venv/Scripts/python.exe`.

| Step | Command |
|---|---|
| Format check | `python -m black --check --quiet src tests` |
| Import order | `python -m isort --check-only src tests` |
| Lint | `python -m flake8 src tests` |
| Type check | `python -m mypy --disable-error-code redundant-cast` |
| Tests (gate) | `python -c "import os, sys, pytest; os.environ['PATH'] = os.path.dirname(sys.executable) + os.pathsep + os.environ['PATH']; os.environ['MYPYPATH']=os.path.abspath('src'); raise SystemExit(pytest.main(['-q', '-o', 'pythonpath=src', '--mypy-ini-file=setup.cfg', '--mypy-only-local-stub', '--deselect', 'tests/test_moneyed_classes.py::test_all_babel_currencies']))"` |

**`test_all_babel_currencies` is deselected at the gate until XCG and ZWG are added** — those
currencies are absent from `CURRENCIES`; this is a tracked defect. Re-enable the test once both
currencies are present. [cite: source:transcript-run-a080ea35@r1]

pytest runs `--doctest-modules` and `--doctest-glob='*.rst'`; keep all docstring examples
correct. [cite: setup.cfg]

Releases: tag `v<version>`, no PyPI. QA (gina or hal) signs off, then a product owner (erin or
frank). Any change to a rounding result or arithmetic output is a **minor** version bump minimum,
called out at the top of `CHANGES.rst`. Both `setup.cfg` and `docs/conf.py` must carry the same
version string in the release commit. [cite: source:how-we-release@r1]

## Risky areas

| Area | Risk | Notes |
|---|---|---|
| `Money.round()` | Does **not** explicitly pass `rounding=ROUND_HALF_EVEN`; relies on the ambient `decimal` context. A caller that changes context will silently get wrong rounding on settlement amounts. | Planned fix: pass `ROUND_HALF_EVEN` unconditionally. [cite: source:transcript-run-a080ea35@r1] |
| `Money.get_amount_in_sub_unit()` | `int(sub_unit * amount)` **truncates** toward zero. Calling this on an unrounded `Money` silently loses precision for a payment provider expecting exact minor-unit amounts. | Planned fix: raise if `amount` has more precision than `sub_unit` allows. [cite: source:transcript-run-a080ea35@r1] |
| `CURRENCIES` registry | Module-level mutable dict. `add_currency()` is public. SHOP rule: services never call it at runtime; only `classes.py` itself registers currencies. A runtime call corrupts the registry for the process lifetime. | [cite: source:transcript-run-a080ea35@r1] |
| Currency-mismatch error | `Money.__add__` raises a bare `TypeError` without naming the currencies. Callers catching `TypeError` for other reasons may accidentally swallow it. Planned: `CurrencyMismatchError(TypeError)`. | [cite: src/moneyed/classes.py] [cite: source:transcript-run-a080ea35@r1] |
| Float arithmetic | Multiplying or dividing `Money` by a `float` emits `DeprecationWarning` and produces a result — it does **not** raise. New code must never introduce float paths. | [cite: src/moneyed/classes.py] |
| `__init__.py` star-import | Every name added to `classes.py` at module level becomes public automatically. The ~250 currency constants (`USD`, `EUR`, `JPY`, …) are all exported. | [cite: src/moneyed/__init__.py] |
| `docs/conf.py` version | Must be updated together with `setup.cfg` in the release commit; easy to forget. | [cite: source:how-we-release@r1] |

## Connections

### Provides

- `money.type` (component): `Money` and `Currency` types — amount + currency, arithmetic, rounding; paths: `src/moneyed/classes.py`, `src/moneyed/__init__.py` [cite: src/moneyed/classes.py]
- `money.currency-registry` (component): `CURRENCIES` dict, `add_currency`, `get_currency`, `list_all_currencies`, `get_currencies_of_country` — ISO 4217 currency data with minor units; paths: `src/moneyed/classes.py`, `src/moneyed/__init__.py` [cite: src/moneyed/classes.py]
- `money.formatting` (component): `format_money` — locale-aware display amounts via Babel; paths: `src/moneyed/l10n.py` [cite: src/moneyed/l10n.py]
- `money.term.money` (business term): **Money** — an amount inseparable from its ISO 4217 currency; a bare `Decimal` intended as money is a defect; paths: `src/moneyed/classes.py` [cite: source:product-note@r1]
- `money.term.currency` (business term): **Currency** — an ISO 4217 code; SHOP never invents codes outside tests; paths: `src/moneyed/classes.py` [cite: source:product-note@r1]
- `money.term.minor-unit` (business term): **Minor unit** — `Currency.sub_unit` is the authoritative minor-unit value for every currency, never assumed to be 2; paths: `src/moneyed/classes.py` [cite: src/moneyed/classes.py]

### Uses

- None found. This library makes no outbound calls and imports nothing from other SHOP Projects. Exchange rates reach SHOP services only through shop-django-money, which itself depends on this library — not the other way round. [cite: source:transcript-run-a080ea35@r1] [cite: source:product-note@r1]
