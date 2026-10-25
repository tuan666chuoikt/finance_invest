# 3-pr AI-rw-bench-na
## Round 1 — APPROVE (head 34383caa8167574ff82e6941192c52ef5eeef946)
Files reviewed: ScenarioCard.tsx, ScenarioCard.test.tsx, vi.json, en.json (+20/-6, plan ~40; no outside edits). Synced with origin/sprint-04 (merge clean).
Logic matches plan: null -> nodate; first_available > buy -> bench_na; else new bench_na_gap (vi/en text exact). Tests: dated case moved to post-buy date; new gap test fails without change.
Must-fix: none. Nits: none.
Checks: vitest scenarios+i18n 7 files/50 pass; full web vitest 12 files/77 pass; tsc exit 0. No e2e spec touches bench lines.
Re-sync: sprint-04 moved (AI-rw-curve, python only); re-merged clean, web vitest 77 pass, tsc 0. Final reviewed head e634254ace695703d06496a8f281004b69252a1a.
Merged: ee8cc9832f3c6bc286dad850b3475cb374f5945d
