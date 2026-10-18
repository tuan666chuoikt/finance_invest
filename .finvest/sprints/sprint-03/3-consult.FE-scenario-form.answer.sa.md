# 3-consult FE-scenario-form — architect answer

Decision: **A — accept 442 as-is.** No trim, no split.

Why (2-tech-plan.md lines 336-363): every file in the diff is named in the card's Files line (lines 338-341) —
api.ts with all six hooks including `useWhatIf`/`useDeleteScenario`, `ScenarioForm.test.tsx`, both i18n files.
The Acceptance section (lines 356-362) mandates the combobox, validation, 422-mapping, edit-mode and Esc-focus tests,
so the 122 test lines are required, not padding. Nothing is outside the card: the overage is my estimate's error.

Option B drops mandated coverage (a11y/keyboard) for a number. Option C moves `useWhatIf`/`useDeleteScenario` to
FE-scenario-cards, which already consumes them (lines 374, 381) and runs in the other lane — that only reshuffles
~15 lines and makes the cards task wait on a changed api.ts. Not worth it.

Corrections made (so the lead's size check passes, 442 ≤ 1.5 × 300 = 450):
- `2-tech-plan.md` line 337: Size ~250 → ~300 lines (old copy: `2-tech-plan.prev-1.md`).
- `dag.json`: FE-scenario-form `size` 250 → 300; `dagRev` 3 → 4 (old copy: `dag.prev-1.json`).

Still required before approval: the lead's nit (`color: "crimson"` → theme token) — fix in this PR round.

Note for later estimates (second time, after FE-web-scaffold): an FE task with a component test file plus two locale
files runs ~1.6× the production lines. I will size FE-scenario-cards / FE-scenario-table that way at next revision.
