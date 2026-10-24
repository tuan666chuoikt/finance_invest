# 3-pr FE-fix-u5-u7 round 1
APPROVE. Head H=e7ae474f13d70d13b67b12ad23bb269f64e55fe4 (synced with origin/sprint-03 via merge commit).
Files reviewed: format.ts, ScenarioCard.tsx, ScenarioForm.tsx, states.tsx, en/vi.json, i18n.test.ts + tests. Size 75/12 vs ~110 budget.
Must-fix: none. Nits: skeleton sr-only span uses position:absolute (fine if .sc-card is relative); axe run not done (not installed).
Checks: tsc exit 0; vitest 11 files / 68 tests passed; no e2e suite exists in apps/web. formatVnd(-19847507) -> "−19.847.507 ₫" verified by test; table uses formatVnd.
Merge sha 7e80f50afe4ee81146bfb7f65921c977367c358d
