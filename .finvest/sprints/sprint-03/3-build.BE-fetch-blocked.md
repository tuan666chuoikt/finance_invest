# 3-build BE-fetch-blocked
Result: done. Branch task/sprint-03/BE-fetch-blocked.
Files: crawler fetch.py, feeds/ticks.py, tests/test_fetch.py, tests/test_feed_ticks.py.
Changes: fetch.get timeout -> blocked+1 (SourceBlocked.last_status 0, message "blocked (timed out)"); ticks._run FAIL_RUN=3 consecutive skipped names -> rest skipped source_blocked, status/reason blocked, break (counter resets on fetched or no-trades).
Contract: platform.md §4 v1.12, data.md §1.2.
Checks: make test-kernel green (238 passed, ruff + mypy + lint-imports clean). Diff 78 ins / 6 del (plan ~55, cap 82).
Tests: 3 new in test_fetch (3 timeouts, timeout reset, timeout+418+418); test_http_and_timeout_reasons rewritten; 2 new ticks tests (A404/B503/Cshape/D -> blocked, D not requested; reset on B -> partial).
Deviations / outside-set edits: none.
Tester note: a lone timeout in `get` no longer yields reason `timeout` unless a 5xx follows within the same get.
