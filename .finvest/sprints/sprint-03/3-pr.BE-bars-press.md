# 3-pr BE-bars-press (sprint-03, S03-BE3)

## Round 1 — CHANGES_REQUIRED (lead BE, opus, 2026-10-24)

Head H=88d74311ff08030b8bd48b9723d61bee389ba8ef, already contains origin/sprint-03 (88a13a0), no merge needed.
Files reviewed: feeds/bars_1d.py, jobs/runner.py, repositories.py (`last_bar_dates`), test_feed_bars_1d.py, test_jobs.py,
test_repositories_db.py (outside-set, 5 lines, declared, accepted), ops/README.md. cli.py untouched (default None) - ok.
Size: 7 files +292 / -60 vs plan ~200 (1.5x = 300 insertions, the measure used in earlier sprint-03 rounds): within.

Checked and correct: unit order index x2 -> snapshot -> gaps (lazy generator, gaps computed after the board answer);
oldest-first cut then name-sorted fetch (checksum streams; held list sorted, names disjoint across units); deferred ->
skipped, status partial; delisted only when `count >= COUNT`; snapshot fetched_at = mtime of `board-hose` (the real
SsiSource archives it under feed `bars_1d`, so the path exists); stale board -> one JSON line, nothing marked, names become
gaps; T5 running row after every committed unit, final rows == last running rows; invariant assert kept; runner `_target`
(Sat -> Fri, Fri 14:00 -> Thu, Fri 15:10 -> Fri), `_count(target)`, `gap_max=40`, VN message for `_Blocked` and
`SourceBlocked`, `http_status` kept. Acceptance example 1 recomputed by hand: requests 2 + 1 + 1 = 4; names 8 =
fetched 7 (A,B,C,E,F + VNINDEX, VN30) + no_trades 1 (D) + skipped 0. The plan's "symbols_fetched == 5" omits the two
indices, which have always counted; the test's `5 + 2` is right. No look-ahead (all reads bounded by run_date), no SQL
strings, no secrets, free sources only.

### Must-fix
1. **FAIL_RUN: a dropped snapshot must count as a skipped unit.** `services/crawler/finvest_crawler/feeds/bars_1d.py:136-141`
   `continue`s on `SourceNoLongerServes`/`Unsupported` without `streak += 1`. platform.md §2.6 v1.12: "3 consecutive skipped
   units (**any reason**, `FAIL_RUN`) end the run `blocked`", and the plan block lists "(indices, snapshot or gap batches)"
   with these two exceptions among the snapshot skips. The build report flags this as a deliberate deviation; the lead cannot
   accept a contract change. Fix: increment the streak there (same as the HTTP/shape branch), or, if you think the contract
   is wrong (a pre-15:05 press always starts with a stale board), write `3-consult.BE-bars-press.md` for the software
   architect instead of changing code. Test: board raises `SourceNoLongerServes`, the first two gap batches answer 503 ->
   `blocked`, the third gap name `source_blocked` and never requested (fails on H, where the third batch is requested).

### Nits (no action required)
- When the run blocks in indices/snapshot, names already current are reported `source_blocked` although their bar is in
  the table (build report says so). Acceptable for a blocked run; the tester may note it.
- A gap name whose V2 answer has bars but none for run_date still counts as fetched (pre-existing semantics).
- A skipped snapshot writes no running ledger row and no progress tick (no commit happens); fine.

### Checks on H
- `make test-kernel` (q.sh): exit 0, 256 passed, 26 deselected; ruff clean; mypy no issues (5 files); lint-imports 5 kept, 0 broken.
- `pytest -m db` on a throwaway timescale/timescaledb:2.17.2-pg16 (finvest_test, removed after): 26 passed, 256 deselected;
  `test_last_bar_dates_is_the_latest_per_symbol` PASSED.

## Round 2 — APPROVE (lead BE, opus, 2026-10-24)

Head H=80d6e763c6e2abb557ce014b2ec7631e7ea0336c (one fix commit on top of 88d7431); already contains origin/sprint-03
(88a13a0), no merge needed. Files reviewed (fix diff): feeds/bars_1d.py, test_feed_bars_1d.py.
Size vs origin/sprint-03: 7 files +300 / -61 = 1.5x of ~200, not over: within.

Must-fix 1 (FAIL_RUN) resolved: the snapshot's SourceNoLongerServes/Unsupported now share the HTTP/shape branch, log one
`{"snapshot": "skipped", ...}` line and `streak += 1` (bars_1d.py:136-150); non-snapshot units still re-raise those two.
Traced the new test: index x2 ok (streak 0) -> board gone (1) -> S000 503 (2) -> S001 503 (3) -> blocked; S002/S003
`source_blocked`, never requested (BATCH_MAX = 1). On 88d7431 the streak was 2 at S002, so S002 was requested: the test
fails without the fix. Contract platform.md §2.6 v1.12 kept, no consult needed.

Must-fix: none. Nits from round 1 stand (no action).

### Checks on H
- `make test-kernel` (q.sh): exit 0, 257 passed, 26 deselected; ruff clean; mypy no issues (5 files); lint-imports 5 kept, 0 broken.
- `-m db`: not re-run; repositories/SQL unchanged since round 1 (26 passed on 88d7431).
- Merged into sprint-03: 2b3432202eba7ad91a7a36f7f3061c3c23263f86 (sm.sh merge, base 88a13a0).
