# 3-build FE-crawl-button (F-034)
Result: DONE. Branch task/sprint-03/FE-crawl-button, head cf7ba0b27162455000875dfab21dca49128fb2d2 (branch-only, no gh).
Files: app/useCrawlJob.ts, components/CrawlButton.tsx, CrawlStatus.tsx, TopBar.tsx (button before LangSwitch, status line in header, full width), CrawlButton.test.tsx (4 tests), TopBar.test.tsx (jobs 404 in mock + tab order), i18n en/vi (crawl.*, JOB_ALREADY_RUNNING renamed JOB_RUNNING).
Contract: platform.md 2.6 / 1.3 v1.9; 404 on /jobs/current -> null; 409 reads details.started_at; poll 2000 ms only while running; bars-status invalidated when a job is no longer running.
Checks: tsc clean; vitest 12 files / 73 tests green (incl. i18n parity). No lint script exists in apps/web. Size 325 lines changed (budget 220, cap 330; ~60 are i18n JSON).
Deviations: a done job found on load is not shown in the status line (only in the button tooltip); it shows when the job was seen running this session. Failed jobs always show. formatDuration is local to CrawlStatus (needs t), not in lib/format.ts. Job.progress/summary/error are untyped JSON in the generated types, so CrawlStatus reads them as loose records. "Chi tiet" link not built (out of scope).
Outside-set edits: none.
Tester notes: skipped count = ticks.symbols_skipped + bars_1d.symbols_skipped; partial shows "(một phần, đến HH:mm)".
