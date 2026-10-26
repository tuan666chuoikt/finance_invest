# 3-pr BE-market-view-ca (F-023, F-015)

## Round 1 — 2026-10-26, fi-tech-lead (BE, opus) — APPROVE

Reviewed head H = `b2f7076702b24e78162b19e2f42bca1541055c03` (dev `09eeed7` + clean sync merge of origin/sprint-05 `5d1976a`, no conflicts).

### Files reviewed (diff vs origin/sprint-05: 5 files, +185/-12; card ~180, stop 270)
- `apps/api/finvest_api/market_view.py`, `apps/api/finvest_api/main.py`, `apps/api/tests/test_health.py`,
  `apps/api/tests/test_market_view_db.py`, `apps/api/tests/test_whatif_reproducible_db.py` (new). All in the card's file set;
  `openapi.json` not needed (`test_openapi_current` green).

### Findings
- Contract: port signatures `corporate_actions(symbol, start, end, *, as_of)` / `adjusted_close(...)` match analytics.md §1.1
  (architecture) exactly; the card's `(symbol, as_of)` was shorthand. `/api/health.rules_version = RULES_VERSION` per platform.md §2.6 v1.14.
- R5: `adjusted_close` loads nominal rows (observed + reconstructed) and stored 12-dp `adj_factors` and delegates to the AI
  `adjusted()`; no formula in the api. R4 respected (factors not re-derived).
- Decisions ("simulator basis"): observed rows x `cumulative(factors, d, today)`, `round_vnd` half-up; shortcut comment removed.
- R9/G11: one `_serve()` path; CA rows served (INNER JOIN `adj_factors`, `ex_date <= min(end, as_of)`) move the snapshot; a future
  ex-date does not. Same rule as the AI fixture view (`fixtures.py:31-45`).
- Look-ahead: `adjusted_close` and `corporate_actions` bounded by `as_of`; `bars_1d` rows bounded by `as_of`, factors to `today`
  is the planned source-adjusted basis. No test stubs `as_of` away (honesty note).
- Security: SQLAlchemy Core only, no string SQL, no secrets, no new dependency.
- Money hand-check (whatif test): buy 100 x 93,500 = 9,350,000 + fee 0.15% 14,025 -> cash 635,975; sell 100 x (100,000 x 0.98 =
  98,000) = 9,800,000 - fee 14,700 - tax 0.1% 9,800 -> 10,411,475 = asserted. 50,000 x 0.98 = 49,000 / 49000.00 also verified.

### Must-fix
None.

### Nits / follow-ups (not blocking)
1. (owner ai, contract deviation, pre-existing, outside this set) `services/analytics/finvest_analytics/sim/whatif.py:143` sets
   `data_snapshot` from the bars' `fetched_at` only, not `view.snapshot()` (contracts/analytics.md §2.3 "view.snapshot() is copied into the
   result"; R9). A CA whose factor scales an observed bar does not move `/whatif`'s `data_snapshot`. One-line AI follow-up; the dev's
   finding confirmed.
2. (owner ai, plan) `bars_1d` applies factors over `(d, today]` with a wall-clock `today`: between the start of an ex-date and the next
   crawl press the served values change while the snapshot can stay put if the CA was fetched before the newest bar. Narrow window; the
   saved-scenario re-check (contracts §4) should key on this when it lands.
3. `adjusted_close` serves every factored CA with `ex_date <= as_of` from `date.min`, including ones before the range that scale no bar:
   conservative (snapshot may move without a value change), matches R9's literal wording and the fixture view. Keep.
4. `Decimal(str(f))` in `_factors`: NUMERIC already returns Decimal; harmless.

### Checks on H (real numbers)
- `make test-kernel` (q.sh lead-mvca-kernel): exit 0, 324 passed, 39 deselected; ruff clean; mypy 5 files clean; import-linter 5 kept, 0 broken.
- `pytest -m db` on a fresh db (`finvest_lead_mvca_b2f7076_test`, live db container, dropped after): exit 0, 39 passed.
- Negative check: with `market_view.py` reverted to origin/sprint-05, the 3 new db tests fail (liquidation 10,610,975 vs 10,411,475;
  49,000 vs 50,000). Each acceptance criterion has a failing-without test.

### Merge
Merged: `9cf1d44d88f147c02d4658ae761bec4962bb10fb` into sprint-05 (base 5d1976a, head b2f7076). Worktree removed.
