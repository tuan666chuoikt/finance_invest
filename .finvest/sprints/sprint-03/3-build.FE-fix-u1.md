# 3-build FE-fix-u1
Result: DONE. Benchmark `first_available` is now nullable; null renders "VN-Index — n/a" (en and vi) on the card.
Files: result.ts (type), ScenarioCard.tsx (branch), i18n en/vi `card.bench_na_nodate`, ScenarioCard.test.tsx, ScenarioTable.test.tsx (+1 test each).
Table: ScenarioTable.bench() already returned "n/a" for `available:false` and never formats first_available, so no prod change there.
Checks: tsc exit 0; vitest scenarios 6 files / 37 tests passed.
Deviations: `fe-tester.gaps.test.tsx` does not exist on origin/sprint-03 (tester branch unmerged), so the U1 `it.fails` -> `it` flip was not done; flip it when that file lands.
Outside-set edits: none. Notes: no error boundary added (out of listed change).
