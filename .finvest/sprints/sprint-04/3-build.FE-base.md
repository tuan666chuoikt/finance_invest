# 3-build FE-base (F-129)
Result: DONE. Base elements in app.css (links, button/.btn variants, inputs, .seg, .chip, .visually-hidden, focus ring, mobile 40px, reduced motion; dark .btn-primary in media block). ~190 lines added.
Files: apps/web/src/styles/app.css, apps/web/src/styles/app.test.ts (new).
Checks: vitest 13 files / 79 tests pass; tsc --noEmit exit 0.
Deviations: jsdom ignores @media and var(), so the .btn-primary test asserts the light rule text (`background: var(--primary)`) and `:root --primary: #1f5fbf` instead of a computed rgb.
## Outside-set edits
- apps/web/vite.config.ts: `test.css: true`. Without it vitest returns empty text for `?raw` css, so setup.ts mounted no styles and getComputedStyle saw nothing (existing tests were unaffected only because they did not depend on css).
Notes for tester: check /scenarios in a browser, light and dark; button.btn-icon.sm 24px.
