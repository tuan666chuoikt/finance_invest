# 3-build FE-fix-u2-u3 (F-032 RW-U2, F-056 RW-U3)
Result: done. tsc exit 0; vitest 11 files / 62 tests pass.
Changes: Disclaimer now has aria-label (key disclaimer.name, en+vi) and renders inside <main> (Layout moved it). ScenarioCard header is <h3>{name || defaultName(...)}</h3> with symbol · style in <small> below; article aria-label removed.
Tests: ScenarioCard (two names via heading role, unnamed fallback), disclaimer.test (inside main on every analysis route).
## Deviations
- Kept role="note" (not complementary): axe rule landmark-complementary-is-top-level flags a complementary nested in main; a note inside main has no region violation.
- No axe in deps and fe-tester.gaps.test.tsx does not exist on sprint-03, so no axe run; containment asserted via closest("main"). Gaps test U2 -> `it` not done (file absent).
## Outside-set edits
- apps/web/src/app/routes.tsx (Layout lives here, not App.tsx): Disclaimer moved inside <main>.
