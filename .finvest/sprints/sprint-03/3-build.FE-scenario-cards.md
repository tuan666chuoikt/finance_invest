# 3-build FE-scenario-cards (F-056 / F-055 / F-048)

**Result:** DONE. Branch `task/sprint-03/FE-scenario-cards` from `origin/sprint-03` (58156bb). No unmerged task branch touched these files.

## Files
- New: `features/scenarios/{ScenariosPage,ScenarioCard,CardMenu,states}.tsx`, `ScenariosPage.test.tsx`, `ScenarioCard.test.tsx`
- Edited: `app/routes.tsx` (mount at `/scenarios`), `i18n/{en,vi}.json` (keys `page.*`, `card.*`)

## What changed
- Page: header (title, + Add, Cards/Table toggle with Table disabled until FE-scenario-table, "Dữ liệu đến dd/mm/yyyy · nguồn VCI"), 3/2/1 grid (CSS media queries 1024/768), plain `N` hotkey (ignored in fields, with modifiers, while the form is open or No-bars).
- States: skeletons, Empty (with example), NoBars (`make backfill`, Add disabled), UNREACHABLE -> `ApiErrorState` with `refetch`, other list errors -> `error.<code>` + retry.
- Card: one `useWhatIf` each; skeleton; error -> "Không tính được: <error.code>" + Edit; success -> header (lump / DCA "Mỗi tháng … (ngày N)", day from `buy_date`), dates + shift notices, `approximate-flag`, invested, value if sold (i), P/L VND and % with arrow, sign, colour, cash left, Sparkline, benchmark lines (available / n/a with date / none), missing-sessions note, `below_one_lot` note.
- CardMenu: ⋯ with Edit / Delete, arrow keys, Esc returns focus; Delete confirm dialog -> `useDeleteScenario`.

## Contract honored
Types from `result.ts` / `api.ts`; no money math (only string formatting; sign taken from the string). Dates via `formatDate` (no `new Date`).

## Checks
- `q.sh web-tsc`: exit 0. `q.sh web-test` (vitest run, whole web side, includes i18n key parity and disclaimer-on-routes): 10 files, 52 tests passed (13 new).
- No lint script exists in `apps/web`. No e2e spec written (task lists unit tests only).
- Size: 258 non-test non-json lines vs ~250 planned.

## Deviations / shortcuts
- Missing-sessions `(i)` is a native `<details>` (a `InfoButton` needs a Figure with `how`; `missing_sessions` is a plain date list).
- VN-Index "non-investable" is a `title` tooltip only (as UX says "in its tooltip"); no keyboard-reachable equivalent.
- `below_one_lot` note has no amount: the success envelope carries no `details.min_amount`.
- Dark/light colours for up/down/zero via `prefers-color-scheme`, no shared theme tokens exist yet.
- Stale chip beyond the shell's, delisted note, sorting: out of scope as planned.

## Outside-set edits
None.

## Notes for the tester
- `useWhatIf` inherits the app QueryClient `retry: 1`, so a 422 card shows its error about a second late in the real app. Consider `retry: false` for `ApiError` status < 500 in `api.ts` (not in my file set).
- jsdom does not do layout: the 3/2/1 columns are untested; check at 1024 / 768 / 360 px in a browser.
