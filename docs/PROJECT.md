# Project: shop-py-moneyed

## Purpose and users

`shop-py-moneyed` is SHOP's fork of the upstream `py-moneyed` library.
It provides every SHOP service with a single `Money` type — a `Decimal` amount bound to an ISO 4217
currency — together with the full currency registry (each currency's minor unit), arithmetic that
refuses to mix currencies, and Babel-backed locale-aware display formatting. [cite: source:product-note@r1]

SHOP forked `py-moneyed` in 2026 so the payments and catalogue teams can change it under SHOP's own
review process instead of waiting on the upstream maintainers. [cite: source:transcript-run-a080ea35@r1]

**Direct users (internal services):**

- **Catalogue** — stores prices as `Money` in the currency they were set in; never converts on save.
  [cite: source:product-note@r1]
- **Basket and checkout** — the heaviest arithmetic users: totals, per-line tax (computed and
  rounded in the service, not here), and discounts. [cite: source:product-note@r1]
- **Payments and the ledger** — settlement amounts and refunds. The ledger service imports
  `moneyed` directly as well as through `shop-django-money`. [cite: source:transcript-run-a080ea35@r1]
- **`shop-django-money`** — SHOP's fork of `django-money`; it depends on this library for its
  Django model and form fields (`moneyed.Money`, the currency registry). The dependency is
  one-way: this library does not import from `shop-django-money`.
  [cite: source:transcript-run-a080ea35@r1]

The library has no network connections at import time or in tests. Exchange rates are fetched only
through `shop-django-money` from external rate providers (Open Exchange Rates, the ECB feed).
[cite: source:product-note@r1]

## Domain and constraints

**Regulations and safety:** None. This is retail software. [cite: profile:regulatory_context]

**Rounding:** Settlement amounts must always be rounded to the currency's minor unit using half-even
(banker's) rounding. Every other amount stays unrounded until it becomes a settlement amount. The
minor unit is always taken from the currency's own definition — never hard-coded as 2 (JPY has no
sub-cent unit; KWD has 3). [cite: profile:languages] [cite: src/moneyed/classes.py]

**Currency mixing:** Adding or subtracting `Money` in different currencies must raise, never convert
silently. [cite: source:product-note@r1]

**Amounts:** `Decimal` throughout; `float` operands are accepted with a `DeprecationWarning` and
are on the way out. [cite: src/moneyed/classes.py]

**Display amounts:** Formatted via `moneyed.l10n.format_money`, which delegates to Babel's
`format_currency`. Display amounts are never parsed back into `Money` and never used in
calculations. [cite: src/moneyed/l10n.py]

**Runtime dependencies:** `babel>=2.8.0` (hard; used for display formatting and currency names) and
`typing-extensions>=3.7.4.3`. Both are listed in `install_requires`. [cite: setup.cfg]

**Python version:** `setup.cfg` (inherited from upstream) declares `python_requires = >=3.8` and
classifiers up to CPython/PyPy 3.11; mypy is configured with `python_version = 3.8`. These are
stale upstream metadata. SHOP's actual floor is Python 3.12; services and CI run 3.13. The
metadata will be raised deliberately in a later dedicated change, not as a side effect.
[cite: source:transcript-run-a080ea35@r1] [cite: setup.cfg]

**Releases:** No PyPI. SHOP services install from a git tag (`v<version>`). A release requires QA
sign-off (with test report) followed by product-owner sign-off; releases are blocked in the last
week of a month-end close unless the change fixes a wrong settlement amount. Any change to rounding
results or arithmetic output is a minor-version bump at minimum, noted at the top of `CHANGES.rst`.
Version lives in both `setup.cfg` and `docs/conf.py`; both change in the same commit.
[cite: source:how-we-release@r1]

**Currency registry extensibility:** `moneyed.add_currency` exists and works at runtime, but
SHOP's rule is that services must never call it and must never invent non-ISO codes outside tests
(tests may use `XYZ` only with an explanation). New ISO currencies (e.g. XCG, ZWG) enter the
library's own `CURRENCIES` dict only through a reviewed change.
[cite: source:transcript-run-a080ea35@r1]

## Decisions so far (and why)

**Fork rather than upstream contribution** — SHOP needs control over the review and release
timeline for money-critical changes. Forked in 2026. [cite: source:transcript-run-a080ea35@r1]

**`Money` requires a currency at construction** — `Money(amount)` without a currency raises
`TypeError`; there is no default currency. A bare `Decimal` treated as money is a defect per the
domain glossary. [cite: src/moneyed/classes.py] [cite: profile:languages]

**Arithmetic refuses currency mixing** — `__add__` raises `TypeError` when currencies differ. A
dedicated `CurrencyMismatchError` subclassing `TypeError` (so existing `except TypeError` callers
keep working) is planned; the message will name both currencies (e.g. `"cannot add EUR to USD"`).
Not yet implemented. [cite: source:transcript-run-a080ea35@r1] [cite: src/moneyed/classes.py]

**Half-even rounding via `Decimal.quantize`** — `Money.round()` calls `Decimal.quantize()` without
an explicit `rounding=` argument, relying on Python's default decimal context (which is
`ROUND_HALF_EVEN`). This is fragile; the plan is to pass `rounding=ROUND_HALF_EVEN` explicitly. Not
yet done. [cite: source:transcript-run-a080ea35@r1] [cite: src/moneyed/classes.py]

