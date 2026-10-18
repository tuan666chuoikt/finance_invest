# 3-build BE-bars-backfill (F-012 feed)

**Result:** code done and pushed, PR open. Branch `task/sprint-02/BE-bars-backfill`. **Live back-fill (M3) NOT yet run**: see "Live run pending".

## Files
- `feeds/bars_1d.py`: `run_bars_1d(settings, run_date, *, only, fetcher, conn, repo, today)`. Universe = `repo.list_symbols(include_delisted=True)` + `VNINDEX`, `VN30` (`universe.source = "symbols table"`, or `cli:--only`). One `source.bars` / `source.index_bars` call per name (count 6000). Zero bars -> `symbols_no_trades`; `PayloadShapeError`/HTTP -> `symbols_skipped` (ticks reasons); `SourceBlocked` -> `blocked`, rest skipped. Upsert with `fetched_at` = archive file mtime (indices -> `upsert_index_1d`). `commit()` per name. Checksum = sha256 over per-name sorted canonical lines (names sorted, so the concatenation is globally sorted). End: `daily_coverage` in the summary line `{"summary": ..., "coverage": {...}}`.
- `cli.py`: `bars --date [--only]`, exit 2 when `blocked`. `Makefile`: `backfill` target.
- `domain/ports.py` + kbs/ssi/vci `source.py`: `index_bars` on the `MarketDataSource` port (kbs/ssi raise `Unsupported`; vci shares `_gap_chart` with `bars`). Outside-set edits, mechanical (4-12 lines each); needed because index levels (2 dp) cannot travel as integer-VND `Bar` (BE-bars-store `IndexBar`).
- Tests: `test_feed_bars_1d.py` (5), `test_cli.py` (+1), fixtures `fixtures/feeds/bars_1d/{FPT,ZZZ}.json.gz`.

## Contract honored
platform.md §4 (manifest keys, bars checksum line, `requests` excludes replays, exit codes); data.md §1.2 V2, §4 `bars_1d_src`; ADR-S-008 (re-run = resume, identical rows/checksum).

## Deviation (live finding, VCI payload)
Fixed in `vci/payloads.py` + `vci/source.py` + `test_adapter_vci.py` (outside the file set, > 1 line; found live on 2026-10-16, the alternative is the back-fill failing for most symbols):
- `accumulatedValue` is `null` on old bars -> `value = None` (column is nullable).
- Placeholder rows (`v == 0` and any o/h/l/c <= 0) are skipped.
- A traded day with `c = 0` (e.g. ABI 2009-09-16) is dropped with a `log.warning` instead of raising `PayloadShapeError`, so one bad day does not discard ~19 years of history. The old test case `bars_payload(c=[0])` in `test_bad_bars_are_shape_errors` moved to a new test `test_bar_with_zero_close_is_dropped_not_fatal`.
Architect to confirm this relaxation of the S01 "bad bar = shape error" rule (not a contract change; data.md V2 is silent on null value and zero-close days).

## Checks (merged origin/sprint-02 aec977c first, clean)
- `make test-kernel`: 129 passed, 18 deselected; ruff clean; mypy no issues (5 source files); lint-imports kept.
- `make test` db set: 18 skipped here (no test DB reachable from the host); the feed tests use a fake repo, the repo functions were db-tested in BE-bars-store.
- Acceptance asserted: first run complete / fetched 1 / no_trades ("ZZZ",) / rows 50 / requests 2; replay: same checksum, requests 0; interrupt on symbol 2 -> run closed `failed`, re-run requests 1, same rows as uninterrupted; blocked on symbol 2 -> `blocked`, symbol 1 rows kept, CLI exit 2; full universe adds indices rounded to 2 dp; future date refused.
- Size: 170 non-test lines vs plan ~200 (1.5x = 300): fine.

## Live run pending (M3)
Written at 20:0x VN on 2026-10-18, inside the 15:00-23:00 VN window reserved for the shared rate budget, so I did not run it. Local DB is empty (0 symbols). To do outside the window: `make` stack up, run the `symbols` feed (`docker compose run --rm crawler symbols`), then `make backfill`. Then record here: `SELECT count(DISTINCT symbol) FROM bars_1d_src` (>= 1,500), FPT earliest `trading_date` (2006-12-13), coverage per exchange (G2 >= 99.5 %), shortfall by symbol.

## Notes for the tester
Re-running `make backfill` replays archived payloads (0 requests). `--only FPT,VNINDEX` is a cheap live smoke test.
