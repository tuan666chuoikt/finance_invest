# 3-build FE-fix-table (BUG-2, BUG-4)

Result: built, checks green. Branch task/sprint-04/FE-fix-table.

Files: apps/web/src/features/scenarios/ScenarioTable.tsx, ScenarioTable.test.tsx, table.css.

Changes
- BUG-2: local `signedVnd` (explicit "+" for > 0) for the pl_vnd cell; `arrow`/`cls` now take the numeric `cell.num`
  (>0 up / <0 down / else zero). pl_pct gets the same path. Benchmark cells untouched (plain text, sign already in text). Sorting still uses `num`.
- BUG-4: `thead th { white-space: normal }` (td.num stays nowrap via the table rule), cell padding 0 8px.
- Contract: visual-design.md 3.2 (cards and table identical sign/colour rule).

Checks
- typecheck: exit 0 (5s)
- vitest full web suite (kernel): 14 files, 86 tests passed
- New test "gain and zero rows": fails on the old ScenarioTable.tsx (verified by restoring HEAD version), passes now.
  Gain 1290559 / 2.58 -> "▲ +1.290.559 ₫" up, "▲ +2,58 %" up; zero -> "= 0 ₫" zero. Existing losing-row test green.
- Lint: apps/web has no lint script.

Deviations: benchmark headers keep the long i18n label; no short label exists in i18n (en/vi only have table.vs_*), and none was added (header wraps instead).
Outside-set edits: none.
Tester notes: the 1280 fit (wrap.scrollWidth <= clientWidth with 4 scenarios) was NOT checked here (no browser run); FE-shots-rw must confirm. Size: +26/-7 lines vs ~60 planned.
