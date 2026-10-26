# 3-build FE-crawl-step3 (F-014)

Result: DONE. Branch task/sprint-05/FE-crawl-step3. Diff vs origin/sprint-05: 5 files, +76/-15 (plan ~120).

## Changes
- CrawlStatus.tsx: step 3 label/unit (`crawl.step3`, unit symbols); `stepParts()` shared by done and failed lines
  (ticks, sessions, events when `corporate_actions` non-null); done adds skipped, deferred (`bars_1d.symbols_deferred + corporate_actions.symbols_deferred`, only > 0), duration.
  Failed with `summary.bars_1d` keeps steps 1-3 parts before the error line; `source: vci_iq` renders "VCI IQ".
- i18n en/vi: crawl.step3, crawl.done.events, crawl.done.deferred.
- CrawlButton.test.tsx: step 3 running (vi/en), spec-sample done line (events 3, changes 1, deferred 12), deferred 0 and corporate_actions null cases, failed step 3 + VCI IQ, crawl.* key parity.
- screens.mjs (f): running mock at step 3 (18/40), failed/done mocks with new summary.

## Checks
- vitest apps/web: 14 files, 91 tests passed. tsc --noEmit: exit 0. No eslint config in repo (lint not run).
- screens.mjs on vite dev (5199, real api proxy): crawl-running/failed PASS incl. axe contrast, no overflow.

## Deviations
- `crawl.done.deferred` text has no leading "· " (parts are already joined with " · "; a leading dot would double it).
- en step unit stays "symbols" (existing key), not "names".
- Failed step-3 line repeats ticks info with the existing "saved x/y symbols" tail; left as is.

## Notes for tester
Shots: shots/FE-crawl-step3/crawl-running-1280-light.png, crawl-failed-1280-light.png. Done state is not in the screens.mjs loop
(shown only after a running state), so no done shot; covered by vitest.
