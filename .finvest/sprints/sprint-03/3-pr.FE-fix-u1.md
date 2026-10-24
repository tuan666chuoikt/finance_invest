# 3-pr FE-fix-u1 — round 1
Verdict: APPROVE. Head H=97c73c98e938ec37528396a2f24e6bb9e7ef6ce6 (already up to date with origin/sprint-03).
Files reviewed (6, +23/-2, plan ~60): result.ts, ScenarioCard.tsx, ScenarioCard.test.tsx, ScenarioTable.test.tsx, en.json, vi.json. Size within 1.5x.
Contract: first_available nullable (platform.md 2.5 v1.8); null -> "VN-Index — n/a" en+vi; dated case unchanged. Table never formats first_available, so the test is a regression guard only.
Checks: tsc exit 0; vitest apps/web 11 files / 58 tests passed. No e2e harness in apps/web; the change is render-only, covered by component tests.
Nit/follow-up: the it.fails -> it flip in fe-tester.gaps.test.tsx is not possible (file not on sprint-03); flip it when the tester branch merges.
Merge sha: 7b0411e4688d6dee17efe2c311bdda9a4b067fa2
