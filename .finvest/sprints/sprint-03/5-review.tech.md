# 5-review.tech — sprint-03 (fi-software-architect, 2026-10-24)

Reviewed: `origin/sprint-03` **2b34322** (96 merges since `origin/main` 0615915; `origin/sprint-02` 4c0baeb is an ancestor, so this
review covers sprint-02 too) against `dag.json` rev 11, `2-tech-plan.md` / `2-tech-plan.ai.md`, the 42 `3-pr.*.md`, `4-test.be.md`
(round 3, PASS + minors), `4-test.fe.md` (round 3, PASS), `contracts/platform.md` v1.12, `contracts/analytics.md` v1.1, `data.md` v1.2.

**Verdict: PASS — merge `origin/sprint-03` into `main`.** No blocker. Sprint-02's FAIL (B1/B2) is closed on this branch (§1).
Four minor items are carried to sprint-04 rework (§3); none changes data, money or a contract the FE/BE already agree on.

## 1. Sprint-02 blockers — closed
| Bug | Fix on sprint-03 | Live proof |
|---|---|---|
| B1 past-day empty tape = `missed` (ticks) | FIX-ticks-probe merged `e2ff2e3` (probe FPT/HPG/VNM, flaky probe = missed). Its live replay exposed T1 (a smaller `partial` replay downgraded the 10-16 ledger row) → FIX-session-ledger `458c8d6` (`rows` never lowered) + FIX-sessions-repair `a50e58b` (migration 0008 repairs from `ticks`). | 4-test.be round 3: `crawl_sessions` ticks 2026-10-16 = 145,184 rows / 911 fetched = `ticks` table count. **Closed.** |
| B2 V2 `accumulatedValue` unit → index rows lost | FIX-index-value merged `e0402af` (`_value_vnd`, BIGINT guard). | 4-test.be round 2 T2: VNINDEX 5,675 bars 2004-01-05..2026-10-23, VN30 3,672, no null `value`, VN-Index benchmark 14,753,846 matches hand calc; stocks `value > 1000·v·c` = 0 rows. **Closed**; F-048 benchmark unblocked. |
Sprint-02 stories S02-3 (10-16 re-crawl) and F-012 index coverage are therefore accepted with this branch; nothing from sprint-02 is rolled back.

## 2. Per task (dag rev 11, 42 tasks)
| Group | Verdict | Note |
|---|---|---|
| M1–M4 (BE-rules-costs, AI-analytics-scaffold, AI-whatif-lumpsum/dca/benchmarks, BE-api-symbols-bars, BE-scenarios-api, BE-contracts-ts, BE-market-view, BE-whatif-api, S-etf-bars, FE-web-scaffold, FE-shell-bar, FE-disclaimer, FE-how-computed, FE-sparkline, FE-scenario-form/cards/table, OPS-web-compose) | PASS | every PR APPROVE + merged; every CHANGES_REQUIRED round closed by a later APPROVE; what-if lump sum and DCA match the tester's independent Decimal oracle 8/8 (4-test.be round 1). |
| Sprint-02 fixes + LIVE-03 (FIX-ticks-probe, FIX-index-value, FIX-whatif-empty-history, FIX-symbols-exact-first) | PASS | §1; L1/L2 retested in round 1 (NO_DATA, exact-first). |
| M5 replan (BE-crawl-hooks, BE-jobs-crawl, BE-fix-u4, OPS-crawl-manual, FE-fix-u1, FE-fix-u2-u3, FE-fix-u5-u7, FE-crawl-button) | PASS | jobs API live 202/409/400/404 + restart → `interrupted`; timer fully removed (test_no_scheduler); FE U1–U7 retested green. |
| M5 rework (S-v2-batch, BE-bars-batch, FIX-session-ledger, FIX-whatif-nodata-msg, FE-fix-crawl-c1-c2-s1) | PASS | cap = 1 verdict applied (`BATCH_MAX = 1`); T3 message PASS; C1/C2/S1 fixed (4-test.fe round 3). |
| M5 round 3 (BE-fetch-blocked, FIX-sessions-repair, BE-ssi-snapshot, BE-bars-press) | PASS | one real press: 1531/1542 in < 60 s, 21 requests, ended with the VN `SourceBlocked` message at ≈ 97 % (round 2 was ≈ 1 name/min, never finished). Block detection only unit-tested on purpose (not provoked). |

