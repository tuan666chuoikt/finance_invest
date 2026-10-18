# 3-build FE-scenario-table (F-056)
Result: DONE. Branch task/sprint-03/FE-scenario-table.
Files: ScenarioTable.tsx, ViewToggle.tsx (+ useView hook), ScenariosPage.tsx (toggle + rows via useQueries), ScenarioTable.test.tsx, i18n en/vi `table.*`.
Decision: plain `<table>` (no TanStack), <=100 rows. Rows come from `useQueries(whatIfQuery)` sharing the card cache keys.
Behaviour: default P/L % desc; any numeric column sortable (aria-sort, header buttons; first click desc, then toggles); failed/loading/n/a cells (null) sort last in both directions; failed row shows error in Value cell (role=alert); flag column shows warning + "Approximate" while env.approximate; sticky Name column in horizontally scrolling wrapper; footer note per language; view in localStorage `finvest.scenarios.view` (try/catch).
Contract: displays API strings via formatVnd/formatPct/formatPp; Number() used only for ordering.
Checks: typecheck exit 0; vitest 11 files / 56 tests pass (4 new). Size 261+/20- vs ~190 plan (tests included, under 1.5x).
Deviations: none. Footer is per-language, not the bilingual pair string in the UX file.
Outside-set edits: api.ts - extracted `whatIfQuery(s)` so useWhatIf and the table share one query definition (mechanical).
Tester notes: Start column is not sortable (dates, not numeric). Benchmarks matched by name "VN-Index"/"E1VFVN30". Dollar-free: no e2e written.
