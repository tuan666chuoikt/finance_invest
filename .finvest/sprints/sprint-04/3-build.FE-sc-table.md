# 3-build FE-sc-table (F-131)
Result: done. Branch task/sprint-04/FE-sc-table.
Files: scenarios/table.css (new), ScenarioTable.tsx, ScenarioTable.test.tsx, test/setup.ts.
Changed: inline CSS moved to table.css per visual-design 6.4; th-btn sort buttons with faint hidden-until-hover sort hint; P/L and % cells use local arrow/cls (up/down/zero); flag cell is a warn-coloured "⚠" with title/aria-label; footer .sc-tablefoot. table.css imported by ScenarioTable.tsx.
Checks: tsc exit 0; vitest 14 files / 85 tests passed (new test: losing row shows "▼ −" with class down). No lint script in apps/web package.json (not run). Diff +36/-11, under 1.5x of ~110.
Deviations: flag cell no longer shows the visible word "Gần đúng" text (spec: icon with title/aria-label only). Footer uses a class instead of .muted .fs-xs utility (none exists). n/a benchmark unchanged.
Outside-set edits: none.
Tester: only .sc-tablewrap should scroll sideways at 375; sticky name column below 1024; check dark mode hover.
