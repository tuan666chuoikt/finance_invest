# 3-build AI-rw-bench-na
Result: done. Bench takes `buy` (r.dates.buy); n/a branch: first_available null -> bench_na_nodate; > buy -> bench_na (dated); else new `card.bench_na_gap` (vi/en).
Files: ScenarioCard.tsx, ScenarioCard.test.tsx, i18n/vi.json, i18n/en.json (+20/-6).
Contract: analytics.md §2.4 first_available unchanged.
Checks: vitest scenarios 6 files / 47 tests pass; tsc --noEmit exit 0 (no lint script in apps/web).
Tests: dated test now uses first_available 2026-10-13 (> buy 2026-10-12); new gap test (fixture 2014-10-06) asserts wording, no date.
Deviations / outside-set edits: none. npm ci run in worktree (node_modules untracked).
