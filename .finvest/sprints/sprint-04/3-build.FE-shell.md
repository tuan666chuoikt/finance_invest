# 3-build FE-shell (F-130)
Result: done. Inline CSS/`style=` removed from shell components; `shell.css` holds top bar, band, status, chip-short/long, menu sheet.
Files: styles/shell.css (new), TopBar, CrawlButton, CrawlStatus, Disclaimer, FreshnessChip, LangSwitch, routes.tsx, test/setup.ts, TopBar.test.tsx.
Behaviour: TopBar returns header + Disclaimer (analysis routes) + CrawlStatus; `main.page`. Status gets status-running/done/error, spinner, 3px bar (computed width), error parts in `<code>`.
Checks: tsc exit 0; vitest 13 files / 81 tests passed. eslint: repo has no eslint config (flat-config error), not run.
Deviations: menu button has aria-label + aria-hidden "☰" (tests query `.tb-menu` since jsdom display:none hides it from role queries). Chip: stale "⚠ " prefix only on the short span (long text already contains "⚠" from chip.stale). Short chip text = dd/mm hh:mm derived from formatDateTime. Status "Chi tiết" link not added (not in the card).
## Outside-set edits
- src/main.tsx: import shell.css.
- src/app/disclaimer.test.tsx: "inside main landmark" test now asserts band is outside and before main (spec: full-width band).
## Notes for tester
CSS media rules are not run by jsdom: check 375 px one-row bar, scrollWidth<=375, menu sheet, icon-only crawl button in Chromium (FE-shots).
