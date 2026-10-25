# 3-pr FE-shell - round 1 (fi-tech-lead)
Verdict: APPROVE. Reviewed head H=7b635d21769f05c6f19889c47fc7fe7218efb407 (synced with origin/sprint-04; chore(merge) resolved the setup.ts import/array conflict, both shell and scenarios css kept).
Files reviewed: all 12 (shell.css, TopBar, CrawlButton, CrawlStatus, Disclaimer, FreshnessChip, LangSwitch, routes, main, setup, 2 tests). Size 277+/64- vs ~210 estimate (<1.5x).
Checks: tsc exit 0; vitest 14 files / 84 tests passed (incl. guards.test.ts, disclaimer, TopBar 32px + status-after-disclaimer). Only inline style left is computed status-bar width (allowed). No e2e dir in apps/web; 375 px scrollWidth is the tester's FE-shots.
Must-fix: none. Nits: eslint config absent (pre-existing).
Merge sha: 4f632585e4e5c3e43791b76f3a5f8a118d4d2a77
