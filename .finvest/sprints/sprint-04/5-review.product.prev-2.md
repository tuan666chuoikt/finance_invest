# 5-review.product — Sprint 04 (round 2)

Author: `fi-pm`, 2026-10-25 ~17:55. Previous: `5-review.product.prev-1.md` (10/18 pending retest, written on the round-1 shots).
Inputs: `1-sprint-plan.md`, `product/backlog.md` Sprint-04 slice, `product/ux/visual-design.md` §9, the FE retest
(FE-shots-rw: PASS, §9.2 18/18, screens.mjs 138/0, real-stack.mjs 40/0, vitest 87). **Note:** that report is in
`finance_invest-worktrees/test-fe-04/.finvest/sprints/sprint-04/4-test.fe.md`, while the copy in this folder is still round 1 (12/6),
so SM must copy it in. Also read: `4-test.be.md`, SM `make smoke` on the live db (check 1 = 0 rows, check 2 = 0 rows), `5-review.tech.md` (**PASS**,
e591bde). Shots I opened myself (all 17:47–17:49, after the last FE merge 17:45): `how-1280-dark`, `table-1280-light`,
`crawl-failed-375-light`, `cards-768-light`.

## Verdicts

| Story | Pts | Verdict | Evidence / failing criterion | Stage at fault |
|---|---|---|---|---|
| F-129 Tokens + base stylesheet | 5 | **DONE** | §9.2 lines 1 (no serif, no OS grey button, bg/surface = tokens both schemes) and 17 (axe color-contrast 0, light+dark) PASS; token/serif guards in vitest. Seen in the shots: system sans font, tabular figures, buttons/inputs/chips styled in light and dark. | — |
| F-132 Visual acceptance check | 2 | **DONE** | All 3 criteria met: the script wrote 44 shots + 4 focus shots (above the 28 required); guards run in `npm test`, and the proof was done by removing a token (FE-guards); `4-test.fe.md` carries 18 checklist lines with pass/fail. Deviation (accepted): folder is `shots/`, not `screens/`. | — |
| F-130 Shell look | 3 | **NOT DONE (pending FE-shots-rw)** | §9.2 line 11 FAIL (BUG-1): I see "đầu tư·Educational" and "ⓘMô phỏng" in all the shots I opened. Line 18 FAIL (BUG-3, axe `region`/`heading-order`). Line 16 FAIL (BUG-6, doubled ✕). Fixes merged in 696ee6d, with no visual proof yet. Lines 9 and 10 PASS (top bar is one line at 375, band visible). | build |
| F-131 Scenarios screen look | 5 | **NOT DONE (pending FE-shots-rw)** | Line 4 FAIL (BUG-2): table P/L ₫ shows "=" in yellow for a gain. This is a **money-display** error and the most serious bug. Line 7 FAIL (BUG-4): table clipped at 1280. Line 13 FAIL (BUG-5): `how-1280-dark` shows "Công thức:" at heading size, the formula broken across 2 lines and right-aligned, and the approximate note as huge bold text overflowing the drawer, which is clearly off §6.6. Fixes are merged in 5dd0944 / 931ce32, and both new tests fail on the old code, but the 1280 fit and the drawer were not checked in a browser. Grid 1/3 columns, cards, sticky Name column and states PASS. | build |
| S04-RW Carry-overs | 3 | **DONE** | T5b rank guard (db 27 passed, new test red on old code); T5c 0 orphan/weekend rows; T6 the tester ran the db suite on a throwaway DB; `sell_date` pinned in real-stack.mjs (FPT 30.152.493, −39,70 %); VNINDEX smoke query added; AI-1 curve i=0 + assert, AI-2 "n/a — thiếu dữ liệu ETF trong kỳ" + test, AI-3 comment. Smoke found legacy data (B1); BE-fix-index-value 7894e44 fixes it. Doc bug B2 fixed in 860af49. Open check: `make up` → `make smoke` (1) = 0 rows (expected N=8 nulled); not yet run by a tester. | — |

**Accepted now: 10 / 18 pts.** Accepted after FE-shots-rw if it shows §9.2 18/18, screens.mjs and real-stack.mjs 0 FAIL: 18 / 18.

## Product observations (not scored)
- OBS-7: 768–1023 px (2-column grid, drawer from 768) was never shot; §9.1 asks for a 2-column check at 800 px. FE-shots-rw adds one
  `cards-800-light` shot and checks for header/top-bar wrapping at 768.
- The HPG DCA card shows 5 "Ngày bán dời sang …" lines, which is noisy. Candidate for a backlog item (collapse into one line "5 ngày bán dời ▸").
- The 375 table shows only 3 columns before horizontal scroll, which is acceptable (Name is sticky, per spec).

## To close the sprint
1. fi-fe-tester runs FE-shots-rw (`2-tech-plan.md` §FE-shots-rw) and adds an 800 px shot (OBS-7). PM then re-opens the shots for
   lines 4, 7, 11, 13, 16, 18 and updates this file.
2. A tester runs `make up && make smoke`, and check (1) must print 0 rows.
3. `5-review.tech.md` PASS.
