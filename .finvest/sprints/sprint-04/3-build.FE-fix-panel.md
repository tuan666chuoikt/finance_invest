# 3-build FE-fix-panel (BUG-5)
Result: DONE. Root cause: not specificity. InfoButton renders the dialog inside `dd.headline` of the card, so the drawer inherited font-size xl, weight 600 and text-align right from `.sc-card dd.headline` / `.sc-card dd`.
Files: apps/web/src/features/scenarios/panel.css (reset on `.scenario-panel.how`: fs-sm, 400, left; p/dd fs-sm 400; `.formula` display block; `.note-warn-block` left, fs-sm, 400, max-width 100%), HowComputed.test.tsx (+1 jsdom test: computed weight 400, text-align not right, formula display block, rendered inside dd.headline with setup.ts sheets).
Checks: vitest 14 files / 86 tests pass; tsc exit 0; lint exit 0. New test verified red without the CSS fix.
Diff: +15/-1. Deviations: none. Outside-set edits: none (scenarios.css untouched).
Tester: §9.2 line 13; check formula wraps at 375 and 1280 (not checked visually by me).
