# 6-retro — Sprint 04

Author: `fi-pm`, 2026-10-25. Inputs: `5-review.product.md`, `4-test.{fe,be}.md`, `activity.log`, `2-tech-plan.md` rev 2,
`product/sponsor-answers.md` A25, sprint-03 retro, `5-review.tech.md` (PASS). Updated 2026-10-26 11:32 after review round 3 (prev: `6-retro.prev-2.md`).

## Velocity
- Committed **18 pts**. Accepted **18/18** (review round 3, after FE-shots-rw 18/18 and `make smoke` 0/0).
- Elapsed time: about 1 h of build (16:59 plan → 17:46 last merge) against a 2.5-day sprint. 13 tasks merged, 1 FE + 1 BE test round, dag rev 2 (+6 fix tasks).
  Two FE tasks were blocked twice on the same `setup.ts` line while sibling tasks were unmerged (a file-set overlap in the plan).
- **Decision: velocity stays 20.** This sprint was small, CSS-heavy work and says nothing about feature capacity.

## What went well
- The screenshot DoD worked on its first use: 6 of 18 checklist lines failed, and it found a money-display bug (BUG-2 "=" on a gain) that 85 green vitest tests missed.
- Smoke check (1) found 4 legacy VNINDEX value rows (B1). The fix guards the adapter and repairs existing data via a migration.
- The BE tester caught a silent false green (B2: a test DB name that skips all 27 tests and exits 0).

## What did not go well
1. **A25 root cause: UI work had no visual spec and no visual check for 3 sprints.** No task covered styling, and the testers checked only behaviour,
   so the sponsor saw browser-default pages. visual-design.md + screenshot DoD now cover it, and both stay.
2. Even with the spec, the first build broke it in 6 places. Developers and leads ran no browser, so CSS inheritance (BUG-5: the drawer sat inside
   `dd.headline`) and table overflow were only visible in shots.
3. The plan gave several FE tasks the same `setup.ts` lines, which caused 2 blocked starts.
4. The 768–1023 px range (2 columns, drawer breakpoint) was never shot (OBS-7).
5. The FE-shots-rw PASS report sat only in the test worktree (`finance_invest-worktrees/test-fe-04/...`), while FI_ROOT's SPRINT_DIR still held the round-1 report; this caused a false NOT DONE at review round 2.

## Action items (≤ 5)

| # | Owner | File | Rule / work | Sponsor |
|---|---|---|---|---|
| R1 | pm | `product/ux/visual-design.md` §9.4; `.finvest/briefs/owner.md` DoD | **Keep the screenshot DoD permanently** for every UI story: §9.1 shots + §9.2 checklist in `4-test.fe.md`; PM opens them at review; no shots = NOT DONE. | no |
| R2 | pm + fe-tester | `visual-design.md` §9.1; `apps/web/e2e/screens.mjs` | **OBS-7:** add a 768 px (and 800 px 2-column) shot set; checklist line "top bar / page header does not wrap unexpectedly at 768". | no |
| R3 | sa | `.finvest/briefs/fe-dev.md`, `lead.md` | A UI task's build note attaches one 1280 light shot of the touched screen (the dev runs `screens.mjs` for that screen); the lead rejects a UI PR without it. This brings visual checking forward from the test round. | no |
| R4 | sa | `.finvest/briefs/architect.md` (dag rules) | Two tasks that edit the same lines of a shared file (`setup.ts`) must have an `after` edge, or be merged into one task. | no |
| R5 | sa (brief) + fe/be-tester | `.finvest/briefs/tester.md` | **A tester's run is not finished until its `4-test.<lane>.md` and `shots/` are copied into FI_ROOT's SPRINT_DIR** (archive the old one as `*.prev-<n>.md` first); the log line names the FI_ROOT path. PM reviews only from FI_ROOT. | no |

Open sponsor item (not an action): **A24-D1**. SM's revised recommendation: keep counting tests in the size stop, exclude i18n catalogues only. Until answered, the current rule (production + tests) applies.

## Câu hỏi cho sponsor
- **A24-D1 (vẫn mở):** Giới hạn kích thước task (dừng ở 1,5×) có tính test không? Khuyến nghị mới của SM là **vẫn tính test, chỉ bỏ file dịch i18n**.
