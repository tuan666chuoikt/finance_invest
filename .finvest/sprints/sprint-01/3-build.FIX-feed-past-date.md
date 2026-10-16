# 3-build FIX-feed-past-date (sprint-01)

Result: built to plan, 71 lines added/13 removed (block Size ~90). Branch task/sprint-01/FIX-feed-past-date.

## Files
services/crawler: finvest_crawler/fetch.py, adapters/kbs/source.py, feeds/ticks.py; tests/test_fetch.py, test_adapter_kbs.py, test_feed_ticks.py.

## What changed
- `Fetcher.get(..., archive=True)`: `archive=False` returns the 200 body without writing (replay-read still first).
- `KbsSource.ticks`: get(archive=False) -> parse_ticks -> write only if parse accepted and file absent. Empty / other-session tape never lands under trading_date.
- `run_ticks(..., today=None)` (VN day, injectable). Rule: `conclusive = e.served_date is not None or trading_date < today`. Conclusive -> stop; `missed` if nothing fetched else `partial`, reason `source_no_longer_serves`; partial lists `names[i:]` as skipped with that reason. Not conclusive -> `no_ticks` skip, continue. "probe" removed from docstring.

## Contract honored
platform.md 4 v1.2, ADR-S-008, data.md 1.2 K1. parse_ticks unchanged.

## Checks (py3.12 venv borrowed from test-be-01 with PYTHONPATH pointing at this worktree; no uv on host)
- pytest -m "not db": 78 passed, 7 deselected
- ruff: all checks passed; mypy: no issues (5 files); lint-imports: kept (run before the final small edits, only line-wrap changes since)
- `-m db` tests not run (no Timescale on host); test_two_runs_against_db uses good tapes only, unaffected by the new rule.

## New tests
fetch archive=False; KBS empty tape / 10-15 tape for 10-14 never archived; good tape written once, replayed, mtime unchanged; feed partial (FPT pre-archived, VNM empty, today=10-16: 2 requests, 1 replay, no VNM file); feed missed (first empty: 2 requests).
Existing tests: `run()` helper now passes `today=D`, so test_empty_first_tape_is_inconclusive_not_missed stays green; test_past_date_is_missed_after_probe renamed `..._other_session_is_missed`.

## Deviations
None. Spec said "1 (universe) + 1 (VNM)" requests: matches only when the universe is not yet archived, as in the test.

## Outside-set edits
None.

## Notes for tester
Real-clock default: running `ticks --date <yesterday>` with an empty first tape now yields missed/source_no_longer_serves instead of a no_ticks skip. Stale empty tapes already on disk are still replayed (code never deletes): delete them manually.
