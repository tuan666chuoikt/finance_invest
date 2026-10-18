# 3-build AI-whatif-lumpsum
Result: done. `run_whatif(req, view, rules=finvest_rules.costs)` returns the contracts §1.4 envelope with the §2.4 lump-sum
`result` (all bullets except `benchmarks`, which is `[]`).

Files (services/analytics): `finvest_analytics/sim/{__init__,dates,whatif,figures}.py`,
`tests/{test_golden,test_whatif_lumpsum}.py`, `tests/golden/sim/001..004*.json`.

Behaviour
- Validation: style != lump_sum, fill_rule != close, sell < buy, sell < buy after shifting -> VALIDATION; no bars ->
  SYMBOL_UNKNOWN; buy < first bar -> NO_DATA(first_available); buy > last bar -> VALIDATION(last_available);
  no bar on the shifted buy day -> NO_DATA(missing_bar).
- Buy reads `bars_1d(.., as_of=N)` only; valuation reads `as_of=M`. The only read past N before the buy is the
  validation-only "last bar" lookup, which feeds no number.
- Sell: shift back over the calendar (reason `non_trading`), then latest bar <= that day (reason `no_bar`, extra).
  `sell_date=None` -> last bar <= snapshot date.
- CAGR: `Decimal ** Decimal(365/days)`, exact for 365 and 730 days; null + `returns.cagr_note{text,how}` for 0 days.
- Equity curve over the trading calendar [N, M] (contract wording), last close carried over gaps.
- `data_snapshot` = max fetched_at of the bars N..M, rendered +07:00 (naive timestamps taken as VN time).

Contract honored: contracts/analytics.md §1.1, §1.4, §2.1 errors, §2.4.
Checks: `make test-kernel` exit 0 (155 passed incl. 12 new, ruff clean, mypy ok, import-linter kept). Golden 001..004
match the hand numbers (610,975 / 6.1098 / 3.0096).

Deviations / decisions (please confirm in review)
1. `contributions[]` rows keep the contract's plain ints; the plan says `fee_vnd` is a "figure" with cite. Both are met by a
   row-level `how` (same idea as the ledger row, §1.2) with `cite: VN§5`. Additive field.
2. Extra `result.details.min_amount` (a Figure) holds the below-one-lot minimum; contract only says "details.min_amount".
3. Shift reason `no_bar` added next to `non_trading` (sell day has no bar).
4. `rules_unverified:<rule_id>` flags (contracts §1.3) are not emitted: `rules=costs` returns only values. Needs a small
   follow-up if the sponsor wants unverified fee rates shown.
5. Size: ~340 production lines + 260 test/golden lines vs plan ~250 (ruff format expanded figures.py). No work left.
6. Pydantic `Literal` already rejects fill_rule != close at request construction; the in-function check is a guard.

Outside-set edits: `services/analytics/pyproject.toml` (dependency + workspace source `finvest-rules`), `uv.lock` regenerated.

For the tester: `uv run pytest services/analytics -q`; add golden cases by dropping a JSON in tests/golden/sim
(keys documented in test_golden.py: view, request, expected, approx, flags_contain, error).

## Fix round 1 (lead 3-pr round 1)
1. Size stop: wrote `3-consult.AI-whatif-lumpsum.md` (recommend accept as is; no code split). No answer file existed yet.
2. Buy day without a bar: `whatif.py` now moves N forward to the first stored bar >= the shifted day (shift row
   `buy_date`, reason `no_bar`, flag `fill_shifted`), replacing the `NO_DATA {missing_bar}` error; if no bar exists
   at all after it, `NO_DATA {last_available}`. Still reads the buy with `as_of = N` (new N). The date comes from the
   validation history read already made (no extra read, never feeds a number).
   Test: `test_buy_day_without_bar_moves_forward` (drop 2026-10-12, buy 2026-10-12 -> buy 2026-10-13, reason no_bar,
   fill_shifted, qty 100); failed on H with NO_DATA.
Checks: `make test-kernel` exit 0, 162 passed (was 161), ruff + mypy clean; `pytest services/analytics` 17 passed.
Merge of origin/sprint-03: already up to date.

## Fix round 2
No code change needed. 3-pr round 2 lists no code must-fix; the only open item (size consult) is answered A (accept as is)
in `3-consult.AI-whatif-lumpsum.answer.ai.md`. Merge of origin/sprint-03: already up to date. Head stays
`36f9dbafa5b2ed7c0eaf4a8f4d0fa6ba358b1214` (pushed). No checks rerun (no files touched; round-2 lead run: kernel 165 passed, analytics 17 passed).
