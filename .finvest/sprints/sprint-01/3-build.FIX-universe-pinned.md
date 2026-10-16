# 3-build FIX-universe-pinned
Result: DONE.
## Changes
- Port `symbols(as_of: date)`; KBS/SSI stubs take it; `VciSource.symbols(as_of)` archives under `as_of`, `today` ctor kw dropped.
- `feeds/ticks.py`: `symbols(trading_date)`; `universe.as_of` = archive file mtime (UTC); `fail_unfinished_runs` before `insert_crawl_run`.
- `repositories.fail_unfinished_runs(conn, feed, trading_date) -> int` (status NULL -> failed/interrupted, finished_at=now()).
## Checks
- pytest -m "not db": 82 passed; ruff clean; mypy clean.
- db tests: 8 skipped (no Postgres here), so `test_fail_unfinished_runs` is NOT run. Tester must run `pytest -m db`.
## Tests added
VCI archive path + replay (existing test adapted), feed rerun same count/as_of with 0 requests, feed closes unfinished FakeRepo run, db test for fail_unfinished_runs.
## Deviations / outside-set edits
Also updated test_adapter_ssi.py and test_adapter_kbs.py (call `symbols(D)`), one-line each.
