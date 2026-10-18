# 3-build FE-web-scaffold (F-031)

Result: DONE. `apps/web` scaffold built per task card; branch task/sprint-03/FE-web-scaffold.

Files: all in the card's file set under `apps/web` plus `package-lock.json`. Extra: `tsconfig` types vitest globals.
Versions (Node 18): vite 5, vitest 2, react 18, react-router 6, react-query 5, i18next 23 / react-i18next 14 (v23 keeps `returnNull`), jsdom 25.

What changed: ROUTES table + redirect `/`→`/scenarios`, App (QueryClient retry 1 / stale 30 s), minimal TopBar, i18n (default vi, `finvest.lang`, `<html lang>` synced),
formatters, `api()` + `ApiError` (`UNREACHABLE` on network failure), en/vi json with `error.*` for platform.md §1.3 codes + `NO_DATA` (§2.5) + `UNREACHABLE`.

Contract honored: platform.md §1.2 (decimal strings, no float math in `formatPct`: BigInt half-away rounding), §1.3, §2.5 same-origin `/api`.
Negative pct uses U+2212 (`−2,83 %`); zero after rounding has no sign. `parseVndInput("")` returns null.

Checks: typecheck exit 0; `npm test` 8 passed (2 files); `npm run build` exit 0; `vite` dev served `/scenarios` HTTP 200.

Deviations:
- Vite proxy does NOT strip `/api` (API is mounted under `/api`, platform.md §1.1); the card said only `/api → 127.0.0.1:8000`.
- `gen` script exists but `packages/contracts/openapi.json` / `types.ts` come from BE-contracts-ts; client.ts does not import types.ts.
- i18n test also statically scans src for literal `t('key')` to fail on keys absent from both files.
Outside-set edits: none.
Tester notes: the language buttons are `aria-pressed`; no e2e in this task.
- Size: 412 insertions vs ~230 planned (en/vi json and tests are ~170 of it); over 1.5x by raw count.

## Fix round 1
Only must-fix was the skipped size stop (412 vs ~230 Size). No code change; wrote 3-consult.FE-web-scaffold.md
justifying the overage (json 56 + tests 62 lines, error.* keys per platform.md 1.3/2.5) and recommending acceptance.
Head unchanged: 570afb19ea8537530307718b86139e2134862c3b. Awaiting plan-owner answer.
