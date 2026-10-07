# CLAUDE.md — shop-py-moneyed agent guide

See `docs/agents/CODEBASE_MAP.md` for the full codebase map before designing any change.

## Stack and dependencies

- **Python 3.12+ required** (SHOP floor); CI and production run 3.13. The `setup.cfg` metadata
  (`python_requires`, classifiers, mypy `python_version`) is stale upstream text — do not update
  it as a side effect of another change; it gets a dedicated commit. [cite: setup.cfg]
  [cite: source:transcript-run-a080ea35@r1]
- **Runtime deps** (both in `install_requires`): `babel>=2.8.0` (formatting + currency names),
  `typing-extensions>=3.7.4.3`. Do not add a dependency without team approval; this library is
  imported by every SHOP service. [cite: setup.cfg]
- **Dev/test extras**: `pytest`, `pytest-mypy-plugins`, `mypy>=1.9.0`, `black` 24.4.0,
  `isort` 5.13.2, `flake8` 7.0.0. All are already in the venv. Versions are pinned in
  `.pre-commit-config.yaml`; use the gate's pinned versions. [cite: .pre-commit-config.yaml]
- **No network access** at import time or in tests. Exchange rates are never this library's
  responsibility. [cite: source:product-note@r1]

## Layout

```
src/moneyed/
  classes.py   # Currency, Money, CURRENCIES dict, add_currency, get_currency — the whole public API
  l10n.py      # format_money (thin Babel wrapper); display amounts only, never parsed back
  utils.py     # cached_property helper
  __init__.py  # star-imports classes.py; everything in classes.py is public
tests/
  test_moneyed_classes.py  # Currency and Money unit tests
  test_l10n.py             # format_money tests
  test_money.yaml          # pytest-mypy-plugins type-checking cases
docs/                      # Sphinx; conf.py holds the second version string
```

Full map: `docs/agents/CODEBASE_MAP.md` [cite: docs/agents/CODEBASE_MAP.md]

## Coding conventions

- **Type annotations everywhere.** mypy runs in strict mode; all public and private functions must
  be fully annotated. `tests/test_l10n.py` is exempt (`disallow_untyped_defs = False`). [cite: setup.cfg]
- **`from __future__ import annotations`** at the top of every source file (already present).
  [cite: src/moneyed/classes.py]
- **`Decimal`, never `float`.** Floats in arithmetic operators emit `DeprecationWarning`; new code
  must not introduce float paths. Convert unknown numeric input via `force_decimal()`. [cite: src/moneyed/classes.py]
- **`Final` for immutable attributes.** `Money.amount`, `Money.currency`, `Currency.code`, etc. are
  `Final`; keep new immutable fields the same way. [cite: src/moneyed/classes.py]
- **Error types.** Currency-mismatch arithmetic raises `TypeError` today; the planned replacement is
  `CurrencyMismatchError(TypeError)` naming both currencies. `MoneyComparisonError(TypeError)` is the
  pattern to follow. Do not swallow or widen existing exception types. [cite: src/moneyed/classes.py]
  [cite: source:transcript-run-a080ea35@r1]
- **Line length 119**, `black` formatting, `isort --profile black`. [cite: setup.cfg]
- **`cached_property`** from `moneyed.utils` (not `functools`) for lazily computed `Currency`
  attributes. [cite: src/moneyed/utils.py]

## Testing

- **Framework**: pytest with `--doctest-modules` and `--doctest-glob='*.rst'` — keep docstrings
  runnable. [cite: setup.cfg]
- **Type tests**: `tests/test_money.yaml` runs via `pytest-mypy-plugins`; add a case whenever a
  new overload or type guard is added. [cite: tests/test_money.yaml]
- **Naming**: test classes are `TestCurrency`, `TestMoney`; test functions are `test_<thing>` inside
  them or at module level for l10n. Match the existing style. [cite: tests/test_moneyed_classes.py]
- **Run only the area you changed**:
  - Core types: `pytest tests/test_moneyed_classes.py`
  - Formatting: `pytest tests/test_l10n.py`
  - Type cases: `pytest tests/test_money.yaml`
- **Gate command** (exact form, do not alter):
  ```
  python -c "import os, sys, pytest; os.environ['PATH'] = os.path.dirname(sys.executable) + os.pathsep + os.environ['PATH']; os.environ['MYPYPATH']=os.path.abspath('src'); raise SystemExit(pytest.main(['-q', '-o', 'pythonpath=src', '--mypy-ini-file=setup.cfg', '--mypy-only-local-stub', '--deselect', 'tests/test_moneyed_classes.py::test_all_babel_currencies']))"
  ```
  `test_all_babel_currencies` is intentionally deselected — XCG and ZWG are missing from
  `CURRENCIES`; this is a tracked defect, not to be fixed as a side effect. [cite: source:transcript-run-a080ea35@r1]
- **Test-only currency codes**: may use `XYZ` only with an inline comment explaining why.
  [cite: source:transcript-run-a080ea35@r1]

## Boundaries

- **Public API = everything in `src/moneyed/classes.py`** (re-exported via `__init__.py`). Any
  change to a signature, return type, or exception type requires a **minor version bump** in
  `setup.cfg` *and* `docs/conf.py` in the same commit, plus a `CHANGES.rst` entry. Arithmetic
  result changes also require a minor bump even with no signature change. [cite: source:how-we-release@r1]
- **CODEOWNERS-protected files** — changes require a code-owner review and must not be made as a
  side effect: `setup.cfg`, `pyproject.toml`, `tox.ini`, `CLAUDE.md`, `.github/**`. [cite: .github/CODEOWNERS]
- **`moneyed.add_currency`** is a public function but SHOP services must never call it at runtime.
  New currencies (e.g. XCG, ZWG) go into `classes.py` via a reviewed change. [cite: source:transcript-run-a080ea35@r1]
- **Change only what the requirement needs.** Do not touch unrelated formatting, docstrings, or
  currency definitions.

## Security

- **No network I/O** in library code or tests — no `requests`, `urllib`, `socket`. The library
  must be fully functional offline. [cite: source:product-note@r1]
- **No invented currency codes** in production code. ISO 4217 only; `XYZ` is test-only with
  justification. [cite: source:transcript-run-a080ea35@r1]
- **`Decimal(str(amount))`** is the only safe way to convert an untrusted numeric input into a
  `Decimal`; never pass an untrusted string directly to `Decimal()` without `str()` wrapping
  (already the pattern in `force_decimal`). [cite: src/moneyed/classes.py]
- **Half-even rounding** is required for all settlement amounts. `Money.round()` currently relies
  on the ambient decimal context (a known gap); until fixed, callers must set
  `ROUND_HALF_EVEN` in context before calling `round()`. [cite: source:transcript-run-a080ea35@r1]
