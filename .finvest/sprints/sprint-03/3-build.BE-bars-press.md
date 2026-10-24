# 3-build BE-bars-press (sprint-03, story S03-BE3)

## Result
Step 2 of a press is now: indices, then the SSI board snapshot (all names, latest session), then at most `GAP_MAX = 40`
VCI gap fetches (oldest last bar first, rest `deferred`). Live `partial/running` ledger row after each committed unit.
Runner stores the last final session (`_target`) and shows the VN blocked message.

## Files
- `services/crawler/finvest_crawler/feeds/bars_1d.py`: `_run` rewritten around a lazy `units()` generator
  (index x2 -> snapshot -> gap batches; gaps need the snapshot answer). `GAP_MAX`, `gap_max` param, `FAIL_RUN` imported from ticks.
- `apps/api/finvest_api/jobs/runner.py`: `_target`, `CUTOFF`, `_count(engine, target)`, `_blocked_msg`, step 2 passes `gap_max=GAP_MAX`.
- `packages/market_data/.../repositories.py`: `last_bar_dates(conn)`.
- tests: `test_feed_bars_1d.py` (+6 tests, FakeRepo gains `last_bar_dates`/delisted flag, autouse `snap` fixture for the board),
  `test_jobs.py` (+3 parametrized target cases, blocked message). `ops/README.md` step-2 paragraph replaced.
- `cli.py`: untouched (default `gap_max=None`).

## Contract honored
platform.md 2.6 v1.12 / 4 v1.12, data.md 1.2 S1 as in the plan block. Checksum definition unchanged
(snapshot and index blocks are held and sorted; gap names stream in name order, so gaps are fetched in name order
AFTER the oldest-first cut). Names disjoint across units, so `OLD_DIGEST` and batch-size tests pass unchanged.

## Checks
- `make test-kernel`: 256 passed, 26 deselected; ruff clean; mypy "no issues found in 5 source files"; lint-imports green.
- `test_feed_bars_1d.py`: 17 passed. `test_jobs.py`: 15 passed.
- DB test `test_last_bar_dates_is_the_latest_per_symbol` was added but SKIPPED here (no `FINVEST_DATABASE_URL`); `make test` on a compose db should run it.

## Deviations / interpretations
- A snapshot skipped for `SourceNoLongerServes` / `Unsupported` does NOT count toward the `FAIL_RUN` streak (not a transport failure; a
  not-yet-rolled board plus two VCI hiccups would otherwise block). HTTP/shape errors on the snapshot do count.
- Blocked in indices/snapshot (before gaps are computed): names already current are listed `source_blocked` with the rest (they are not yet counted as fetched).
- `symbols_no_trades` is now sorted in the manifest (was processing order).
- Bars returned for names outside the unit are now dropped before the upsert (before: stored, only the digest ignored them).
- Per-name `{"symbol":..}` stdout lines are printed for indices and gaps, not for the ~1 500 snapshot names.
- Size: 292 insertions / 60 deletions vs plan ~200 lines (prod ~190 incl. the `_run` rewrite, tests ~150). Over the 1.5x line if
  deletions are counted; nothing is left unfinished, so no split asked.

## Outside-set edits
- `packages/market_data/tests/test_repositories_db.py`: 5-line test for `last_bar_dates`.

## Notes for the tester
- Real-DB run of `last_bar_dates`; a live press against SSI/VCI was NOT run (unit tests only, fake board).
- A back-fill (`count >= COUNT`) skips names whose stored last bar is already >= run_date (spec rule `last < run_date`); interior holes stay for `make backfill` as the plan says.
- Ticks step still dominates press time (~12 min), unchanged (retro note).

## Fix round 1
- Must-fix 1 (FAIL_RUN): bars_1d.py now merges the snapshot SourceNoLongerServes/Unsupported branch into the HTTP/shape branch, so a dropped snapshot logs its skip line and does `streak += 1` (non-snapshot units still re-raise those two). Contract kept, no consult.
- Test: test_a_dropped_snapshot_counts_toward_the_fail_run (board gone + gap batches 1-2 answer 503 -> blocked; names 3-4 source_blocked, never requested). Fails on 88d7431, passes now.
- Checks: make test-kernel exit 0, 257 passed, ruff clean, mypy no issues (5 files). origin/sprint-03 already contained. Head 80d6e763c6e2abb557ce014b2ec7631e7ea0336c.
