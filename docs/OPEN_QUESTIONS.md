# Open questions and discrepancies

## Open questions

**1. When will `setup.cfg` python metadata be updated?**
`setup.cfg` declares `python_requires = >=3.8` and classifiers only up to 3.11, but SHOP's actual floor is 3.12 and services run 3.13. Alice confirmed the metadata is stale upstream and will be raised deliberately in a later change, but no target release has been named. Until it is updated, tooling (mypy's `python_version = 3.8` in `setup.cfg`) may miss Python-version-specific type errors. [cite: source:transcript-run-a080ea35@r1] [cite: setup.cfg]

**2. Will `Money.round()` be fixed to enforce half-even unconditionally?**
`Money.round()` calls `Decimal.quantize()` without passing `rounding=ROUND_HALF_EVEN`, relying on Python's default decimal context. The plan is to make it explicit, but no release is targeted and the change is not yet made. Until then, any caller that alters the decimal context (e.g. via `decimal.localcontext`) will silently get the wrong rounding on settlement amounts. [cite: source:transcript-run-a080ea35@r1] [cite: src/moneyed/classes.py]

**3. What should `get_amount_in_sub_unit()` do with unrounded amounts?**
The method returns `int(self.currency.sub_unit * self.amount)`, which truncates toward zero. SHOP considers passing an unrounded amount a latent defect: such a call should raise rather than truncate silently. No fix is scheduled. A team decision is needed on the right API: raise, round internally, or document that callers must round first. [cite: source:transcript-run-a080ea35@r1] [cite: src/moneyed/classes.py]

**4. When will XCG and ZWG be added to `CURRENCIES`?**
`test_all_babel_currencies` fails because Babel recognises XCG and ZWG but the library's `CURRENCIES` dict does not contain them. The test is an accepted known failure in the gate. No target release has been set for adding the two currencies; a reviewed change is required. [cite: source:transcript-run-66c5f847@r1] [cite: source:product-note@r1]

**5. Is `CurrencyMismatchError` API finalised?**
The plan is a dedicated exception subclassing `TypeError` with a message naming both currencies (e.g. `"cannot add EUR to USD"`). The subclassing of `TypeError` was agreed so existing `except TypeError` callers keep working. The exception is not yet implemented; no target release has been named. [cite: source:transcript-run-a080ea35@r1]

**6. Is the percentage-discount API (`Money.discounted`) finalised?**
The leaning is toward `Money.discounted(percent: Decimal) -> Money` returning new, unrounded `Money` (rounding to a settlement amount stays a separate explicit step). The method name, parameter name, and exact signature are still open design. No target release. [cite: source:transcript-run-a080ea35@r1]

**7. Roadmap sequencing and target releases**
The agreed order — `CurrencyMismatchError` → `Money.round()` half-even fix → `Money.discounted()` → `Money.allocate()` → `setup.cfg` metadata update — has no published target releases attached to any step. The team needs to assign versions (or at least sequence milestones) so downstream services can plan. [cite: source:transcript-run-a080ea35@r1] [cite: source:how-we-release@r1]

---

## Documents vs code

**1. Allocation: product note says absent; code says present**
The product note states "Allocation (splitting Money by ratios so the parts add up exactly) is not in the library yet; checkout does it by hand today." [cite: source:product-note@r1] The interview with alice also described `Money.allocate(ratios)` as a planned future feature. [cite: source:transcript-run-a080ea35@r1] However, `Money.allocate` is fully implemented in the current codebase, matching the glossary specification (floor to minor unit, leftovers to first parts in order). [cite: src/moneyed/classes.py] The product note is out of date; the code is the authoritative state.

**2. `test_all_babel_currencies` gate status: alice vs carol**
Alice's interview (the earlier run) stated "The gate deselects it." [cite: source:transcript-run-a080ea35@r1] Carol's interview (the later run) confirmed "nothing is deselected; the test stays in the gate and is accepted as a known failure." [cite: source:transcript-run-66c5f847@r1] The `CLAUDE.md` instructions also prohibit deselecting tests. Carol's answer is the current truth; alice's answer predates the reconnect and should be disregarded.

**3. `setup.cfg` Python version vs SHOP's stated floor**
`setup.cfg` declares `python_requires = >=3.8` and lists classifiers only up to CPython/PyPy 3.11. [cite: setup.cfg] SHOP's actual floor is Python 3.12 and services run 3.13. [cite: source:transcript-run-a080ea35@r1] The file is acknowledged stale upstream metadata; it has not yet been updated. Any tooling that reads `python_requires` from `setup.cfg` will see incorrect information until a deliberate update lands.
