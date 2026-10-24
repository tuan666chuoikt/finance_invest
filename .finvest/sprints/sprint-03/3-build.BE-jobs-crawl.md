# 3-build BE-jobs-crawl (F-034)

Result: built, all acceptance cases covered. Branch task/sprint-03/BE-jobs-crawl.

## Files
- `apps/api/migrations/versions/0007_jobs.py`: `jobs` table (data.md §3 + progress/summary/error JSONB, status CHECK running|done|failed).
- `apps/api/finvest_api/jobs/__init__.py`: SQLAlchemy `jobs` Table (own MetaData, JSON with JSONB variant).
- `apps/api/finvest_api/jobs/runner.py`: `start_crawl`, `mark_interrupted`, thread body.
- `apps/api/finvest_api/routes/jobs.py`: `POST /api/jobs` (202/409/400), `GET /api/jobs/current`, `GET /api/jobs/{id}`.
- `main.py`: router + lifespan (`mark_interrupted`; a DB failure there is logged, not fatal). `pyproject.toml`: `finvest-crawler` dep (+ `uv.lock`).
- `tests/test_jobs.py` (9 tests), `tests/conftest.py` (jobs table in seed; optional `path=` for a file db).
- `packages/contracts/openapi.json`, `apps/web/src/api/types.ts` regenerated with `make contracts`.

## Contract honored (platform.md §2.6)
Non-blocking `threading.Lock`; 409 `JOB_RUNNING` details `{id, started_at}`; `kind != crawl` -> 400 VALIDATION (Literal body); `current` = newest crawl row, 404 NOT_FOUND; step 1 only on trading days (partial_until = now when before 15:00 VN), step 2 `run_bars_1d(today, count)`; progress written at most every 2 s, the final row write always carries the last progress; failure -> `failed` + `error{code,message,path?,source?,http_status?}`, summary keeps finished steps; lock released in `finally`; start-up marks `running` -> `failed/interrupted`.

## Checks
- `make test-kernel`: 222 passed, 22 deselected; ruff clean; mypy ok; lint-imports ok.
- `test_jobs.py`: 9 passed, 25 repeated runs without a flake (after moving the jobs tests to a file SQLite: a shared StaticPool connection raced between the job thread and the test).
- `test_openapi_current` green after `make contracts`.

## Deviations / decisions (for the architect)
1. **Size**: 438 added lines excluding lock/generated files vs plan ~240 (1.5x = 360). Nothing is left to split; the plan under-sized prod (232 vs 110) and tests (166 vs 105). Pushed whole.
2. **`sessions_added`** is not in any crawler manifest, so it is computed as `COUNT(DISTINCT trading_date)` of `bars_1d_src` after minus before step 2 (contract is silent). Test proves it with a fake that inserts a new date. Plan text "from the fakes' manifests" cannot hold for this field; `ticks.rows` does come from the manifest.
3. **`count`** reads "MIN(MAX(trading_date)) over bars_1d_src and index_1d" as the min of the two TABLE maxima; an empty table is ignored when the other has data, `COUNT` only when both are empty. Risk: while `index_1d` stays empty (live VNINDEX empty), the job never back-fills indices; `make backfill` still does. A per-symbol MIN(MAX) would make delisted symbols force count ~ hundreds on every run, so it was not used.
4. `symbols_skipped` in the summary is the count (`len(m.symbols_skipped)`), the contract lists no shape.
5. The Job response omits `args` and `log` (not in the contract's Job object).

## Outside-set edits
None beyond the listed file set (`uv.lock` follows the dependency change).

## Notes for the tester
- Thread tests monkeypatch `runner.run_ticks`, `runner.run_bars_1d`, `runner._now`; real crawl needs `FINVEST_DATABASE_URL`/`FINVEST_DATA_DIR` in the api container (OPS-crawl-manual).
- Lock is per process: several uvicorn workers would each allow one job. Compose runs one worker.
- POST returns the row as inserted; with instant fakes the response could already be `done` only if the thread finishes before the re-read (not seen in practice).

## Fix round 1 (2026-10-24)
- Must-fix 1 (size stop): filed `3-consult.BE-jobs-crawl.md` (size + deviations 2-3 + the §1.3 name clash); awaiting the sa answer. No tests cut.
- Must-fix 2: `runner.py` raises `_Blocked` when a step's manifest has `status == "blocked"`; job -> `failed`, `error = {code: SourceBlocked, message, source}`; the finished step stays in `summary`; blocked ticks -> `run_bars_1d` not called. Tests `test_blocked_bars_fails_job`, `test_blocked_ticks_skips_bars`.
- Must-fix 3: `start_crawl` checks for a `running` crawl row in the insert transaction, releases the lock and returns None (409 reports that row). Test `test_stale_running_row_blocks`.
- Checks: `make test-kernel` 226 passed, 22 deselected, ruff clean, mypy ok; `test_jobs.py` 12 passed. Merged `origin/sprint-03` (no change pulled in).
- Size: prod+tests now ~+60 over the 438 reported at round 1 (blocked handling, guard, 3 tests).

## Fix round 1b (2026-10-24)
sa answer read (`3-consult.BE-jobs-crawl.answer.sa.md`): size accepted (Size ~350), contract gaps written into platform.md v1.9, no code change. Head `2141d92` already pushed and synced with `origin/sprint-03` (7e80f50). `test_jobs.py`: 12 passed.
