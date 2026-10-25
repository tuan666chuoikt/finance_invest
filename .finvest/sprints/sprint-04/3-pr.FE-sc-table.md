# 3-pr FE-sc-table round 1
Verdict: APPROVE. Head H=daa37856b96bedd83ff2c872d6c44a2700348218 (synced with origin/sprint-04, chore merge daa3785).
Files reviewed: table.css, ScenarioTable.tsx, ScenarioTable.test.tsx, test/setup.ts (all in plan set). Diff +36/-11 vs ~110 est, no size stop.
Must-fix: none.
Nits: flag cell drops the visible "Gần đúng" word (spec says icon + title/aria-label; ok). Tester to check sticky name col <1024 and dark hover.
Checks: tsc exit 0; vitest 14 files / 85 tests passed (new losing-row "▼ −" + class down test). No e2e suite in apps/web.
Merged into sprint-04: 0b0ad4d2c2c79caa0f9e551517026815283b84af
