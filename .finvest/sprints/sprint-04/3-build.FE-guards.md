# 3-build FE-guards (F-132)
Result: DONE. Files: apps/web/src/styles/guards.test.ts (new, ~35 lines).
Tests: (1) every var(--x) in src (non-test, non-tokens.css) is declared in the light block; (2) every light #/rgb token has a dark value; (3) body rule uses var(--font-sans), --font-sans starts with system-ui, no css font-family has bare serif.
Checks: npm test 14 files / 83 tests pass; tsc 0; lint 0.
Deviation: jsdom drops the `font` shorthand containing var(), so getComputedStyle(body).fontFamily is '' ; the test reads the body rule text instead.
## Proof (token removed)
Deleted `--chart-line` from tokens.css light block, test failed:
`AssertionError: undefined tokens: --chart-line in /src/features/scenarios/Sparkline.tsx`
Restored with git checkout; green again.
## Outside-set edits
none
