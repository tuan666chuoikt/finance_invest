# 3-build BE-rules-costs (F-006)

Result: DONE. Branch task/sprint-03/BE-rules-costs.

## Files
- packages/market_rules/finvest_rules/costs.py (new, ~65 lines): Rule, Costs, RuleNotEffective, RULES (5 v1 entries), RULES_VERSION="2026.10.16", rule(), costs().
- packages/market_rules/finvest_rules/__init__.py: exports.
- packages/market_rules/tests/test_costs.py (new, 4 tests).

## Contract honored
Plan block as written. effective_from=2006-01-01 for all five (docstring says it is the apply-from date). Cites VN§4 / VN§5; buy/sell fee verified=False (sponsor A6), tax/lot/settlement verified 2026-10-15.

## Checks
- kernel (pytest -m "not db", ruff check ., ruff format --check, mypy, lint-imports): exit 0; 133 passed, 18 deselected.
- Acceptance: costs(2026-10-12) = 0.0015/0.0015/0.001/100/2; appended 2027-01-01 entry takes over exactly on its date (test-local copy); board_lot 2005-01-01 raises RuleNotEffective; RULES hash test (sha256 of repr(sorted(RULES.items())), stored RULES_HASH=2019ac0ca54a268d) fails with a "bump RULES_VERSION" message.

## Deviations
- rule() takes an optional third arg `rules` (default RULES) so the test can pass a local copy without mutating the global; plan signature rule(name, on) still works.
- Hash covers repr of the dataclasses (including source/cite text), so editing a source string also asks for a bump; accepted as stricter, not looser.

## Outside-set edits
None. No money-calculating code here (rates only), so no hand-computed fee test.

## Notes for tester
RULES_VERSION must be bumped with RULES_HASH in the test on any rule change.

## Fix round 1
- Must-fix 1: `costs()` now uses typed `_rate`/`_count` helpers (isinstance narrowing, TypeError on wrong type) and takes optional `rules` (passed through). Nit applied: `RULES if rules is None else rules`.
- Test added: `test_wrong_type_entry_raises` (int fee, Decimal lot -> TypeError). RULES unchanged, so RULES_VERSION/RULES_HASH unchanged.
- Checks: `mypy --strict packages/market_rules/finvest_rules` exit 0 (3 files); ruff check + format clean; `make test-kernel` exit 0, 134 passed, import-linter kept.
- origin/sprint-03 had no new commits; no merge needed.
