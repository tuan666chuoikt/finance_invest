# 4-test BE round 3 — sprint-03 (fi-be-tester)

**Verdict: PASS with 1 minor + 1 minor note** (T1b fixed, T4 resolved to a clear blocked message, T5 partly). Branch test/sprint-03/be merged with origin/sprint-03 (2236c1e). Previous: `4-test.be.prev-2.md`.
Suites: `make test-kernel` 257 passed / 26 deselected, ruff, mypy, lint-imports green (includes the block-detection unit tests; the source was not provoked). db suite (`-m db`, 26 tests): NOT RUN - the .env password is refused by the compose DB for role finvest (finvest_test exists; 172.20.0.2:5432 reached, auth failed); I did not alter roles. Owner: ops/architect.

| Check | Result |
|---|---|
| T1b migration 0008 | PASS. alembic 0008; crawl_sessions ticks 2026-10-16: partial, fetched 911, skipped 1522, rows 145,184 = ticks table count (145,184 rows / 911 symbols that day). |
| T4 one real press | POST /api/jobs -> job 6, 17:27:45. Progress jumped to 1531/1542 in <60 s (round 2: 1 symbol/min; now fast). Ended `failed` at 17:29:05, duration 79 s, error SourceBlocked source vci "nguồn vci đang chặn tạm, thử lại sau ~1 giờ" (clear message). Summary: bars_1d fetched 962, skipped 8, no_trades 572, rows 10,357, 21 requests (session log), coverage HOSE 100 / HNX 99.0 / UPCOM 91.5. The source blocked us at ~97% of the run (not provoked; I made no second press or probes). |
| Weekend snapshot (Sat 10-24) | Press used trading_date 2026-10-23 (Friday) with total 1542; summary `no_session_today: true`. Good. But the stale bars_1d row for 2026-10-24 from round 2 is still `partial 0/2 skipped` (nothing cleans it up). |
| T5 session row | Row 2026-10-23 was updated by the press (blocked, 962 fetched, 10,357 rows, reason source_blocked). |
| Block detection | unit tests only: green in kernel. |

## Bugs
| Id | Sev | Owner | What |
|---|---|---|---|
| T5b | minor | build | A `complete` bars_1d 10-23 row (4949 rows, 1 fetched) was overwritten by `blocked` (rows 10,357) - status regresses from complete to blocked, because only `rows >=` guards. Probably fine data-wise (more rows) but the status says blocked for a day that was previously complete. |
| T5c | minor | build/ops | Orphan bars_1d row 2026-10-24 partial/0 from the weekend run of round 2 remains. |
| T6 | minor | ops | db-marked suite can't run: .env POSTGRES_PASSWORD does not match the DB role (also round 2). |
| T4 | info | ops | Source (vci) blocks after ~1.5 min of a full catch-up (21 requests per session log); the retry window is ~1 h, so the full press can't finish in one go today. |
