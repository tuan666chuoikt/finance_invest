# 3-build FE-fix-u5-u7
Result: done. Branch task/sprint-03/FE-fix-u5-u7. Diff vs origin/sprint-03: 10 files, +75/-12 (budget ~110).

## Changes
- format.ts: formatVnd emits U+2212 for negatives; ScenarioCard signedVnd reuses it; table P/L goes through formatVnd.
- states.tsx: skeleton is role="status" aria-busy with visually hidden "Đang tải…", no aria-label.
- Plural: card.missing_one/_other (EN 1 session / N sessions; VI same text in both).
- error.NO_DATA_before ("No {{symbol}} data before {{date}}"): form (422 -> start-date field, input kept) and card (details.first_available).
- Tests: format.test, ScenarioCard.test (NO_DATA, plural x2, no ASCII hyphen before digit, skeleton), ScenarioForm.test (NO_DATA).

## Checks
tsc exit 0; vitest 11 files, 68 tests passed (whole web package, it is small).

## Deviations
- Key is card.missing_* (real key), not chip.sessions_missing_*.
- fe-tester.gaps.test.tsx does not exist on sprint-03; U5 tests added to ScenarioCard.test.tsx instead.
- axe not installed; skeleton checked by role/attribute assertions only, not an axe run.

## Outside-set edits
- src/i18n/i18n.test.ts: literal-key scan accepts `<key>_other` plural keys (one line).

## Notes for tester
Real axe pass on the skeleton is still worth one run. "No FPT data before" uses the form's selected symbol.
