# Sprint-04 FE test (fi-fe-tester) — verdict: FAIL (6 bugs, 0 blockers of F-132 delivery; 1 major, 3 minor-moderate)

Branch `test/sprint-04/fe` (worktree test-fe-04, from origin/sprint-04 5ab2655). Real stack 127.0.0.1:8080/8001 untouched; crawl button never pressed (job calls mocked); all "E2E ..." scenarios deleted (API list `[]` after).

## Numbers
- vitest: 14 files / 85 tests PASS (includes token/serif guards); tsc --noEmit PASS.
- real-stack.mjs (with `sell_date` pin 2026-10-16, expected FPT lump liquidation 30.152.493, P/L −39,70 %, 400 shares): 36 PASS / 4 FAIL. All 4 FAIL = axe `region` (BUG-3).
- screens.mjs: 134 PASS / 4 FAIL (axe all-rules on /scenarios, both schemes x 2 widths: `heading-order`, `region`). axe `color-contrast`: 0 violations on cards, how-computed, form, table, empty, crawl running/failed, api-error, no-bars in light+dark, 375+1280.
- Playwright stays out of package.json. Files: `apps/web/e2e/{screens,real-stack,crawl-button}.mjs`.
- crawl "done" line is not shown unless a running state was seen first (by design in CrawlStatus) so no done shot.

## Shots (`shots/`, 11 screens x {375,1280} x {light,dark} = 44 + 4 focus at 1280 light + metrics.json)
cards, how, form (validation errors), table, empty, crawl-running, crawl-failed, api-error, loading, nobars; focus-add/-toggle/-card/-form. Cards use 4 real saved scenarios (FPT lump P/L down, HPG DCA, FPT < 1 lot, ACB lump P/L up). 2-column at 768-1023 not shot (CSS media query only read).

## §9.2 checklist (each line looked at in the images)
| # | Line | Result |
|---|---|---|
| 1 | No serif, no grey OS button, bg/surface = tokens in both schemes | PASS |
| 2 | Columns 1 at 375 / 3 at 1280; scrollWidth <= 375 on every 375 shot | PASS |
| 3 | Cards: P/L ▲/▼/= + sign + §3.2 colour | PASS |
| 4 | Table: P/L ₫ cue | FAIL (BUG-2) |
| 5 | Approximate = warn chip; benchmark n/a muted text | PASS |
| 6 | Table figures right-aligned/tabular | PASS |
| 7 | Table at 1280 fits without clipped column | FAIL (BUG-4) |
| 8 | Name column sticky at 375 | PASS |
| 9 | Top bar one line at 375 (menu, icon crawl, VI/EN) | PASS |
| 10 | Disclaimer band visible on /scenarios | PASS |
| 11 | Disclaimer text spacing around "·" | FAIL (BUG-1) |
| 12 | Focus ring on Add, toggle, card button, form field | PASS |
| 13 | How-computed panel look vs §6.6 | FAIL (BUG-5) |
| 14 | Add/edit panel + validation errors | PASS |
| 15 | Empty / loading / API error / no-bars states | PASS |
| 16 | Crawl status running + failed lines | FAIL (BUG-6, minor) |
| 17 | axe color-contrast 0, light+dark | PASS |
| 18 | axe all rules 0 | FAIL (BUG-3) |
Total 12 PASS / 6 FAIL.

## Bugs (stage = build unless stated; owner FE)
- BUG-1 minor, FE-shell: disclaimer renders "…đầu tư·Educational…" and "ⓘMô phỏng": no spaces around the "·" and after ⓘ (all shots).
- BUG-2 major, FE-sc-table: table "Lãi/lỗ ₫" shows "= 1.290.559 ₫" (yellow "=") for a positive P/L whose % column shows ▲ +2,58 %; sign/colour of ₫ column must follow the P/L sign (cards are right).
- BUG-3 moderate, FE-shell: axe `region` — disclaimer `<aside>` (and status band) sits outside any landmark (regression vs sprint-03 where empty page had 0 violations); axe `heading-order` — h1 followed by card h3.
- BUG-4 minor, FE-sc-table: at 1280 the table is wider than the container; last benchmark column ("so với ...") is cut off (needs scroll).
- BUG-5 major(visual), FE-sc-panel: how-computed drawer: "Công thức:" and values use oversized heading/bold style, the formula wraps, and the approximate note is huge bold right-aligned text that overflows the drawer (both widths, both schemes). Off-spec vs §6.6.
- BUG-6 minor, FE-shell: failed crawl line shows a doubled "✕ ✕ Lỗi: ..." (icon + text prefix).
Observations (not scored): DCA card lists 5 "Ngày bán dời sang" lines (noisy); focus shots 1280 light taken while freshness chip still "Đang tải…".
