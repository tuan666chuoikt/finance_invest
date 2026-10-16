# 3-build BE-feed-ticks (sprint-01)

**Result:** DONE. Branch `task/sprint-01/BE-feed-ticks`. ~135 prod lines (ticks.py 124, cli.py net +4) vs ~240 planned; tests ~190.

## Files
- `services/crawler/finvest_crawler/feeds/ticks.py` (new): `run_ticks(settings, trading_date, only, *, fetcher=None, conn=None, repo=repositories) -> Manifest`.
- `services/crawler/finvest_crawler/cli.py`: `ticks` calls `run_ticks`; exit 2 on `blocked`, else 0; `--only` is split/stripped/upper-cased.
- `services/crawler/tests/test_feed_ticks.py`, `tests/fixtures/feeds/ticks/{symbols_getAll,FPT,VNM}.json.gz` (FPT = adapter K1 fixture, VNM = same tape +2000 VND).
- `tests/test_cli.py`: removed `test_weekday_not_implemented` (the stub it covered is gone).

## What changed
Flow as planned: insert_crawl_run -> universe (`--only` | VCI symbols, sorted) -> per symbol `ticks()` -> `dedupe` -> `upsert_ticks` -> anomaly `duplicate_tick` (value = displaced + changed) -> commit -> manifest file, `crawl_sessions`, `finish_crawl_run`. First symbol is the probe (its tape is reused, not refetched, so replays stay 3). `SourceNoLongerServes` on it -> `missed/source_no_longer_serves`; `SourceBlocked` -> `blocked/source_blocked`, remaining symbols (incl. the blocked one) skipped `source_blocked`, CLI exit 2. Per-symbol JSON line + final summary line on stdout.
When `fetcher`/`conn` are None, run_ticks builds httpx client + Fetcher (`data_dir/raw` archive, `rate_per_s` buckets) and an engine, commits per symbol, closes them. A caller-supplied conn is never committed by run_ticks.
Unexpected exception: rollback, `crawl_runs` row finished `failed`, exception re-raised (no manifest).

## Contract honored
platform.md §4 manifest keys (test asserts the exact 13-key set), status/reason enums, `universe.source` values, exit non-zero on blocked; ADR-S-008 archive-first replay; data.md §3 tables via the existing repositories.

## Checks
- `make test-kernel`: 70 passed, 7 deselected; ruff ok; mypy strict ok; lint-imports ok.
- `pytest -m db` on timescaledb 2.17.2 `finvest_test` (port 55433, container stopped after): 7 passed (incl. new test: two runs, one on a caller conn, one on run_ticks' own conn -> `count(*) ticks`=100, 1 `crawl_sessions` row with checksum == manifest, 0 anomalies).
- Acceptance map: complete/100 rows/3 requests/manifest keys; rerun requests=0 replays=3 same checksum+ticks; past date missed with 2 requests; 429 on VNM -> blocked, skipped source_blocked, `cli.main` exit 2 (exit mapping tested with run_ticks monkeypatched); renamed field -> partial payload_shape, FPT rows stored.
- Live M3 (`make crawl DATE=<day>` < 45 min) not run here; to be recorded by the M3 run.

## Deviations
1. **Checksum is streamed, not collected in memory.** Symbols are processed in sorted order and each symbol's canonical lines are sorted then hashed. Because `,` (0x2c) sorts below every symbol character, per-symbol sorted blocks concatenated in symbol order equal the global bytewise sort. Test asserts equality with `domain.manifest.checksum` over all stored ticks. This removes the ~200 MB in-memory sort risk; the plan's `shortcut` comment is therefore not needed. Cost: universe is crawled alphabetically (F-018 priority order is out of scope and would need per-symbol sub-checksums then).
2. Extra kw `repo=repositories` on `run_ticks` so the offline test injects the in-memory fake (the plan said "replaced by a fake" without saying how).
3. Skip reason `no_ticks` added for an empty/foreign-date tape on a non-probe symbol (halted stock); it is not in the plan's `http_<status> | payload_shape | timeout` list. Without it one halted symbol would abort the run as an unhandled exception.
4. 5xx/timeout reasons are parsed from `Fetcher`'s `"... last status N"` error text (status 0 -> `timeout`), because `fetch.py` raises a plain `httpx.HTTPError`; a typed error there would be cleaner (outside my set).

## Risks for lead / tester
- Probe = first symbol alphabetically from the VCI list. If that symbol is halted (empty tape) the whole session is recorded `missed/source_no_longer_serves`. Spec-conformant, but worth a look at M3 (maybe probe the first symbol with a non-empty tape).
- `--only` sets `universe.as_of` to the run start.
- A caller-supplied `conn` gets no commit from `run_ticks`; the db test commits itself.

## Outside-set edits
`services/crawler/tests/test_cli.py`: deleted the obsolete stub test.

## Fix round 1
- Must-fix 1: `SourceNoLongerServes` with `served_date None` (empty tape) is now `no_ticks` skip and the next symbol stays the probe; `missed` only when a tape of another session arrives while nothing is fetched yet. Test `test_empty_first_tape_is_inconclusive_not_missed` (partial, FPT no_ticks, VNM 50 rows, 3 requests); past-date test still 2 requests.
- Must-fix 2: `SourceBlocked` from the universe call now yields status blocked/source_blocked, 0 fetched, manifest + session + run written (CLI exit 2 via status). Test `test_universe_blocked_records_manifest_and_session`.
- Nit taken: dead `_skip_reason` branch removed.
- Checks: make test-kernel exit 0 (72 passed, 7 deselected; ruff, mypy, lint-imports ok). db test not re-run.
