# PR review: FIX-whatif-empty-history (LIVE-03 L1)

## Round 1 (fi-tech-lead, BE, opus) 2026-10-18

Verdict: APPROVE

Reviewed head H = 9717f5e89f4ecf3bd2cf1cbfb750a34a79cda01b (dev commit 147dec0 + sync merge of origin/sprint-03 a2d6a1c;
the sync was clean, it touched only apps/api/tests/conftest.py and test_symbols.py from FIX-symbols-exact-first).

### Files reviewed
- services/analytics/finvest_analytics/sim/whatif.py: validation read is now `bars_1d(sym, first, date.max, as_of=date.max)`,
  plus a `NO_DATA {first_available}` guard before `bar_days[-1]`. Matches the plan exactly (lines 36-43 only, plus the `date` import).
  No other control-flow change. Look-ahead: `bar_days` only picks dates (fill days, last bar); every price read is still
  `bars_1d(sym, t, t, as_of=t)`, so no price after the decision time is used.
- services/analytics/tests/test_whatif_lumpsum.py: `test_history_hidden_by_as_of_is_no_data` (the plan allowed the existing
  error module of AI-whatif-lumpsum).
- apps/api/tests/test_whatif_api.py: real `SqlMarketView` on in-memory SQLite (StaticPool), `test_sql_view_first_request_ok`,
  `test_sql_view_no_calendar_is_400`.

### Plan / size / contract
- File set: as planned. Size: 3 files, +60/-3 (plan ~70). No consult needed.
- Contract: `NO_DATA` -> 422 and `VALIDATION no_trading_day_near_buy` -> 400 per platform.md §2.5; `SqlMarketView` unchanged.
- Dev deviations (test-only, both accepted):
  1. `data_snapshot` literal is `2026-10-17T10:00:00+07:00` (no `.000`), which matches the contracts/analytics.md §1.4
     example format; the plan literal had a wrong format. The seed is naive local 10:00 because SQLite drops tzinfo.
  2. `buy_date=2024-01-02` with only Oct-2026 bars hits `buy < first` (422 NO_DATA) before the calendar. The test adds one
     2024 FPT bar so the calendar path is reached -> 400 `no_trading_day_near_buy`. That is the transitional state the plan
     wanted to document.

### Must-fix
None.

### Nits / follow-ups for 5-review.tech (no rework in this task)
- F1 (contract wording, architect): the validation read over the full history now counts as "served", so on `SqlMarketView`
  `data_snapshot` = max `fetched_at` of the symbol's whole history, not strictly "of the bars used" (§1.4). With a historical
  `sell_date` and a later refetch, the stamp moves although `result` does not. Reproducibility (same params + snapshot ⇒ same
  result) still holds. The plan chose this on purpose (no `SqlMarketView` change). Either amend §1.4 to "rows read" or
  later have the validation read skip `_served`.
- F2: the API test seeds naive local time, so UTC -> +07:00 conversion of an aware `fetched_at` is not covered on this path
  (Postgres returns aware values). A `-m db` test could cover it later.
- Already listed by the plan: holidays.csv back to 2006; the validation read loads the full history (perf only, N2 met).
- Dev note: one bare `git stash` (popped at once, no loss). That breaks common.md; reminder only.

### Checks on H
- `make test-kernel` (q.sh, flock fi-test): exit 0; 210 passed, 22 deselected; ruff, mypy, lint-imports clean.
- `make lint`: exit 0.
- Affected modules (test_whatif_api, test_whatif_lumpsum, test_benchmarks, test_golden): 37 passed. Golden 001-009 unchanged.
- Fails without the change: with whatif.py reverted to origin/sprint-03, all 3 new tests fail with `IndexError`.
- `-m db` not needed: no migration, repository or SQL change.
- Money recompute by hand on the real-view 200 response (FPT 93,500, 10,000,000 VND, fee 0.15%, tax 0.1%, lot 100):
  qty = floor(10e6 / (93,500·100·1.0015))·100 = 100; buy fee 14,025; cash 635,975; MV 9,350,000; sell fee 14,025; tax 9,350;
  liquidation 9,962,600; P/L -37,400 (-0.374%). This matches the API exactly.

### Merge
Merge sha: 4c5037e6f87053c43719e6c89ef8d5ca4b6ea9dd (base a2d6a1c, pushed to origin/sprint-03)
