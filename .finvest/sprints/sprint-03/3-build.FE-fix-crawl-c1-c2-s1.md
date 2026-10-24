# Build FE-fix-crawl-c1-c2-s1
Result: done. C1 start failure shows cause (envelope message, or "cannot reach the server"); C2 ref-based guard in the start handler (one POST for two same-tick clicks); S1 `.tb button,.tb a{min-height:24px;min-width:24px}`.
Files: useCrawlJob.ts (startError, inflight ref), CrawlStatus.tsx (startError prop), TopBar.tsx (CSS + prop), en/vi.json (crawl.start_failed, crawl.unreachable), CrawlButton.test.tsx (+2 tests), TopBar.test.tsx (+1 test).
Checks: tsc exit 0; vitest 12 files / 76 tests pass. No eslint config in apps/web (no lint script). Diff +63/-6.
Notes for tester: the language switch renders 3 buttons total in the bar (Menu, crawl, language), test asserts >= 3. startError is cleared on the next successful start only. node_modules in the worktree is a symlink to test-fe-03's (untracked).
