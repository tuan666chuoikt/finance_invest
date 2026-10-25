# 3-build FE-tokens (F-129)
Result: done. Branch task/sprint-04/FE-tokens.
Files: apps/web/src/styles/tokens.css (new, all visual-design.md 3.1-3.5 tokens, dark block redefines every colour + shadows none), styles/app.css (body/num/mono), main.tsx (imports before ./i18n), test/setup.ts (?raw sheets in one style[data-testid=app-css]).
Checks: typecheck exit 0; npm test 12 files / 76 tests pass (plan said 81; I changed no tests, so the plan count looks stale). 70 lines of custom properties in tokens.css. Existing var() uses (--chart-invested, --chart-line, --color-error) are all declared.
Not run: browser check of #111418 at dark scheme (values copied verbatim from spec).
Deviations: --chart-point is var(--chart-line) once in :root (spec: same in dark), so it is not duplicated.
Outside-set edits: none.
