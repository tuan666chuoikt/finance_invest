# 3-build FE-fix-dca-shifts
Result: DONE. DCA shifts (`field` buy_date or contribution) now render as one `dca-shifts` line "... N lần" with a `from → to` list; `after_end` (or `to: null`) shows "bỏ qua". Lump-sum lines unchanged.
Files: ScenarioCard.tsx (local `isBuy` predicate used by buyShifts and per-line filter), ScenarioCard.test.tsx (+1 test, real shape: 4 non_trading + 1 after_end `to:null`; old buy_date test kept).
Checks: tsc exit 0; vitest scenarios 6 files / 52 tests pass. Diff 4 files, +18/-3.
Outside-set edits: i18n vi.json/en.json one key `card.shift_skip` ("bỏ qua"/"skipped").
Deviations: `Shift.to` type left `string` (API may send null; handled with a truthiness check) to avoid touching result.ts. Fixture is built from the API shape in dca.py/golden 006, not a live curl.
Screenshot: not attached; no served build of this branch (stack on :8080 runs main code). Tester FE-shots should verify fe05-widths.mjs DCA lines.

## Fix round 1
Must-fix 1 (screenshot): attached `.finvest/sprints/sprint-05/shots/FE-fix-dca-shifts/dca-card-1280-light.png` (1280 wide, light, vite dev of this branch, ScenarioCard with real API shape: 4 non_trading + 1 after_end). One "Ngày mua dời sang ngày giao dịch kế tiếp: 5 lần" line, expanded list, last row "→ bỏ qua". Temp harness removed; no code change. Merged origin/sprint-05 (head 3c07f77).
