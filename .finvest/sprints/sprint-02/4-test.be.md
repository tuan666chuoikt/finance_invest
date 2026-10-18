# 4-test BE — sprint-02 (fi-be-tester, 2026-10-18)

Head tested: origin/sprint-02 50dce14 + `services/crawler/tests/test_qa_sprint02.py` (branch `test/sprint-02/be`).
**Verdict: FAIL (3 product bugs, 1 blocking M3).** Suite: 154 passed (incl. 7 new, db set against a private `*_test` db), ruff, mypy, lint-imports clean.

## 1. Coverage map
| Story / criterion | Test | Status |
|---|---|---|
| S02-1 only no-trade names => `complete`, separate field, skips only real | test_qa_sprint02::no_trade_session_is_complete; dev test_feed_ticks | pass |
| S02-1 one real skip => `partial` | test_qa_sprint02::no_trade_plus_real_skip | pass |
| S02-3 10-14 `missed` / `source_no_longer_serves` | test_qa_sprint02::past_date_empty_tape_is_still_missed; LIVE | pass |
| S02-3 10-16 re-run, same checksum 145,184 rows | LIVE (see 2) | **FAIL (B1)** |
| S02-2 new files owned by host user | LIVE (see 3) | pass for new files; root-owned old files remain |
| S02-4 clean 1,186 tapes | not in this stage (OPS-cleanup-1015 not built; needs sudo) | n/a |
| F-003 holiday/weekend/trading + name, nothing inferred, 5 trading days 10-19..23 | test_qa_sprint02 (4) + dev test_calendar | pass |
| F-003 2026-09-02 not a gap / weekday is a gap | calendar basis only (catchup uses `trading_days`); no gap-report API exists yet | partial |
| F-019 15:30 timer, 20:00 retry, boot catch-up, non-trading nothing | dev test_catchup (unit); `last_session_date` covered by db run via catchup db? no | unit only; timer never installed (M2 is Thu) |
| F-019 `crawl --date` manual | LIVE (10-14 run) | pass |
| F-004 fields, delisted kept, idempotent | dev test_feed_symbols (db) ; LIVE symbols feed: 1,775 symbols (235 delisted), 6 requests | pass |
| F-012 stored for all years | LIVE | **partial (B2, B3)** |
| F-012 interrupt/resume, no duplicates | LIVE: back-fill died at the indices, re-run replayed 1,609 names with 0 live requests, rows unchanged 4,528,537 | pass |
| F-012 coverage % per exchange | LIVE, computed by hand from DB (the summary line never printed) | see below |

## 2. Live checks
### Back-fill (app DB, real, public VCI endpoint, project rate limit, no block seen)
Run from the worktree (host-owned `data/`), `bars --date 2026-10-18`, started 20:07:06, stocks done 20:28:19 = **21 min 13 s**, then crashed at the index upsert (B2). Run row `failed`, no `crawl_sessions` row.
- Universe 1,775 symbols (+ VNINDEX, VN30). **1,609 symbols have bars**, 4,528,537 rows, 2001-12-19 .. 2026-10-16. FPT: 4,944 bars from 2006-12-13 (matches plan).
- By exchange (symbols with bars / non-delisted listed): HOSE 400/427, HNX 284/299, UPCoM 925/814 (includes delisted). 166 symbols without bars (122 listed STOCK: HOSE 27, HNX 15, UPCoM 80; 44 delisted UPCoM). No-trade vs skipped split is unknown because the summary was never written. Symbol-level coverage 90.6 %, below G2 99.5 % on its face; needs the summary to judge.
- **E1VFVN30 got bars**: 2,687 rows 2016-01-07 .. 2026-10-16.
- **VNINDEX: no bars. VN30: no bars. `index_1d` is empty (0 rows).** F-048 (sprint-03) is blocked until B2 is fixed.
- Resume: second run 1,119 s, 0 live requests, 1,609 replays, no duplicate rows, same crash at indices.
- 281 `vci bar dropped ... prices must be > 0` warnings (documented relaxation).

