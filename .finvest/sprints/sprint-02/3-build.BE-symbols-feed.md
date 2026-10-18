# 3-build BE-symbols-feed (F-004 core)

## Result
DONE. Branch `task/sprint-02/BE-symbols-feed`. `symbols` table (migration 0003) + `symbols` feed + `finvest-crawl symbols [--date]`.

## Files
- `apps/api/migrations/versions/0003_symbols.py`: table as data.md §3 (+ `type IN ('STOCK','ETF')` check, NOT NULL on names/source/fetched_at).
- `domain/models.py`: `SymbolRecord` gains `listed_at`, `delisted_at` (default None). `infrastructure/tables.py`: `symbols`.
- `infrastructure/repositories.py`: `upsert_symbols(conn, rows, fetched_at)`, `mark_delisted(conn, present, run_date)`, `list_symbols(conn, include_delisted=True)`.
- `adapters/vci/source.py`: `parse_symbols(payload, raw_path, include_delisted=False)`; `VciSource.symbols(as_of, include_delisted=False)`.
- `feeds/symbols.py`: `run_symbols(settings, run_date, *, fetcher=None, conn=None, repo=repositories) -> int` (fetcher/conn optional like `run_ticks`, so the CLI is one call).
- `cli.py`: `symbols [--date]`, exit 2 on `SourceBlocked`.
- Tests: `test_repositories_db.py`, `test_adapter_vci.py`, `test_feed_symbols.py` (new), `test_cli.py`.

## What changed / behaviour
- Delisted rows: `exchange` is unknown on V3. Parser emits placeholder `UPCOM`; the upsert keeps the stored exchange for delisted rows (`CASE WHEN excluded.is_delisted THEN symbols.exchange`). A delisted symbol first seen already delisted is stored as `UPCOM` and gets anomaly `delisted_exchange_unknown` (once, not per run).
- `delisted_at = COALESCE(stored, run_date)`; never cleared. Re-listing flips `is_delisted` false, keeps `delisted_at`, writes anomaly `relisted`.
- `fetched_at` = archive file mtime, so re-running the same day rewrites byte-identical rows (F-004 criterion 3).
- `mark_delisted` with an empty `present` is a no-op (a bad/empty payload must not delist everything). `present` = every STOCK/ETF symbol in the payload, delisted board included.
- `crawl_runs.status` for this feed is `ok|blocked|failed` (the DDL comment), unlike ticks which stores the manifest status `complete`.
- The ticks universe is unchanged (default `include_delisted=False`, same archive file).

## Contract
platform.md §4 "Other feeds" `symbols` row honoured (one `crawl_runs` row, shared archive file, no manifest). No `<exchange>.json.gz` files (S1 listings are BE-symbols-enrich).

## Checks
- `make test-kernel`: 116 passed, 13 deselected; ruff clean; mypy clean (5 source files); import-linter clean.
- `pytest -m db` against `finvest_test` (compose db): 13 passed (incl. migration round trip 0003/0002/0001, rerun identical + `requests` 1 then 0, vanished row -> `is_delisted`, `delisted_at == run_date`, row count unchanged, re-listing -> flag false, date kept, anomaly `relisted`).
- Live (23:12 VN, 2026-10-16): `finvest-crawl symbols` against real VCI into `finvest_test`: 1 request, 1,775 symbols. `SELECT exchange,is_delisted,count(*)`: HOSE 427, HNX 299, UPCOM 814, delisted 235 (data.md V3: ~427 / 299 / 815 / 234). Second run: 0 requests, same counts.
- Size: 241 non-test lines added vs plan ~230 (limit 345).

## Deviations
- Live run was local `uv run finvest-crawl symbols` on the compose `finvest_test` db, not `docker compose run --rm crawler symbols`: the compose image is built from the main checkout (no `symbols` command yet) and I did not want to touch the real `finvest` db from an unmerged branch. Re-run with docker after merge.
- Port gained an optional kwarg (see below). It is backwards compatible but it is a port signature change.

## Outside-set edits
- `packages/market_data/finvest_market_data/domain/ports.py`, `adapters/kbs/source.py`, `adapters/ssi/source.py`: `symbols(self, as_of, include_delisted: bool = False)`. Needed because the feed calls the source through the port and the plan's `source.symbols(run_date)` cannot carry the flag. kbs/ssi still raise/ignore as before.
- `codebase.md` §3 still shows `symbols(self)`; it was already stale (no `as_of`), suggest the architect updates it.

## Notes for the tester
- Test db: `FINVEST_DATABASE_URL=postgresql+psycopg://finvest:finvest@<db container ip>:5432/finvest_test` (db port is not published).
- Crawler `conftest` strips `FINVEST_*` env, so `test_feed_symbols.py` re-sets the URL for alembic.
- Not covered: 429 mid-run is only tested with a mock repo; `delisted_exchange_unknown` is asserted only through the sample fixture (5 rows).
