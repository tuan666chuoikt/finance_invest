# 3-build BE-market-view-ca (F-023, F-015)

## Result
Done. Branch `task/sprint-05/BE-market-view-ca`, diff vs origin/sprint-05: 5 files, +185/-12 (plan ~180, stop 270). No unmerged task branch touched these lines.

## Files / what changed
- `apps/api/finvest_api/market_view.py`
  - `corporate_actions(symbol, start, end, *, as_of)`: `corporate_actions` INNER JOIN `adj_factors` on (symbol, ex_date), `ex_date` in `[start, min(end, as_of)]`,
    ordered ex_date, id. A CA with no factor row (invalid / not recomputed yet) is not "applied" and does not move the snapshot. Rows served bump `_served`.
  - `adjusted_close(symbol, start, end, *, as_of)`: `bars_1d` nominal rows (observed and reconstructed) + stored `adj_factors` (12 dp rows, not re-derived)
    through the AI `adjusted()` (R5, 2 dp half-up). No formula in the api. Bumps `_served` with the bar rows and with every CA row applied (`ex_date <= as_of`).
  - `bars_1d` (simulator basis): observed rows for days with no source row = O/H/L/C x `cumulative(factors, d, today)`, `round_vnd` (integer half-up);
    the shortcut comment is gone. The CA rows applied also bump `_served`.
  - `_serve()` is the single place `_served` moves (R9); `_today()` = Asia/Ho_Chi_Minh date.
- `apps/api/finvest_api/main.py`: `/api/health` returns `rules_version = RULES_VERSION` (from `finvest_rules.costs`), the "null until F-001" comment removed.
- `apps/api/tests/test_health.py`: expects `RULES_VERSION`.
- `apps/api/tests/test_market_view_db.py` (+2 tests), `apps/api/tests/test_whatif_reproducible_db.py` (new).
- `openapi.json`: not regenerated, `test_openapi_current` is green (the health body is an untyped dict).

## Contract honored
platform.md §2.6 v1.14 `/health`; analytics.md §1.1 signatures (`corporate_actions(symbol, start, end, *, as_of)`, as the AI build also chose over the card's `(symbol, as_of)`),
§1.4; tech-plan.ai R4/R5/R9.

## Checks (real numbers)
- `make test-kernel`: 316 passed, 39 deselected; ruff clean; mypy 5 files clean; lint-imports pass.
- db (own db `finvest_be_market_view_ca_test`, fresh): `pytest -m db` 39 passed (4 new/changed here).
  - G11: bars fetched 2026-10-26T16:14+07, CA fetched 2026-10-27T16:22+07, ex 10-05: `as_of 10-05` snapshot = `2026-10-27T16:22:00+07:00`; `as_of 10-02` snapshot = `2026-10-26T16:14:00+07:00` and `corporate_actions(... as_of 10-02) == []`.
  - observed close 50,000 on D-1, factor 0.98 ex D: `bars_1d` serves 49,000; `adjusted_close` `49000.00` for `as_of >= D`, `50000.00` for `as_of < D`.
  - reproducibility: seed src bars + observed bar + CA + factor, `POST /whatif` twice -> equal `json.dumps(sort_keys=True)`, `rules_version == RULES_VERSION`,
    `liquidation_vnd == 10411475` (hand: cash 635,975 + 100 x 98,000 - fee 14,700 - tax 9,800).
- Note: the db suite needs a fresh db (`test_migration_round_trip` fails with DuplicateTable on a db the market-view db tests have already filled; same as before this task).

## Decisions where the card was silent
1. "today" in `bars_1d` = Asia/Ho_Chi_Minh date, so a future announced ex-date is not applied to observed rows (the source does not have it either).
   `bars_1d` applies factors up to today even when `as_of < ex_date`: this is the source basis (look-ahead on bars is still blocked by the date filter); charts use `adjusted_close` which does honour `as_of`.
2. The "applied" CA set for the snapshot is every factored CA row with `ex_date <= as_of` for the symbol (adjusted_close) / `> first observed day` (bars_1d), like the AI fixture view. A correction to an old CA moves the snapshot though it may not change the served bars: conservative, honest.
3. Empty range: `adjusted_close` returns `[]` and bumps nothing.

## Finding for the architect / AI (not changed, outside the set)
`services/analytics/.../sim/whatif.py:143` builds `Ctx(iso_vn(max(b.fetched_at for b in bars)), ...)`: `/whatif`'s `data_snapshot` is the max `fetched_at` of the bars only and never calls `view.snapshot()`.
So the CA rows whose factors scaled an observed bar do not move `/whatif`'s `data_snapshot` (R9 is right in the SQL view and unit-tested, but not used by the what-if result). Suggest a one-line AI follow-up: use `view.snapshot()`.

## Outside-set edits
None.

## Notes for the tester
- Reconstructed-nominal days appear in `adjusted_close` (kind reconstructed); `bars_1d` still serves only source rows + observed rows.
- Pre-existing: `.distinct(...)` DISTINCT ON deprecation warning in `bars_1d` (the repository `newest_src_bars` already uses `postgresql.distinct_on`); left as is.
