# 3-build AI-whatif-dca (F-057 monthly DCA + D4 rules_unverified flags)

Result: DONE. Branch task/sprint-03/AI-whatif-dca, based on origin/sprint-03 78e636c. No unmerged task branch touched the same lines.

## Files (all under services/analytics)
- `finvest_analytics/sim/dca.py` (new): `schedule(start, end, calendar, shifts=None) -> [(requested, actual)]`; day = `start.day`
  clamped to the month length, shifted forward to a trading day, dropped when `> end` (shift row `reason: after_end`).
  `shifts` is an optional extra argument so F-081 can call it without the list.
- `sim/whatif.py`: dispatch on `style` (the "style_not_supported" error is gone). One contribution loop serves both styles
  (lump sum = one fill); decision time per contribution `as_of = t_i`; cash carried; `invested = sum(amount)`;
  `cagr_pct = None` for DCA; valuation, curve, `missing_sessions` shared. `equity_curve.invested` = cumulative contributions.
- `sim/figures.py`: `lump_sum_result` renamed `whatif_result`, takes the contribution rows; DCA `how` formulas for
  shares / cash / invested; `cagr_note` text "not defined for multiple contributions (S03: no IRR)". Lump-sum output unchanged.
- D4: `flags += rules_unverified:<rule>` for each rule with `verified == false` that fed a number (buy_fee_rate per
  contribution date, sell_fee_rate, sell_tax_rate, board_lot); the fee rules are skipped when `fee_rate` overrides them.
  Today that is `rules_unverified:buy_fee_rate` and `rules_unverified:sell_fee_rate` on every result (both styles).
- Tests: `tests/test_whatif_dca.py` (6), golden `005-dca-fpt`, `005b-dca-fpt-5-contributions` (the backlog 6.1098 variant, kept as
  its own file because the runner takes one request per file), `006-dca-day-31`, `007-dca-carried-cash`.

## Contract honored
contracts/analytics.md §2.4: `contributions` (one row per fill day, `cash_after` carried), `returns.pl_pct` = P/L / total
contributed, `cagr_pct null`, `equity_curve.invested` step line, `dates.buy` = first actual contribution, `holding_days` from it.
Every golden number is hand-computed in the file's `hand` array (005: 12,610,975 / 5.0915; 005b: 10,610,975 / 6.1098;
007: 3,886,650 / -2.8338; 006: 4 contributions, 20,000,000).

## Checks
- `q.sh kernel make test-kernel`: 175 passed, 20 deselected (db); ruff All checks passed; mypy Success (5 files); import-linter ok.
- analytics alone: 27 passed (17 before). No full-run path touched.
- Look-ahead: for each contribution i, bars after t_i multiplied by 2 -> `contributions[:i+1]` identical (test_no_look_ahead_per_contribution).

## Deviations / decisions
- Shift fields in DCA: every contribution shift, the first included, is `field: "contribution"` (plan text); lump sum keeps
  `buy_date`. The sell shift row comes first in `dates.shifts`, then the contribution rows. FE `Shift` type is generic on `field`.
- A contribution day with no stored bar moves to the next bar (`reason: no_bar`), like lump sum; beyond the end it is dropped (`after_end`).
- `below_one_lot` follows the contract literally: set when any contribution has qty 0 (so a normal DCA that accumulates
  cash for months carries it); `details.min_amount` is computed at the first qty-0 contribution's close.
  If the dashboard must not warn once shares were bought, FE or SA should decide; engine change is a one-line condition.
- `rules_unverified` reads the shipped `finvest_rules.RULES`, not an injected `rules` callable (code comment `shortcut:`).
- Size: +382/-71 (diff) vs plan ~215 (1.5x = 322). Code is ~170 lines; the rest is tests and golden data (212),
  which the plan again undercounted. Nothing is left to split, so no consult.

## Outside-set edits
- `tests/test_golden.py`: `build_view` accepts `closes {date: close}` overrides (needed for 007's varying price), 8 lines.
- `tests/test_whatif_lumpsum.py`: dropped the assertion that `style: dca` is a VALIDATION error (now supported), 1 line.
- Extra golden file `005b-...json` (not in the plan's file list).

## Notes for the tester
- Try a DCA where the monthly amount is below one lot for the whole range: shares 0, `below_one_lot`, liquidation = cash, pl 0 minus nothing.
- Day-of-month 29/30/31 across February (leap 2028) is covered only by `schedule` unit tests, not by golden files.
- Benchmarks stay `[]` (F-048 is another task).

## Fix round 1 (3-pr round 1)
- Must-fix 1 (size stop): wrote `3-consult.AI-whatif-dca.md` (+410/-73 vs 1.5x = 322, recommendation: accept). Waiting for the answer.
- Must-fix 2 (fee rate in `how`): each contribution row now carries the `buy_fee_rate` its fee used (`whatif.py`), and the
  `min_amount` tuple carries the rate of its own contribution; `figures.py` prints those. `contributions[i].how.inputs.buy_fee_rate`
  is per row; `position.shares.how.inputs` is now `buy_fee_rate_i` (comma list, like `qty_i`) for DCA, `buy_fee_rate` for lump sum.
  The shared `buy_rate` parameter of `whatif_result` is gone. Test: `test_how_reports_each_contributions_own_fee_rate`
  (injected `rules` with 0.0010 in January, 0.0020 after; each row's `how` rate reproduces its `fee_vnd`).
- Checks: `q.sh kernel make test-kernel` exit 0 — 176 passed, 20 deselected; ruff clean; mypy no issues (5 files); import-linter ok.
- Nits not taken (optional): after_end double row, rules_unverified reading shipped RULES. `details.min_amount` still uses `lot` of `rules(n)`.
