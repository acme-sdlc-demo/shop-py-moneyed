<!-- Generated from: source:product-note@r1, source:how-we-release@r1, source:transcript-run-a080ea35@r1,
     profile fields, and the codebase. -->

# PROJECT — shop-py-moneyed

## Purpose and users

SHOP's fork of upstream py-moneyed, created in 2026 so the payments and catalogue teams can change
it under SHOP's own review process instead of waiting on upstream. [cite: source:product-note@r1]

It provides the single authoritative `Money` type (an amount together with its ISO 4217 currency),
the currency registry with each currency's minor unit, and the arithmetic, rounding and
display-formatting that every SHOP service uses for prices, totals, taxes and refunds.
[cite: profile:purpose] [cite: docs/agents/CODEBASE_MAP.md]

**Direct users:**

- **Catalogue** — stores prices as `Money` in the currency they were set in.
  [cite: source:product-note@r1]
- **Basket and checkout** — totals, discounts, per-line tax; the heaviest users of arithmetic and
  rounding. [cite: source:product-note@r1]
- **Payments and ledger** — settlement amounts and refunds, which must match the payment provider
  to the minor unit. The ledger service imports `moneyed` directly as well as through
  shop-django-money. [cite: source:product-note@r1] [cite: source:transcript-run-a080ea35@r1]
- **shop-django-money** — SHOP's fork of django-money; depends on this library for `Money` and the
  currency registry. No import goes the other way. [cite: source:transcript-run-a080ea35@r1]

The library is not published to PyPI. SHOP services install it from a git tag (`v<version>`).
[cite: source:how-we-release@r1]

## Domain and constraints

**Regulations:** none — retail software. [cite: profile:regulatory_context]

**Safety class:** none. [cite: profile:safety_class]

**Network I/O:** forbidden at import time and in tests. Exchange rates are always the
responsibility of rate providers (Open Exchange Rates, the ECB feed), reached through
shop-django-money; never this library's job. [cite: source:product-note@r1]

**Platform:** Python 3.12 minimum; CI and production run 3.13. (`setup.cfg` still says 3.8 —
see *Decisions* and *Open Questions*.) [cite: source:transcript-run-a080ea35@r1]

**Numeric correctness:**

- `Decimal` only; floats in arithmetic emit `DeprecationWarning` and must not be introduced in new
  code. [cite: src/moneyed/classes.py]
- Settlement amounts must be rounded to the currency's own minor unit using half-even (banker's)
  rounding. [cite: source:product-note@r1]
- Minor unit comes from `Currency.sub_unit`; never assumed to be 2 (JPY has none; BHD uses
  1 000). [cite: src/moneyed/classes.py]

**Dependency budget:** Babel ≥ 2.8.0 and typing-extensions ≥ 3.7.4.3 are the only two runtime
dependencies. No new dependency may be added without team approval, because this library is
imported by every SHOP service. [cite: setup.cfg]

**Currency codes:** ISO 4217 only in production code. `XYZ` is permitted in tests only, with an
inline comment explaining why. [cite: source:transcript-run-a080ea35@r1]

**Type safety:** mypy runs in strict mode on all source files. `from __future__ import annotations`
is present in every source file. [cite: setup.cfg] [cite: src/moneyed/classes.py]

## Decisions so far (and why)

**1. Fork upstream py-moneyed rather than contribute upstream.**
SHOP needs to move at its own pace for payments-critical changes. Forking gives the team full
review control. [cite: source:product-note@r1] [cite: source:transcript-run-a080ea35@r1]

