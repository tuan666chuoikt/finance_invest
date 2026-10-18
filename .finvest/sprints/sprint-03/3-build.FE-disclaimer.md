# 3-build FE-disclaimer
Result: DONE. Branch task/sprint-03/FE-disclaimer.
Files: components/Disclaimer.tsx (new), app/routes.tsx, app/disclaimer.test.tsx (new).
Change: `<aside role="note" data-testid="disclaimer">` with both literal lines (inline-block spans wrap below 768 px), no focusable children, no close button. Rendered in Layout (routes.tsx) when the matched ROUTES entry has `analysis: true`. `analysis` was already required in AppRoute.
Checks: typecheck exit 0; vitest 3 files, 14 tests passed. Test iterates ROUTES (present iff analysis), asserts /scenarios is analysis, both lines in vi and en, nothing focusable.
Deviations: Layout lives in routes.tsx, not App.tsx, so the render hook is there (App.tsx untouched). routes.tsx also exports `routeObjects` (shared by the browser router and the memory router in the test).
Outside-set edits: none.
Tester notes: banner has no shell-bar styling yet (inline style only); FE-shell-bar may restyle.
