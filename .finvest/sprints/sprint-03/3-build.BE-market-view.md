# 3-build BE-market-view (sprint-03)

Result: DONE except one acceptance item deferred (see Deviations). Branch task/sprint-03/BE-market-view.

## Files
- apps/api/finvest_api/market_view.py (new, 67 lines): `SqlMarketView(engine)` implements `finvest_analytics.domain.ports.MarketView`.
- apps/api/tests/test_market_view.py (SQLite, 6 tests), apps/api/tests/test_market_view_db.py (Postgres, 1 test, `db`).
- apps/api/pyproject.toml (+ finvest-rules, finvest-analytics deps), uv.lock (workspace entries only).

## What changed
- `bars_1d`: `DISTINCT ON (trading_date) ORDER BY trading_date, fetched_at DESC`, `trading_date BETWEEN start AND min(end, as_of)`,
  `adj_* -> o/h/l/c`, `price_basis="source_adjusted"`.
- `index_1d`: `c` is `Decimal` quantized to 0.01. `first_bar_date`: `min(trading_date)` or None. `price_basis()` constant.
- `snapshot()`: max `fetched_at` over bar rows served by this instance; before any bar read returns `datetime.min` UTC.
- `calendar`: per year, `finvest_rules.trading_days`; on `CalendarNotMaintained` falls back to VNINDEX `index_1d` dates
  (`shortcut:` comment). Result is sorted and de-duplicated. No private rules internals used.

## Contract honored
analytics.md §1.1 port signatures (checked against ports.py), §1.4 data_snapshot, data.md §3 tables. `market_data` untouched,
so codebase.md §2 layering holds (`lint-imports` green).

## Checks
- kernel: `139 passed, 19 deselected` (`pytest -m "not db"`, whole repo); ruff, mypy (5 files), lint-imports: all green.
- db: `1 passed` against the compose db `finvest_test` (FPT 10-14 stored twice: c==93_500, as_of 10-14 hides 10-15, snapshot==10-16 fetched_at).
- SQLite: calendar (weekend skip; 2016 VNINDEX-only; 2024-12-30..2025-01-03 mixed, holiday dropped), index_1d Decimal "1260.00",
  first_bar_date, snapshot; bars_1d on SQLite works because `.distinct(col)` degrades to plain DISTINCT there (days are unique in the test).

## Deviations
- Acceptance "end to end `run_whatif(req, SqlMarketView(engine))` on golden 001": NOT done. `run_whatif` and the golden 001 JSON
  (AI-whatif-lumpsum) are not on origin/sprint-03 yet. The view matches the port, so the N2 route task (`POST /api/whatif`) tests it
  end to end (its acceptance already has the 10,610,975 check). Needs a follow-up check in that task or the tester.

## Outside-set edits
- apps/api/pyproject.toml and uv.lock (new workspace deps for the api package).

## Notes for the tester
- db test drops and recreates only `bars_1d_src` in a `*_test` db. Run: `FINVEST_DATABASE_URL=...finvest_test uv run pytest -m db apps/api/tests/test_market_view_db.py`.
- Compose db has no host port; the container IP was used.
- Holidays.csv covers 2025-2026 only, so any range in other years uses VNINDEX dates; a day with a VNINDEX row but no stock bar is still a session.
