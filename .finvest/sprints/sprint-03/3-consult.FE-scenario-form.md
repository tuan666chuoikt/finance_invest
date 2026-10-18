# Consult FE-scenario-form (size stop)
Diff vs origin/sprint-03: 442 insertions (limit 1.5 x ~250 = 375). Breakdown: ScenarioForm.tsx 132, SymbolCombobox.tsx 80, api.ts 57, test 122, i18n 48, defaultName 5. Excluding test+i18n: 274.
## Question
Accept the overrun, or split?
## Options
A. Accept 442 (tests + both-language i18n account for 170; production code ~274 is within plan).
B. Trim to <=375: would need cutting ~67 lines, i.e. about half the tests (a11y/keyboard cases) or the api.ts hooks (useWhatIf/useDeleteScenario) that sibling tasks may own. Risky for quality.
C. Split: move api.ts hooks not used by the form into the task that consumes them.
## Recommendation
A. Plan size did not count tests/i18n; trimming means dropping coverage. Nit (crimson colour) will be fixed on approval.
