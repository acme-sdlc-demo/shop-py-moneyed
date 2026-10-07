# OPEN QUESTIONS — shop-py-moneyed

## Open questions

**1. When will `Money.round()` enforce half-even explicitly?**
`round()` calls `Decimal.quantize()` without passing `rounding=ROUND_HALF_EVEN`; it inherits
whatever the ambient decimal context says. Python's default happens to be `ROUND_HALF_EVEN`, but
a caller that changes the context will silently produce wrong settlement amounts. Alice confirmed
this is a known gap and a planned change, with no release date set. Until it is fixed, callers
must set `ROUND_HALF_EVEN` in the decimal context before calling `round()`.
[cite: source:transcript-run-a080ea35@r1] [cite: src/moneyed/classes.py]

**2. When will `Money.get_amount_in_sub_unit()` raise instead of truncate?**
`int(self.currency.sub_unit * self.amount)` truncates toward zero. For a payment provider that
expects an exact minor-unit integer, calling this on an unrounded `Money` silently loses
precision. Alice described it as a latent defect for SHOP (upstream treats it as callers'
responsibility to round first). This does not block releases today — SHOP's rules already require
every settlement amount to be rounded before this method is called. Planned fix: raise if the
amount has more precision than the minor unit allows; no fix is scheduled.
[cite: source:transcript-run-a080ea35@r1] [cite: src/moneyed/classes.py]

**3. When will XCG and ZWG be added to `CURRENCIES`?**
Babel gained these two currency codes but the library has not. `test_all_babel_currencies` is
gate-deselected and tracked as a defect until XCG and ZWG are added via a reviewed change to
`classes.py`; it does not block releases because no settlement amount is affected. No timeline
given. [cite: source:transcript-run-a080ea35@r1] [cite: docs/agents/CODEBASE_MAP.md]

**4. What is the final API shape for `Money.discounted(percent)`?**
The team's leaning is a method that returns new, unrounded `Money` (e.g.
`Money.discounted(percent: Decimal) -> Money`) so the caller rounds explicitly to a settlement
amount, per the glossary rule that a percentage discount is applied before rounding, never after.
The design is still open and no release is targeted.
[cite: source:transcript-run-a080ea35@r1] [cite: profile:purpose]

**5. What is the release target for `Money.allocate(ratios)`?**
The agreed shape is `Money.allocate(ratios) -> list[Money]` where the parts sum exactly to the
original and leftover minor units go to the first parts one each in order. No implementation
exists yet and there is no target release. Checkout does allocation by hand today.
[cite: source:transcript-run-a080ea35@r1] [cite: source:product-note@r1]

**6. When will the stale `setup.cfg` metadata be raised to Python 3.12?**
`python_requires`, classifiers and mypy `python_version` all declare 3.8; SHOP's floor is 3.12
and CI/production run 3.13. The raise is planned as a dedicated commit but no owner or target
release has been assigned. [cite: source:transcript-run-a080ea35@r1] [cite: setup.cfg]

**7. When will `CurrencyMismatchError` be released?**
Introducing `CurrencyMismatchError(TypeError)` naming both currencies is the first planned change
[cite: source:product-note@r1] [cite: source:transcript-run-a080ea35@r1], but no tagged release
exists yet and no date is set.

**8. Is there a code-level guard preventing services from calling `add_currency` at runtime?**
The rule that services never call `add_currency` is a policy only; nothing in the code enforces
it. A runtime call would mutate the module-level `CURRENCIES` dict for the life of the process.
Is a lint rule, deprecation warning, or other in-code guard planned?
[cite: source:transcript-run-a080ea35@r1] [cite: src/moneyed/classes.py]

## Documents vs code

**1. `setup.cfg` Python version vs. SHOP's stated floor.**
`setup.cfg` declares `python_requires >= 3.8`, lists classifiers only up to Python 3.11, and sets
mypy's `python_version = 3.8` [cite: setup.cfg]. The interview records SHOP's actual floor as
3.12, with CI and production on 3.13 [cite: source:transcript-run-a080ea35@r1]. Alice confirmed
the mismatch is intentional stale upstream metadata, not a real constraint, and will be fixed in
a dedicated commit. Readers of `setup.cfg` alone would reach the wrong conclusion about which
Python versions the library actually supports.

**2. `Money.round()` docstring says "current Decimal rounding algorithm"; SHOP requires half-even.**
The docstring reads "Rounds the amount using the current Decimal rounding algorithm"
[cite: src/moneyed/classes.py], implying caller-controlled rounding. The domain glossary and
product note require half-even for all settlement amounts [cite: source:product-note@r1]. Alice
confirmed this is a known gap in the implementation (not a deliberate policy divergence): the
ambient default happens to be `ROUND_HALF_EVEN` so it is correct in practice today, but the code
does not enforce it and the docstring does not warn callers about the constraint.
[cite: source:transcript-run-a080ea35@r1]

**3. `add_currency` is public API but SHOP policy forbids services from calling it.**
`__init__.py` star-imports `classes.py`, making `add_currency` part of the public API
[cite: src/moneyed/classes.py]. SHOP's rule is that services must never call it at runtime; new
currencies go in through a reviewed change to `classes.py`
[cite: source:transcript-run-a080ea35@r1]. The code exposes the function freely with no docstring
note, deprecation warning, or type-level barrier that discourages runtime use. A reader of the
code alone would not know the restriction exists.

**4. `CHANGES.rst` unreleased section does not reflect SHOP's fork history.**
The release process requires every change merged since the last release to be listed in
`CHANGES.rst` under the new version before the next release [cite: source:how-we-release@r1].
The product note identifies several planned changes that have been in progress since the fork
(clearer mismatch error, percentage-discount method) [cite: source:product-note@r1], but the
`CHANGES.rst` unreleased section contains only upstream entries
[cite: CHANGES.rst]. None of the SHOP-originated work since the fork appears to
be recorded there. Before the next release this section must be updated to comply with the release
process.
