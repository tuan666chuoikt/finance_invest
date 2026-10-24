# 4-test BE round 2 — sprint-03 (fi-be-tester)

**Verdict: FAIL** — 0 blocker, 2 major, 1 minor. Branch `test/sprint-03/be` merged with origin/sprint-03 (fb785ee). Previous report: `4-test.be.prev-1.md`.
Numbers: `make test-kernel` 233 passed / 24 deselected, ruff, mypy, lint-imports green. Live: T2 PASS, T3 PASS, T1 not verifiable live, T4 FAIL (see below). Real stack (finance_invest project) used, not stopped. One press only (job 5).

## Retest of round-1 bugs
| Id | Result |
|---|---|
| T1 session ledger | CODE PASS (`where=excluded.rows >= crawl_sessions.rows` in packages/market_data/.../repositories.py, commit 4fb491c; builder reports 2 db tests). NOT run by me: db-marked tests need the finvest_test password (the .env password was refused), and no live replay (it would hit the source again). **Row 10-16 NOT repaired**: still `ticks|2026-10-16|partial|16 fetched|1522 skipped|2578 rows|source_no_longer_serves` while the `ticks` table holds 145,184 rows / 911 symbols for that day. The builder left the repair to the tester; my UPDATE was blocked by the permission classifier, so it stays for the architect/owner to repair (rows 145184, fetched 911). The raw `_manifest.json` for 10-16 is also the overwritten one. |
| T2 index + pre-2025 | PASS. After the press started (indices first): index_1d VNINDEX 5,675 rows 2004-01-05..2026-10-23, VN30 3,672 rows 2012-02-06..2026-10-23, no null value, 0 gaps seen at the ends. What-if FPT buy 2024-02-12 (Tet) now 200, shifted to 2024-02-15 (reason non_trading); FPT 2020-03-02 200. VN-Index benchmark available: 10,000,000 * 1774.15 / 1202.50 = 14,753,846 (matches API, VNINDEX 2024-02-15 c = 1202.50 in DB). B2 index `value` plausible (VNINDEX 10-23: 16.94e12 VND). |
| T3 NO_DATA message | PASS: HLO 2024-01-02 -> 422-class NO_DATA "no data for HLO before 2024-06-24", details {symbol, first_available}. |
| T4 one real press | FAIL on expectation. POST /api/jobs 202 (job 5, 16:25:55). Progress bars_1d done/total: 48 at +4 min, 53 at +9, 61 at +18, 67 at +24 min of 1777 -> about 1 symbol/min and slowing (round 1 was ~9/min), i.e. ~30 h, not the ≈15 min expected at BATCH_MAX=1 (config 2 req/s would be ~15 min, so the source or retry/backoff is the limiter, not our bucket). Never reached `done` in my window; job left running. 418 -> blocked fast: not observed (no 418 happened; unit tests only). Daily-bars session row for 2026-10-24 still `partial 0 fetched` while running. |

## Bugs
| Id | Sev | Owner | What |
|---|---|---|---|
| T1b | major | ops/architect | crawl_sessions row ticks 2026-10-16 still holds the downgraded numbers (2578 rows vs 145,184 in `ticks`); needs the manual repair the FIX note asks for. |
| T4 | major | build (BE-bars-batch) / ops | Full catch-up press does not finish in ~15 min: ~1 symbol/min after the first 50 (60 symbols in 24 min). Needs a cause (per-request latency vs 2**n backoff on soft throttling) and a UI/sponsor expectation; the "1777 in ≈15 min" claim is unproven. |
| T5 | minor | build | While a job runs, bars_1d crawl_sessions row stays `partial/0` and the 2026-10-24 (Saturday) trading_date is used for progress; cosmetic, row is written only at the end. |

Not checked: job `done` summary, 418 live, injection params beyond earlier round, analytics eval harness.
