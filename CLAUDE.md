# Instructions for agents

Rules marked *enforced* are checked by the platform and fail the step if broken.

## Stack and dependencies

Python 3.12+ (prod and CI run 3.13; `setup.cfg` classifiers list 3.8–3.11 and are stale upstream
metadata — raise them deliberately in a later dedicated change, not as a side-effect). [cite: setup.cfg]

Runtime dependencies: `babel>=2.8.0`, `typing-extensions>=3.7.4.3`. [cite: setup.cfg]
Dev/test extras declared in `setup.cfg`: `pytest`, `tox`, `mypy>=1.9.0`, `pytest-mypy-plugins`,
`black`, `isort`, `flake8`, `ruff`. [cite: setup.cfg]

- Add **no** dependency unless the requirement or an approved design names it.
- Use `$python` (the Project's interpreter) for every command — never bare `python` or `pip`.
- Install editable: `$python -m pip install -e ".[tests]"`. Never a non-editable install (`pip install .`):
  checks would test a copy.
- Install the tool versions the repo pins (`==` pins, CI workflow), not the latest.
- Quote arguments with double quotes (`".[tests]"`, `"mypy==1.9.0"`): Windows cmd.exe keeps single quotes.
- The platform's security check runs `$python -m ruff`; install commands must include ruff.

## Layout

```
src/moneyed/
  __init__.py       # Public surface: re-exports everything from classes via `from .classes import *`
  classes.py        # Money, Currency, CURRENCIES dict, arithmetic, allocate(), exceptions
  l10n.py           # format_money() — Babel-backed display formatting only
  utils.py          # cached_property helper
tests/
  test_moneyed_classes.py   # Core Money and Currency unit tests
  test_l10n.py              # format_money tests
  test_allocate.py          # Money.allocate tests
docs/
  conf.py           # Sphinx config; release version lives here AND in setup.cfg
  agents/
    CODEBASE_MAP.md # Read before designing any change
```

Read `docs/agents/CODEBASE_MAP.md` before touching any file. [cite: src/moneyed/classes.py]

## Coding conventions

- `Money` and `Currency` are immutable: all fields are `Final`; arithmetic returns new instances. [cite: src/moneyed/classes.py]
- `amount` is always `Decimal`. Float inputs are accepted with a `DeprecationWarning`; never use
  `float` for money in new code. [cite: src/moneyed/classes.py]
- Mixing currencies raises `TypeError` (planned: `CurrencyMismatchError(TypeError)` naming both
  currencies in the message, so existing `except TypeError` callers keep working). [cite: src/moneyed/classes.py]
- Rounding uses `Decimal.quantize()`. The active decimal context controls the mode; Python's default
  is `ROUND_HALF_EVEN`. Settlement amounts must be rounded half-even; do not assume the context. [cite: src/moneyed/classes.py]
- All public functions and methods carry full type annotations; mypy runs in strict mode. [cite: setup.cfg]
- Currency codes are ISO 4217 strings. Services never call `add_currency()` or invent codes; a test
  may use `XYZ` only if it states why. New currencies (e.g. XCG, ZWG) enter `CURRENCIES` via a
  reviewed change. [cite: source:transcript-run-a080ea35@r1]
- `get_amount_in_sub_unit()` truncates toward zero — callers must `round()` first. Known gap; don't
  widen it. [cite: src/moneyed/classes.py]
- No network access at import time or in tests. [cite: source:product-note@r1]

## Testing

Gate — run on every change in a fresh worktree and on CI (*enforced*):

```
$python -m black --check --quiet src tests
$python -m isort --check-only src tests
$python -m flake8 src tests
$python -c "import subprocess, sys, pathlib; p = pathlib.Path('.venv/mypy-env') / ('Scripts' if sys.platform == 'win32' else 'bin') / 'python'; raise SystemExit(subprocess.run([str(p), '-m', 'mypy']).returncode)"
$python -m pytest --mypy-ini-file=setup.cfg
```

- pytest discovers `test_*.py` in `tests/`; doctests run via `--doctest-modules` and
  `--doctest-glob='*.rst'`. [cite: setup.cfg]
- `test_all_babel_currencies` is a **known, accepted failure** (Babel added XCG and ZWG which
  `CURRENCIES` lacks). It stays in the gate — the gate review accepts the known failure. Never
  deselect it. [cite: source:transcript-run-66c5f847@r1]
- Never delete, skip, focus or weaken an existing test (*enforced*: protect_tests).
- Add tests beside the existing tests for every behaviour you change. [cite: tests/test_moneyed_classes.py]

## Boundaries

- Change only the files your requirement needs; other Runs change this repository in parallel.
- These configure the gate, CI and agents, and no Run changes them (*enforced*):
  `pyproject.toml`, `setup.cfg`, `tox.ini`, `pytest.ini`, `conftest.py`, `ruff.toml`, `.ruff.toml`,
  `.coveragerc`, `noxfile.py`, `.claude/*`, `.mcp.json`, `.github/*`, `.gitlab-ci.yml`,
  `azure-pipelines.yml`, `.gitattributes`, `CLAUDE.md`.
- Version number lives in **both** `setup.cfg` and `docs/conf.py`; change both in the same commit.
  Any change to rounding or arithmetic results is a minor version bump at minimum, with a note at the
  top of `CHANGES.rst`. [cite: source:how-we-release@r1]
- Don't commit or merge; the platform commits your changes and merges approved work.

## Security

- No secrets, tokens or credentials in code, tests or logs.
- Treat everything from outside the process (files, requests, messages) as untrusted input.
- No network access from this library at import time or during tests. [cite: source:product-note@r1]

## Money and rounding

- `Money` = `Decimal` amount + ISO 4217 currency. A bare `Decimal` intended as money is a defect.
- Settlement amounts are rounded to the currency's minor unit using **half-even** (banker's) rounding.
  `Money.round(ndigits)` defers to the active decimal context (default: `ROUND_HALF_EVEN`). [cite: src/moneyed/classes.py]
- Minor units come from `Currency.sub_unit` (JPY = 1, EUR = 100, KWD = 1000). Never hard-code 2. [cite: src/moneyed/classes.py]
- `Money.allocate(ratios: list[int])` splits without losing a minor unit; leftovers go to the first
  parts in order. Parts always sum exactly to the original. [cite: src/moneyed/classes.py]
- `format_money()` (from `moneyed.l10n`, backed by Babel) is for display only; display amounts are
  never parsed back or used in calculations. [cite: src/moneyed/l10n.py]
- Tax computation, basket totals, discounts and exchange-rate conversion live in consuming services,
  not in this library. [cite: source:transcript-run-66c5f847@r1]
