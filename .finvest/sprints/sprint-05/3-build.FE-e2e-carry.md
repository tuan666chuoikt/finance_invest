# 3-build FE-e2e-carry
Result: apps/web/e2e (screens, real-stack, crawl-button, w768 .mjs) copied verbatim via `git checkout origin/test/sprint-04/fe -- apps/web/e2e`; `e2e:shots` script added to apps/web/package.json.
Checks: `node --check` on all 4 files OK; `git diff origin/test/sprint-04/fe -- apps/web/e2e` empty (0 diff). No src change, so `npm test` is unaffected (not run: apps/web has no node_modules in this checkout, vitest not found).
Deviations: none. Outside-set edits: none. UI screenshot: n/a (no UI change; this task only ships the script).
Tester note: run `PW_DIR=/tmp/pw BASE=... OUT=... npm run e2e:shots`.
