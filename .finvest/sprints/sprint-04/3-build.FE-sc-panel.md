# 3-build FE-sc-panel
Result: DONE. Branch task/sprint-04/FE-sc-panel.
Files: panel.css (new), ScenarioForm.tsx, SymbolCombobox.tsx, HowComputed.tsx, ScenarioForm.test.tsx, test/setup.ts.
Changes: drawer 440px from 768px (full-screen sheet below, stacked buttons Luu on top), sticky head/foot, .field/.amount/.radio-row, .combo-list, how-computed as same drawer with .formula block, dl.rows, .note-warn-block; inline styles removed; error p is .field-error role=alert; close X in both heads.
Checks: tsc exit 0; vitest 14 files / 84 tests passed. Lint: no eslint config in apps/web, not run.
Deviations: backdrop for the non-modal form dialog is a 100vmax spread box-shadow (no ::backdrop without showModal); shortcut comment in panel.css. Form footer order is Huy then Luu (Luu last on desktop; column-reverse gives Luu on top on mobile).
Outside-set edits: ScenariosPage.tsx imports ./panel.css (1 line).
Tester: check 1280 (440px + backdrop) and 375 (full screen, formula wraps). node_modules is a symlink to FE-sc-table (untracked).
