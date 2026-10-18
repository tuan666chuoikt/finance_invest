# Build: FIX-whatif-empty-history (LIVE-03 L1)

Result: DONE. Branch task/sprint-03/FIX-whatif-empty-history.

## Files
- services/analytics/finvest_analytics/sim/whatif.py: validation history read now `bars_1d(sym, first, date.max, as_of=date.max)` (no `view.snapshot()`); `NO_DATA {first_available}` guard before `bar_days[-1]`; `date` import.
- services/analytics/tests/test_whatif_lumpsum.py: `test_history_hidden_by_as_of_is_no_data` (the existing error module of AI-whatif-lumpsum).
- apps/api/tests/test_whatif_api.py: real `SqlMarketView` on SQLite (StaticPool): `test_sql_view_first_request_ok`, `test_sql_view_no_calendar_is_400`.

## Checks
- make test-kernel: 210 passed, 22 deselected; ruff, mypy, import-linter clean. Golden 001-009 unchanged.
- The 3 new tests fail on the old whatif.py (IndexError / 500) and pass with the fix.
- Size: 60 insertions, 3 deletions (plan ~70).

## Deviations (test-only, plan literals not reachable)
1. `data_snapshot` literal: plan says `2026-10-17T10:00:00.000+07:00` from `fetched_at = 03:00Z`. On SQLite the tzinfo is dropped (naive 03:00 -> `03:00+07:00` via iso_vn) and `isoformat()` has no `.000`. Test seeds naive local 10:00 and asserts `2026-10-17T10:00:00+07:00`. On Postgres (aware) the value would be 10:00+07:00 too.
2. `buy_date=2024-01-02` with only Oct-2026 FPT bars returns 422 NO_DATA (buy < first bar) before the calendar check, not 400. Test adds one FPT bar on 2024-01-02 so the calendar path is reached -> 400 `no_trading_day_near_buy`.

## Outside-set edits
None. Follow-up for 5-review.tech (per plan): backfill holidays.csv to 2006; validation read loads full history (perf only).

## Notes for tester
Accidentally ran a bare `git stash` once (popped immediately, no loss).
