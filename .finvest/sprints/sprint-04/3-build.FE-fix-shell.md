# 3-build FE-fix-shell
Result: BUG-1, BUG-3 (landmark + heading order), BUG-6 fixed. tsc 0; vitest 14 files / 85 tests green. No eslint script in apps/web.
Changes: removed `.band span {inline-block}` (BUG-1); Disclaimer + CrawlStatus now rendered in `Layout` inside `<main>`; TopBar returns only `<header>`; card title h3->h2 (+css); `crawl.error` i18n already carries "✕ ", so dropped the icon span for error.
Design note: `useCrawlJob` state (refused/startError) is local, so it is lifted into `Layout` and passed to `TopBar` as `crawl` prop; `Layout` is exported.
Tests: disclaimer.test (one role=note inside main, starts "ⓘ ", contains "đầu tư · Educational"), TopBar.test (status after disclaimer, inside main), CrawlButton.test (one ✕), ScenarioCard.test (level 2).
Outside-set edits: CrawlButton.test.tsx (renders `<Layout/>` instead of `<TopBar/>`, + ✕ assertion).
Tester: axe region / heading-order on /scenarios. Banner now sits in the .page padding (no longer full-bleed).
