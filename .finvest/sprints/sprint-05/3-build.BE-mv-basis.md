# 3-build BE-mv-basis (F-015)

Result: DONE. Branch task/sprint-05/BE-mv-basis.

## Files
- apps/api/finvest_api/market_view.py: `SqlMarketView.bars_1d`
- apps/api/tests/test_market_view_db.py

## What changed
- `bars_1d` checks (symbol-level, no date bound) for a `reconstructed` row in `bars_1d`.
  - Present: serves every `bars_1d` row in range (observed + reconstructed) x Pi factors over (d, today] (the existing observed branch, now for all rows). No `bars_1d_src` read.
  - Absent: today's behaviour (DISTINCT-ON newest-version src rows + `bars_1d` days not in src), marked with a `shortcut:` comment (drop when V5 coverage is full, S06).
- `_served` / G11 untouched (max fetched_at of served rows + CA rows applied).

## Contract honored
data.md §1.4 (4); platform.md §2.5/§2.6; 2-tech-plan.ai.md R5, R7 `ours`.

## Checks
- db (market view file, per-branch db finvest_mvbasis_test): 5 passed (new test: F0 full 50,000 + short F1 after E + reconstructed rows -> 49,000 on all 5 pre-E days, no 51,020x0.98 step; snapshot = CA fetched_at (G11); VNM without reconstructed row -> newest src 68,000).
- kernel `pytest -m "not db"`: 335 passed; ruff, mypy: clean.
- Size: +57/-18 vs ~80 planned.

## Deviations / outside-set
- None outside the file set. The two older db tests in the file now create/drop all of `T` + `bars_1d_src` (the new reconstructed-row probe reads `bars_1d`, so the old test 1 needed the table; test 2 needed `adj_factors` on a fresh db).

## Notes for the tester
- The db tests of this file leave tables behind, so `test_migration_round_trip` (test_scenarios.py) fails if run after them on the same db (pre-existing order coupling, fresh db passes: 2 passed).
- A symbol with a single reconstructed row anywhere switches wholly to the `bars_1d` basis; days not yet in `bars_1d` are not filled from src.
