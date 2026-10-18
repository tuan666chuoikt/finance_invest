# 3-build FE-shell-bar (F-031)
Result: built, all acceptance cases covered.
Files: apps/web/src/{components/{TopBar,LangSwitch,FreshnessChip,ApiErrorState}.tsx, app/useBarsStatus.ts, lib/useHotkey.ts, i18n/{en,vi}.json (chip.*, shell.menu)} + TopBar.test.tsx, ApiErrorState.test.tsx.
Contract: platform.md 2.5 GET /bars/1d/status (hand-typed); ux/app-shell.md. App.tsx untouched.
Checks: vitest 15/15 pass (4 files); tsc exit 0; vite build exit 0. Diff vs sprint-03 ~ 250 lines (plan 210).
Deviations: none. Stale rule is the weekday shortcut (commented in FreshnessChip.isStale). Hotkey matches on KeyboardEvent.code or key (Mac Alt+L gives a symbol).
Notes for tester: menu collapse is CSS media query (<768px); jsdom ignores media queries and applies display:none to the menu button, so tests use getByText. Chip stale text: "⚠ stale: last success dd/mm/yyyy". Loading/error chip states: "Loading…" / "Data status unavailable".
Outside-set edits: none.

## Fix round 1
- Must-fix 1: `apps/web/src/app/disclaimer.test.tsx` `at()` now wraps in QueryClientProvider (retry off) and stubs fetch. Outside-set edit (allowed). App.tsx untouched.
- Merged origin/sprint-03. `npx vitest run`: 5 files, 21/21 passed; tsc exit 0.
