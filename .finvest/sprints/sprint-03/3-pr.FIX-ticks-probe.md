# 3-pr FIX-ticks-probe (sprint-03)

## Round 1 (fi-tech-lead, BE, opus), 2026-10-18

**Verdict: CHANGES_REQUIRED** (1 must-fix). Reviewed head H = `884a6aa` (task `1a437df` + clean sync merge of
`origin/sprint-03` at `58156bb`, pushed). Size: 96 ins / 17 del, 7 files (plan ~120, within 1.5x).

Files reviewed: `feeds/ticks.py`, `repositories.py` (`upsert_crawl_session`), `ops/README.md`, `test_feed_ticks.py`,
`test_repositories_db.py`, `test_catchup.py`, `test_qa_sprint01.py` (outside-set, reported, needed: it asserted the old
rule; accepted).

### Must-fix
1. `services/crawler/finvest_crawler/feeds/ticks.py:110-113` — an inconclusive probe (`PayloadShapeError` /
   `httpx.HTTPError`, i.e. 5xx or timeout after TRIES) breaks the probe rule. Contract platform.md §4 v1.6: "if none of
   them returns a tape for `trading_date` the session is `missed` / `source_no_longer_serves`". The code only marks
   `missed` when `empties == 3`; one flaky probe falls through to the loop, where every empty tape becomes no_trades.
   Reproduced on H (scratch test, removed): universe A32/FPT/VNM, day not served (all empty), FPT 500 x3 on the probe
   then empty → `complete`, reason None, fetched 0, rows 0, requests 8, `symbols_no_trades == ("A32","FPT","VNM")`.
   On the real ~1,600-name universe that is a `complete` 0-row session, and `complete` passes the new upsert guard, so
   it overwrites the stored 10-16 `partial` (145,184 rows): the exact B1 outcome this task exists to stop.
   Fix (smaller than today): no probe returned a tape → missed, e.g. `if todo and not probed:` and drop `empties`.
   Test that must prove it (add to `test_feed_ticks.py`, via `probe_run`): FPT probe raises 5xx (callable override),
   HPG and VNM empty → `missed`, `source_no_longer_serves`, `rows == 0`, `symbols_no_trades == ()`, loop not entered
   (requests = probe calls only). It fails on H.

### Nits (optional)
- An empty probe that is also in the universe (e.g. FPT empty, HPG tape) is fetched again in the loop; could go
  straight to `no_trades`. Contract only requires a fetched *tape* to count once, so not required.

### Contract note (for fi-software-architect, not the dev)
- platform.md §4 v1.6 says the missed run overwrites nothing "unless the stored session is not `complete`" (literally:
  a stored `partial` may be overwritten). The plan block and its acceptance test say `partial` and `complete` are both
  protected; the code follows the plan, which is the data-safe reading (10-16 is a stored `partial`). Please align the
  contract wording to "neither `partial` nor `complete`". Not blocking this task.

### Verified
- Contract: probe order FPT/HPG/VNM, other-session probe → missed after 1 request, probe tape reused (requests == 3 in
  the A32/FPT/VNM case), loop empty tape → no_trades on any date, invariant assert unchanged. `ON CONFLICT ... WHERE`
  references the stored row (`crawl_sessions.status`) and `EXCLUDED.status` correctly. No SQL string building, no
  secrets, no new dependency, no paid source.
- Tests: new feed tests fail on the old code (old rule gives missed for any past empty tape); db test covers partial
  and complete both kept, missed replaced by a later status.

### Checks on H
- `make test-kernel` (pytest -m "not db", ruff, mypy, lint-imports): **197 passed, 22 deselected**; ruff "All checks
  passed!"; mypy "no issues"; import-linter kept. Exit 0.
- `pytest -m db` repositories_db + crawler tests against compose `finvest_test` (container IP): **20 passed**.

## Round 2 (fi-tech-lead, BE, opus), 2026-10-18

**Verdict: APPROVE.** Reviewed head H = `f95dfe2` (fix `e71f52c` + clean sync merge of `origin/sprint-03` at `e0402af`,
pushed). Size vs sprint-03 at `e71f52c`: 7 files, +102 / -17 (plan ~120, within 1.5x).

Files reviewed (fix delta `717c1ad..e71f52c`): `feeds/ticks.py`, `test_feed_ticks.py`.

### Must-fix 1 (round 1): fixed
- `feeds/ticks.py:112` `if todo and not probed:`: no probe returned a tape (empty, 5xx/timeout, shape error in any mix)
  → `missed` / `source_no_longer_serves`; `empties` counter removed. Blocked/other-session probes still exit first
  (`todo = []`), so they are not overwritten. Matches platform.md §4 v1.6 probe rule.
- Test `test_past_date_flaky_probe_plus_empty_probes_is_missed_not_no_trades`: FPT 500 x TRIES(3) + HPG + VNM empty →
  missed, rows 0, no_trades (), skipped (), requests 5 (probe calls only). Verified it **fails** on the pre-fix
  `ticks.py` (1 failed) and passes on H.

### Nits (optional, not blocking)
- `test_feed_ticks.py` comment "TRIES-ish": it is exactly TRIES = 3 + 2.
- Round-1 nits (empty probe refetched in loop) and the contract-wording note for fi-software-architect still stand.

### Checks on H
- `make test-kernel`: **207 passed, 22 deselected**; ruff "All checks passed!"; mypy "no issues"; lint-imports kept. Exit 0.
- `pytest -m db` repositories_db + crawler tests against compose `finvest_test` (container IP): **20 passed**.
- Base moved during merge (`sm.sh` refused at `f95dfe2`): re-synced with `origin/sprint-03` at `6120e23` (FE + `.finvest`
  only, no `services/`/`packages/`/`apps/api` change), clean. **Final H = `1c2eabe`**; checks re-run on it: kernel
  207 passed / 22 deselected, ruff/mypy/lint-imports clean; db 20 passed.
- **Merged** into `sprint-03`: merge sha `e2ff2e3` (base `6120e23`, head `1c2eabe`). Worktree removed.
