# 5-review.product — Sprint 04 (round 3, final)

Author: `fi-pm`, 2026-10-26 11:32. Previous: `5-review.product.prev-2.md` (round 2, 10/18 accepted, 18/18 conditional on FE-shots-rw).
Inputs: `4-test.fe.md` (FE-shots-rw **PASS**: §9.2 18/18, screens.mjs 138/0, real-stack.mjs 40/0, vitest 87, tsc 0; now in this folder),
`4-test.be.md`, SM `make smoke` on the live db after BE-fix-index-value 7894e44 (check 1 = 0 rows, check 2 = 0 rows), `5-review.tech.md` **PASS**.
Shots I opened myself (re-taken 17:47–17:49, after the last FE merge 17:45): `table-1280-light`, `how-1280-dark`.

## Verdicts

| Story | Pts | Verdict | Evidence | Stage at fault |
|---|---|---|---|---|
| F-129 Tokens + base stylesheet | 5 | **DONE** | Unchanged from round 2 (§9.2 lines 1, 17 PASS; guards in vitest). | — |
| F-132 Visual acceptance check | 2 | **DONE** | Unchanged from round 2; the retest re-took 47 shots and filled the 18-line checklist. | — |
| F-130 Shell look | 3 | **DONE** | Line 11 (BUG-1): both shots show "ⓘ Mô phỏng … · Educational simulation, not investment advice" with correct spacing. Line 18 (BUG-3): axe 0 violations (screens.mjs 138/0). Line 16 (BUG-6): `how-1280-dark` shows a single ✕. | — |
| F-131 Scenarios screen look | 5 | **DONE** | Line 4 (BUG-2, money display): `table-1280-light` shows ▲ +1.290.559 ₫ green, = 0 ₫ warn, ▼ −2.321.993 ₫ / ▼ −19.847.507 ₫ red; FPT 30.152.493 ₫ / −39,70 % matches the independent figure (real-stack.mjs 40/0). Line 7 (BUG-4): all 11 columns fit at 1280, last column "so với E1VFVN30" visible. Line 13 (BUG-5): drawer has a normal-size "Công thức:" label, the formula on one line in a code box, a right-aligned values list, and the approximate note in a warn box with no overflow. | — |
| S04-RW Carry-overs | 3 | **DONE** | Open check closed: `make smoke` after 7894e44 gives check (1) 0 rows, (2) 0 rows. | — |

**Accepted: 18 / 18 pts.** Sprint goal met.

## Product observations (not scored, carried to sprint-05 backlog grooming)
- OBS-7: at 768 px the top bar wraps (nav links and "⟳ Cào dữ liệu" on 2 lines). The spec only requires one line at 375, so this is not a fail; add a §9.2 line for 768 (retro R2).
- Table header "so với E1VFVN30 (điểm %)" wraps to 3 lines at 1280. Readable, cosmetic.
- HPG DCA card shows 5 "Ngày bán dời sang …" lines (noisy). Candidate item: collapse to "5 ngày bán dời ▸".