### `crawl --date 2026-10-14`
`{"summary":"missed","reason":"source_no_longer_serves","requests":2}`. Run against an isolated `*_test` db (the app db 10-14 row was not touched; see B1 for why).

### 2026-10-16
Still served by KBS today (20:09 and 20:40: FPT 2,383 rows, AAA 297 rows).
- Checksum of the archived 10-16 tapes, recomputed with my own script (911 files, plain json/datetime, sorted unique lines): 145,184 rows, `sha256:3bb625c1758502ba4ed16669b33f57ad018cd26b654072ff147f09d41cd5b6b5` = manifest value. Archive is intact.
- Full `crawl --date 2026-10-16` via CLI (isolated db): **`missed`, fetched 0**, even with all 911 archived tapes copied next to it. Cause **B1**.
- A live re-fetch would not give the same checksum anyway: FPT's `t` field differs between 10-16 capture and today's (e.g. 14:45:06:73 vs 14:45:07:57; every row differs, and `TD` is stamped with today's date, harmless as the checksum ignores TD). AAA differs only in TD, so its checksum would match.

### No-trade-only session
Fixture test (all names empty tape, today) => `complete`, rows 0, `symbols_no_trades` filled, `symbols_skipped` empty. The app DB still holds the old S01 row for 10-16 (`partial`, no_trades NULL) because it was never re-run (blocked by B1).

## 3. Ownership of files in data/
Worktree `data/` after symbols + back-fill + 3 ticks runs: 1,694 files + dirs, **0 not owned by stein**. Container runs as 1000:1000. Pre-existing `FI_ROOT/data/raw` (+ ticks/symbols dirs) is still root:root 755: the host-user container cannot create `data/raw/bars_1d` there, so `make backfill`/`make crawl` from the main checkout fails until the documented `sudo chown` runs (needs the sponsor; I have no sudo). I therefore ran from the worktree.

## 4. Bugs
- **B1 (build, BE ticks / S02-3 blocker).** Re-running a past date that is still served reports `missed` when the first name in the sorted universe is a legitimately no-trade symbol (A32 had no tape on 10-16): empty tape on `trading_date < today` is read as "source moved on". Steps: `make crawl DATE=2026-10-16` (or my isolated run). Expected `partial`/`complete`, 145,184 rows (archive replay + live for the rest). Actual `missed`, 0 rows. Risk: it would also overwrite the good 10-16 session row/manifest with `missed`. Do not run S02-3 against the app db until fixed. Fix idea: past-date empty tape => `no_trades` unless served_date is another date or N consecutive names are empty.
- **B2 (build, BE-bars-store/backfill, M3 blocker).** Index `value` unit is mixed inside one payload: VN30 `accumulatedValue` is raw VND until about 2024 (2012-02-06: 222,242,000,000) and million VND afterwards (2026-10-16: 6,386,472.73). `parse_index_bars` applies x1e6 to all, so old values reach 2.2e17 and larger, overflowing BIGINT (`NumericValueOutOfRange`); the whole run dies after the stocks and nothing is written for indices. Stocks may have the same shape of issue (not proven); `value` is NULL for 3,607,103 of 4,528,537 rows (80 %), so "matched value" is only present for about 0.9 M recent rows.
- **B3 (observation, data.md/plan).** `adj_*` prices are the source's adjusted series; F-012 criterion says nominal (C9). value/volume vs adj_close ratios outside [0.5 l, 1.5 h] on 361k of 921k valued rows is consistent with adjustment. Architect to confirm intent.
- **B4 (ops).** `finvest_test` on the compose db is shared and was migrated to revision 0006 by another process during my run (breaks sprint-02 `-m db` with "No such revision 0006"); I used a private `finvest_be02_test` (dropped after). The full-suite pass is from that db.

## 5. Not done
F-019 timer install/fire (M2 is Thu 10-22); S02-4; app-db 10-14 row; `value` NULL root cause; ETFs/FUE* exchange mapping.
