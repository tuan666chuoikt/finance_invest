# 3-pr BE-fetch-blocked

## Round 1 — APPROVE (lead BE, opus, 2026-10-24)
Head H=f4d34b44b296e4f12574f6797cd82477d64eb49a (already up to date with origin/sprint-03; no sync commit).
Files reviewed (4 = plan set): fetch.py, feeds/ticks.py, tests/test_fetch.py, tests/test_feed_ticks.py.
Size: +78/-6 vs plan ~55 (1.5x = 82): within, no consult needed.

Review:
- fetch.get: TimeoutException -> blocked+1, failed=0, status 0; SourceBlocked message "(timed out)" when last_status 0.
  timeout=20 unchanged; failed now counts 5xx only. Matches plan.
- ticks._run: FAIL_RUN=3; streak resets on fetched and no-trades names; at 3 -> rest of names source_blocked,
  status/reason blocked/source_blocked, break (same exit as the SourceBlocked branch; names[i+1:] == todo[i+1:]
  whenever the loop runs). Probe loop untouched; accounting assert holds. Matches platform.md §4 v1.12.
- Tests: all plan acceptance cases present; fake transport URL match "/history/<SYM>?" verified against
  serve() and the KBS URL, so "D not requested" is a real check.
- No secrets, no SQL, no new dependency, no paid source.

Checks (synced head):
- make test-kernel via q.sh: exit 0 — 238 passed, 24 deselected; ruff, mypy, lint-imports clean.
- Mutation: prod files reverted to origin/sprint-03 -> 4 fail (test_three_timeouts_are_blocked,
  test_418_after_a_timeout_is_still_blocked_at_the_third_try, test_http_and_timeout_reasons,
  test_three_failed_names_in_a_row_end_the_run_blocked). The two reset tests guard a missing-reset mutation.
- -m db not required (no migration/repository/SQL change).

Must-fix: none.
Nits (no action): `timeout` skip reason is now only reachable via a non-timeout transport error (e.g. ConnectError)
that _skip_reason maps to "timeout"; plan keeps _skip_reason unchanged, fine. bars_1d now also sees 3 timeouts as
SourceBlocked through fetch.get (plan-accepted; BE-bars-press owns the FAIL_RUN rule there).

Merged: 8c7716ef608f9920c1bb8479e7dd6f4321ba7518 (--no-ff of f4d34b4 into sprint-03, base 184bab1).
