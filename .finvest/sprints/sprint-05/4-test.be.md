# Sprint 05 — BE test report, retest round 2 (fi-be-tester, 2026-10-26)

Head: `origin/sprint-05` merged into `test/sprint-05/be` (4c37f29); stack `finvest-test-be` rebuilt on it (db kept: live copy at 0010 + 10-26 press).
Round 1 report: `4-test.be.prev-1.md`. **Verdict: PASS** (B-05-1/2/3/4/5/6 verified fixed; two new low/medium notes below).

## Retests
| Bug | Check | Result |
|---|---|---|
| B-05-1 high | replay of the archived 10-26 pages (`crawl corporate-actions`, then `recompute`): HPG stock_dividend 2026-05-25 (10:1) now stored, adj_factors (2026-05-25) = 0.909090909091; nominal HPG 2026-05-22 = **26,350** (hand 23,955 x 1.1 = 26,350.5), 05-25 = 24,100 (continuous) | **fixed** |
| B-05-1 oracle | `realdata_check.py` Fractions over all 1,346 stored factors (110 names after recompute of every name with events): 1,303 equal to 12 dp, 43 differ by <= 7.4e-5 relative (= 1 VND of P, inversion rounding); reconstructed x G vs V2 source: 292,577 rows, **0 > 1 VND**. 205 stock_dividend rows now in the 27 first-press names | pass |
| B-05-1 replay path | python replay with `ca_symbols_in_order` pinned to the 110 archived names: **0 requests, 0 changes, row count stable (2,197)**; `recompute --symbols HPG` x2: bars md5 identical | pass |
| B-05-2 | `Settings().ca_budget` 28 (unit test); ordering tier, ca_checked_at NULLS FIRST, symbol (db test passes). Live behaviour: see note A | pass |
| B-05-3 | my strict-xfail probe now XPASSes = js/mjs/jsx are scanned | fixed |
| B-05-4 | `ruff check apps services packages` clean; mypy, lint-imports ok | fixed |
| B-05-5 | unit test 14:50 / 15:06 targets; not exercised in a real press (cap) | pass (unit) |
| B-05-6 | `crawl recon` with 4 missing names exits **1**; unit test asserts S2 rows stored as `ssi_s2` (live cross-check not re-run, S2 needs 30 calls) | pass |
| B-05-7 | docker-compose.test.yml db port now 15433 | fixed |

## Suites (q.sh, own db `finvest_test` :15433)
kernel `pytest -m "not db"` **342 passed**; db `pytest -m db` **62 passed**; mypy, lint-imports ok; ruff on product dirs ok
(`ruff check .` also lints my `tests_be05/`: 60 style errors there, not product; `make test-kernel` itself runs `ruff check .` — lead merges my tests, so exclude or fix them then);
oracle `tests_be05` 13 passed (the 1 "failed" is the strict xfail turned XPASS = B-05-3 fixed). `ops/smoke.sql` against my stack: 0 rows on checks 1-2 (equivalent of `make smoke`, which targets the default project).

## Migration rehearsal (fresh read-only pg_dump of finvest-live-db-1, live still 0009)
dump 7.8 s / 47.6 MB; restored into throwaway db (timescaledb pre/post_restore) -> `upgrade head` **1.0 s**: ssi 947 -> 0 in `bars_1d_src`, `bars_1d` 947 observed/ssi, vci 4,534,014 / index_1d 9,347 / symbols 1,775 / ticks 225,520 identical.
Downgrade 0009 0.6 s (947 ssi back), up again ok. Throwaway db dropped. Verdict: no blocker for the live deploy.

## Notes / new findings
- **Note A (my test error, not a bug):** my first "replay" reset `ca_checked_at` for the 27 archived names but tier ordering still put other VN30/never-checked names first, so run 1 made 26 real V5 requests (ok), run 2 a further 33 (V5 **blocked** after ~30 ok calls, as documented). So this round did ~59 extra V5 requests on my stack, spread over 2 runs ~10 min apart; the blocked state is only on my test IP window. No live impact. The clean 0-request replay was then done as above.
- **B-05-8 medium, owner ops/crawler (data):** recon is still 26/30: VNM, VPB, VPL, VRE have **1** `vci` row each in `bars_1d_src` (FPT has 9,893) and 0 reconstructed history, so F-016 "30/30" is not reachable by more CA presses; their V2 daily history is missing in the live copy (bars backfill not done for these 4). Needs a `crawl bars --only VNM,VPB,VPL,VRE` backfill on live or a plan decision.
- B-05-9 info: `corporate_action_unmapped` anomalies are appended per run (364 -> 411 -> ...), so the count grows on every replay; not harmful, but the sentinel in the UI/ops should count distinct (symbol, source_event_id).
- Not exercised: board bar of the run date in a real press (B-05-5 live), an ex-date change in V5.

## Stack left running for the FE tester
Project `finvest-test-be` (worktree `finance_invest-worktrees/test-be-05`, `-f docker-compose.yml -f docker-compose.port.yml`): web :18080, api :18001, db :15433 (db `finvest`, throwaway `finvest_test`). api rebuilt on the merged head, `/api/health` ok, rules_version 2026.10.28; CA data now includes the ISS events for ~110 names with factors recomputed.
