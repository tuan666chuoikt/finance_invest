# 3-pr BE-scheduler (F-019)

## Round 1 — CHANGES_REQUIRED (lead BE, 2026-10-16)
Reviewed head H = 42327506bbe981a87e909db7974eca4aeb28ba2e (already contains origin/sprint-02 24697db; no sync commit).
Files reviewed: Makefile, ops/README.md, ops/systemd/finvest-crawl.{service,timer}, market_data repositories.py,
crawler cli.py, feeds/catchup.py, tests/test_catchup.py, tests/test_cli.py. Size 224 (+) / 2 (-) vs ~200 = 1.1×, ok.

### Must-fix
1. **The 20:00 retry never happens; `partial`/`blocked` days are never re-run.** `feeds/catchup.py:32`
   `start = last + timedelta(1)`. `last_session_date` is the max `crawl_sessions` date, so a day with a row is always
   `<= last`. If the 15:30 run writes `blocked` (or `partial`) for today, the 20:00 run starts tomorrow and runs nothing.
   Reproduced: fake repo last=2026-10-16 with status blocked, now 2026-10-16 20:00 → `ran == []`. On real Postgres,
   `last_session_date` returns the blocked day (2026-10-16). Contract: ADR-S-009 amendment 2026-10-16 says to walk "from the
   last `crawl_sessions` row to today" and run each day that is absent, `partial`, `blocked` or `failed`. Backlog F-019
   says "retry at 20:00 if it failed". Fix: `start = last if last else today`, so the last day counts too (it is skipped
   when `complete`/`missed`). The plan line "+ 1 day" disagrees with the ADR and with the plan's own acceptance; the
   contract wins.
   Test that must prove it: in `tests/test_catchup.py`, a fake that matches a real repo (last = latest row): last=10-16
   `blocked`, now 10-16 20:00 → runs [10-16]; last=10-16 `complete` → runs []. Also fix
   `test_complete_and_missed_skipped_others_run`. Its fake says last=10-11 while rows exist for 10-12..10-15, which a real
   repo cannot return. That is why it passes today. Set last=10-15 so it covers the real case.

### Nits (optional)
- `cli.py` catchup: the status-read `conn` stays idle in a transaction for the whole crawl. It is harmless at READ
  COMMITTED, but a `conn.commit()` after each status read, or one short connection per read, would be cleaner.
- `finvest-crawl.service` runs without `--build`, so after a code change the timer uses the old image until `make up`
  rebuilds it. Add one line to ops/README.md.
- `test_cli.py:38`: the second `import pytest` inside the test is redundant. `ops/README.md:4`: "out of scope for sprint 01
  (F-019)" still cites F-019.

### For sa (not part of this PR)
- With must-fix 1, a past day whose row is `partial` is re-run once. K1 no longer serves it, so `ticks._run` makes it
  `missed` with rows=0 and overwrites the partial manifest and session row, even though its ticks are still in the db.
  The ADR lists `partial` as retryable, so this follows the contract. Decide whether a past `partial` should be final
  instead (catchup would then retry `partial` only for today).

### Post-merge (owner sm, not a PR gate)
- `make install-timers` must run from the **main checkout** after the merge. It writes `$(CURDIR)` into
  `WorkingDirectory`, and run from this worktree it would point at a folder that is deleted after the merge. Record
  `systemctl --user list-timers finvest-crawl.timer` (next 15:30 +07), then M2 on Thu 2026-10-22.

### Checks on H
- `make test-kernel`: 111 passed, 8 deselected; ruff green; mypy no issues; lint-imports 4 kept / 0 broken.
- `pytest -m db` on a throwaway timescale/timescaledb:2.17.2-pg16 (finvest_test, removed after): 8 passed.
  `last_session_date` checked by hand on the same db: rows ticks 10-14 complete, 10-16 blocked, bars 10-20 → returns
  2026-10-16 for `ticks` and None for an unknown feed.

