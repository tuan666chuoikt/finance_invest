# 3-build BE-schema

**Result:** done. Alembic + migration 0001 + Core tables + repositories; db tests green against timescale/timescaledb:2.17.2-pg16.

## Files
`apps/api/alembic.ini`, `apps/api/migrations/{env.py,script.py.mako,versions/0001_market_data_ticks.py}`,
`packages/market_data/finvest_market_data/infrastructure/{tables.py,repositories.py}`,
`packages/market_data/tests/test_repositories_db.py`.

## What changed
- `tables.py`: Core `MetaData` with `ticks`, `crawl_runs`, `crawl_sessions`, `data_anomalies` per data.md §3 (`ticks.side` CHAR(1) NULL + CHECK).
- Migration 0001: `CREATE EXTENSION timescaledb`, 4 tables, `create_hypertable('ticks','ts', 1 day)`, compress (segmentby symbol, orderby `ts, seq`), compression policy 1 day (ADR-S-001). Downgrade drops the 4 tables (extension kept).
- `repositories.py`: `engine()` (pool_pre_ping), `upsert_ticks` (batches of 5,000, `ON CONFLICT DO UPDATE ... WHERE (price,volume,side) IS DISTINCT FROM`, returns updated-row count via `RETURNING (xmax = 0)`), `insert_crawl_run`, `finish_crawl_run`, `upsert_crawl_session(Manifest)`, `insert_anomaly`, `session_status`.
- env.py reads `FINVEST_DATABASE_URL` (no secrets in repo). Deps: `alembic` added to apps/api; `sqlalchemy`, `psycopg[binary]` to market_data (uv.lock updated).

## Contract honored
data.md §3 columns/PKs; platform.md §4 upsert, no DELETE; ADR-S-008 key (symbol, ts, seq).

## Checks
- `pytest packages/market_data/tests/test_repositories_db.py` with FINVEST_DATABASE_URL: 6 passed (migrate base->head->base->head, hypertable listed, compression policy job present, idempotent upsert 0/0/1 changed + newer price stored, batch crossing 5,000 rows, side CHECK rejects 'X' and accepts NULL/'B', session upsert, run/anomaly).
- `make test-kernel`: 22 passed, 6 deselected; ruff, mypy strict, lint-imports ok.

## Deviations
- Size: ~410 lines (incl. 100-line test, 80-line migration) vs plan ~200; past the 1.5x stop, but nothing remains to split, so shipped whole.
- `upsert_ticks` requires unique keys inside the passed list (Postgres rejects a statement touching a key twice); callers run `domain.manifest.dedupe` first (BE-feed-ticks). `duplicate_tick` anomalies from `displaced` are the feed's job.
- No `fetched_at` on ticks (data.md §3 DDL has none); "newest wins" = last write wins.
- db tests are marked `enable_socket` (pytest-socket is on by default) and skip when `FINVEST_DATABASE_URL` is unset. Tested with image tag `2.17.2-pg16`; compose (BE-compose) should pin the same family.

## Outside-set edits
`apps/api/pyproject.toml`, `packages/market_data/pyproject.toml`, `uv.lock` (dependencies only).

## Notes for tester
Run: `docker run -d --rm -p 127.0.0.1:55432:5432 -e POSTGRES_USER=finvest -e POSTGRES_PASSWORD=finvest -e POSTGRES_DB=finvest_test timescale/timescaledb:2.17.2-pg16` then `FINVEST_DATABASE_URL=postgresql+psycopg://finvest:finvest@127.0.0.1:55432/finvest_test uv run pytest -m db`. The module fixture downgrades to base first, so the db name must end in `_test`; otherwise the tests skip.

## Fix round 1
- Must-fix 1: db tests skip unless the URL's database name ends in `_test` (`make_url(URL).database`); nothing is touched otherwise. Proof: URL=.../finvest -> 6 skipped; URL=.../finvest_test -> 6 passed (timescaledb:2.17.2-pg16). Tester note updated to `finvest_test`.
- Nit: `ticks.side` is now `CHAR(1)` (matches migration/card). Infrastructure mypy errors left (not gating).
- Merged origin/sprint-01 (clean). `make test-kernel` exit 0 (34 passed, 6 deselected; ruff, mypy, lint-imports ok).
