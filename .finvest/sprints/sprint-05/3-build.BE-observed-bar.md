# 3-build BE-observed-bar (F-013)

Result: built, kernel green. Branch task/sprint-05/BE-observed-bar (113 lines changed vs plan ~190).

## What changed
- `Bar.ref: int | None = None` (last field); `SsiRow.refPrice`; `parse_snapshot` fills `ref` (0/absent -> None).
- `feeds/bars_1d.py`: snapshot unit -> `repo.upsert_bars_1d(kept, nominal_kind="observed", fetched_at=<archive mtime>, ref={symbol: ref})`;
  V2 units still `upsert_bars_1d_src`. Manifest/checksum lines unchanged.
- `jobs/runner.py`: `_count`/`_sessions` use the union of `bars_1d_src` and `bars_1d` dates; `summary.bars_1d.symbols_deferred` =
  count of `deferred` entries in `m.symbols_skipped` (the manifest already carried them; `run_bars_1d` needed no new return value).
- `market_view.py`: `bars_1d` = newest-version src rows + `bars_1d` observed rows for dates absent from src, unscaled
  (`# shortcut:` comment as planned), `_served` includes their `fetched_at`; `first_bar_date` = min over both tables.

## Contract
platform.md §2.6 v1.12-v1.14, data.md §1.2 S1 / §1.4 (1). The repo function `upsert_bars_1d` (BE-mig-0010) was reused as is.

## Checks
- `make test-kernel` equivalent via q.sh: 284 passed, 31 deselected (db); ruff clean; mypy clean (5 files); lint-imports ok.
- New tests: fixture AAA `ref == 7000`; ref None for 0/absent; feed lands observed + ref, none in src, replay = identical rows and checksum;
  `symbols_deferred` in job summary; `_count`/`_sessions` see a bars_1d-only day.
- The stale-board case (tradingDate != target -> SourceNoLongerServes -> names become gaps) was already covered by existing tests.
- NOT run: the new db test `test_a_day_only_in_bars_1d_is_served_and_moves_the_snapshot` (no Postgres on this machine; skipped).
  The union query compiles for the postgresql dialect.

## Deviations / notes for the tester
- Not changed: crawler gap detection (`last_bar_dates`) still reads `bars_1d_src` only, so a name observed in `bars_1d` but absent from a
  later stale board looks like a gap and is fetched via V2. Outside the file set; harmless (extra request), flag for the architect.
- `first_bar_date` and the served rows follow the plan literally; the served set is `nominal_kind = 'observed'` only, `first_bar_date`
  counts every `bars_1d` row (reconstructed rows do not exist yet).
- Please run the db test under `make test-db`.

## Outside-set edits
none
