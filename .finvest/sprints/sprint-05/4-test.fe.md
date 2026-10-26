# Sprint 05 — FE test report, round 2 (fi-fe-tester, 2026-10-26)
Head: origin/sprint-05 merged into `test-fe-05` (test/sprint-05/fe). Stack: `finvest-test-be` (web :18080, api :18001), not started/stopped by me. Crawl calls mocked.
**Verdict: PASS** — F-05-1 fixed, no new bugs.

## Runs
| Run | Result |
|---|---|
| vitest (incl. guards.test.ts, app.test.ts) | 14 files / 94 tests pass |
| tsc --noEmit | exit 0 |
| e2e/screens.mjs (axe + guards, 375/1280 light+dark) | 138 pass / 0 fail |
| e2e/fe05-widths.mjs (768/800/375/1280 x light/dark) | 88 pass / 0 fail |
| e2e/real-stack.mjs | 40 pass / 0 fail |
| e2e/crawl-button.mjs | ALL PASS |

## F-05-1 retest: PASS
Real API: DCA HPG 2.000.000, 2025-03-03 -> 2026-10-16 returns 5 shifts. Card (800 light, DOM-checked) shows ONE line "Ngày mua dời sang ngày giao dịch kế tiếp: 5 lần" + `<details>` "Xem" listing 5 `from → to` rows (e.g. 03/05/2025 → 05/05/2025). No "Ngày bán dời sang" anywhere (widths test now asserts that, all 8 combos).

## visual-design.md §9 checklist (375/768/800/1280, light+dark): all PASS
No serif/default button/bg matches scheme; columns 1/2/3 (375/768+800/1280), no hscroll @375; P/L ▲▼= sign+colour, approx chip, benchmarks muted, table figures right; top bar 1 line (h=53) all widths; disclaimer visible; header single line; th <=2 lines (all 1); DCA <=1 shift line; focus rings; guards (var defined, font, axe color-contrast 0) both schemes. Crawl running/done/failed texts per app-shell.md.

## Bugs
None.
Note: widths metric `shift <= 1` also passes at 0 lines; presence proven by the DOM check above.
Shots: `shots/FE-test/`.