**2. Tag-based releases, not PyPI.**
SHOP services install from `v<version>` git tags. Release requires QA sign-off (gina or hal)
followed by product-owner sign-off (erin or frank); nobody signs off a release they prepared.
No release in the last week of a month (finance's month-end close) unless it fixes a wrong
settlement amount. [cite: source:how-we-release@r1]

**3. Any rounding or arithmetic result change triggers a minor version bump.**
Downstream services are settlement-critical; even a silent change to what `round()` returns
requires a bump called out at the top of `CHANGES.rst`. Both `setup.cfg` and `docs/conf.py` must
carry the same version string in the release commit. [cite: source:how-we-release@r1]

**4. Babel is a hard runtime dependency (in `install_requires`).**
`moneyed.l10n` wraps `babel.numbers.format_currency` for locale-aware display amounts, and Babel
is the source of currency names. Every caller gets it. [cite: source:transcript-run-a080ea35@r1]
[cite: setup.cfg]

**5. Currency-mismatch arithmetic raises `TypeError` today; `CurrencyMismatchError` is planned.**
`Money.__add__` raises a bare `TypeError` without naming the currencies. The planned
`CurrencyMismatchError(TypeError)` subclass will name both currencies in its message, while
keeping backward compatibility for callers that already catch `TypeError`.
[cite: src/moneyed/classes.py] [cite: source:transcript-run-a080ea35@r1]

**6. `CURRENCIES` is a mutable module-level dict; services may not call `add_currency` at runtime.**
`add_currency` is public API (star-imported from `__init__.py`) but SHOP's rule is that services
never call it. New currencies (e.g. XCG, ZWG) enter through a reviewed change to `classes.py`.
A runtime call would corrupt the registry for the lifetime of the process.
[cite: source:transcript-run-a080ea35@r1] [cite: src/moneyed/classes.py]

**7. Display amounts are produced by Babel and never parsed back.**
`format_money` is for receipts and human display only; it is never used as input to arithmetic.
[cite: source:product-note@r1] [cite: src/moneyed/l10n.py]

**8. `setup.cfg` metadata (`python_requires`, classifiers, mypy `python_version`) is intentionally
left at its stale upstream values (3.8) for now.**
SHOP's actual floor is 3.12. Raising it is planned as a dedicated commit, not done as a side
effect of any other change. [cite: source:transcript-run-a080ea35@r1] [cite: setup.cfg]

**9. `Money.round()` currently inherits the ambient decimal context (a known gap).**
Python's default context happens to be `ROUND_HALF_EVEN`, which is correct. Passing
`rounding=ROUND_HALF_EVEN` explicitly to `Decimal.quantize` is a planned fix, not yet done.
Until then, callers must ensure the context is set before calling `round()`.
[cite: source:transcript-run-a080ea35@r1] [cite: src/moneyed/classes.py]

**10. `Money.get_amount_in_sub_unit()` truncates (a known gap).**
`int(sub_unit * amount)` truncates toward zero. Upstream intends callers to round first; SHOP
treats calling this on an unrounded amount as a latent defect. Planned fix: raise if the amount
has more precision than the minor unit allows. [cite: source:transcript-run-a080ea35@r1]
[cite: src/moneyed/classes.py]

**11. Allocation is not yet in the library.**
Checkout does it by hand today. The agreed shape is `Money.allocate(ratios)` returning a list
that sums exactly to the original, with leftover minor units going to the first parts one each in
order. No target release. [cite: source:product-note@r1] [cite: source:transcript-run-a080ea35@r1]

**12. Planned roadmap order.**
`CurrencyMismatchError` → `Money.round()` half-even fix → percentage-discount method
(`Money.discounted(percent)`) → allocation (`Money.allocate(ratios)`) → stale `setup.cfg`
metadata raise. [cite: source:transcript-run-a080ea35@r1]

## Glossary

Terms as SHOP uses them. Where a term has a common meaning elsewhere, SHOP's definition wins in
code, documents and reviews. [cite: profile:glossary]

**Money** — an amount together with its currency, never one without the other. A bare `Decimal`
that is meant as money is a defect. [cite: src/moneyed/classes.py]

**Currency** — an ISO 4217 code (`EUR`, `USD`, `JPY`). SHOP never invents currency codes; a test
may use `XYZ` only if it says why. [cite: src/moneyed/classes.py]

**Minor unit** — the smallest unit a currency is settled in (cents for EUR, none for JPY). Taken
from `Currency.sub_unit`, never hard-coded as 2. [cite: src/moneyed/classes.py]

**Settlement amount** — the amount actually charged or paid out. Always rounded to the currency's
minor unit using half-even (banker's) rounding. Every other amount stays unrounded until it
becomes a settlement amount. [cite: source:product-note@r1]

**Display amount** — an amount formatted for a person in their locale via `format_money`. Never
parsed back into `Money` and never used in a calculation. [cite: source:product-note@r1]
[cite: src/moneyed/l10n.py]

**Exchange rate** — how many units of the target currency one unit of the source currency buys, at
a stated time, from a stated provider. A rate without its time and provider is not usable. Not
this library's responsibility. [cite: source:product-note@r1]

**Rate provider** — an outside service SHOP gets exchange rates from (e.g. Open Exchange Rates,
the ECB feed). Reached only through shop-django-money. [cite: source:transcript-run-a080ea35@r1]

**Conversion** — turning `Money` in one currency into `Money` in another with an exchange rate.
A conversion records the rate it used. Converting twice in a row is a defect.
[cite: profile:glossary]

**Allocation** — splitting one `Money` into parts by ratios so the parts add up exactly to the
whole. Leftover minor units go to the first parts, one each, in order. Not yet in the library.
[cite: source:product-note@r1] [cite: source:transcript-run-a080ea35@r1]

**Price** — what a product costs, as `Money`, before tax and discounts. Stored in the currency it
was set in, never converted on save. [cite: profile:glossary]

**Total** — the sum of a basket's prices, discounts and taxes. A total mixing currencies is
refused, not converted silently. [cite: source:product-note@r1]

**Discount** — a reduction of a price, as `Money` or as a percentage. A percentage discount is
applied before rounding, never after. [cite: profile:glossary]

**Refund** — `Money` paid back against an earlier settlement, in the settlement's currency, never
more than was settled. [cite: profile:glossary]

**Basket** — the lines a customer is about to pay for. Has exactly one currency, chosen when its
first line is added; a line in another currency is converted on adding, with the rate recorded on
the line. [cite: profile:glossary]

**Tax** — `Money` added to a price by a tax rule of the buyer's country, computed per line,
rounded per line to the minor unit (half-even), then summed. Never computed on the total.
[cite: profile:glossary]
