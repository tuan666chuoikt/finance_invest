# 3-build BE-ca-step3 (F-014)

## Result
Done. Crawl step 3 (`run_corporate_actions`), `corporate-actions --date` CLI, runner step 3 + summary. Branch `task/sprint-05/BE-ca-step3`.
Own diff 6 files, about +290 lines incl. tests (plan ~220, stop 330).

## Files
- `services/crawler/finvest_crawler/feeds/corporate_actions.py` (new): `CaResult`, `run_corporate_actions(settings, run_date, *, budget, on_progress, fetcher, conn, repo)`.
- `settings.py`: `rate_per_s["vci_iq"] = 1`, `ca_budget = 40`. `cli.py`: `corporate-actions --date` (exit 2 when blocked).
- `apps/api/finvest_api/jobs/runner.py`: `steps = 3`, step 3 after step 2 (also after `partial`), `summary.corporate_actions`, blocked -> `_Blocked` (source `vci_iq`).
- Tests: `services/crawler/tests/test_feed_corporate_actions.py` (5, in-memory repo + MockTransport), `apps/api/tests/test_jobs.py` (+3, fake step 3 in the `fakes` fixture, 3 old assertions updated).

## What changed / contract
- Loop over `ca_symbols_in_order`; before each read, stop when `requests + 1 >= budget` (the next read costs at least one request) -> status `partial`, rest deferred.
  Per symbol: `fetch_events` -> `upsert_corporate_actions` -> `insert_anomaly(symbol, ex_date, rule, source_event_id)` -> `mark_ca_checked` -> commit.
- `SourceBlocked` -> status `blocked`, run row `reason = source_blocked`, no further request. Any other exception -> rollback, run row `failed`, re-raised (job `failed` with that error).
- `crawl_runs` row: feed `corporate_actions`, `trading_date = run_date`, `requests`, `rows = events_upserted`. `CaResult.source = "vci_iq"` so the runner reuses `_Blocked`.
- `changed_symbols` = symbols with a log row or an event id not stored before (a new event changes factors too); parked in a runner local for BE-ca-recompute (no behaviour).
- Summary exactly `{status, symbols_checked, events_upserted, changes, symbols_deferred}`; `null` when step 3 did not start (step 1/2 blocked). Progress total = `min(symbols, budget - 1)`.

## Checks
- `uv run pytest -m "not db"`: 305 passed, 36 deselected. ruff clean, mypy no issues (5 files), lint-imports 5 kept / 0 broken.
- Acceptance: 3 symbols, budget 2 -> 1 checked, 2 deferred, `partial`, requests 1; ex-date change -> changes 3 (one per symbol) and log row `ex_date 2026-11-05 -> 2026-11-07`; identical third run -> 0; 3 x 418 -> `blocked`, 3 requests, run reason `source_blocked`.
- Job tests: shape, `steps == 3`, step 3 after a partial step 2, blocked step 3 keeps `summary.bars_1d`, blocked step 2 leaves `corporate_actions` null.
- Not run: db-marked suite (no db code touched; the repo functions were tested in BE-ca-repo).

## Deviations
None. The feed test uses a fake repo, so the real diff-log SQL is covered only by BE-ca-repo's db tests.

## Notes for the tester
- `insert_anomaly` has no dedupe: an unmapped/amount-missing event adds one `data_anomalies` row per press that re-reads the symbol (same as ticks/symbols feeds).
- Archive-first: a second press on the same `run_date` replays V5 pages from `data/raw/corporate_actions/<date>` (0 requests), so an ex-date change shows only on the next day's press.
- VN30 and scenario tiers never rotate (`ca_checked_at` only orders tier 2): with budget 40 a large scenario set could starve tier 2. Raise for the architect if it matters.

## Outside-set edits
None.
