# Build: AI-whatif-benchmarks (F-048)

**Result:** done. Branch `task/sprint-03/AI-whatif-benchmarks`, +286/-5 vs plan Size ~340 (stop 510).

## Files
- `sim/benchmark.py` (new): `vnindex(contributions, sell, scenario_pl_pct, ctx, view)`, `etf(req, sell, dates, scenario_pl_pct, ctx, view, run)`.
- `sim/whatif.py`: `run_whatif(..., *, with_benchmarks=True)`; fills `result.benchmarks = [VN-Index, E1VFVN30]`.
- `tests/test_benchmarks.py` (8 tests), goldens `008-vnindex-lump`, `009-vnindex-dca`, `010-etf-engine-and-na`.
- `tests/test_golden.py`: runner accepts `view.index {code: {date: close}}` and `view.extra [view specs]` (second symbol).

## What changed
- VN-Index: `round_half_up(sum(amount_i * idx(sell)/idx(date_i)))`, Decimal end to end, each index read with `as_of = that date`
  (no look-ahead); `pl_pct = pct(value - invested, invested)`; `diff_pp = scenario - benchmark` (4 dp); `investable: false`.
- ETF: `run_whatif` again on `E1VFVN30` with `sell_date = scenario's resolved M`, `with_benchmarks=False` (no recursion).
  Result is n/a (`available false`, `first_available` = ETF's first bar, no `value_vnd`) on any AnalyticsError, or when
  the ETF run's sell date or contribution dates differ from the scenario's (a bar gap on a contribution day does not
  silently shift). ETF flags are not merged into the scenario (so `approximate` stays once).
- Figures (`value_vnd`, `pl_pct`, `diff_pp`) carry `how` with `cite: "PR-034"` and `inputs.investable`; `diff_pp` uses unit `pct`.

## Contract honored
contracts/analytics.md §2.4 `benchmarks`; analytics.md §1.4; sponsor A20-A. Output shape per contract.

## Checks
- `q.sh kernel make test-kernel`: exit 0, 187 passed (20 db deselected), ruff clean, mypy ok (5 files), import-linter ok.
- Analytics alone: 39 passed. Golden hand-checked: 008 (10,500,000 / 5.0000 / 1.1098), 009 (3,960,000 / -1.0000 / -1.8338),
  010 (qty 400, fee 12,000, cash 1,988,000, liq 10,367,000, 3.6700, 2.4398).

## Deviations / notes for tester
- No index bars at all or no ETF symbol: `first_available: null` (key present).
- `shortcut`: VN-Index first_available reads the full index history up to the snapshot (validation only, no number).
- Unit of `diff_pp` is `pct` (contract unit list has no `pp`). FE should label it "điểm %".
- Existing goldens 001-007 now carry two n/a benchmarks (no index/ETF in their views); their numbers are unchanged.

## Outside-set edits
`tests/test_golden.py` (runner support for index/extra series; test infrastructure, not in the file set).
