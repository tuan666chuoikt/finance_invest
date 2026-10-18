# 3-build FE-scenario-form (F-055)
Result: built. Branch task/sprint-03/FE-scenario-form.

## Files
apps/web/src/features/scenarios/{api.ts, ScenarioForm.tsx, SymbolCombobox.tsx, defaultName.ts, ScenarioForm.test.tsx}; i18n en/vi `form.*`.

## What changed
- api.ts: useScenarios, useSaveScenario (POST/PUT, invalidates ["scenarios"]), useDeleteScenario, useSymbolSearch, useSymbol, useWhatIf (types from types.ts + result.ts).
- Form: name (default via defaultName), combobox (listbox, type-ahead, must pick a row), style radios, grouped amount, start (default last - 1 year, clamped to first), end/Today. Non-modal `<dialog open>`: right panel >= 1024 px, full screen below. Enter saves, Esc cancels and refocuses the trigger (captured at mount; first Esc inside an open listbox only closes it). Server errors mapped to field (details.field / SYMBOL_UNKNOWN).
## Contract honored
platform.md 2.5 ScenarioIn body exactly; sell_date null when Today; no money math (formatting only).
## Checks
tsc --noEmit clean; vitest 8 files / 39 tests pass (9 new). No lint script exists in apps/web. No e2e (no route mounts the form yet).
## Deviations / shortcuts
- Below-one-lot hint not live (per plan; `shortcut:` comment in ScenarioForm.tsx).
- Dates use native `<input type="date">` (display follows browser locale, not forced dd/mm/yyyy; values are ISO strings, no Date parsing).
- Start range checked client-side only when symbol detail has bars_1d.
- Size: 442 lines total vs ~250 plan; ~275 excluding tests and i18n.
## Outside-set edits
none.
## Notes for tester
Form is not yet mounted on /scenarios (dashboard task owns the trigger). Props: `<ScenarioForm scenario? onClose />`. Remaining act() warnings in tests are cosmetic.

## Fix round 1
- Size stop: architect answered A (accept 442; plan size raised to ~300) in 3-consult.FE-scenario-form.answer.sa.md; no trim.
- Nit: ScenarioForm.tsx:82 crimson -> var(--color-error, crimson) (no theme token exists yet; same fallback pattern as Sparkline).
