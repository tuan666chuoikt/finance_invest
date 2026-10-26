# 3-build FE-rw (S05-RW)
Result: done. Branch task/sprint-05/FE-rw. Diff 56+/8-, under the ~170 line size.

## Changes
- shell.css: brand and nav links `white-space: nowrap`; `.cb-label/.chip-long` hide and `.chip-short` show moved to `max-width: 1023px` (pure CSS, no JS/TSX change in TopBar/Chip/Crawl). Nav stays inline >= 768; aria-labels untouched.
- ScenarioTable: benchmark headers "so với VN-Index" / "so với E1VFVN30" (EN "vs ..."), `title="(điểm %)"` / "(pp)" on th; second footer line "Cột so với: chênh lệch tính bằng điểm %"; th `max-width: 120px` (existing wrap).
- ScenarioCard: DCA renders one line "Ngày mua dời sang ngày giao dịch kế tiếp: {{n}} lần" with native `<details><summary>Xem</summary>` listing `from -> to` per shift; lump sum keeps the old single line. No `.btn-link` class exists in the repo, so the summary is styled in scenarios.css (primary colour, underline; focus ring is the global :focus-visible).
- i18n vi/en: table.vs_*, table.vs_unit, table.footer_vs, card.shift_dca, card.shift_view.

## Checks
- tsc: exit 0. vitest: 14 files / 93 tests pass (new: DCA 5 shifts = 1 line + 5 dates in details; header labels + title + footer note; shell.css base rules keep min-height 32px + nowrap). Existing DCA shift test updated to the new text.
- eslint: no lint script in apps/web, not run.
- Manual (vite dev + mocked API, playwright): top bar height 53 px (52 + border) at 800 wide; table th height 37 px (1 line) at 1280. The official 768/800 proof is FE-shots'.
- Shot: shots/FE-rw/scenarios-table-1280-light.png. e2e/screens.mjs not run (it creates real scenarios on the live stack at 8080, which serves the old build).

## Deviations / notes
- DCA aggregation covers buy_date shifts only; a sell_date shift keeps its own line (so a DCA card with a sell shift shows 2 lines). Tester: say if this should merge into one.
- No outside-set edits. Added apps/web/src/styles/app.test.ts case (a test file, not in the listed set but "existing tests").
