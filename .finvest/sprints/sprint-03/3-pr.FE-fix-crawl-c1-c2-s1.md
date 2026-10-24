# 3-pr FE-fix-crawl-c1-c2-s1 round 1
Verdict: APPROVE. Head H=3e48fb9b25c7147d6a11df9f94b6c2c5c42933cf (already up to date with origin/sprint-03). Size +63/-6 vs ~90 est.
Files reviewed (7, all in plan set): useCrawlJob.ts, CrawlStatus.tsx, TopBar.tsx, TopBar.test.tsx, CrawlButton.test.tsx, en.json, vi.json. (CrawlButton.tsx untouched; guard lives in hook handler, fine.)
Findings: C1 maps 500 envelope + UNREACHABLE (client.ts:20) to cause text, 409 path unchanged; C2 ref guard + running/isPending check, test fires 2 same-tick clicks; S1 CSS on .tb button,a.
Nits: none blocking. 
Checks (apps/web): tsc exit 0; vitest 12 files / 76 tests pass. No e2e run (needs browser stack; unit coverage per acceptance).
Merged: 51bea2f51835c50216b8bf64d38cdd6842c81948
