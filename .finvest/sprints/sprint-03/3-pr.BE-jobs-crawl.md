# 3-pr BE-jobs-crawl (F-034), lead BE

## Round 1, 2026-10-24: CHANGES_REQUIRED

Reviewed head **H = `8800f09`** (task `8f48e2a` + clean sync merge of `origin/sprint-03` @ `7e80f50`, no conflicts; pushed).

### Files reviewed
`apps/api/migrations/versions/0007_jobs.py`, `apps/api/finvest_api/jobs/__init__.py`, `apps/api/finvest_api/jobs/runner.py`,
`apps/api/finvest_api/routes/jobs.py`, `apps/api/finvest_api/main.py`, `apps/api/pyproject.toml`, `apps/api/tests/conftest.py`,
`apps/api/tests/test_jobs.py`, `uv.lock` (2 lines, follows the dep). Generated `openapi.json` / `types.ts` checked only via
`test_openapi_current`. File set = plan; no outside-set edits.

### Must-fix
1. **Size stop skipped.** `--shortstat` 804+/5- overall; excluding generated + lock = **438 added** vs plan ~240
   (1.5x = 360) and there is no `3-consult.BE-jobs-crawl.md`. The build report explains the overrun but a report
   line is not a consult (retro S01 R2). Fix: file `SPRINT_DIR/3-consult.BE-jobs-crawl.md` (size + deviations 2-3 of
   the build report) and get the sa answer before the next round. Do not cut tests to fit.
2. **A blocked source ends as `done`.** `runner.py:82-96`: `run_ticks` / `run_bars_1d` catch `SourceBlocked` themselves
   (`ticks.py` probe + loop, `bars_1d.py:81-84`) and return a Manifest with `status == "blocked"`, so the job is
   `done`, `error: null`, and the `SourceBlocked` branch of `_error` (`runner.py:52-53`) is dead code. Contract
   platform.md §2.6 lists `SourceBlocked` as a failed `error.code` with `source`; UX app-shell.md:41 wants
   "nguồn KBS chặn" in the Error state, not a green done. Fix: after each step, `m.status == "blocked"` → job
   `failed`, `error = {code: "SourceBlocked", message, source: m.source}`, `summary` keeps that step and earlier ones
   (step 2 not run when step 1 is blocked, since the rate budget is shared). Test in `test_jobs.py`: fake
   `run_bars_1d` returns a manifest with `status="blocked", source="kbs"` → `status == "failed"`,
   `error.code == "SourceBlocked"`, `error.source == "kbs"`, `summary.ticks.rows == 4521`; and a blocked ticks fake →
   `run_bars_1d` not called. Both fail on H.
3. **One-at-a-time is enforced by the lock only.** §2.6: "enforced by a process-level lock **and** the `jobs` row".
   `start_crawl` (`runner.py:108-120`) inserts without checking for a `running` crawl row, so a stale `running` row
   (final `_write` failed with the db down, or a second worker) lets a second job start. Fix: inside the insert
   transaction, if a `running` `crawl` row exists, release the lock and return None (the route's 409 then reports
   that row). Test: seed a `running` row without restarting the app → POST → 409, `details.id` == seeded id.

### Nits (no re-review needed)
- `routes/jobs.py:48`: the `else {}` branch is unreachable once must-fix 3 lands (row always exists when 409); fine to keep.
- No `-m db` test touches `jobs` on Postgres; migration round trip was run by hand (below). Optional.

### For the architect (sa), not the developer
- platform.md §1.3 error table says 409 `JOB_ALREADY_RUNNING`; §2.6 and the plan say `JOB_RUNNING`. Code follows §2.6.
  §1.3 should be corrected.
- `summary.bars_1d.sessions_added` is not in any manifest; dev computes distinct `bars_1d_src` dates after minus
  before. Reasonable; contract should say so (consult item).
