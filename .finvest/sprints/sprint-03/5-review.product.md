# 5-review.product — Sprint 03 (fi-pm, 2026-10-24)

Inputs: `1-sprint-plan.md` (revision A23), `stories.tsv`, `product/backlog.md` (acceptance + RW-U1…U7),
`4-test.fe.md` (round 3 PASS; rounds 1–2 in `.prev-1/.prev-2`), `4-test.be.md` (round 3 PASS + minors),
`5-review.tech.md` (PASS, merge `origin/sprint-03` 2b34322), `5-review.ai.md` (PASS, 0 blockers).

**Verdict: ACCEPT. 30 of 30 committed points DONE; 0 stories NOT DONE.** No `must` item is open. The four
`should` items RW-U4…U7 all passed too. One check is still owed after the merge: F-034's live tick press on Mon 10-26
(see F-034). The sprint plan accepted that limit up front, so it does not block acceptance.

## Per story

| Story | Pts | Verdict | Evidence | Failing criterion / stage at fault |
|---|---|---|---|---|
| F-006 Trading-cost rules v1 | 1 | **DONE** | BE-rules-costs merged; fee 0.15 % / tax 0.1 % cited VN§5 in how-computed; golden 001 fee 14,025 | — |
| F-031 Web shell EN/VI | 3 | **DONE** | EN/VI switch + `<html lang>` + reload persist, missing-key test (i18n parity), freshness chip (4-test.fe r1) | — |
| F-040 Lump-sum buy | 3 | **DONE** | golden 001: 10M @93,500 → 100 shares, fee 14,025, cash 635,975 (AI review recomputed); tester's oracle 8/8 | — |
| F-041 Value at end date | 2 | **DONE** | liquidation 10,610,975, pl_pct 6.1098 (golden 001); live FPT 50M case matches /whatif | — |
| F-057 DCA | 3 | **DONE** | goldens 005–007 + 009 match hand calc; real stack DCA HPG card PASS | — |
| F-055 Saved scenarios | 3 | **DONE** | create/edit/delete/confirm via UI (e2e); restart survives; < 2 s: API budget test 20 × 10-year = 0.170 s on this host (the sponsor's machine) | RW-U4 (should) PASS: 422 NO_DATA with reason, card shows the reason |
| F-056 Scenario dashboard | 5 | **DONE** | cards, table sort, sparkline, approximate flag on every card/row, states (ScenariosPage.test); 375 px clean | RW-U1 (must) PASS (null `first_available` → "VN-Index — n/a", no error boundary); RW-U3 (must) PASS (name in heading); RW-U5/U6/U7 (should) PASS |
| F-032 Disclaimer banner | 1 | **DONE** | route enumeration test, both lines | RW-U2 (must) PASS: axe 0 violations on every screen incl. 375 px and EN |
| F-048 Benchmarks | 2 | **DONE** | VN-Index 14,753,846 matches hand calc (live DB); ETF n/a never 0 | UX note (AI note 2): "n/a since <date>" names a date when the real cause is a mid-range gap, so the wording is wrong. The math is correct. Goes to S04 as a UX fix, not a rejection |
| F-051 How computed | 2 | **DONE** | formula, inputs, as-of, rules version, approximate paragraph, Esc closes; axe clean | — |
| F-034 "Cào dữ liệu" button | 5 | **DONE** | per criterion below | — (one live check owed, see below) |
| S03-RW rework U1–U7 | 0 | **DONE** | 4-test.fe r2: all 7 fixed; vitest `it.fails` flipped to `it` | — |
| S03-BE / S03-BE3 (T1–T5, block detection) | 0 | **DONE with minors** | T1b repaired (145,184 rows = ticks table), T3 message, T4 ends with the VN blocked message | T5b, T5c, T6 minors carried to S04 (stage: arch + build / ops, per 5-review.tech §3) |

### F-034 per criterion
| Criterion | Result | Proof |
|---|---|---|
| Button left of the language switch on every route | PASS | crawl-button.mjs, 375 px icon-only with accessible name |
| Trading-day press: ticks of today + daily catch-up, resumable, no duplicates | PASS on fixtures | Recorded fixtures in CI. No session existed before M5 (weekend), which the plan accepted. **The live check is Mon 10-26 after 15:00, owner sm.** |
| Press during the session → `partial` with cut-off, re-crawl replaces it | PASS on fixtures | BE jobs tests (`partial_until`), FE "(một phần, đến 10:30)" |
| Non-trading day → catch-up only + "Hôm nay không có phiên — chỉ cập nhật giá ngày" | PASS live | real press Sat 10-24: trading_date 10-23, `no_session_today: true` |
| Running: spinner/progress, disabled; 409 from a second press; reload restores | PASS | live 202/409; FE running/refused/reload cases |
| Done line + freshness chip refetch | PASS (mocked job shape) | exact sample line matched; bars-status refetch |
| Failure names the cause + source, is recorded, button returns to idle | PASS live | job 6: `failed`, SourceBlocked vci "nguồn vci đang chặn tạm, thử lại sau ~1 giờ"; C1 (POST 500/unreachable) fixed in r3 |
| No timer / cron / boot crawl | PASS | `test_no_scheduler`; SM ran `make uninstall-timers` |

Release note for the sponsor (from T4): the free source (vci) blocks a full catch-up at about 97 % (21 requests) and
lets us retry after about 1 hour. **The first full catch-up may need 2 presses, about 1 hour apart.** The second press picks up
from where the first stopped, with no duplicates.

## Not story acceptance, still owed for the M5 goal
- The sponsor merges `origin/sprint-03` → `dev` → `main` (tech review PASS; only the sponsor merges there), then opens /scenarios on the real stack with ≥ 2
  saved scenarios. The sm prepares and checks it, by 2026-10-25 18:00.
- The 3 FE "real idle" crawl-button cases were red only while a BE job ran. Re-run them once with no job running (fe-tester, after the merge).
- Sprint-02's 21 points (F-003, F-019, F-004, F-012, S02-1..4) never had a product review: sprint-02's tech review was a FAIL.
  Its blockers B1/B2 are closed on this branch (5-review.tech §1). Sprint-02 is accepted with this merge,
  **except F-019 criteria 1–2 (timer + boot catch-up), which A23 superseded.** Those points are not counted again here.
