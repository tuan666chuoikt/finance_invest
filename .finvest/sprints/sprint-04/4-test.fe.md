# Sprint-04 FE retest (task FE-shots-rw, after Rework R1) — verdict: PASS (0 blocking, 1 new minor observation)

Branch `test/sprint-04/fe` merged with origin/sprint-04 (ffa17aa). Real stack 127.0.0.1:8080/8001 untouched; crawl button never pressed (job calls mocked); "E2E ..." scenarios deleted after each script. Previous report: `4-test.fe.prev-1.md`.

## Numbers
- vitest 14 files / 87 tests PASS; tsc --noEmit PASS.
- screens.mjs: 138 pass / 0 fail (axe all rules + color-contrast, both schemes, 375 + 1280).
- real-stack.mjs: 40 pass / 0 fail (FPT lump: value 30.152.493 ₫, P/L −19.847.507 ₫ / −39,70 %, matches prior independent figure).
- 768 px (new `apps/web/e2e/w768.mjs`): scrollWidth 768, 2 card columns, table fits. Shots: `shots/cards-768-light.png`, `table-768-light.png`.
- All 47 shots re-taken and the key ones viewed by me: cards/table 1280 light, how 1280 dark + 375 light, crawl-failed 375 dark, table 375 light, cards 768.

## BUG retest
| Bug | Result |
|---|---|
| BUG-1 disclaimer spacing | FIXED ("ⓘ Mô phỏng … · Educational …") |
| BUG-2 table P/L ₫ sign/colour | FIXED (▲ +1.290.559 ₫ green, ▼ red, = 0 ₫ warn) |
| BUG-3 axe region + heading-order | FIXED (0 violations) |
| BUG-4 table clipped at 1280 | FIXED (last column visible) |
| BUG-5 how-computed drawer style | FIXED (normal weight, formula fits, note in box, no overflow, both schemes/widths) |
| BUG-6 doubled ✕ | FIXED (single ✕) |

## §9.2 checklist: 18/18 PASS (lines 4, 7, 11, 13, 16, 18 were the previous FAILs). 2 columns at 768 now checked: PASS.

## New observation (not scored, minor, owner FE-shell/build)
- OBS-7 at 768 px the top bar wraps: nav links break to 2 lines and "⟳ Cào dữ liệu" to 2 lines (spec only requires one line at 375). Also DCA card lists 5 "Ngày bán dời sang" lines (noisy), unchanged.
