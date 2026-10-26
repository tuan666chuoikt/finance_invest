# 3-build AI-ca-factors (F-015) — DONE

Branch `task/sprint-05/AI-ca-factors`. Diff vs origin/sprint-05: 5 files, +238/-5 (plan size ~170, 1.5x limit 255).

## Files
- `packages/market_rules/finvest_rules/corporate_actions.py` (new): `CaEvent`, `InvalidCorporateAction(reason)`, `factor(events, pre_close)`, `pre_close_from_adjusted(adj_pre_close, events)`.
- `__init__.py` exports; `costs.py`: `RULES_VERSION = "2026.10.28"`, new `ca_adjustment` rule (value 1, cite `VN§6 v1.1`, verified=False, source S7).
- Tests: `tests/test_corporate_actions.py` (new), `tests/test_costs.py` (hash constant).

## Contract honored
VN§3, VN§6 (combined formula, S ≥ P drop, inversion), ADR-S-005 (Decimal factors, 12 dp half-up, int VND). G1, G2, G3, G3b, G4, G5, G7, G7b asserted exactly; cash 50,000 at P 50,000 raises `InvalidCorporateAction("cash_not_below_pre_close")`; Hypothesis round trip `pre_close_from_adjusted(P*factor) == P` over random cash/bonus/rights/split combos (P 1,000-500,000, S up to 2P, so both rights branches).

## Reasons (for the anomaly `value`)
`cash_not_below_pre_close`, `cash_missing_or_not_positive`, `ratio_missing_or_below_1`, `issue_price_missing_or_not_positive`, `unknown_type:<t>`, `pre_close_not_positive`. Cash of several events on one ex-date is summed before the `< P` check.

## Checks
- pytest market_rules: 28 passed; analytics: 42 passed; ruff clean; mypy clean (5 files); lint-imports kept.
- Hash test: now hashes `repr(RULES)` + source of `corporate_actions.py`. Mutation check (`den = 1 + r_s` -> `2 + r_s`) fails it with "bump RULES_VERSION". Any edit to that module (comments too) needs a bump + new `RULES_HASH`.

## Deviations / notes
- `ca_adjustment` is `Rule(value=1, cite="VN§6 v1.1")`: `Rule.value` is typed Decimal|int, so the version string lives in `cite`.
- `pre_close_from_adjusted` takes `A(D-1)/G(D)` (caller divides by G); the S ≥ P recompute is a single pass, exact for at most one rights event per ex-date (shortcut comment in code).
- split|merge a:b multiplies by a/b and is inverted by dividing first; ex-dates with listing_change only give 1.
- Not done (out of scope): DB, V5 parsing, tick snapping, rounding of P to 1 VND stays in the caller for `factor` use (adjusted close 2 dp).
## Outside-set edits
none.
## Notes for the tester
Check G1-G5/G7b with a calculator; G4 must not equal 0.98 x 0.866667.
