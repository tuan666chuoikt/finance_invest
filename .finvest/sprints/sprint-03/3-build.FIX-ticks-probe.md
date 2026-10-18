# 3-build FIX-ticks-probe (sprint-03)

Result: DONE. Branch task/sprint-03/FIX-ticks-probe, head 1a437df72643b49f32fda1105893d7229cf44f55 (branch-only, no gh). Size: 96 ins / 17 del (plan ~120).

## Files / changes
- `services/crawler/finvest_crawler/feeds/ticks.py`: `PROBE_SYMBOLS = ("FPT","HPG","VNM")`. Past day (`trading_date < today`, no `--only`, universe not blocked): probes in order before the loop. First tape = day served, kept in `probed` so the loop does not refetch it; probe `SourceNoLongerServes` with `served_date` = `missed` at once (skipped empty); all three empty = `missed`/`source_no_longer_serves`, `symbols_skipped = ()`; probe `SourceBlocked` = `blocked` (all names skipped). Loop: empty tape is `no_trades` on any date; `served_date` set = stop (`missed`/`partial`) as before.
- `repositories.upsert_crawl_session`: `ON CONFLICT ... WHERE status NOT IN ('partial','complete') OR EXCLUDED.status <> 'missed'`; manifest file still written by the feed.
- `ops/README.md`: one paragraph on the probe + missed-never-overwrites.
- Tests: `test_feed_ticks.py` (3 new probe tests, `..._after_good_one_is_partial` reworked to a VNM other-session tape, `..._empty_first_tape_is_missed` replaced by the all-empty probe test), `test_repositories_db.py` (2 new), `test_catchup.py` (1 new).

## Contract honored
platform.md 4 v1.6 probe rule; invariant fetched + no_trades + skipped = universe.count (assert unchanged).

## Checks
- `pytest -m "not db"`: 191 passed. ruff: clean. mypy: clean. lint-imports: kept.
- `pytest -m db` (repositories_db + feed_ticks) against finvest_test: 18 passed.

## Deviations / notes
- Acceptance "requests == 3" for the A32/FPT/VNM case holds with the universe pre-archived (test does this); with a live getAll fetch it is 4 (1 universe + 3 tapes).
- Inconclusive probe (payload shape / HTTP error, no tape and not all empty): falls through to the normal loop, so an empty tape then counts as `no_trades` (shortcut; only reachable with a flaky source).
- `test_catchup.py` new test only documents that catch-up hands `run` a date < today (catchup does not pass `today`; `run_ticks` derives it).

## Outside-set edits
- `services/crawler/tests/test_qa_sprint01.py::test_qa_bug2_...`: asserted the old rule (FPT ok + VNM empty on past day = partial). Now expects `complete` with `symbols_no_trades == ("VNM",)`, still checks the empty tape is not archived and a re-run refetches.

## For the tester
Re-crawl 10-16 against the app DB after merge: expect 145,184 rows and the manifest checksum; a `missed` replay must leave the stored partial/complete row alone.

## Fix round 1

- Must-fix 1 done: `feeds/ticks.py` probe block now marks `missed` / `source_no_longer_serves` when no probe returned a
  tape (`if todo and not probed:`); the `empties` counter is gone. An inconclusive probe (5xx/timeout/shape) counts like an
  empty one, so a flaky probe can no longer turn a not-served day into a `complete` 0-row session.
- Test: `test_past_date_flaky_probe_plus_empty_probes_is_missed_not_no_trades` (FPT 500, HPG/VNM empty -> missed, rows 0,
  no_trades (), requests 5 = probe calls only). Fails on the old code ('partial' != 'missed'), passes now.
- Merged `origin/sprint-03` in. Checks: `make test-kernel` exit 0, 198 passed / 22 deselected, ruff and mypy clean.
  Diff vs sprint-03: 7 files, +102/-17 (plan ~120).
- Nit (empty probe re-fetched in loop) left as is; contract wording note is for the architect.
- Head: e71f52c.
