# 3-pr FE-scenario-form (round 1) - CHANGES_REQUIRED
Head reviewed H=566ebf4d4ec9d5f640456ec5e4d34accbecbf501 (already synced with origin/sprint-03).
Files reviewed: ScenarioForm.tsx, SymbolCombobox.tsx (size only), api.ts, defaultName.ts, test, i18n en/vi.
Checks: vitest 8 files / 39 tests pass (q.sh exit 0). Code reads correct vs contract (ScenarioIn body, sell_date null on Today).
## Must-fix
1. Size stop skipped (retro S01 R2): shortstat 442 insertions vs plan ~250 (limit 375 = 1.5x), and no 3-consult.FE-scenario-form.md exists.
   Resolve either by trimming the diff to <= 375 lines (tests+i18n count) or by writing 3-consult.FE-scenario-form.md and getting the architect's answer. Dev's note "275 excl. tests/i18n" does not replace a consult.
## Nits
- Hard-coded `color: "crimson"` in ScenarioForm.tsx:82 ignores dark mode; use a token if one exists.

# 3-pr FE-scenario-form (round 2) - APPROVE
Head reviewed H=72ac7e053d7598dcd2ed6586940850f1c91fd799 (synced with origin/sprint-03, already up to date).
Files reviewed: ScenarioForm.tsx, api.ts, defaultName.ts (full); SymbolCombobox, test, i18n by size/round 1.
Round 1 must-fix 1 resolved: 3-consult.FE-scenario-form.answer.sa.md accepts 442 lines; plan Size now ~300 (limit 450), shortstat 442 insertions.
Round 1 nit (crimson) fixed in 72ac7e0: var(--color-error, crimson).
Checks: vitest 8 files / 39 tests pass (q.sh exit 0); tsc --noEmit exit 0. No e2e spec for this task.
Nits: none blocking.
Merge sha: 3b4bf5cd022f93cc7206f2a2df056410a914ef36
