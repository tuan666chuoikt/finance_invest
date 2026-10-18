# 3-pr BE-market-view (sprint-03)

## Round 1 — fi-tech-lead (BE, opus) — 2026-10-18

Verdict: **APPROVE**
Reviewed head H: `8a3e41c0912967e64293f9d0d1f9da6d069903b6` (task head 3180439 + clean sync merge of origin/sprint-03 at 36f6c0e, no conflicts).

### Files reviewed
- apps/api/finvest_api/market_view.py (67) — matches `finvest_analytics.domain.ports.MarketView` exactly (6 methods, kw-only `as_of`).
- apps/api/tests/test_market_view.py (73, SQLite), apps/api/tests/test_market_view_db.py (37, `db`).
- apps/api/pyproject.toml + uv.lock: adds workspace deps finvest-rules, finvest-analytics (needed by the plan's file location; workspace-only, no new third-party dep).
- Size: 182 insertions vs plan 170 (1.07x) — within 1.5x.

### Checklist
- Contract: `DailyBar` o/h/l/c/v int VND from BigInteger `adj_*` (no thousand-VND scaling), `price_basis="source_adjusted"` (analytics.md §1.3.1); `IndexBar.c` Decimal quantized 0.01 from Numeric(12,2); `snapshot()` = max `fetched_at` of rows served (contracts/analytics.md §1.4).
- No look-ahead: `bars_1d` and `index_1d` bounded by `trading_date <= min(end, as_of)`; tests prove the later day is hidden and does not enter `snapshot()`.
- Dedupe: `DISTINCT ON (trading_date) ORDER BY trading_date, fetched_at DESC` — verified on Postgres (db test fails without it: two 10-14 rows would be returned).
- Calendar: per-year `finvest_rules.trading_days`, fallback to VNINDEX `index_1d` dates on `CalendarNotMaintained`, `shortcut:` comment present as the plan asks. Hand check: 2026-10-16 is a Friday → [16, 19, 20]; 2024-12-29 Sunday; 2025-01-01 holiday — tests match.
- Layering: `market_data` untouched; `apps/api` imports analytics/rules/market_data — allowed; lint-imports green.
- Security: bound parameters only, no SQL string building; no secrets.

### Must-fix
None.

### Deviation accepted (plan defect, not build)
- Acceptance "run_whatif(req, SqlMarketView(engine)) on golden 001 → 10,610,975, approximate" is not testable here: dag.json gives
  BE-market-view `after: [AI-analytics-scaffold]` only, and `run_whatif` / golden 001 land in AI-whatif-lumpsum. The same number
  through `SqlMarketView` is already in BE-whatif-api's acceptance (`get_market_view(engine)` per request; golden 001 →
  `liquidation_vnd == "10610975"`, `approximate is True`). The BE-whatif-api lead must hold that line. Tag: plan.

### Nits (follow-up, not blocking)
1. market_view.py:44 — `.distinct(col)` is deprecated in SQLAlchemy 2.1.4 (SADeprecationWarning; future CompileError) and is silently
   ignored on SQLite, so `test_snapshot_is_max_fetched_at_of_served_rows` passes on SQLite only because days are unique. Switch to
   `.ext(sqlalchemy.dialects.postgresql.distinct_on(...))` and move the snapshot-over-bars assertion into the db test (SQLite then cannot
   compile it). Works correctly today on the pinned version.
2. `snapshot()` before any bar read returns `datetime.min` UTC; a caller must not emit that as `data_snapshot` (BE-whatif-api should
   error out on "no bars" first).
3. Architecture §1.1 says the SQL view should filter `fetched_at <= snapshot` for saved-scenario re-runs (F-088); out of S03 scope, note for F-088.
4. `_rows(self, stmt)` untyped (apps/api is not under mypy strict, so no gate).

### Checks on H
- Kernel `make test-kernel`: `149 passed, 19 deselected, 4 warnings`; ruff "All checks passed!"; mypy "Success: no issues found in 5 source files"; lint-imports green (exit 0).
- db: `uv run pytest -m db apps/api/tests/test_market_view_db.py` against compose `finvest_test` → `1 passed`.
- `-W error` on test_market_view.py: 1 failed / 5 passed — the deprecation in nit 1 only.

### Merge
- `sm.sh merge` → merge sha `efb01b3b5dbaf15fef574f63c5e21b77a5f6c048` on sprint-03 (base ccf6c1f). Base moved after sync
  (36f6c0e → ccf6c1f: FE-shell-bar, FE-how-computed, apps/web only), disjoint from this diff, so BE checks on H stand.
