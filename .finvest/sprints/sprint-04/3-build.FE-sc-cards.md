# 3-build FE-sc-cards (F-131)
Result: done. Cards page/card/menu/states/ApiErrorState styled with tokens; `GRID_CSS` export and all `<style>`/inline styles removed (only `position: relative` in CardMenu wrapper; Sparkline untouched).
Files: scenarios.css (new, ~75 lines), ScenariosPage, ScenarioCard, CardMenu, ViewToggle, states, ApiErrorState, ScenarioCard.test, test/setup.ts (+scenarios.css?raw).
Checks: tsc exit 0; vitest 13 files / 80 tests pass (ScenarioCard test gained chip-warn + headline assertions).
Deviations: NoBars has no second Add button (header Add is already disabled; a duplicate broke the existing "single Add button" test). Stale as-of chip uses `isStale` from FreshnessChip.
Tester: check 1/2/3 columns at 375/800/1280 in Chromium; node_modules in the worktree is a symlink to FE-guards (untracked).
Outside-set edits: none.
