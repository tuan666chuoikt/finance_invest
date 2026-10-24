# 4-test BE — sprint-03 (fi-be-tester)

**Verdict: FAIL** — 0 blocker, 2 major, 2 minor. Branch `test/sprint-03/be` from origin/sprint-03 (a2c9bc4), oracle in `tests_be03/oracle.py`.
Numbers: `make test-kernel` 226 passed / 22 deselected (db-marked not run); live checks 27 pass / 3 fail (the bugs below).
Stack: compose project `test-be-03`, dir `/home/stein/Desktop/Learning/finance_invest-worktrees/test-be-03` (data/ symlinked to FI_ROOT/data, .env copied); api 127.0.0.1:8001, web 127.0.0.1:8080. Left running.
Today is Saturday 2026-10-24.

## Bugs
| Id | Sev | Owner | What |
|---|---|---|---|
| T1 | major | build (FIX-ticks-probe) | Replaying `finvest-crawl ticks --date 2026-10-16` (stored session partial, 145,184 rows) ends `partial/source_no_longer_serves` (16 fetched, 1522 skipped, 2578 rows, 3 requests) and **overwrites** the `crawl_sessions` row: rows 145184 -> 2578, fetched/skipped/checksum replaced. `ticks` table itself untouched (145,184 rows for 10-16, verified). The FIX only protects against a `missed` replay; a smaller `partial` replay still downgrades the ledger. Expected: a replay never replaces a row with fewer rows. (Row left in that state; I did not repair it.) |
| T2 | major | plan/build (calendar + index data) | What-if / save for any buy_date before 2025 fails for every symbol: `400 VALIDATION no_trading_day_near_buy` (FPT has bars 2006+; 2024-12-30 ok, 2024-02-12 fails). Cause: `market_view.calendar()` falls back to VNINDEX `index_1d` outside holidays.csv years and `index_1d` has 0 rows (live VNINDEX still empty, seen by FE as U1). So FIX-index-value (B2) could not be verified live (no index rows to check); also RW-U4 is only half useful as the message is a generic VALIDATION. Needs index backfill or holidays.csv for earlier years. |
| T3 | minor | build | `POST /api/whatif` NO_DATA message is just "NO_DATA" (scenarios route says "no data for HLO before 2024-06-24"). |
| T4 | minor | build/ops | Crawl job is very slow on the real source: ~33 of 1777 symbols in 220 s (rate limit), full catch-up ~3 h; UI must keep polling/showing progress (progress is updated, totals ok). Not a defect, a sponsor expectation. |

## F-034 jobs (live, api 8001)
| Case | Result |
|---|---|
| POST {"kind":"crawl"} | PASS 202 {id,status running} |
| second POST while running | PASS 409 JOB_RUNNING details {id, started_at} |
| kind "x" / no body | PASS 400 VALIDATION details.field |
| GET /jobs/current, /jobs/{id}, 999, "abc" | PASS running with progress {step 2, label bars_1d, done/total}; 404 NOT_FOUND; 400 VALIDATION |
| Saturday: ticks step skipped | PASS progress starts at step 2 (bars_1d); no ticks run |
| daily-bars catch-up real | PASS bars_1d_src gained 10-19..10-23 (24/21/22/21/23 rows so far), none for Sat 10-24; /api/bars/1d/status last_trading_date 2026-10-23; no duplicate (symbol,date) among new rows |
| api restart mid-job (x3) | PASS job -> failed, error {code interrupted, message "the api restarted while the job was running"}; new POST then accepted (202) |
| failure naming the cause | NOT reproduced live (HTTPS_PROXY junk and unwritable data dir did not make the job fail; the job kept running). Covered only by unit tests (test_blocked_*; 12 in test_jobs.py pass). |
| Job to `done` with summary | NOT checked live (3 h run) |

## Other checks
| Check | Result |
|---|---|
| RW-U4 save refuses buy_date before first bar | PASS POST and PUT: 422 NO_DATA details {field buy_date, symbol HLO, first_available 2024-06-24}; the first-bar date and next day accepted (201); unknown symbol 422 SYMBOL_UNKNOWN. Test rows deleted |
| What-if lump sum vs independent oracle (Decimal, vn-market s4/s5, 0.15 % fee half-up, 0.1 % sell tax, lot 100) | PASS 4/4: FPT 50M 2025-03-03 400 sh liquidation 30,152,493; HPG 30M 1500 sh 31,991,270; FPT 5M 0 sh 5,000,000; MWG 77,777,777 900 sh 73,878,395 |
| What-if DCA vs oracle (cash carries, shift forward, per-contribution qty/cash_after) | PASS 4/4: HPG 2M/month from 2025-03-31 -> 1600 sh, cash 1,824,517, invested 38,000,000, liquidation 35,180,917 (19 contributions); FPT, MWG, ACB also exact |
| B1 FIX-ticks-probe | unit tests pass; live replay exposed T1 |
| B2 FIX-index-value | unit tests pass (fixture); live: stocks `value > 1000*v*c` = 0 rows; index not testable (T2) |
| Timer fully removed | PASS: no ops/systemd, no .timer/.service/crontab, test_no_scheduler green, api container has no cron |

Not checked: db-marked pytest, analytics eval harness, injection params on symbol/date beyond ZZZZ, auth, job `done` path live, rules_unverified fee flags (shown, accepted).
