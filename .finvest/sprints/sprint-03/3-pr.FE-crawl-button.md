# 3-pr FE-crawl-button — round 1
Verdict: APPROVE. Head H=cf7ba0b27162455000875dfab21dca49128fb2d2 (already synced with origin/sprint-03, merge was a no-op).
Files reviewed: useCrawlJob.ts, CrawlButton.tsx, CrawlStatus.tsx, TopBar.tsx, CrawlButton.test.tsx, TopBar.test.tsx, i18n en/vi.
Size: 325 changed vs 220 budget, cap 330 (1.5x): within. Contract: 404->null, 409 details.started_at, 2000 ms poll only while running, bars-status invalidated, JOB_RUNNING rename. Tests cover each acceptance item (idle/poll/progress/done numbers/failed/409 once/reload recovery/tab order).
Checks: tsc exit 0; vitest 12 files / 73 tests passed (incl. i18n parity). e2e not run (no new journey; unit-level PR).
Nits: done job on load shows only as tooltip (documented deviation, acceptable); formatDuration local to CrawlStatus; Rec=any needs eslint comment (present).
Merge sha: a2c9bc472d1002a096d8561bbf5d5bf73a4b1dc9
