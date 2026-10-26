# 3-build AI-recon-rules (F-016, sprint-05)

Result: DONE. Branch task/sprint-05/AI-recon-rules from origin/sprint-05 (695ca05, after AI-adjust-series).

## Files
- `services/analytics/finvest_analytics/adjust/recon.py` (new, ~95 lines): `Mismatch`, `ReconResult`, `reconcile`, `summary`, `round_to_tick`, `ref_check`.
- `services/analytics/tests/test_recon.py` (new, 6 tests, hand-computed).

## What changed
- `reconcile(nominal_bars, factors, src_bars, *, threshold=Decimal("0.1"))`: `G = cumulative(factors, d, last)` with `last` = newest source bar (later ex-dates never applied, R6/R7). `ours = nominal x G` (2 dp), `theirs = A(d)`; `diff_pct` 4 places half-up. `ours`/`theirs` in `Mismatch` are integer VND (BIGINT column).
- Rule per row: `observed` and G == 1 -> any diff is a mismatch, note `unit_or_adapter`; `observed` and G != 1 -> `diff_pct > threshold`, note `factor_or_event`; `reconstructed` (pre-crawl) -> self-consistency `|ours - A| <= 1 VND`, note `self_consistency` (the 0.1 % threshold would hide a hand-broken A).
- `summary`: "30/30, k mismatches[; missing X, Y][; first mismatch SYM date]". A symbol with no result or `checked == 0` counts as missing, never as a pass.
- `ref_check(f, pre_close, board_ref, tick)`: `|round_to_tick(f*P) - ref| <= tick`.

## Contract / deviations
- `Mismatch` has one extra defaulted field `note: str = ""` (not stored; `recon_mismatches` has no column). Needed so the CLI can print the "unit_or_adapter" tag the plan asks for. Positional 5-field construction still works.
- `round_to_tick` is local to recon.py (no tick helper exists in `finvest_rules`; tick is passed in, per the plan signature). It rounds to the nearest tick half-up; VN§3 does not state the exchange's direction, and the 1-tick slack in R8 covers either. SA's CLI must supply `tick` from VN§3 itself.
- `exact_days` = days with `ours == theirs` exactly (2 dp).

## Checks
- `make test-kernel`: 322 passed, 36 deselected; ruff clean; mypy 5 source files clean; lint-imports pass (the make chain exited 0).
- Tests: G10 (0.2045 % row, 0.0408 % none, G=1 equal -> 0); G=1 1-VND diff flagged (0.0011); future ex-date not applied; G8 self-consistency passes (0.15 VND) and hand-broken A (1.85 VND, 0.005 %) fails; summary 29/30 naming the missing symbol and 30/30 with first mismatch; ref_check boundaries.

## Outside-set edits
None. Size 177 lines total vs ~130 planned (under the 1.5x stop at 195).

## Notes for the tester
- Try a G=1 pair that differs by 1 VND: must show `unit_or_adapter`. For R8 check VN30 ex-dates 27-29/10 against the board by eye.
- Not done here: the CLI glue, DB writes, S2 cross-check (SA/BE tasks).

## Fix round 1
- Must-fix 1 (diff_pct overflow): `recon.py` caps `pct` at `Decimal("9999.9999")` (`_PCT_MAX`); new test `test_thousand_vnd_adapter_diff_pct_is_capped_to_fit_numeric_8_4` (93500 vs 93.5 -> `unit_or_adapter`, 9999.9999).
- Merged origin/sprint-05 (clean). `make test-kernel`: exit 0, 331 passed, ruff and mypy clean.