- `count` = min of the two table maxima, an empty table ignored: while `index_1d` is empty the job never back-fills
  indices (only `make backfill` does). Accept or redefine in the consult answer.

### Hand check (count rule)
Last bar 2026-10-16, today 2026-10-26: sessions 10-19..10-23 (5) + 10-26 (1) = 6, +2 = **8** = test expectation. OK.

### Checks on H
- `make test-kernel`: **223 passed, 22 deselected**; ruff "All checks passed!"; mypy "no issues"; lint-imports ok.
- `test_jobs.py` 5 consecutive runs: **9 passed** each, no flake.
- db (compose `finvest_test`, container IP, started for the run and stopped after): `alembic upgrade head` exit 0;
  `downgrade 0006 && upgrade head` exit 0; `public.jobs` columns match plan; `pytest -m db`: **22 passed, 223 deselected**.
  Note: TimescaleDB also has `timescaledb_information.jobs`; `public` wins on the search path, no clash.

Verdict: **CHANGES_REQUIRED** (3 must-fix). Not merged.

## Round 2, 2026-10-24: APPROVE

Reviewed head **H = `2141d92`** (already contains `origin/sprint-03` @ `7e80f50`; sync was a no-op, no conflicts).

### Files reviewed
Same set as round 1; round-2 delta `8800f09..2141d92` = `runner.py` (+17) and `test_jobs.py` (+44/-6). File set = plan.

### Round-1 must-fix status
1. Size stop: `3-consult.BE-jobs-crawl.md` filed, sa answered A (Size ~240 -> ~350, platform.md v1.9). Re-check:
   `--shortstat` 853+/5- overall; excluding generated `openapi.json`/`types.ts` + `uv.lock` = **~492** <= 1.5 x 350 = 525. Closed.
2. Blocked source: `runner.py:100-101,109-110` raise `_Blocked` on a `blocked` manifest -> `failed`,
   `error {code:"SourceBlocked", message, source}`; blocked ticks skips step 2; finished steps stay in `summary`.
   Tests `test_blocked_bars_fails_job`, `test_blocked_ticks_skips_bars` (fail on round-1 H). Closed.
3. Row guard: `start_crawl` (`runner.py:128-130`) checks for a `running` crawl row inside the insert transaction,
   releases the lock, returns None -> 409 with that row's id. Test `test_stale_running_row_blocks`. Closed.

Contract re-read against platform.md §2.6 v1.9 (sessions_added, symbols_skipped count, count rule, §1.3 `JOB_RUNNING`): code matches.

### Nits (no re-review)
- `runner.py:133-136`: if `Thread.start()` itself fails after the insert, the lock is released but the row stays `running`
  until the next start-up (`mark_interrupted`). Very unlikely; acceptable.
- A `partial`/`missed` manifest ends `done` with `summary.<step>.status` carrying it (only `blocked` fails). Matches §2.6
  (skips are reported, not fatal); FE should show `status`/`symbols_skipped` from the summary.
- `apps/web/src/i18n/{en,vi}.json` key `error.JOB_ALREADY_RUNNING` -> rename in FE-crawl-button (sa note).

### Checks on H
- `make test-kernel`: **226 passed, 22 deselected**; ruff "All checks passed!"; mypy "no issues found"; lint-imports
  "5 kept, 0 broken".
- `test_jobs.py` + `test_openapi*`: **13 passed** x3 runs, no flake.
- db (compose `db`, database `finvest_test`, started for the run, stopped after): `alembic upgrade head` exit 0;
  `downgrade 0006 && upgrade head` exit 0; `alembic_version = 0007`, `public.jobs` 10 columns; `pytest -m db`:
  **22 passed, 226 deselected**.

Verdict: **APPROVE**. Merging H `2141d92` into `sprint-03`.

Merge sha: **`36834ba`** (`36834baa81af713c73af80750d4b082f6335ef25`), base `7e80f50`, pushed via sm.sh. Worktree removed.
