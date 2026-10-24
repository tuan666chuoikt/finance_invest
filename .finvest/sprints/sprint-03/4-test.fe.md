# 4-test FE — sprint-03 (fi-fe-tester)

**Verdict: FAIL** — 1 blocker, 2 major, 4 minor/UX bugs. Branch `test/sprint-03/fe` from origin/sprint-03 (4c5037e).
Numbers: Vitest 12 files / 61 tests green (56 existing + 5 new; 4 of the new are `it.fails` = open bugs). tsc clean.
Real stack (127.0.0.1:8080, headless Chromium via Playwright 1.47 + axe 4.10 installed in /tmp/pw, no sudo needed): `apps/web/e2e/real-stack.mjs` 33 pass / 7 fail (all 7 are bugs below). Screenshots: /tmp/pw/m375.png, m375form.png, pre2025.png.
Created scenarios were all named "E2E …" and deleted (DB list empty afterwards).

## Bugs
| Id | Sev | Owner | What |
|---|---|---|---|
| U1 | **blocker** | build (FE-scenario-cards) + contract | With the real API while VNINDEX bars are empty, `benchmarks[0] = {name:"VN-Index", available:false, first_available:null}`. `ScenarioCard.tsx:29` calls `formatDate(null)` -> TypeError -> the router error boundary replaces the **whole app** with "Unexpected Application Error"; it persists on reload while any saved scenario exists (page unusable until the scenario is deleted via API). `result.ts:23` types `first_available: string` — the API/contract can send null. Repro: save any scenario, open /scenarios. Expected: "VN-Index — n/a" card line (UX: n/a, never crash). Same null risk in ScenarioTable. Vitest: `U1` (it.fails); e2e "U1 unpatched". The rest of the e2e ran with a route patch that only fills first_available. |
| U2 | major (a11y) | build (FE-disclaimer) | axe `region` on every screen: the disclaimer text (`aside role=note`) is outside any landmark. Repro: axe on /scenarios. Vitest `U2` (it.fails). |
| U3 | major (UX) | build (FE-scenario-cards) | The user-given name is not shown on the card (only `aria-label`); header is "FPT · Mua một lần" (UX: card shows name; F-056 "each is a card showing: name"). With 2 FPT scenarios the cards are indistinguishable except by amount. Table does show it. |
| U4 | minor | plan/build | FPT from 2020-01-02 (refused by the engine: VALIDATION no_trading_day_near_buy) is **saved** (POST /scenarios accepts) and the card then says only "Không tính được: Dữ liệu nhập không hợp lệ." — no crash, but the reason (no data for that date) is not stated. Cost: a permanently broken saved scenario. |
| U5 | minor | build | EN pluralisation: "1 sessions missing". Vitest `U5` (it.fails). |
| U6 | minor (a11y) | build | `div.sc-card[data-testid=card-skeleton]` has `aria-label="Loading…"` and no role -> axe `aria-prohibited-attr` (4 nodes while loading). |
| U7 | minor | build | Table "Lãi/lỗ ₫" shows ASCII hyphen `-19.847.507 ₫` while the % column and the card use U+2212 `−`. |
Observation (no bug): `useWhatIf` retry:1 delays a 422 card about 1 s (noted by the builder); DCA HPG card shows the "sẽ tích luỹ đến khi đủ 1 lô" note although shares were bought (flag is from month 1) — correct per the flag, maybe confusing wording.

## Real-stack results (expected vs actual)
| Case | Result |
|---|---|
| Lump-sum FPT 50,000,000 ₫ 2025-03-03 -> today | PASS: 400 shares (API), liquidation **30.152.493 ₫**, P/L **−19.847.507 ₫**, API pl_pct **−39.6950**, card shows `▼ −39,70 %` (2 dp, vi-VN), cash left 6.930.693 ₫, sell date 16/10/2026 (last bar; "today" resolves to the latest stored bar) |
| DCA HPG 2,000,000 ₫/month from 2025-03-03 | PASS (with U1 patch): "Mỗi tháng 2.000.000 ₫ (ngày 3)", invested, value 37.588.232 ₫, P/L −6,03 %, cash left shown, approximate flag |
| Edit (EN UI): 10M -> 50M | PASS: recomputed to 30.152.493 ₫, no duplicate |
| Delete | PASS: confirm dialog -> card gone; list empty after cleanup |
| EN/VI switch | PASS: labels, `<html lang>`, persists on reload; numbers stay vi-VN |
| Disclaimer both lines + approximate flag | PASS on cards (icon + text) and every table row ("Xấp xỉ"); freshness chip shows date + source |
| How-computed panel | PASS: opens from (i), shows formula and rules version, axe clean while open, Esc closes |
| Below one lot (FPT 10,000,000 ₫) | PASS: value 10.000.000 ₫, `= 0 ₫ = 0,00 %`, cash 10.000.000 ₫, note "Ít hơn 1 lô — không mua được cổ phiếu nào" |
| Refused pre-2025 date | PASS no crash; card error "Không tính được: Dữ liệu nhập không hợp lệ." (see U4) |
| 375 px | PASS: no page-level horizontal scroll (cards and table), form fills width |
| axe | form/how-panel/cards: only U2 (`region`) and U6; no contrast or label violations found |
Not checked: visual appearance beyond three screenshots (not reviewed by eye by the agent), dark mode contrast, 768/1024 column counts, 20-scenario <2 s, stale-banner/market-closed states on the real stack (not producible), benchmarks with real VN-Index data (empty), keyboard walk-through beyond Esc/Enter.

## Coverage map (acceptance -> tests)
| Story / criterion | Test |
|---|---|
| F-031 nav + start page /scenarios; chip date | TopBar.test (chip, stale, null), disclaimer.test routes; e2e "freshness chip" |
| F-031 EN/VI persists on reload; labels all switch | TopBar.test (switch, storage, Alt+L); e2e EN/VI + reload |
| F-031 missing key fails suite | i18n.test.ts (parity + static scan) |
| F-032 banner on every analysis route, both lines | disclaimer.test (ROUTES enumeration); e2e disclaimer; **U2** landmark |
| F-055 form fields, defaults, validation messages, server error mapping | ScenarioForm.test (9); e2e create lump/DCA via UI |
| F-055 edit recomputes / delete confirm | ScenarioForm.test edit, ScenariosPage.test menu/delete; e2e edit + delete |
| F-055 refused input shown | ScenarioForm.test (end<start, SYMBOL_UNKNOWN); e2e pre-2025 (U4) |
| F-055 survives restart | not FE (BE); e2e reload shows saved cards |
| F-056 card fields, sign+arrow, approximate flag | ScenarioCard.test; e2e card text; **U3** name |
| F-056 table sortable, flag on rows, footer | ScenarioTable.test; e2e table + axe |
| F-056 empty / no bars / API down / one-card failure / loading | ScenariosPage.test; e2e empty page |
| F-056 mini curve + accessible name | Sparkline.test |
| F-048 benchmark n/a never 0 | ScenarioCard.test; new U1 test (null first_available) |
| F-051 formula, inputs, as-of, rules version, approximate paragraph, every figure | HowComputed.test; e2e panel open/Esc |
| F-056 20 scenarios < 2 s | not tested (no FE perf harness) |
| 375 px / axe | e2e only (jsdom has no layout/axe) |

## Files
`apps/web/src/features/scenarios/fe-tester.gaps.test.tsx` (vitest), `apps/web/e2e/real-stack.mjs` (run: `PW_DIR=/tmp/pw node apps/web/e2e/real-stack.mjs`; Playwright is not an `apps/web` dependency, installed outside the repo).
