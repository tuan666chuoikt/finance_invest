# 3-pr FE-sc-panel round 1
Verdict: APPROVE. Reviewed head 9759eb59e09108bf78ba4f99f50be2414c7565a4 (after chore(merge) of origin/sprint-04: setup.ts import conflict, kept both table.css and panel.css).
Files reviewed: panel.css, ScenarioForm.tsx(+test), SymbolCombobox.tsx, HowComputed.tsx, ScenariosPage.tsx (1-line import), test/setup.ts. Size 128+/64- (~192) vs ~190 est: ok.
Checks: tsc exit 0; vitest 14 files / 85 tests passed (FE kernel; no e2e spec in this PR). node_modules symlink was dangling (FE-sc-table worktree gone), replaced by npm ci (git-ignored).
Must-fix: none. Nits: visual 440px/375px checks left to tester; backdrop shadow shortcut is commented.
Merged: 82824eba07b99d6833dc4870a13a9077b3721626
