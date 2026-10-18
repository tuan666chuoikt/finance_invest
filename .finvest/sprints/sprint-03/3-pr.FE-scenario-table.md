# 3-pr FE-scenario-table
## Round 1: APPROVE (head aec79d343a7685c4dde6a7afe2085d80d8e3c452)
Files reviewed: ScenarioTable.tsx, ViewToggle.tsx, ScenariosPage.tsx, api.ts, ScenarioTable.test.tsx, i18n en/vi.
Must-fix: none.
Nits: (1) api.ts: two queryKey lines lost indentation (useSymbolSearch, useSymbol); (2) useQueries also runs in cards view (shares cache, harmless); (3) footer per-language vs bilingual pair in UX (disclosed).
Checks: branch already synced with sprint-03 (up to date); tsc exit 0; vitest 11 files / 56 tests pass (4 new covering default order, asc/desc aria-sort, flag+footer VI/EN, toggle persistence); size 261+/20- vs ~190 (<1.5x). No money math beyond display via formatters; Number() ordering only.
Merged: 5c3a8c9f5e529893f99fde83c87af687a9d84d91