## 3. Open minor items — merge or carry?
| Id | Finding | Stage at fault | Blocks merge? | Disposition |
|---|---|---|---|---|
| T5b | bars_1d 10-23 ledger row `complete` (4,949 rows) overwritten by `blocked` (10,357 rows): the T1 rule guards only `rows >=`, not a status rank. Data is richer, no reader decides on `bars_1d` status (`catchup` reads the ticks feed only). | **arch** (my rule "a replay never lowers `rows`" has no status ordering) + build | No | **Carry → sprint-04 rework**: guard becomes `rows >= AND rank(EXCLUDED.status) >= rank(stored)` with `complete > partial = blocked > missed`, or `complete` only replaced by `complete`; one db test. ~15 lines. |
| T5c | orphan `bars_1d 2026-10-24 partial/0` row from the round-2 Saturday press (pre-BE-bars-press wrote the run date; now the target session). | build (fixed root cause) / ops (leftover row) | No | **Carry → sprint-04 ops cleanup**: `DELETE FROM crawl_sessions WHERE feed='bars_1d' AND trading_date='2026-10-24'`, logged in ops/README; no code. |
| T6 | `-m db` suite not runnable by the tester: `.env POSTGRES_PASSWORD` ≠ compose role `finvest`. Coverage still exists: the lead ran the 26 db tests on a throwaway DB for every M5 PR. | ops | No | **Carry → sprint-04 OPS task** together with sprint-02 B4 (per-branch `FINVEST_TEST_DB`): one documented test DSN for the tester. |
| analytics.md §2.4 | `benchmarks[].first_available` shown as a date only; platform.md §2.5 v1.8, `benchmark.py:22` (`None`), the OpenAPI/TS types and FE (FE-fix-u1 "n/a") all agree on `string \| null`. Doc drift only. | ai-arch (doc) | No | **Carry → sprint-04 planning**: fi-ai-architect mirrors `string \| null` into §2.4 (v1.2) before the next analytics task starts. |
| T4 (info) | VCI blocks a full catch-up at ≈ 97 % (21 requests); retry window ≈ 1 h; the press is resumable by design (gap list from DB). | — (source behaviour) | No | Sponsor expectation, not a defect: the first full catch-up may need 2 presses an hour apart. PM: one line in the release note. |

## 4. Per contract
| Contract | Verdict | Change made now (archived first) |
|---|---|---|
| platform.md §2.5/§2.6/§4 v1.12 | PASS (code follows it: step-2 order, `GAP_MAX 40`, `FAIL_RUN 3`, VN blocked message, live `partial/running` row) | **v1.13** (`platform.prev-13.md`): §4 wording the lead flagged twice — `missed` never overwrites a stored `partial` or `complete` (was "unless not `complete`"); the DB row mirrors the **richest** manifest, repair may set `checksum NULL`. Wording only, no behaviour change. |
| data.md §1.2 V2 | PASS | **v1.3** (`data.prev-3.md`): V2 row records the S-v2-batch verdict (one symbol per call, `BATCH_MAX = 1`, 418 hold) in place of the `[unverified]` note. |
| analytics.md §2.4 v1.1 | PASS with the nullable drift above | none (owner fi-ai-architect). |
| openapi.json → `apps/web/src/api/types.ts` | PASS | drift test green in BE-contracts-ts and every later FE PR. |

## 5. Other notes (no task)
- FE: the 3 crawl-button "real idle" cases were red only while the BE tester's job ran; they passed in round 2. Pin `sell_date` in `real-stack.mjs` next sprint (tester's own suggestion) so live numbers stop drifting.
- Plan nit (FIX-index-value PR nit 1): the acceptance example "av = 1e13, v = c = 1 → None" in 2-tech-plan.md contradicts the closest-to-1 rule; the test uses a correct substitute. Left as is in the archived plan.
- Index rule assumes raw-VND index days ≥ 1e9 VND; pre-2012 VNINDEX looked plausible live (5,675 rows, no null) but the lead's ratio query (`value / v` outside [100, 1e7]) was not run — add it to the sprint-04 BE smoke.
