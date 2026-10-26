# 3-pr AI-ca-factors (F-015) — round 1 — APPROVE

Reviewer: fi-tech-lead (BE, opus), 2026-10-26. Reviewed head H = 8ca3d7f (5bbd3a5 + clean sync merge of origin/sprint-05 4132ed5, no conflicts).

## Files reviewed (git diff origin/sprint-05...H)
- packages/market_rules/finvest_rules/corporate_actions.py (new, 95)
- packages/market_rules/finvest_rules/__init__.py (exports)
- packages/market_rules/finvest_rules/costs.py (RULES_VERSION 2026.10.16 -> 2026.10.28, `ca_adjustment` Rule verified=False, cite "VN§6 v1.1")
- packages/market_rules/tests/test_corporate_actions.py (new, 120)
- packages/market_rules/tests/test_costs.py (hash now covers RULES + corporate_actions source)
Size: 5 files, +238/-5 vs plan ~170 (1.5x = 255): within limit, no consult needed. File set exactly as planned.

## Contract / correctness
- R2/R3 (VN§6 S7) combined formula `(P - c + S·r_r)/(1 + r_s + r_r)/P`, rights dropped when S >= P (VN§3/§6), split/merge a/b, listing_change 1; 12 dp ROUND_HALF_UP Decimal, P int VND (ADR-S-005). Validation `0 < c < P` on summed cash, ratios >= 1, NULL cash/issue_price -> InvalidCorporateAction(reason).
- R6 inversion `P = A/G·(1 + r_s + r_r) - S·r_r + c`, then rights with S >= P dropped and recomputed. Checked by hand: if the forward rule dropped rights (P <= S), the first pass gives P + r_r(A - S) < S, so the term is always dropped and the second pass is exact; if live (S < P), the first pass is exact and kept. One-pass shortcut for >1 rights per ex-date is commented in the required form.
- Hand recompute (python Decimal): G4 51,000/1.2/50,000 = 0.85; G3 520,000/12/50,000 = 0.866666666667; G5 92,500/1.3/93,500 = 0.761003702180(17) -> test value correct.
- Pure module, no I/O, no look-ahead surface (as_of handling belongs to the next task).

## Tests
- G1, G2, G3, G3b, G4 (incl. != product), G5, G7, G7b asserted exactly; cash 50,000 at P 50,000 -> `cash_not_below_pre_close`; Hypothesis round trip (cash/bonus/rights S up to 2P/split) == P.
- Mutation `den = 1 + r_s` -> `2 + r_s`: hash test + 7 tests fail (would fail without the change). Hash test forces an edit on any formula change.

## Checks on H
- `make test-kernel`: 280 passed, 28 deselected; ruff clean; mypy "no issues in 5 source files"; lint-imports 5 kept, 0 broken (exit 0, 11 s).
- `pytest packages/market_rules`: 28 passed; `mypy --strict corporate_actions.py`: clean.
- No migrations/SQL touched -> `-m db` not required.

## Must-fix
none.

## Nits (no action required this sprint)
1. `[tool.mypy] files` covers only market_data/domain, so the kernel mypy does not check finvest_rules (pre-existing; the build note's "mypy clean (5 files)" is that scope). SA may add `packages/market_rules/finvest_rules` to the list.
2. The hash test detects a rule/formula change but cannot tell a version bump from a hash-only update (pre-existing design); fine as a reminder.

## Merge
Merged into sprint-05: 33e63c16a3d3e22705f23953a44dfcd3500ec9de (base 4132ed5, head 8ca3d7f), pushed under the merge lock. Worktree removed.