## Round 2 — CHANGES_REQUIRED (lead BE, 2026-10-16)
Reviewed head H = de6be52 (fix 30acf28 + style de6be52 on top of round-1 4232750). origin/sprint-02 is still 24697db, already
in H; no sync commit. Files reviewed: feeds/catchup.py, tests/test_catchup.py, tests/test_cli.py, ops/README.md,
.finvest/sprints/sprint-02/3-build.BE-scheduler.md. Size: whole PR now +247/-14, within 1.5x of ~200 counting code only.

Round-1 must-fix 1: **fixed.** `catchup.py:32` `start = last or today`. The Repo fake now always has a row for `last`, like a
real repo. `test_last_day_blocked_is_retried_at_20h` and `test_last_day_complete_runs_nothing` were added, and
`test_complete_and_missed_skipped_others_run` now uses last=10-15. I put the old line back as a check and 2 tests failed
(`..._skipped_others_run` and `..._retried_at_20h`), so these tests do prove the fix. Edge case: last=today before 15:05
gives end < start, and `trading_days` returns [] without raising. The plan example (last 08-27, now 09-03 15:30 runs 08-28
and 09-03) still holds, because 08-27 is visited and then skipped as `complete`. Nits: `import pytest` was moved up, the
stale F-019 wording was fixed, and the `make up` rebuild line was added. The conn.commit nit was skipped, which is fine.

### Must-fix
1. **A report file is committed in the task branch: `.finvest/sprints/sprint-02/3-build.BE-scheduler.md`. It is a new
   file of 5 lines with only the fix round.** It is outside the file set, and no other task commits its 3-build. The
   real report is the untracked 20-line file in the main checkout. That file does not have the fix-round notes. After the
   merge, sprint-02 would track a cut-down copy of the report. The SM's next `sm.sh finvest` / pull in the main checkout
   would then fail on that path: the untracked file would be overwritten, or both sides add the file and conflict.
   Fix: `git rm` that file in the task branch, in a new commit (no rewrite). Then append the "Fix round 1" section to
   `/home/stein/Desktop/Learning/finance_invest/.finvest/sprints/sprint-02/3-build.BE-scheduler.md` (main checkout,
   absolute path). Proof: `git diff origin/sprint-02...HEAD --stat -- .finvest` is empty.

### Checks on H
- `make test-kernel`: 113 passed, 8 deselected; ruff green; mypy no issues; lint-imports 4 kept / 0 broken.
- `pytest -m db` on a throwaway timescale/timescaledb:2.17.2-pg16 (finvest_test, removed after): 8 passed, 113 deselected.
- With the round-1 catchup.py put back: 2 failed (see above). Code-wise this PR is ready. The only must-fix is the
  stray file, and the next round can approve once that file is gone and the checks stay green.

## Round 3 — APPROVE (lead BE, 2026-10-16)
Reviewed head H = 9bf90e9033a78b64cb0e5bc1dc4650aeac50105e (one commit on top of round-2 de6be52, which removes the stray
report). origin/sprint-02 is still 24697db, already in H; no sync commit. Files reviewed: the one-file diff de6be52..9bf90e9,
plus the whole-PR `--stat`. Size: +238/-5 over 9 files, all in the plan's file set (~200, 1.2x).

Round-2 must-fix 1: **fixed.** `git diff origin/sprint-02...HEAD --stat -- .finvest` is empty. Code is unchanged since round 2,
where it was reviewed and shown to fail without the fix.

### Nits (optional, outside the PR)
- The main-checkout `3-build.BE-scheduler.md` "Behaviour" line still says `start = last session + 1`, and it has no
  "Fix round 1" section. The code is now `start = last or today`. Only the report is stale.

### Checks on H
- `make test-kernel`: 113 passed, 8 deselected; ruff green; mypy no issues; lint-imports 4 kept / 0 broken.
- `pytest -m db` on a throwaway timescale/timescaledb:2.17.2-pg16 (finvest_test, removed after): 8 passed, 113 deselected.

### Post-merge (owner sm, from round 1)
- Run `make install-timers` from the **main checkout** (not a worktree). Record `list-timers` (next 15:30 +07). M2 is on Thu 2026-10-22.
- Merged: 7a745814675eaf7024ef8886e4cf8260b78d5158 into sprint-02 (sm.sh merge, base 24697db).
