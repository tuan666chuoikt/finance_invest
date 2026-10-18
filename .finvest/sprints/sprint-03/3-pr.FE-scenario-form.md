# 3-pr FE-scenario-form (round 1) - CHANGES_REQUIRED
Head reviewed H=566ebf4d4ec9d5f640456ec5e4d34accbecbf501 (already synced with origin/sprint-03).
Files reviewed: ScenarioForm.tsx, SymbolCombobox.tsx (size only), api.ts, defaultName.ts, test, i18n en/vi.
Checks: vitest 8 files / 39 tests pass (q.sh exit 0). Code reads correct vs contract (ScenarioIn body, sell_date null on Today).
## Must-fix
1. Size stop skipped (retro S01 R2): shortstat 442 insertions vs plan ~250 (limit 375 = 1.5x), and no 3-consult.FE-scenario-form.md exists.
   Resolve either by trimming the diff to <= 375 lines (tests+i18n count) or by writing 3-consult.FE-scenario-form.md and getting the architect's answer. Dev's note "275 excl. tests/i18n" does not replace a consult.
## Nits
- Hard-coded `color: "crimson"` in ScenarioForm.tsx:82 ignores dark mode; use a token if one exists.