**Percentage discount returns unrounded `Money`** — the planned API leans toward
`Money.discounted(percent: Decimal) -> Money`, returning a new unrounded `Money` so the caller
performs the explicit half-even round to a settlement amount as a separate step (per the glossary:
"a percentage discount is applied before rounding, never after"). Method name and signature are
still open design. Not yet implemented. [cite: source:transcript-run-a080ea35@r1]

**Allocation** — `Money.allocate(ratios: list[int]) -> list[Money]` is implemented in the library.
Parts are floored to the minor unit; leftover minor units go to the first parts one each in order,
so parts always sum exactly to the original. Earlier interviews and the product note described this
as absent; the code now contains it.
[cite: src/moneyed/classes.py] [cite: source:product-note@r1]

**`get_amount_in_sub_unit()` truncates** — `int(self.currency.sub_unit * self.amount)` truncates
toward zero. For SHOP, a settlement amount passed here must already be rounded half-even; passing an
unrounded amount silently truncates, which is a latent defect. Upstream intended callers to round
first. SHOP considers it a known gap; no fix is scheduled yet.
[cite: source:transcript-run-a080ea35@r1] [cite: src/moneyed/classes.py]

**Babel as hard runtime dependency** — Babel supplies currency names and drives
`moneyed.l10n.format_money`; it is in `install_requires` so every caller gets it.
[cite: source:transcript-run-a080ea35@r1] [cite: setup.cfg]

**Tax, exchange-rate, and basket logic stay in consuming services** — this library only supplies
`Money`, arithmetic, rounding, and display formatting. Tax is computed and rounded per line in
basket/checkout. Exchange rates are fetched through `shop-django-money`.
[cite: source:transcript-run-66c5f847@r1] [cite: source:product-note@r1]

**Four known failing tests** — the gate and CI carry four accepted, known failures; none are
deselected:

- `tests/test_money.yaml::can_instantiate_money` [cite: tests/test_money.yaml]
- `tests/test_money.yaml::instantiating_money_without_currency_gives_error` [cite: tests/test_money.yaml]
- `tests/test_moneyed_classes.py::TestMoney::test_str` [cite: tests/test_moneyed_classes.py]
- `tests/test_moneyed_classes.py::test_all_babel_currencies` — Babel added XCG and ZWG, which
  `CURRENCIES` does not yet contain; adding them is tracked as a defect but does not affect
  settlement amounts so it does not block releases.
  [cite: source:transcript-run-66c5f847@r1]

## Glossary

Terms as SHOP uses them [cite: profile:languages]:

| Term | Meaning |
|---|---|
| **Money** | An amount together with its currency, never one without the other. A bare `Decimal` meant as money is a defect. |
| **Currency** | An ISO 4217 code (`EUR`, `USD`, `JPY`). SHOP never invents currency codes; a test may use `XYZ` only if it says why. |
| **Minor unit** | The smallest unit a currency is settled in (cents for EUR, none for JPY). Taken from the currency's own definition, never hard-coded as 2. |
| **Settlement amount** | The amount actually charged or paid out. Always rounded to the currency's minor unit using half-even rounding. Every other amount stays unrounded until it becomes a settlement amount. |
| **Display amount** | An amount formatted for a person in their locale. Never parsed back into `Money` and never used in a calculation. |
| **Exchange rate** | How many units of the target currency one unit of the source currency buys, at a stated time, from a stated provider. A rate without its time and provider is not usable. |
| **Rate provider** | An outside service SHOP gets exchange rates from (e.g. Open Exchange Rates, the ECB feed). This library does not fetch rates. |
| **Conversion** | Turning `Money` in one currency into `Money` in another with an exchange rate. Records the rate used. Converting twice in a row is a defect. |
| **Allocation** | Splitting one `Money` into parts by ratios so the parts add up exactly to the whole. Leftover minor units go to the first parts, one each, in order. Implemented as `Money.allocate(ratios)`. |
| **Price** | What a product costs, as `Money`, before tax and discounts. Stored in the currency it was set in; never converted on save. |
| **Total** | Sum of a basket's prices, discounts, and taxes. A total mixing currencies is refused, not silently converted. |
| **Discount** | A reduction of a price, as `Money` or as a percentage. A percentage discount is applied before rounding, never after. |
| **Refund** | `Money` paid back against an earlier settlement, in the settlement's currency, never more than was settled. |
| **Tax** | `Money` added to a price by a tax rule, computed per line and rounded per line to the minor unit (half-even), then summed. Computed in basket/checkout, not in this library. |
| **Basket** | The lines a customer is about to pay for. Exactly one currency; a line in another currency is converted on adding, with the rate recorded on the line. |
| **Ledger entry** | An append-only record of one settlement, refund, or adjustment, with its `Money`, its time, and who caused it. Never edited. |
| **Money field** | In Django, the pair of model fields (amount and currency) that store one `Money`. Both required; a blank currency is a defect. |
