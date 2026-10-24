# Sprint 03 — Tech plan (FE / BE / API / ops)

Owner: `fi-software-architect`, 2026-10-18, plan v1.0. Inputs: `1-sprint-plan.md`, `2-tech-plan.ai.md` (5 AI-side blocks +
notes N1–N5; merged into `dag.json` here), `product/ux/app-shell.md`, `product/ux/scenario-dashboard.md`,
`contracts/platform.md` **v1.5** (§2.5 written for this sprint; v1.4 = `platform.prev-5.md`), `contracts/analytics.md` v1.1
§2.4, `data.md` v1.1 (`scenarios` table), `codebase.md` v1.1, ADR-S-004, origin/sprint-02 head `50dce14` (bars_1d_src,
index_1d, symbols, finvest_rules.calendar).

## Decisions for this sprint

- **Web stack = ADR-S-004**: React 18 + Vite + TypeScript, TanStack Query, i18next (`en.json`/`vi.json`, key-parity test),
  Vitest + Testing Library (jsdom). Sparkline = inline SVG (no chart lib yet). TanStack Table only in the table task.
  `apps/web/package.json` is self-contained (codebase.md §1). No Playwright in S03 — route/state tests are Vitest;
  axe/e2e start in S04.
- **Same-origin API** (platform.md §2.5): the web calls `/api`; Vite proxies to `127.0.0.1:8000`, prod nginx on
  `127.0.0.1:8080` proxies `/api/` to `api:8000`. Nothing binds beyond loopback (A23 pending → loopback is the default).
- **Saved scenarios store inputs only**; the web runs one `POST /api/whatif` per saved row, so one failing row is one
  failing card and no result table is needed (platform.md §2.5). The N2 budget (20 × 10-year < 2 s) is measured in the API
  test on the server side.
- **`SqlMarketView` lives in `apps/api`** (not `packages/market_data`, N1's suggestion): the market-data context must not
  import `finvest_analytics` (codebase.md §2 dependency rule); the API is the composition layer that sees both.
- **Calendar outside `holidays.csv`** (2025–2026 only, `finvest_rules.calendar.CalendarNotMaintained`): the view serves
  VNINDEX bar dates from `index_1d` for those years (data.md §1.2 V2: VNINDEX daily since 2004-01-05, one bar per
  session). A 10-year scenario therefore never fails on the calendar and holidays do not show as missing sessions.
- **Types**: `packages/contracts/openapi.json` is exported from the FastAPI app and `apps/web/src/api/types.ts` is
  generated with `openapi-typescript` (`npm run gen`); a kernel test fails when the committed export is stale. The what-if
  **result** is a plain dict in the engine (AI plan), so the web types it by hand from analytics.md §2.4 in
  `features/scenarios/result.ts` (FE-how-computed) — one normative source, two renderings.
- **Error envelope** platform.md §1.3 + §2.5 mapping; the web maps `error.code` to `error.<code>` i18n keys.
- **Sizes** count prod + test (+ migration) lines; generated files (`types.ts`, `openapi.json`, lockfiles) are excluded.
  Lead `opus` only on contracts/API/money/ops blocks (owner.md).

## Order and lanes

```
BE-1  BE-api-symbols-bars → BE-scenarios-api → BE-contracts-ts → BE-whatif-api
BE-2  BE-rules-costs (ai plan) ∥ S-etf-bars → BE-market-view (after AI-analytics-scaffold)
AI-1  AI-analytics-scaffold → AI-whatif-lumpsum → AI-whatif-dca → AI-whatif-benchmarks
FE-1  FE-web-scaffold → FE-shell-bar → FE-scenario-cards → FE-scenario-table
FE-2  FE-disclaimer → FE-how-computed → FE-sparkline → FE-scenario-form (after BE-contracts-ts)
OPS   OPS-web-compose (after FE-web-scaffold)
BE-3  FIX-ticks-probe ∥ FIX-index-value (sprint-02 B1/B2, start now; AI-whatif-benchmarks after FIX-index-value)
      → FIX-whatif-empty-history ∥ FIX-symbols-exact-first (LIVE-03 smoke, everything merged; start now)
```
Start immediately (sprint-02 merged): BE-api-symbols-bars, BE-rules-costs, S-etf-bars, AI-analytics-scaffold, FE-web-scaffold.
M1 = scaffold + shell + rules + symbols API. M2 = engine + market view + what-if API. M3 = scenarios CRUD + form + cards +
table + banner + compose. M4 = benchmarks + how-computed. First to slip (1-sprint-plan): AI-whatif-benchmarks + S-etf-bars,
then FE-scenario-table.

## BE / API tasks

#### BE-api-symbols-bars — F-055/F-031 support: `GET /api/symbols`, `GET /api/symbols/{symbol}`, `GET /api/bars/1d/status`
- Story: F-055 ; Side: be ; Effort: medium ; Size: ~200 lines ; Lead: opus
- Files: `apps/api/finvest_api/deps.py` (new: `get_engine` moved here), `apps/api/finvest_api/errors.py` (new),
  `apps/api/finvest_api/routes/__init__.py`, `apps/api/finvest_api/routes/symbols.py`, `apps/api/finvest_api/routes/bars.py`,
  `apps/api/finvest_api/main.py` (import `get_engine` from deps, `include_router` ×2), `apps/api/tests/test_health.py`
  (import path), `apps/api/tests/conftest.py` (SQLite in-memory engine via `tables.metadata.create_all` + `TestClient`
  with `get_engine` override), `apps/api/tests/test_symbols.py`, `apps/api/tests/test_bars_status.py`
- Change:
  - `errors.py`: `ApiError(code, status, message, details={})` exception + FastAPI handler → platform.md §1.3 body; handler
    for `RequestValidationError` → 400 `VALIDATION` with `details.field` = first error `loc[-1]`.
  - `routes/symbols.py`: `GET /api/symbols?q=&limit=20&include_delisted=false` — `q` upper-cased prefix on `symbol` OR
    `ILIKE %q%` on `name_vi`/`name_en`; `limit` 1–200; order `symbol`; fields per platform.md §2.5. `GET /api/symbols/{symbol}`
    → record + `bars_1d: {first, last, as_of} | null` (`min/max(trading_date)`, `max(fetched_at)` from `bars_1d_src`);
    unknown → 404 `NOT_FOUND`.
  - `routes/bars.py`: `GET /api/bars/1d/status` → `{last_trading_date, as_of, source: "vci", symbols}`; empty table → nulls, 0.
  - Timestamps serialised with `+07:00` offset (ADR-S-006; `astimezone(ZoneInfo("Asia/Ho_Chi_Minh"))`); dates ISO.
  - Pydantic response models in each route module (they feed the OpenAPI export in BE-contracts-ts).
- Contract: platform.md §1.2 (time, snake_case), §1.3, **§2.5** rows 1–3; data.md §3 `symbols`, `bars_1d_src`; ADR-S-006.
- Acceptance:
  - SQLite fixture with `FPT`, `FPTX` (delisted), `VNM`, 3 `bars_1d_src` rows for FPT (two `fetched_at` for the same date):
    `?q=fp` → `[FPT]`; `?q=fp&include_delisted=true` → `[FPT, FPTX]`; `?q=sữa` matches `VNM` by `name_vi`; `?limit=0` → 400.
  - `/api/symbols/FPT` → `bars_1d.first == "2026-10-14"`, `last == "2026-10-16"`, `as_of` ends with `+07:00`;
    `/api/symbols/VNM` → `bars_1d: null`; `/api/symbols/ZZZ` → 404 body `{"error": {"code": "NOT_FOUND", …}}`.
  - `/api/bars/1d/status` → `symbols == 1`, `last_trading_date == "2026-10-16"`; empty table → `{null, null, "vci", 0}`.
  - `/api/health` test still green; `make test-kernel` green (no `db` mark needed: plain SQL only).
- Out of scope: `index_memberships` on the symbol record, pagination cursors, `GET /bars/1d` series (F-012 API, S04),
  data-quality endpoints.

#### BE-scenarios-api — F-055: `scenarios` table + CRUD routes
- Story: F-055 ; Side: be ; Effort: medium ; Size: ~230 lines ; Lead: opus
- Files: `apps/api/migrations/versions/0006_scenarios.py`, `apps/api/finvest_api/scenarios/__init__.py`,
  `apps/api/finvest_api/scenarios/tables.py` (own `MetaData`, SQLAlchemy Core table), `apps/api/finvest_api/scenarios/schemas.py`
  (`ScenarioIn`, `Scenario`), `apps/api/finvest_api/routes/scenarios.py`, `apps/api/finvest_api/main.py` (`include_router`),
  `apps/api/tests/conftest.py` (also `create_all` the scenarios metadata), `apps/api/tests/test_scenarios.py`
- Change:
  - Migration `0006` = data.md §3 `scenarios` DDL (raw SQL like `0005`; `downgrade` drops the table).
  - `ScenarioIn` validators per platform.md §2.5: `name` 1–60 (strip), `symbol` 1–12 upper-cased, `style` literal,
    `amount_vnd: int` `ge=1 le=100_000_000_000` (reject floats/strings with decimals), `sell_date >= buy_date` else 400
    `VALIDATION` `details.field == "sell_date"`.
  - Routes: `GET` (newest first), `POST` 201, `PUT` 200 full replace + `updated_at = now()`, `DELETE` 204; unknown id → 404
    `NOT_FOUND`; symbol absent from `symbols` (any `is_delisted`) → 422 `SYMBOL_UNKNOWN` `details.symbol`.
  - Timestamps stored UTC, serialised `+07:00` (ADR-S-006).
- Contract: platform.md §1.3, **§2.5** (`ScenarioIn`, `Scenario`, validation bullets); data.md §3 `scenarios`; UX
  scenario-dashboard.md "Form (add / edit)" validation column; ADR-S-006.
- Acceptance:
  - Create FPT lump sum 10,000,000 from 2025-10-12, `sell_date: null` → 201 with `id`, `symbol == "FPT"` from input `"fpt"`;
    `GET` lists it first after a second create; `PUT` changes `amount_vnd` and bumps `updated_at`; `DELETE` → 204 then 404.
  - 400 cases with `details.field`: `name` 61 chars, `amount_vnd: 0`, `amount_vnd: 1e11 + 1`, `amount_vnd: "10,000,000"`,
    `sell_date < buy_date`. 422 `SYMBOL_UNKNOWN` for `"ZZZ"`; delisted `FPTX` is accepted.
  - Restart persistence is the migration's job: `alembic upgrade head` then `downgrade -1` round-trips on the compose db
    (`db`-marked test, skipped without `FINVEST_DATABASE_URL`).
- Out of scope: stored results, re-run/journal (analytics.md §4, R4), pagination, several symbols per scenario (F-089).

#### BE-contracts-ts — OpenAPI export → `packages/contracts/openapi.json` → `apps/web/src/api/types.ts`, drift test
- Story: F-031 ; Side: be ; Effort: medium ; Size: ~80 lines (+ generated) ; Lead: opus
- Files: `apps/api/finvest_api/export_openapi.py` (`python -m finvest_api.export_openapi [--check]`),
  `packages/contracts/openapi.json` (generated, committed), `packages/contracts/README.md` (5 lines: how to regenerate),
  `apps/web/src/api/types.ts` (generated by `npm run gen`, committed), `apps/api/tests/test_openapi_current.py`
- Change:
  - `export_openapi.py`: `app.openapi()` → `json.dumps(sort_keys=True, indent=2, ensure_ascii=False) + "\n"` to
    `packages/contracts/openapi.json`; `--check` exits 1 with a diff summary when the file differs.
  - `make contracts` (target added by OPS-web-compose) = export + `npm --prefix apps/web run gen` (`openapi-typescript
    ../../packages/contracts/openapi.json -o src/api/types.ts`; the script and dev dependency come from FE-web-scaffold).
  - `test_openapi_current.py`: the in-process schema equals the committed JSON (message: "run `make contracts`").
  - Run both generators once and commit the outputs; `types.ts` must contain `components["schemas"]["Scenario"]`,
    `ScenarioIn`, `SymbolOut`, `BarsStatus`.
- Contract: codebase.md §1 (`packages/contracts`), §6 "Export contracts" row; platform.md §2.5; system.md `packages/contracts` row.
- Acceptance: `uv run python -m finvest_api.export_openapi --check` exits 0 on the branch; editing a response model
  without re-exporting makes `test_openapi_current` fail; `npm --prefix apps/web run typecheck` passes with the
  generated file; `types.ts` has the four schemas above.
- Out of scope: typing the what-if result (plain dict; web hand-types it from analytics.md §2.4), publishing a client
  package, CI wiring beyond the kernel test.

#### BE-market-view — N1: `SqlMarketView` over `bars_1d_src` / `index_1d` / calendar for the engine
- Story: F-040 ; Side: be ; Effort: high ; Size: ~170 lines ; Lead: opus
- Files: `apps/api/finvest_api/market_view.py`, `apps/api/tests/test_market_view.py`, `apps/api/tests/test_market_view_db.py`
  (`db`-marked, Postgres `DISTINCT ON`)
- Change:
  - `SqlMarketView(engine)` implements `finvest_analytics.domain.ports.MarketView` (AI-analytics-scaffold):
    `bars_1d(symbol, start, end, *, as_of)` = newest `fetched_at` per `(symbol, trading_date)` from `bars_1d_src`
    (`DISTINCT ON (trading_date) … ORDER BY trading_date, fetched_at DESC`), rows with `trading_date <= as_of` only,
    `adj_* → o/h/l/c`, `price_basis = "source_adjusted"`; `index_1d(code, start, end, *, as_of)` from `index_1d`
    (`c` as `Decimal`, 2 dp); `first_bar_date(symbol)` = `min(trading_date)` or `None`; `price_basis()` =
    `"source_adjusted"`; `snapshot()` = max `fetched_at` of every bar row served so far by this instance (one instance per
    request; contracts §1.4 `data_snapshot`).
  - `calendar(start, end)`: per year — inside the `finvest_rules.calendar` maintained range → `trading_days`; outside →
    `SELECT DISTINCT trading_date FROM index_1d WHERE index_code = 'VNINDEX' AND trading_date BETWEEN …` (data.md §1.2 V2:
    VNINDEX daily since 2004-01-05). `shortcut:` comment naming the rule and "drop when holidays.csv covers 2006+".
  - Tests: SQLite (`create_all` of `finvest_market_data.infrastructure.tables`) covers `calendar`, `first_bar_date`,
    `index_1d`, `snapshot`; the `DISTINCT ON` dedupe in `bars_1d` is Postgres-only → the `db`-marked test (one query,
    no SQLite variant).
- Contract: analytics.md (architecture) §1.1 ports, §1.3.1 source-adjusted mode; contracts/analytics.md §1.4
  (`data_snapshot`), §2.4; data.md §1.2 V2, §3 `bars_1d_src`, `index_1d`; 2-tech-plan.ai.md note N1; codebase.md §2
  (`market_data` never imports `finvest_analytics` — hence `apps/api`).
- Acceptance:
  - `db` test: FPT 2026-10-14 stored twice (`fetched_at` 10-15 and 10-16, `adj_c` 93,000 vs 93,500) → `bars_1d` returns one
    row with `c == 93_500`; `as_of = 2026-10-14` hides the 10-15 bar; `snapshot()` equals the 10-16 `fetched_at`.
  - `calendar(2026-10-16, 2026-10-20)` → `[10-16, 10-19, 10-20]` (weekend skipped, `finvest_rules`); `calendar(2016-01-04,
    2016-01-08)` with VNINDEX rows on 01-04…01-07 only → those four dates (no `CalendarNotMaintained`); a range spanning
    2024-12-30…2025-01-03 joins both sources and drops 2025-01-01 (holiday) and the 2024 dates without an index row.
  - `index_1d("VNINDEX", …)` returns `Decimal("1260.00")`-typed closes; `first_bar_date("ZZZ") is None`.
  - End to end on fixtures: `run_whatif(req, SqlMarketView(engine))` on the golden 001 rows loaded into the `db` test →
    `liquidation 10,610,975`, `approximate is True`.
- Out of scope: nominal series (F-015), caching across requests, `bars_1d` (reconstructed) table, venue other than HOSE.

#### BE-whatif-api — N2: `POST /api/whatif` wiring the engine to the SQL view, error mapping, 2 s budget
- Story: F-040 ; Side: be ; Effort: high ; Size: ~160 lines (+ regenerated contracts) ; Lead: opus
- Files: `apps/api/finvest_api/routes/whatif.py`, `apps/api/finvest_api/errors.py` (add `AnalyticsError` handler),
  `apps/api/finvest_api/main.py` (`include_router`), `apps/api/tests/test_whatif_api.py`, `packages/contracts/openapi.json`
  and `apps/web/src/api/types.ts` (regenerate with `make contracts`)
- Change:
  - `get_market_view(engine) -> MarketView` dependency (new `SqlMarketView` per request); `POST /api/whatif` body =
    `finvest_analytics.domain.models.WhatIfRequest`; returns `run_whatif(req, view)` unchanged (JSON-ready dict).
  - `AnalyticsError` → platform.md §2.5 mapping (`VALIDATION` 400; `SYMBOL_UNKNOWN`, `NO_DATA`, `RANGE_TOO_LARGE` 422),
    `details` passed through. Pydantic errors keep the generic 400 handler.
  - Tests inject `FixtureView` (from `finvest_analytics.fixtures`) via `app.dependency_overrides[get_market_view]`:
    golden 001 request → 200, `result.value.liquidation_vnd.value == "10610975"`, envelope `approximate is True`;
    `amount_vnd: 0` → 400; unknown symbol → 422 `SYMBOL_UNKNOWN`; `buy_date` before the first bar → 422 `NO_DATA` with
    `details.first_available`; `fill_rule: "open"` → 400.
  - Budget test: 20 requests, constant series 2016-01-04 → 2026-01-04 (`constant_series` helper) → total wall time < 2 s on
    the fixture view (N2; prints the measured time in `3-build`).
- Contract: contracts/analytics.md §1.4, §2.1 request, **§2.4**, §2.3 Python interface; platform.md §1.3, **§2.5**
  (`POST /whatif` row + error mapping); 2-tech-plan.ai.md N2.
- Acceptance: the five response cases above; `make contracts` leaves the tree clean after the regenerate; the budget
  test passes with its time printed; `make test-kernel` green.
- Out of scope: caching results, `GET /whatif/{id}/ledger.csv` (F-092), batch endpoint, rate limiting.

#### S-etf-bars — spike (N3): does the back-fill cover `E1VFVN30`? One recorded V2 payload + listing check
- Story: F-048 ; Side: be ; Effort: medium ; Size: ~30 lines ; Lead: sonnet
- Files: `services/crawler/tests/fixtures/vci/gap_chart/E1VFVN30-1d.json.gz` (≤ 60 bars, envelope kept, gzip),
  `SPRINT_DIR/3-build.S-etf-bars.md` (report)
- Change (no production code):
  - Outside 15:00–23:00 VN, anonymous, ≤ 2 req/s: V2 `POST https://trading.vietcap.com.vn/api/chart/OHLCChart/gap-chart`
    for `E1VFVN30` (`ONE_DAY`, `countBack` 60): record status, bar count, first date, whether closes are integer VND after
    the ×1000 half-up rule used by `adapters/vci` (BE-bars-store fixture `vci/gap_chart/FPT-1d`).
  - V3 `getAll` (fixture `vci/symbols_getAll/sample` has no ETF row): fetch once, report whether `E1VFVN30` is listed and
    its `type` value (`ETF`?) and `board`. If listed as ETF, the sprint-02 `symbols` feed stores it and `make backfill`
    (universe = `symbols` table, BE-bars-backfill) covers it with no code change.
  - If the local db has bars (`make backfill` done): `SELECT count(*), min(trading_date) FROM bars_1d_src WHERE
    symbol = 'E1VFVN30'`; report the numbers.
  - Report = data.md §1.2-style row(s) for the architect + the verdict: covered / needs a follow-up task (named, ~size).
- Contract: data.md §1.2 (row format), §1.3; 2-tech-plan.ai.md N3; contracts/analytics.md §2.4 `benchmarks` (n/a when
  no bars — the engine does not block on this spike).
- Acceptance: fixture committed (exact bytes, ≤ 20 KB); the report names HTTP status, bar count, first date, the
  `type` string in `getAll`, and the verdict; `make test-kernel` unaffected.
- Out of scope: adapter or feed changes; FUEVFVND or other ETFs; index symbols beyond VNINDEX/VN30.

## FE tasks (`apps/web`)

#### FE-web-scaffold — F-031: `apps/web` React + Vite + TS + i18n + formatters + API client
- Story: F-031 ; Side: fe ; Effort: medium ; Size: ~300 lines ; Lead: sonnet
- Files: `apps/web/package.json`, `apps/web/vite.config.ts` (dev proxy `/api → http://127.0.0.1:8000`, Vitest jsdom),
  `apps/web/tsconfig.json`, `apps/web/index.html`, `apps/web/.gitignore`, `apps/web/src/main.tsx`, `apps/web/src/app/App.tsx`,
  `apps/web/src/app/routes.tsx`, `apps/web/src/app/Placeholder.tsx`, `apps/web/src/components/TopBar.tsx` (minimal: name,
  nav links, language buttons; FE-shell-bar replaces it), `apps/web/src/i18n/index.ts`, `apps/web/src/i18n/en.json`,
  `apps/web/src/i18n/vi.json`, `apps/web/src/lib/format.ts`, `apps/web/src/api/client.ts`, `apps/web/src/test/setup.ts`,
  `apps/web/src/lib/format.test.ts`, `apps/web/src/i18n/i18n.test.ts`
- Change:
  - Dependencies: `react@18`, `react-dom`, `react-router-dom@6`, `@tanstack/react-query@5`, `i18next`, `react-i18next`;
    dev: `vite`, `@vitejs/plugin-react`, `typescript`, `vitest`, `jsdom`, `@testing-library/react`, `@testing-library/user-event`,
    `@testing-library/jest-dom`, `openapi-typescript`. Scripts: `dev`, `build`, `test` (vitest run), `typecheck` (tsc --noEmit),
    `gen` (`openapi-typescript ../../packages/contracts/openapi.json -o src/api/types.ts`). Commit `package-lock.json`.
  - `routes.tsx`: `createBrowserRouter` table `[{path, element, nameKey, analysis: boolean}]` exported as `ROUTES`:
    `/` → redirect `/scenarios`; `/scenarios` (analysis: true, Placeholder until FE-scenario-cards), `/data-quality`,
    `/rules` (Placeholder "coming in a later sprint", analysis: false). Every route element root has
    `data-testid="route-<name>"` (codebase.md §4).
  - `App.tsx`: `QueryClientProvider` (retry 1, `staleTime` 30 s) + `RouterProvider`; layout = `<TopBar/>` + `<main><Outlet/></main>`.
  - `i18n/index.ts`: default `vi`, persisted in `localStorage["finvest.lang"]`, `document.documentElement.lang` kept in sync;
    `en.json`/`vi.json` flat keys: `nav.*`, `lang.*`, `error.<code>` for every platform.md §1.3 + §2.5 code, `state.*`,
    `disclaimer.line_vi/line_en` (both lines are literal in both files).
  - `lib/format.ts`: `formatVnd(n: number | string)` → `10.610.975 ₫`; `formatPct("6.1098")` → `+6,11 %` (sign always, 2 dp,
    from the 4-dp decimal string, no float parse beyond `Number` on a ≤ 15-digit string); `formatPp("1.1098", lang)` →
    `+1,11 điểm %` / `+1,11 pp`; `formatDate("2026-10-23")` → `23/10/2026`; `formatDateTime(iso)` → `23/10/2026 15:42`
    in Asia/Ho_Chi_Minh; `parseVndInput("10.000.000")` → `10000000` (digits only).
  - `api/client.ts`: `api<T>(path, init?)` → fetch same-origin `/api…`, JSON; non-2xx with `{error}` body → throws
    `ApiError(code, message, details, status)`; network failure → `ApiError("UNREACHABLE")`.
- Contract: ADR-S-004; codebase.md §1 (`apps/web` layout), §4 Web conventions, §5 FE kernel; ux/app-shell.md "Language
  switch" (vi-VN numbers in both languages, default VI, local storage); platform.md §1.2, §1.3, §2.5 (same-origin).
- Acceptance:
  - `format.test.ts`: the six examples above plus `formatPct("-2.8338") == "−2,83 %"` (U+2212 or `-`, state which) and
    `formatPct("0.0000") == "0,00 %"` (no sign).
  - `i18n.test.ts`: key sets of `en.json` and `vi.json` are identical and non-empty; a missing key renders the key
    (i18next `returnNull: false`) and the test fails on any `t()` of a key absent from both; first start → `vi`; after
    `changeLanguage("en")` the choice is in local storage and `<html lang>` is `en`.
  - `npm run typecheck`, `npm test`, `npm run build` pass; `npm run dev` serves `/scenarios` with the top bar and
    placeholders in VI.
- Out of scope: freshness chip, API error state, mobile menu, Alt+L (FE-shell-bar); disclaimer banner (FE-disclaimer);
  any feature screen; Playwright/axe.

#### FE-shell-bar — F-031: top bar with nav, freshness chip, language switch (aria-pressed, Alt+L), API-down state
- Story: F-031 ; Side: fe ; Effort: medium ; Size: ~210 lines ; Lead: sonnet
- Files: `apps/web/src/components/TopBar.tsx` (rewrite), `apps/web/src/components/LangSwitch.tsx`,
  `apps/web/src/components/FreshnessChip.tsx`, `apps/web/src/components/ApiErrorState.tsx`, `apps/web/src/app/useBarsStatus.ts`,
  `apps/web/src/lib/useHotkey.ts`, `apps/web/src/components/TopBar.test.tsx`, `apps/web/src/components/ApiErrorState.test.tsx`,
  `apps/web/src/i18n/en.json`, `apps/web/src/i18n/vi.json` (keys `chip.*`, `shell.*`)
- Change:
  - `useBarsStatus()` = TanStack Query on `GET /api/bars/1d/status` (hand-typed `{last_trading_date, as_of, source,
    symbols}` per platform.md §2.5; `refetchInterval` 60 s). `FreshnessChip`: "Dữ liệu đến 17/10/2026 15:42 · nguồn VCI" /
    "Data as of …"; `last_trading_date == null` → "Chưa có dữ liệu / No data yet"; amber + "⚠ stale" when
    `last_trading_date` < the previous weekday (shortcut: weekday rule until `GET /session` exists — comment it);
    `<a href="/data-quality">`.
  - `LangSwitch`: segmented `VI | EN` buttons with `aria-pressed`, active bold + underlined; `useHotkey("Alt+L")` toggles
    (ignored while focus is in an input/textarea).
  - `TopBar`: "Finvest" · nav (Scenarios, Data quality, Rules) from `ROUTES` · chip · switch; below 768 px the nav
    collapses behind a `<button aria-expanded>` menu. Tab order nav → chip → switch (DOM order).
  - `ApiErrorState({onRetry})`: full-width "Cannot reach the local server. Is `docker compose` running?" + retry;
    `App.tsx` is **not** edited — pages render it when their query throws `UNREACHABLE` (first use: FE-scenario-cards).
- Contract: ux/app-shell.md (Layout, Language switch, States, Keyboard and accessibility, Mobile width); platform.md §2.5
  `GET /bars/1d/status`; codebase.md §4 (no colour-only state).
- Acceptance (Testing Library, fetch mocked):
  - Status `{last_trading_date: "2026-10-16", as_of: "2026-10-16T15:42:00+07:00", source: "vci", symbols: 1612}` →
    chip text contains `16/10/2026 15:42` and `VCI` in both languages; `null` status → "No data yet"; a date older than
    the previous weekday → chip has `data-stale="true"` and the ⚠ text.
  - Clicking `EN` sets `aria-pressed="true"` on EN, nav labels switch without reload, `localStorage["finvest.lang"] == "en"`;
    `Alt+L` toggles back to VI; `Alt+L` inside an `<input>` does nothing.
  - `ApiErrorState` renders the message and calls `onRetry` on click; axe-free basics: every button has a name.
- Out of scope: holiday/market-closed chip text (needs `GET /session`, S04), `Data quality` page content, dark theme polish.

#### FE-disclaimer — F-032: non-dismissible EN+VI banner on every analysis route, enumeration test
- Story: F-032 ; Side: fe ; Effort: medium ; Size: ~70 lines ; Lead: sonnet
- Files: `apps/web/src/components/Disclaimer.tsx`, `apps/web/src/app/App.tsx` (render `<Disclaimer/>` under the top bar when
  the matched route has `analysis: true`), `apps/web/src/app/routes.tsx` (flags only), `apps/web/src/app/disclaimer.test.tsx`
- Change:
  - `Disclaimer`: `<aside role="note" data-testid="disclaimer">` with both lines literal (not translated), wraps to two
    lines below 768 px; no close button.
  - `App.tsx` uses `useMatches()` (or the `ROUTES` table) to decide; the flag list is the single source for the test.
  - Test renders the router at every `ROUTES` path: banner present ⇔ `analysis === true`; the test also asserts
    `/scenarios` is in the analysis set (so a future route must declare itself).
- Contract: ux/app-shell.md "Disclaimer banner"; ux/scenario-dashboard.md Layout item 1; codebase.md §5 "disclaimer-on-
  every-analysis-route test (F-032)" (here in Vitest; Playwright version in S04).
- Acceptance: both lines appear verbatim on `/scenarios` in VI and in EN; absent on `/data-quality` and `/rules`; no
  element inside the banner is focusable; the route-enumeration test iterates `ROUTES` (adding a route without the flag
  fails the typecheck: `analysis` is required in the route type).
- Out of scope: per-route disclaimer texts, glossary (PR-111).

#### FE-how-computed — F-051: result types from analytics §2.4 + "How computed" panel for any Figure
- Story: F-051 ; Side: fe ; Effort: medium ; Size: ~200 lines ; Lead: sonnet
- Files: `apps/web/src/features/scenarios/result.ts` (TS types `Figure`, `How`, `WhatIfResult`, `WhatIfEnvelope`,
  `Benchmark`, `Contribution`, `EquityPoint`, `Shift` + `isFigure()`), `apps/web/src/features/scenarios/HowComputed.tsx`,
  `apps/web/src/features/scenarios/figureText.ts`, `apps/web/src/features/scenarios/HowComputed.test.tsx`,
  `apps/web/src/features/scenarios/fixtures/envelope-001.json` (golden 001 envelope, copied from the AI plan numbers),
  `apps/web/src/i18n/en.json`, `apps/web/src/i18n/vi.json` (keys `how.*`, `approximate.*`, `figure.*`)
- Change:
  - `result.ts` mirrors contracts/analytics.md §1.4 + §2.4 exactly (decimal strings stay strings; `cagr_pct: Figure | null`;
    `cagr_note?: Figure`); `isFigure(x)` = has `value`, `unit`, `how`.
  - `figureText(fig, lang)`: `unit vnd` → `formatVnd`, `pct` → `formatPct`, `pp` → `formatPp`, `shares` → `100 cp / 100 sh`,
    `days` → `3 ngày / 3 days`.
  - `HowComputed({figure, envelope, onClose})`: `<dialog>` (native, `showModal`, Esc closes, focus returns to the opener):
    title = figure label, `how.formula`, table of `how.inputs` (name → value formatted by unit heuristics: integers as VND,
    4-dp strings as %), "Data as of" `data_snapshot`, `rules_version`, `price_basis`, `how.cite`; when `envelope.approximate`
    the `approximate.source_adjusted` paragraph (VI + EN text from UX) is shown.
  - `InfoButton({figure, envelope})`: the `(i)` button (`aria-label` "How computed: <label>") that opens the dialog —
    the cards and table reuse it.
- Contract: contracts/analytics.md §1.1 Figure, §1.4 envelope, §2.4 (`how.cite`, approximate text as FE key
  `approximate.source_adjusted`); ux/scenario-dashboard.md "How computed panel (F-051)", "Number and date formats";
  2-tech-plan.ai.md N4.
- Acceptance:
  - Fixture 001 `value.liquidation_vnd` → panel shows `635.975`, `100`, `100.000`, `15.000`, `10.000`, `10.610.975 ₫`,
    `rules_version`, `source_adjusted`, `VN§5`; the approximate paragraph is present (envelope `approximate: true`) and absent
    when set to false.
  - Every-figure test: walk the fixture envelope, for each `isFigure` leaf render `<InfoButton>` and open it → the dialog
    lists every key of `how.inputs` (F-051 "every figure has how").
  - Esc closes and focus returns to the (i) button; `npm run typecheck` passes with `result.ts` used by the fixture JSON
    (`satisfies WhatIfEnvelope`).
- Out of scope: ledger/breakdown views (F-047/F-049), editing inputs, linking cites to vn-market.md.

#### FE-sparkline — F-056: mini equity curve (inline SVG) with invested line/step, hover/focus value, accessible name
- Story: F-056 ; Side: fe ; Effort: medium ; Size: ~150 lines ; Lead: sonnet
- Files: `apps/web/src/features/scenarios/Sparkline.tsx`, `apps/web/src/features/scenarios/Sparkline.test.tsx`,
  `apps/web/src/i18n/en.json`, `apps/web/src/i18n/vi.json` (keys `curve.*`)
- Change:
  - Props `{points: {date, market_value: number, invested: number}[], symbol, width?, height = 48}`; viewBox scaled to the
    container (100 % wide); market-value polyline; invested as a dashed line (constant) or dashed step path (changes);
    no axes.
  - Hover/focus: the `<svg>` is focusable (`tabIndex 0`), arrow keys move the active point, mouse move picks the nearest
    point; a `<title>`-free tooltip `<div role="status">` shows `dd/mm/yyyy · 10.610.975 ₫`.
  - `aria-label` = "Đường giá trị FPT từ 12/10/2025 đến 23/10/2026, cao nhất 10.800.000 ₫, thấp nhất 9.985.975 ₫" (EN
    variant); colour from CSS variables, never the only cue (dashed vs solid).
  - Empty `points` → renders nothing (the card decides what to say).
- Contract: ux/scenario-dashboard.md "Mini curve" and "Keyboard"; contracts/analytics.md §2.4 `equity_curve`
  (`invested` steps on contribution dates); codebase.md §4 (no colour-only state).
- Acceptance: 5 points with a step in `invested` → the invested path has exactly one vertical segment; max/min appear in
  the accessible name formatted vi-VN; focusing + `ArrowRight` moves the status text to the second date; the polyline's
  first y maps the lowest value to the bottom padding (snapshot of `points` attribute for a 3-point series).
- Out of scope: axes, benchmark curves on the card, zoom, candles (`lightweight-charts` arrives with the board).

#### FE-scenario-form — F-055: add/edit side panel with symbol combobox, style, amount, dates, hints; CRUD hooks
- Story: F-055 ; Side: fe ; Effort: medium ; Size: ~300 lines ; Lead: sonnet
- Files: `apps/web/src/features/scenarios/api.ts` (TanStack hooks: `useScenarios`, `useSaveScenario`, `useDeleteScenario`,
  `useSymbolSearch(q)`, `useSymbol(symbol)`, `useWhatIf(scenario)` typed from `src/api/types.ts` + `result.ts`),
  `apps/web/src/features/scenarios/ScenarioForm.tsx`, `apps/web/src/features/scenarios/SymbolCombobox.tsx`,
  `apps/web/src/features/scenarios/defaultName.ts`, `apps/web/src/features/scenarios/ScenarioForm.test.tsx`,
  `apps/web/src/i18n/en.json`, `apps/web/src/i18n/vi.json` (keys `form.*`)
- Change:
  - Fields and validation per UX table: name (optional → `defaultName(symbol, amount, start)` = "FPT · 10.000.000 ₫ ·
    12/10/2025"), symbol combobox (`role="combobox"` + listbox, type-ahead on `GET /api/symbols?q=`, shows exchange;
    must pick an existing row), style radios, amount with grouping as typed (`parseVndInput`), start date (default one year
    before `useSymbol().bars_1d.last`, min = `bars_1d.first`, max = `last`), end date or "Today" checkbox (checked →
    `sell_date: null`). Messages EN/VI under the field; Enter saves, Esc cancels and returns focus to the trigger.
  - Below-one-lot hint: `lot_cost = ceil(close × 100 × 1.0015)` needs the start close — S03 shortcut: the hint appears
    **after** the first computation on the card (engine flag `below_one_lot` + `details.min_amount`), not live in the form;
    `shortcut:` comment; saving is allowed either way.
  - Side panel on ≥ 1024 px (`<dialog>` non-modal positioned right), full screen below; Save → `POST`/`PUT` then
    `invalidateQueries(["scenarios"])`; API 400/422 → the message under the named field (`details.field`/`details.symbol`).
- Contract: platform.md §2.5 (`ScenarioIn`, validation, `GET /symbols`, `GET /symbols/{symbol}`); ux/scenario-dashboard.md
  "Form (add / edit)", "Keyboard", "Mobile"; generated `types.ts` (BE-contracts-ts).
- Acceptance (fetch mocked):
  - Typing `fp` lists `FPT · HOSE`; choosing it fills the symbol and fetches `/api/symbols/FPT`; start defaults to
    `bars_1d.last − 1 year`; amount typed `10000000` displays `10.000.000`; Save posts `{name: "FPT · 10.000.000 ₫ ·
    17/10/2025", symbol: "FPT", style: "lump_sum", amount_vnd: 10000000, buy_date: "2025-10-17", sell_date: null}`.
  - Validation: empty symbol, amount `0`, amount above `100.000.000.000`, end < start → EN/VI message, no request;
    server 422 `SYMBOL_UNKNOWN` → message under symbol.
  - Edit mode pre-fills from a `Scenario`; Esc returns focus to the trigger button; DCA shows the "Monthly" label.
- Out of scope: live below-one-lot hint, several symbols, import/export, undo delete.

#### FE-scenario-cards — F-056/F-055/F-048: scenarios page, header, cards grid, per-card compute, all states, delete
- Story: F-056 ; Side: fe ; Effort: high ; Size: ~250 lines ; Lead: sonnet
- Files: `apps/web/src/features/scenarios/ScenariosPage.tsx`, `apps/web/src/features/scenarios/ScenarioCard.tsx`,
  `apps/web/src/features/scenarios/CardMenu.tsx`, `apps/web/src/features/scenarios/states.tsx` (Empty, NoBars, Skeleton),
  `apps/web/src/app/routes.tsx` (mount `ScenariosPage` at `/scenarios`), `apps/web/src/features/scenarios/ScenariosPage.test.tsx`,
  `apps/web/src/features/scenarios/ScenarioCard.test.tsx`, `apps/web/src/i18n/en.json`, `apps/web/src/i18n/vi.json` (keys `card.*`, `page.*`)
- Change:
  - Page header: title, **+ Add scenario** (opens `ScenarioForm`; hotkey `N` outside fields), view toggle placeholder
    (Cards active; Table wired by FE-scenario-table), "Data as of dd/mm/yyyy · source VCI" from `useBarsStatus`.
  - Grid 3/2/1 columns (1024/768/360), newest first (API order). Each card runs `useWhatIf(scenario)` independently:
    skeleton while loading; error → "Không tính được: <error.<code>>" + Edit; success → UX card lines: header
    (symbol · style / DCA "Mỗi tháng … (ngày 15)"), dates + shift notices, **approximate flag** (icon + text) whenever
    `envelope.approximate`, Invested, Value if sold (i), P/L ₫ and % with ▲/▼/= + colour + sign, Cash left, `<Sparkline>`,
    benchmark lines (`available` → `+5,00 %  (+1,11 điểm %)`, VN-Index tooltip "non-investable"; `available: false` →
    "n/a — data from dd/mm/yyyy"; empty list → no lines), "thiếu N phiên" note with (i) listing `missing_sessions`.
  - `(i)` = `InfoButton` from FE-how-computed. `CardMenu` ⋯: Edit / Delete (confirm dialog "Xoá kịch bản …?"; Delete →
    `useDeleteScenario`); roving arrow keys, Esc closes.
  - States: `useBarsStatus().last_trading_date == null` → NoBars ("Chạy back-fill: `make backfill`", Add disabled); no
    scenarios → Empty with the example line; `UNREACHABLE` → `ApiErrorState` with retry (`refetch`); stale chip is the shell's.
- Contract: ux/scenario-dashboard.md (Layout, Card, States, Keyboard, Mobile); contracts/analytics.md §1.4, §2.4
  (`benchmarks[].available`, `missing_sessions`, `dates.shifts`, flags `below_one_lot`); platform.md §2.5 (one `POST /whatif`
  per row; `error.code` → i18n); 2-tech-plan.ai.md N4.
- Acceptance (fetch mocked with fixture envelopes):
  - Two scenarios, one returning the 001 envelope and one 422 `NO_DATA`: card 1 shows `10.000.000 ₫`, `10.610.975 ₫`,
    `▲ +610.975 ₫`, `▲ +6,11 %`, `635.975 ₫`, the approximate text; card 2 shows the NO_DATA message + Edit; the page still
    renders both (one failure never blanks the grid).
  - Approximate flag test: every rendered card has `[data-testid="approximate-flag"]` while `approximate: true`; a
    fixture with `approximate: false` has none (F-056 criterion, test-enforced).
  - Benchmarks: `available: true` line shows `+5,00 %` and `+1,11 điểm %`; `available: false` shows `n/a` and `06/10/2014`;
    never the string `0 %` for an unavailable benchmark.
  - Shift notice "Ngày mua dời sang 19/10/2026" from `dates.shifts`; DCA fixture shows "Mỗi tháng 2.000.000 ₫ (ngày 15)".
  - Empty / NoBars / API-down states each render their text; `N` opens the form; Delete confirm then the row disappears.
- Out of scope: table view (FE-scenario-table), sorting, delisted note (needs `delisted_at` join — S04), stale logic
  beyond the shell chip.

#### FE-scenario-table — F-056: table view toggle, sortable numeric columns, sticky name column, footer note
- Story: F-056 ; Side: fe ; Effort: medium ; Size: ~190 lines ; Lead: sonnet
- Files: `apps/web/src/features/scenarios/ScenarioTable.tsx`, `apps/web/src/features/scenarios/ViewToggle.tsx`,
  `apps/web/src/features/scenarios/ScenariosPage.tsx` (wire the toggle + pass the computed rows), `apps/web/src/features/scenarios/ScenarioTable.test.tsx`,
  `apps/web/src/i18n/en.json`, `apps/web/src/i18n/vi.json` (keys `table.*`)
- Change:
  - `ViewToggle` segmented `Cards | Table` with `aria-pressed`, choice in `localStorage["finvest.scenarios.view"]`.
  - `ScenarioTable` (TanStack Table v8 or plain `<table>` — plain is fine at ≤ 100 rows; developer's call, state in
    `3-build`): columns per UX (Name · Symbol · Style · Start · End · Invested · Value · P/L ₫ · P/L % · vs VN-Index (pp) ·
    vs E1VFVN30 (pp) · ⚠); header buttons sort any numeric column (`aria-sort`), default P/L % desc; rows whose compute
    failed show the error in the Value cell and sort last; `n/a` benchmark cells sort last; flag column shows ⚠ + text
    while `approximate`.
  - Container scrolls horizontally on narrow widths with the Name column sticky; footer note (both languages).
- Contract: ux/scenario-dashboard.md "Table view (same data)", "Mobile"; contracts/analytics.md §2.4; codebase.md §4.
- Acceptance: three fixture rows (6.1098 %, −2.8338 %, failed) → default order `6,11 %`, `−2,83 %`, failed last; clicking
  "Invested" twice gives desc then asc with `aria-sort` updated; the ⚠ column is filled for every approximate row; toggle
  persists across remount; footer text present in VI and EN.
- Out of scope: column chooser, CSV export (F-049), pagination.

## Ops

#### OPS-web-compose — `web` service (nginx static + `/api` proxy) on 127.0.0.1:8080, Makefile web/contracts targets
- Story: F-031 ; Side: be ; Effort: medium ; Size: ~90 lines ; Lead: opus
- Files: `apps/web/Dockerfile` (node:20-alpine build → nginx:1.27-alpine), `ops/nginx/web.conf`, `docker-compose.yml` (`web`
  service), `Makefile` (`web-install`, `web-test`, `web-build`, `contracts`), `.dockerignore` (node_modules, data)
- Change:
  - `web`: `build: apps/web`, `ports: ["127.0.0.1:8080:80"]`, `depends_on: api`; nginx serves `/usr/share/nginx/html`
    with SPA fallback (`try_files $uri /index.html`) and `location /api/ { proxy_pass http://api:8000/api/; }`; no other
    port, no `0.0.0.0` anywhere (system.md N1, A23 pending).
  - Makefile: `web-install` (`npm --prefix apps/web ci`), `web-test` (`npm --prefix apps/web run typecheck && npm --prefix
    apps/web test`), `web-build`, `contracts` (export + gen, BE-contracts-ts); `test-kernel` **unchanged** (Python only; the
    FE kernel is `make web-test`, run by the FE lead).
  - `make up` builds `web` too; README one line: UI at `http://127.0.0.1:8080`.
- Contract: system.md §N1 and deployment diagram (web 127.0.0.1:8080, api 8000); platform.md §1.1, §2.5 (same-origin
  proxy); codebase.md §6 (Start row); ADR-S-001 (loopback only).
- Acceptance: `docker compose config` shows `web` published on `127.0.0.1:8080` only; `docker compose up -d --build` then
  `curl -s http://127.0.0.1:8080/api/health` returns the API body and `curl -sI http://127.0.0.1:8080/scenarios` is 200
  `text/html`; `ss -ltn` shows no `0.0.0.0:8080`; `make web-test` passes in a fresh checkout after `make web-install`.
- Out of scope: Vite dev container (developers run `npm run dev` on the host), TLS, auth, exposing beyond loopback (A23).

## Sprint-02 fixes (folded in by 5-review.tech sprint-02, 2026-10-18; dag rev 4)

#### FIX-ticks-probe — S02-3/F-019 B1: past-date empty tape is `no_trades` once a probe proves the day is still served
- Story: S02-3 ; Side: be ; Effort: high ; Size: ~120 lines (≈ 45 prod + 60 tests + 15 docs) ; Lead: opus
- Files: `services/crawler/finvest_crawler/feeds/ticks.py`, `services/crawler/tests/test_feed_ticks.py`,
  `packages/market_data/finvest_market_data/infrastructure/repositories.py` (`upsert_crawl_session` only),
  `packages/market_data/tests/test_repositories_db.py`, `ops/README.md` (one line)
- Change:
  - `feeds/ticks.py`: `PROBE_SYMBOLS = ("FPT", "HPG", "VNM")`. When `trading_date < today` and no `--only`, fetch the probes
    (in that order) before the loop; first probe that returns a tape for `trading_date` → day is served, keep its tape so
    the loop does not fetch it again; a probe raising `SourceNoLongerServes` with `served_date` set → `missed` at once;
    all three empty → `missed` / `source_no_longer_serves`, `requests ≤ 3`, `fetched = 0`, `symbols_skipped = ()`.
  - In the loop drop the `trading_date < today` branch: empty tape (`served_date is None`) → `no_trades` on any date;
    `served_date is not None` → stop (`missed` if nothing fetched else `partial`, rest skipped) as today.
  - `upsert_crawl_session`: a `missed` manifest must not overwrite a stored `partial`/`complete` row (`ON CONFLICT ... WHERE
    crawl_sessions.status NOT IN ('partial','complete') OR EXCLUDED.status <> 'missed'`); the manifest file is still written.
  - `ops/README.md`: catch-up of a past day probes FPT/HPG/VNM first; `make crawl DATE=` behaves the same.
- Contract: platform.md §4 v1.6 (probe rule, `requests`, invariant `fetched + no_trades + skipped = universe.count`);
  ADR-S-009; data.md §1.2 K1.
- Acceptance:
  - Fixture universe `A32, FPT, VNM`, `trading_date = today − 1`, `kbs/trade_history/empty` for A32 and VNM, FPT tape for
    `trading_date` → `complete`, `symbols_fetched == 1`, `symbols_no_trades == ("A32","VNM")`, `requests == 3` (FPT probe
    counted once).
  - Same, every tape empty → `missed`, `reason == "source_no_longer_serves"`, `requests == 3`, `rows == 0`.
  - Probe FPT returns another session's tape → `missed` after 1 request.
  - `today == trading_date` cases of `test_feed_ticks.py` unchanged (`test_empty_tape_today_is_no_trades_and_complete` etc.);
    `test_past_date_empty_first_tape_is_missed` is rewritten to the probe rule, not deleted.
  - db test: session row `partial` (rows 145,184) then a `missed` manifest for the same day → row still `partial`, rows
    145,184; a `complete` manifest does overwrite.
  - `test_catchup.py`: unchanged (catch-up calls `run_ticks`; the fix is inside). Add one test: `run` for `today − 1`
    receives `trading_date < today` and the probe path is taken (fake `run` records the call) — documents the morning-after
    replay case from 5-review.tech §2.
- Out of scope: cross-checking `no_trades` against daily volume (platform.md §4 caveat, F-021), changing `catchup()` order,
  re-crawling 10-16 against the app DB (BE tester does it after merge: expected 145,184 rows, same checksum as the manifest).

#### FIX-index-value — F-012 B2: mixed-unit V2 `accumulatedValue`, BIGINT guard, VNINDEX/VN30 bars present
- Story: F-012 ; Side: be ; Effort: high ; Size: ~110 lines (≈ 30 prod + 60 tests + fixture + 20 docs) ; Lead: opus
- Files: `services/crawler/finvest_crawler/adapters/vci/source.py`, `services/crawler/finvest_crawler/adapters/vci/payloads.py`
  (docstring), `services/crawler/tests/test_adapter_vci.py`, `services/crawler/tests/fixtures/vci/gap_chart/VN30-1d.json.gz`
  (new: recorded V2 payload for `VN30`, envelope kept, trimmed to ≤ 60 bars that include 2012-02-06 and 2026-10-16),
  `services/crawler/tests/test_feed_bars_1d.py`
- Change:
  - `vci/source.py`: `_value_vnd(av, ref)`: `ref = v × c` for stocks → choose `av` or `av × 1e6` whose ratio to `ref` is
    closest to 1 (log distance); indices (`ref is None`) → `av ≥ 1e9` is VND else `× 1e6`. `_rows` yields the raw `av`;
    `parse_bars` / `parse_index_bars` call the helper. Result `> 2**63 − 1` or `< 0` → `None` + `log.warning` naming the
    raw path (same style as the close = 0 warning); `v == 0` → `ref` unusable → index rule.
  - `payloads.py` docstring + `accumulatedValue` comment: mixed unit, cite the two live values.
  - `feeds/bars_1d.py` is **unchanged**; the overflow trigger is gone.
- Contract: platform.md §4 v1.6 (`value` rule, NULL on overflow); data.md §1.2 V2 v1.2, §3 `index_1d` / `bars_1d_src`.
- Acceptance (worked numbers):
  - Index: `accumulatedValue = 222242000000` (VN30 2012-02-06) → `value == 222_242_000_000`; `6386472.73` (2026-10-16) →
    `6_386_472_730_000`; `20000.5` → `20_000_500_000` (existing `test_index_bars_keep_two_decimals` still passes).
  - Stock: `v = 6_618_016, c = 65_000, accumulatedValue = 474963.63` → `474_963_630_000` (ratio 1.10 to `v × c`);
    `accumulatedValue = 474963630000` with the same `v, c` → `474_963_630_000` (raw VND recognised); `accumulatedValue =
    1e13` with `v = 1, c = 1` → `value is None`, one warning, bar kept.
  - Fixture `VN30-1d.json.gz` parses without raising; every `value` fits BIGINT; `max(value)/min(value) < 1e4` across the
    fixture's bars (no 1e6 jump between eras).
  - `test_feed_bars_1d.py`: a fake source returning the VN30 fixture + one stock → run `complete`, `index_1d` upsert
    called with 2 index codes' bars, summary line printed with `coverage`.
  - Live (BE tester after merge, from the worktree with host-owned `data/`): `make backfill` replays the archive (0 live
    requests except the two indices), run `complete`/`partial`, `index_1d` has VNINDEX rows from 2004 and VN30 rows,
    `SELECT count(*) FROM bars_1d_src WHERE value IS NOT NULL AND value > 1000 * v * adj_c` = 0, summary/coverage printed.
- Out of scope: `value` NULL on old bars (source null), nominal reconstruction (F-014), adding other indices (HNX, UPCoM).

## Live smoke fixes (LIVE-03, SM smoke test on the real DB, 2026-10-18; dag rev 5)

Root cause of L1 (reproduced on SQLite with `SqlMarketView`, not on the fixture view): `SqlMarketView.snapshot()` is
"max `fetched_at` of the rows served so far" (BE-market-view) and returns `datetime.min` before the first read, but
`run_whatif` calls `view.snapshot()` **first** and uses it as the upper bound of its validation read
(`bars_1d(sym, first, snap, as_of=snap)`) → window `[first, 0001-01-01]` → `bar_days == []` → `IndexError`. Every live
what-if 500s, regardless of VNINDEX. The empty VNINDEX table is a second, independent state: `calendar()` for years
outside `holidays.csv` (2025–2026) is served from VNINDEX dates (platform.md §2.5), so a 2024 `buy_date` currently
yields `calendar == []` → `VALIDATION no_trading_day_near_buy` (a contract error, not a 500); it disappears once the
BE tester runs the FIX-index-value `make backfill`. Decision: keep the VNINDEX calendar fallback (documented shortcut,
no cost), fix the engine's dependency on `snapshot()` for validation, and make the empty case a contract error.

#### FIX-whatif-empty-history — LIVE-03 L1: `POST /whatif` must not read history bounded by `snapshot()`, empty history is `NO_DATA`
- Story: F-040 ; Side: ai ; Effort: high ; Size: ~70 lines (≈ 5 prod + 55 tests + 10 docs) ; Lead: opus
- Files: `services/analytics/finvest_analytics/sim/whatif.py` (lines 36–43 only), `services/analytics/tests/test_whatif_errors.py`
  (new or the existing error test module of AI-whatif-lumpsum — one file), `apps/api/tests/test_whatif_api.py`
- Change:
  - `whatif.py`: the validation-only history read must not depend on `view.snapshot()` (a `SqlMarketView` has served
    nothing yet). Replace `snap = view.snapshot().date()` + `bars_1d(sym, first, snap, as_of=snap)` by a read bounded by
    `date.max` (`bars_1d(sym, first, date.max, as_of=date.max)`; "never feeds a number" comment stays). Do not touch
    `snapshot()` uses after the first fill read (`benchmark.py` fallback is fine: bars were served by then).
  - Guard: `if not bar_days: raise AnalyticsError("NO_DATA", {"first_available": first.isoformat()})` before `bar_days[-1]`.
    No other control-flow change; golden files unchanged.
  - No change to `SqlMarketView` (its `snapshot()` semantics stay = `data_snapshot` of rows served, contracts/analytics.md §1.4).
- Contract: contracts/analytics.md §2.3 (`view.snapshot()` is copied into the result — it is a data stamp, not "today"),
  §2.4 errors; platform.md §2.5 `POST /whatif` error mapping (`NO_DATA` → 422, never 500).
- Acceptance:
  - `apps/api/tests/test_whatif_api.py`: new test over the **real** `SqlMarketView` on in-memory SQLite (seed like
    `test_market_view.py::put_bar`: FPT bars 2026-10-14/15/16 at `adj_c = 93_500`, `fetched_at = 2026-10-17T03:00Z`;
    override `get_market_view` with `lambda: SqlMarketView(eng)`), body `{"symbol":"FPT","amount_vnd":10000000,
    "buy_date":"2026-10-14","sell_date":"2026-10-16","style":"lump_sum"}` → 200, `result.dates.buy == "2026-10-14"`,
    `data_snapshot == "2026-10-17T10:00:00.000+07:00"`. This test fails on the current head with `IndexError` (the live L1).
  - Same seed, `buy_date = "2024-01-02"` (no VNINDEX rows → empty calendar for 2024) → 400 `VALIDATION`
    `details.reason == "no_trading_day_near_buy"`, never 500 (documents the transitional state until the backfill).
  - Analytics unit test: a view whose `first_bar_date` returns `2026-10-01` but `bars_1d` returns `[]` (as_of hides
    everything) → `AnalyticsError` code `NO_DATA`, `details.first_available == "2026-10-01"`; fails with `IndexError` today.
  - Existing kernel (golden 001–009, `test_whatif_api.py`, `test_benchmarks.py`) unchanged and green.
- Out of scope: changing `SqlMarketView.calendar()` (VNINDEX fallback stays, platform.md §2.5), `holidays.csv` back to 2006
  (would remove the fallback; log as a follow-up in 5-review.tech), loading only the symbol's first/last dates instead of the
  full history for validation (perf, N2 budget still met).

#### FIX-symbols-exact-first — LIVE-03 L2: `GET /symbols?q=` ranks the exact symbol match first
- Story: F-055 ; Side: be ; Effort: medium ; Size: ~30 lines (≈ 3 prod + 20 tests + 7 docs) ; Lead: sonnet
- Files: `apps/api/finvest_api/routes/symbols.py` (`list_symbols` only), `apps/api/tests/test_symbols.py`, `apps/api/tests/conftest.py`
  (seed only)
- Change:
  - `list_symbols`: when `q` is non-empty, order by `case((symbols.c.symbol == q.upper(), 0), else_=1), symbols.c.symbol`
    (SQLAlchemy `case`; works on SQLite and Postgres). Empty `q` keeps `symbol asc`. `limit` applies after the ordering, so
    the exact match is never cut off.
  - `conftest.py` seed: add `sym("FOC", "FPT Online", "FPT Online Service")` (live: FOC and FOX match `q=FPT` through their
    names). Update `test_search` expectations: `q=fp` → `["FPT", "FOC"]`, no `q` → `["FOC", "FPT", "VNM"]`.
- Contract: platform.md §2.5 v1.7 `GET /symbols` row (exact match first, then symbol asc; `platform.prev-7.md` = v1.6).
  No OpenAPI/TS change (ordering is not in the schema).
- Acceptance:
  - `q=FPT` → `["FPT", "FOC"]` and `q=fpt` → the same (case-insensitive exact); on the current head the order is
    `["FOC", "FPT"]` (the live L2).
  - `q=FPT&limit=1` → `["FPT"]`.
  - `q=FP` (no exact match) → `["FOC", "FPT"]` (symbol asc unchanged when nothing is exact).
  - `test_limit_validation`, `test_detail` unchanged and green.
- Out of scope: ranking symbol-prefix matches above name matches, fuzzy search, FE combobox changes (it already selects
  the first row).

## Mid-sprint replan 2026-10-24 — A23 manual crawl + FE test bugs (dag rev 6; previous: `2-tech-plan.prev-2.md`)

Inputs: `product/sponsor-answers.md` A23, `1-sprint-plan.md` §Revision 2026-10-24, `product/backlog.md` F-034 + RW-U1…U7,
`product/ux/app-shell.md` §Crawl button, `4-test.fe.md`, `sprint-02/5-review.tech.md` (B1/B2 fixed, merged).
Contracts: `contracts/platform.md` **v1.8** (§2.6 jobs, nullable `first_available`, RW-U4 save rule; v1.7 = `platform.prev-8.md`),
`architecture/system.md` (scheduler retired, api host port 8001).

### Decisions
- **Crawl runs inside the api container** as one background `threading.Thread` (uvicorn single worker; the module-level
  lock + the `jobs` row give "one at a time"). No queue, no worker service: same image, `./data` mounted, `FINVEST_DATA_DIR`.
  The thread imports `finvest_crawler.feeds.*` directly — `apps/api` already depends on the workspace; add `finvest-crawler`
  to `apps/api/pyproject.toml`. import-linter has no rule against api → crawler (api is the composition layer).
- **Daily catch-up cost**: `run_bars_1d` today fetches `COUNT` bars for 1 612 names (~21 min, sprint-02 review). The job
  passes `count = sessions since the oldest last bar + 2 (min 5)`, so a press costs 1 612 small requests (ADR rate limits
  apply; still minutes, not seconds — the status line shows step + names done). Not optimised further in S03.
- **Progress** = `jobs.progress` JSONB updated by the thread ≤ every 2 s; the web polls `GET /api/jobs/current` every 2 s
  while running (no SSE in S03). Reload recovery comes from the same endpoint.
- **Host port**: the sponsor's gateway (`gateways/gateway.py`) owns `127.0.0.1:8000` → api host port moves to **8001**
  (Vite dev proxy follows; the browser always uses web 8080 → `api:8000` inside compose, unchanged).
- **No recovery of 10-19…10-23 ticks** (lost; 1-sprint-plan risk row). The daily bars for those days come back through step 2.
- **RW-U1 is a contract fix**: `first_available: string | null` (platform.md §2.5; the ai architect mirrors analytics.md §2.4).
  RW-U4 is a BE contract fix (save refuses a `buy_date` before the first stored bar; §2.5 v1.8) plus an FE message.
- `data/raw` is uid 1000 since 2026-10-24 (SM) — the api runs as `${FINVEST_UID:-1000}` already, so the thread can write.

### Order and lanes (M5, all `after` ids are merged or listed here)
```
BE-4  BE-crawl-hooks → BE-jobs-crawl                   (crawler params, then api job + routes + migration)
BE-5  BE-fix-u4 ∥ OPS-crawl-manual                    (start now)
FE-1  FE-fix-u1 → FE-fix-u2-u3 → FE-fix-u5-u7 (after BE-fix-u4) → FE-crawl-button (after BE-jobs-crawl)
```
Slip order (1-sprint-plan): FE-fix-u5-u7 first (should items), never FE-fix-u1/u2-u3, BE-*, OPS-*, FE-crawl-button.

### BE tasks

#### BE-crawl-hooks — F-034: `run_bars_1d(count=)` and `run_ticks(on_progress=)` so the api job can bound and report a run
- Story: F-034 ; Side: be ; Effort: medium ; Size: ~70 lines (≈ 25 prod + 45 tests) ; Lead: sonnet
- Files: `services/crawler/finvest_crawler/feeds/bars_1d.py`, `services/crawler/finvest_crawler/feeds/ticks.py`,
  `services/crawler/tests/test_feed_bars_1d.py`, `services/crawler/tests/test_feed_ticks.py`
- Change:
  - `run_bars_1d(..., count: int = COUNT, on_progress=None)`: `count` replaces the constant in the adapter calls **and** in
    the archive file name `f"{name}-1d-{count}"`; `on_progress(done, total)` called after each name (fetched, skipped or
    no_trades). CLI default unchanged (`COUNT`).
  - `run_ticks(..., on_progress=None)`: same callback after each symbol of `todo` (probes count once they are consumed).
  - Both callbacks are optional keyword args; `_run` signatures grow by one param; no behaviour change when `None`.
- Contract: platform.md §2.6 ("Progress", step 2 `count` rule); §4 manifest unchanged (checksum input is the bars, not the
  file name).
- Acceptance:
  - bars test: `count=7` → adapter called with `count == 7`, archive path ends `-1d-7`, manifest identical in status/rows to
    the `COUNT` run on the same fixture; `on_progress` receives `(1, n) … (n, n)` with `n == len(names)`.
  - ticks test (existing fixture universe `A32, FPT, VNM`, today): callback gets `(1,3), (2,3), (3,3)`; a blocked run stops
    at the last fetched index; `on_progress=None` runs the unchanged suite green.
- Out of scope: incremental per-symbol `from` dates (adapter API has `to, count` only), any api code.

#### BE-jobs-crawl — F-034: `jobs` table, crawl runner thread, `POST /api/jobs`, `GET /api/jobs/current|{id}`, 409 lock
- Story: F-034 ; Side: be ; Effort: high ; Size: ~350 lines (≈ 25 migration + 160 prod + 165 tests; generated `openapi.json`/`types.ts` and `uv.lock` excluded; re-sized 2026-10-24 after consult, actual ≈ 500) ; Lead: opus
- Files: `apps/api/migrations/versions/0007_jobs.py`, `apps/api/finvest_api/jobs/__init__.py`,
  `apps/api/finvest_api/jobs/runner.py`, `apps/api/finvest_api/routes/jobs.py`, `apps/api/finvest_api/main.py` (router +
  start-up hook only), `apps/api/pyproject.toml` (`finvest-crawler` dep), `apps/api/tests/test_jobs.py`, `apps/api/tests/conftest.py`
  (jobs table in the SQLite seed only), `packages/contracts/openapi.json`, `apps/web/src/api/types.ts` (both regenerated via
  `make contracts`)
- Change:
  - Migration `0007_jobs`: `jobs(id BIGINT identity PK, kind TEXT, args JSONB, status TEXT CHECK (status IN
    ('running','done','failed')), created_at TIMESTAMPTZ, finished_at TIMESTAMPTZ, progress JSONB, summary JSONB, error JSONB,
    log TEXT)` (data.md §3 row + the three JSONB columns).
  - `runner.py`: `start_crawl(engine, settings) -> int | None` — `threading.Lock` non-blocking acquire; `None` when held
    (route → 409 `JOB_RUNNING` with `details {id, started_at}` read from the running row). Inside the thread: step 1 ticks when
    `finvest_rules` says today is a trading day (`partial_until` when now < 15:00 VN), step 2 `run_bars_1d(today, count=…)`
    with `count` from the older of the two table maxima `MAX(trading_date)` of `bars_1d_src` and `index_1d` (+2, min 5; an empty
    table ignored, `COUNT` when both are empty — platform.md §2.6 v1.9); `on_progress` writes `progress` ≤ every 2 s; success → `done` + `summary`; any exception → `failed` +
    `error {code: type(e).__name__, message, path (OSError.filename), source/http_status when present}`; the lock is released
    in `finally`. `mark_interrupted(engine)` on FastAPI start-up: `running` → `failed`, `error.code = "interrupted"`.
  - `routes/jobs.py`: `POST /api/jobs` body `{kind}` (`kind != "crawl"` → 400 `VALIDATION`), 202 Job; `GET /api/jobs/current`
    (newest `crawl` row, 404 `NOT_FOUND` if none); `GET /api/jobs/{id}`. Timestamps via `deps.vn_iso`.
  - The thread receives the crawler `Settings` from env (`FINVEST_DATABASE_URL`, `FINVEST_DATA_DIR`) exactly as the CLI does.
- Contract: platform.md §2.6 (routes, Job object, 409 envelope, crash rule), §1.3 envelope; data.md §3 `jobs`.
- Acceptance (`test_jobs.py`, runner's `run_ticks`/`run_bars_1d` monkeypatched with fakes that call `on_progress`):
  - `POST /api/jobs {kind:"crawl"}` → 202, `status == "running"`; a second POST while the fake sleeps → 409 `JOB_RUNNING`,
    `details.id` equals the first id; after the fake finishes, `GET /api/jobs/current` → `done`, `summary.bars_1d.sessions_added`
    (= new distinct `trading_date`s in `bars_1d_src`, §2.6 v1.9) and `summary.ticks.rows` from the fake's manifest, `progress.done == progress.total`.
  - Fake `run_ticks` raising `PermissionError(13, "Permission denied", "/app/data/raw/ticks/2026-10-26")` → job `failed`,
    `error == {code:"PermissionError", message:…, path:"/app/data/raw/ticks/2026-10-26"}`, `summary.ticks is None`; a new POST
    is accepted (lock released).
  - Non-trading day (`today` injected = 2026-10-25) → `run_ticks` not called, `summary.no_session_today is True`.
  - `count` rule: tables with last bar 2026-10-16 and today 2026-10-26 → `run_bars_1d` called with `count == 8` (6 sessions + 2);
    empty tables → `COUNT`.
  - Start-up: a seeded `running` row → after app start `failed/interrupted`. `kind:"purge"` → 400. `test_openapi_current` green
    after regeneration.
- Out of scope: SSE/WebSocket progress, cancelling a job, `purge`/other kinds, compose/Makefile changes (OPS-crawl-manual),
  the web button (FE-crawl-button), optimising the back-fill.

#### BE-fix-u4 — F-055 RW-U4: `POST/PUT /api/scenarios` refuses `buy_date` before the symbol's first stored bar (422 `NO_DATA`)
- Story: F-055 ; Side: be ; Effort: medium ; Size: ~80 lines (≈ 25 prod + 55 tests) ; Lead: opus
- Files: `apps/api/finvest_api/routes/scenarios.py`, `apps/api/tests/test_scenarios.py`, `apps/api/tests/conftest.py`
  (seed `bars_1d_src` rows only)
- Change:
  - `_check_first_bar(c, symbol, buy_date)`: `SELECT MIN(trading_date) FROM bars_1d_src WHERE symbol = :s`; a row exists and
    `buy_date < first` → `ApiError("NO_DATA", 422, …, {"field": "buy_date", "symbol": sym, "first_available": first.isoformat()})`.
    No bars at all → pass (platform.md §2.5 v1.8). Called by `create_scenario` and `replace_scenario` after `_check_symbol`.
- Contract: platform.md §2.5 v1.8 ScenarioIn validation paragraph (same code + details as `POST /whatif` `NO_DATA`).
- Acceptance: seed FPT first bar 2025-01-02 → POST `buy_date 2020-01-02` → 422 `NO_DATA`, `details.first_available ==
  "2025-01-02"`, `details.field == "buy_date"`, DB count unchanged; `buy_date 2025-01-02` → 201; a symbol with no bars (seed
  VNM without bars) → 201; PUT with the bad date → 422 and the row unchanged. `test_openapi_current` green (no schema change).
- Out of scope: validating `sell_date` against the last bar, re-validating already-saved rows (the card shows the what-if
  `NO_DATA` reason — FE-fix-u5-u7), `DELETE`.

#### OPS-crawl-manual — A23/F-034: api mounts `./data` + host port 8001, timer removed from Makefile/ops/docs, "no scheduler" test
- Story: F-034 ; Side: be ; Effort: medium ; Size: ~70 lines (≈ 20 compose/Makefile + 25 docs + 25 test) ; Lead: opus
- Files: `docker-compose.yml`, `Makefile`, `ops/systemd/` (delete the directory), `ops/README.md`, `README.md` (Chạy section),
  `apps/web/vite.config.ts` (proxy port), `.env.example` (comment only, if a port is mentioned), `apps/api/tests/test_no_scheduler.py`
- Change:
  - compose `api`: `ports: "127.0.0.1:8001:8000"`, add `volumes: ./data:/app/data` and `FINVEST_DATA_DIR: /app/data`; header
    comment updated (web 8080 + api 8001 on loopback; 8000 is the sponsor's gateway). `web`/`crawler`/`db` unchanged.
  - `Makefile`: delete `install-timers`, `uninstall-timers`, `UNITDIR` and the `.PHONY` entries; `up` still `mkdir -p data/raw`.
  - `ops/README.md`: replace the timer section with "manual crawl: the web button (`POST /api/jobs`) or `make crawl DATE=`;
    never run both at once; the api needs `make up` after a code change". `README.md`: health URL → `127.0.0.1:8001`, port line,
    one line about the button. `vite.config.ts` proxy → `http://127.0.0.1:8001`.
  - `test_no_scheduler.py` (kernel, offline): asserts `ops/systemd` does not exist, `Makefile` contains no `timer`/`systemctl`,
    and no `*.timer`/`*.service`/crontab file under `ops/` (F-034 last criterion).
- Contract: system.md §Deployment (ports, no scheduler); platform.md §2.6 (api container runs the crawl, `./data` mounted).
- Acceptance: `docker compose config` shows api published on `127.0.0.1:8001` only and `/app/data` bound; `make up` then
  `curl 127.0.0.1:8001/api/health` ok and `curl 127.0.0.1:8080/api/health` ok (SM/BE tester, real stack);
  `test_no_scheduler.py` green; `make -n install-timers` → "No rule to make target".
- Out of scope: removing ADR-S-009 (architect marks it superseded), the gateway itself, the `crawler` tools profile (kept for
  `make crawl`/`make backfill`), data/raw ownership (done 2026-10-24).

### FE tasks (`apps/web`)

#### FE-fix-u1 — F-056 RW-U1 (blocker): nullable `first_available`, "n/a" benchmark line/cell, no error boundary
- Story: F-056 ; Side: fe ; Effort: medium ; Size: ~60 lines (≈ 15 prod + 45 tests) ; Lead: sonnet
- Files: `apps/web/src/features/scenarios/result.ts`, `apps/web/src/features/scenarios/ScenarioCard.tsx`,
  `apps/web/src/features/scenarios/ScenarioTable.tsx`, `apps/web/src/features/scenarios/ScenarioCard.test.tsx`,
  `apps/web/src/features/scenarios/ScenarioTable.test.tsx`, `apps/web/src/features/scenarios/fe-tester.gaps.test.tsx` (U1 `it.fails`
  → `it`), `apps/web/src/i18n/en.json`, `apps/web/src/i18n/vi.json` (key `card.bench_na_nodate`)
- Change: `result.ts:23` → `first_available: string | null`; `ScenarioCard.tsx:29` branches: null → `t("card.bench_na_nodate",
  {name})` = "VN-Index — n/a" / "VN-Index — n/a"; string → the existing dated text. `ScenarioTable`: the benchmark cell shows
  "n/a" for `available: false` whatever `first_available` is (no `formatDate(null)` anywhere: grep the feature for `formatDate(`
  on an optional value).
- Contract: platform.md §2.5 v1.8 (nullable `first_available`); UX scenario-dashboard.md (benchmark n/a, never 0).
- Acceptance: envelope with `benchmarks[0] = {name:"VN-Index", investable:false, available:false, first_available:null}` renders
  card and table without throwing; card line text `VN-Index — n/a`; table cell `n/a`; dated case unchanged (`E1VFVN30 — n/a
  (from 06/10/2014)` or the current wording); `tsc` clean; the U1 `it.fails` test is now a passing `it`.
- Out of scope: other RW items, benchmark data itself (VNINDEX bars come back via F-034 step 2).

#### FE-fix-u2-u3 — F-032 RW-U2 + F-056 RW-U3: disclaimer inside a landmark; card header shows the scenario name
- Story: F-032 ; Side: fe ; Effort: medium ; Size: ~80 lines (≈ 25 prod + 55 tests) ; Lead: sonnet
- Files: `apps/web/src/components/Disclaimer.tsx`, `apps/web/src/app/App.tsx` (layout wrapper only),
  `apps/web/src/app/disclaimer.test.tsx`, `apps/web/src/features/scenarios/ScenarioCard.tsx`,
  `apps/web/src/features/scenarios/ScenarioCard.test.tsx`, `apps/web/src/features/scenarios/fe-tester.gaps.test.tsx` (U2 → `it`),
  `apps/web/src/i18n/en.json`, `apps/web/src/i18n/vi.json` (key `card.subtitle` if needed)
- Change: `Disclaimer` renders `<aside role="complementary" aria-label={t("disclaimer.name")}>` **inside** `<main>` (or
  `<header>`) — no content outside a landmark; keep non-dismissible and both lines. `ScenarioCard` header: `<h3>{name}</h3>` as
  visible text (name = stored name, else `defaultName(...)`), symbol · style on a line below; `aria-label` removed if it
  duplicated the heading.
- Contract: UX app-shell.md §Keyboard and accessibility, backlog F-032 RW-U2, F-056 RW-U3; codebase.md §4.
- Acceptance: axe (jest-axe already in the suite? else `axe-core` run in jsdom as `fe-tester.gaps.test.tsx` does) on the page shell
  reports no `region` violation; disclaimer still found on every `ROUTES` entry (existing enumeration test). Two scenarios
  named "FPT 50tr 2025" and "FPT DCA thử" → both names visible via `getByRole("heading", {name})`; unnamed → default name.
- Out of scope: visual redesign of the card, dark theme.

#### FE-fix-u5-u7 — RW-U5 plural, RW-U6 skeleton a11y, RW-U7 shared minus, RW-U4 FE message for `NO_DATA`
- Story: F-056 ; Side: fe ; Effort: medium ; Size: ~110 lines (≈ 40 prod + 70 tests) ; Lead: sonnet
- Files: `apps/web/src/lib/format.ts`, `apps/web/src/lib/format.test.ts`, `apps/web/src/features/scenarios/states.tsx` (skeleton),
  `apps/web/src/features/scenarios/ScenarioTable.tsx` (₫ column uses the shared formatter), `apps/web/src/features/scenarios/ScenarioCard.tsx`
  (error text for `NO_DATA` with `first_available`), `apps/web/src/features/scenarios/ScenarioForm.tsx` (422 `NO_DATA` →
  `buy_date` field error), `apps/web/src/features/scenarios/ScenarioForm.test.tsx`, `apps/web/src/features/scenarios/ScenariosPage.test.tsx`,
  `apps/web/src/features/scenarios/fe-tester.gaps.test.tsx` (U5 → `it`), `apps/web/src/i18n/en.json`, `apps/web/src/i18n/vi.json`
  (`chip.sessions_missing_one/_other`, `error.NO_DATA_before`)
- Change: i18next plural keys (`_one/_other`) for "sessions missing" (VI has one form — same text in both keys, parity test
  stays green); skeleton `div` → `role="status" aria-busy="true"` + visually hidden "Đang tải…" (no `aria-label` on a role-less
  element); `formatVnd`/`formatPct` in `lib/format.ts` emit U+2212 for negatives and every ₫/% rendering goes through them
  (grep: no literal `-` concatenation); `NO_DATA` with `details.first_available` → "Không có dữ liệu FPT trước 02/01/2025" /
  "No FPT data before 02/01/2025" on the form's start-date field (422 from BE-fix-u4) and on the card (what-if `NO_DATA`).
- Contract: platform.md §2.5 v1.8 (`NO_DATA` details); backlog RW-U4…U7; UX scenario-dashboard.md states.
- Acceptance: EN `1 session missing` / `2 sessions missing`; VI unchanged; skeleton passes axe (no `aria-prohibited-attr`);
  `formatVnd(-19847507)` → `−19.847.507 ₫` and a test scanning rendered card + table text finds no ASCII `-` directly before a
  digit; form shows the `NO_DATA` message on the start-date field and keeps the input; card error for the same code shows
  the dated reason instead of "Dữ liệu nhập không hợp lệ".
- Out of scope: the `useWhatIf` retry delay, DCA wording note (4-test observations).

#### FE-crawl-button — F-034: "Cào dữ liệu" top-bar button with idle/running/refused/done/error states, reload recovery
- Story: F-034 ; Side: fe ; Effort: medium ; Size: ~220 lines (≈ 110 prod + 110 tests) ; Lead: sonnet
- Files: `apps/web/src/components/CrawlButton.tsx` (new), `apps/web/src/components/CrawlStatus.tsx` (new, the status line),
  `apps/web/src/app/useCrawlJob.ts` (new), `apps/web/src/components/TopBar.tsx` (insert the button left of `LangSwitch`, status
  line under the bar), `apps/web/src/components/CrawlButton.test.tsx` (new), `apps/web/src/components/TopBar.test.tsx` (tab order),
  `apps/web/src/i18n/en.json`, `apps/web/src/i18n/vi.json` (keys `crawl.*`; rename `error.JOB_ALREADY_RUNNING` → `error.JOB_RUNNING`, platform.md §1.3 v1.9)
- Change:
  - `useCrawlJob()`: TanStack Query on `GET /api/jobs/current` (404 → `null`), `refetchInterval` 2 000 ms while
    `status === "running"`, else off; mutation `POST /api/jobs {kind:"crawl"}`; a 409 sets a `refused` flag with
    `details.started_at`; on success/done, invalidate `useBarsStatus` so the freshness chip refreshes. Types from the regenerated
    `api/types.ts` (BE-jobs-crawl).
  - `CrawlButton`: UX table states — idle "⟳ Cào dữ liệu"/"⟳ Crawl data" with `title` = last run ("Lần cuối: 26/10/2026 16:14 ·
    xong"); running: `disabled`, spinner, `aria-busy="true"`; icon-only under 360–479 px with the same accessible name.
  - `CrawlStatus` (`role="status"`, `aria-live="polite"`): running → "Bước 1/2 — lệnh khớp 26/10: 12/30 mã" / "Bước 2/2 — giá
    ngày: 3/6 phiên" + elapsed; refused → "Đang có một lượt cào chạy (bắt đầu 16:10) — chờ xong"; done → the summary line from
    `summary` (ticks symbols/rows, `+N phiên giá ngày`, skipped, finish time, duration; `no_session_today` variant; `partial_until`
    variant), dismissible; error → "✕ Lỗi: <message> (<code>)" with `path`/`source`/`http_status` when present, "đã lưu k/n mã" from
    `summary.ticks` when present, not auto-dismissed. Durations via a small `formatDuration` in `lib/format.ts` if absent.
- Contract: platform.md §2.6 (Job object, 409 envelope, `summary`/`error` shapes); UX app-shell.md §Crawl button, §Keyboard
  (tab order nav → chip → crawl button → language switch).
- Acceptance (fetch mocked):
  - current = 404 → idle, no status line; click → POST called once, button disabled + `aria-busy`, polling starts (fake timers:
    2 fetches of `/jobs/current` in 4 s); `progress {step:1, steps:2, done:12, total:30, trading_date:"2026-10-26"}` → status
    text contains `1/2` and `12/30`; `done` → summary text contains `30 mã`, `812.344`, `+6 phiên`, `2 mã bỏ qua`, `3 phút 41 giây`,
    polling stops, `bars/1d/status` refetched; `failed` with `error {code:"PermissionError", path:"data/raw/ticks/2026-10-26"}` →
    text contains both, button enabled again.
  - POST → 409 `{details:{started_at:"2026-10-26T16:10:03+07:00"}}` → "bắt đầu 16:10" refused text, no second POST.
  - Mount with current = `running` → Running state without a click (reload recovery). Tab order test: chip, crawl button,
    VI/EN. All buttons have names in EN and VI; `i18n.test` parity green.
- Out of scope: "Chi tiết" link target (Data quality page, S04), SSE, cancelling, dark-theme polish.

## Mid-sprint rework 2026-10-24 (pm) — BE test bugs T1–T4 (dag rev 9; previous: `2-tech-plan.prev-4.md`; also 4-test.fe.md C1/C2/S1)

Inputs: `4-test.be.md` (T1–T4), origin/sprint-03 head `a2c9bc4` (all M5 tasks merged), `contracts/platform.md` **v1.10**
(§2.5 `NO_DATA` message, §2.6 step 2 batching + indices first; v1.9 = `platform.prev-10.md`), data.md §1.2 V2 ("several
symbols per call"), `3-build.S-etf-bars.md` (E1VFVN30 covered by the symbols universe — nothing to add).

### Decisions
- **T4 root cause is request count, not the bucket**: step 2 sends one V2 request per name (1 777 incl. 234 delisted) and the
  live source answers in ≈ 6.7 s each (33 names / 220 s) → ≈ 3 h. The adapter already posts `symbols: [...]` to V2 and
  `parse_bars` already yields several symbols per payload, so the fix is **batching**: ≤ 50 names per request for a catch-up
  (`count ≤ 60`), fewer for a long back-fill (`batch = max(1, min(50, 50_000 // count))` keeps a payload ≈ ≤ 50 000 bars).
  Normal press: 36 requests + 2 index requests → **about 1–4 min** at the observed latency, < 1 min if the latency was per
  request. No threads, no second source (S1 is nominal, mixing it into the source-adjusted `bars_1d_src` series is wrong).
  The batch cap is a live-source assumption with no fixture → spike `S-v2-batch` first (owner.md rule).
- **Initial back-fill** (empty tables, `count = COUNT`) stays long (≈ 220 batches of 8 names) but is resumable as today:
  every V2 response is archived before parsing and the feed commits per batch, so a re-press replays the archive with 0 live
  requests for what it already has; progress shows names done / total.
- **T2 root cause**: the job fetches the indices with the same small `count` and reaches them last (sorted names), so a
  never-finished job never fills `index_1d`; the calendar then has no sessions before 2025. Fix in the feed: **indices
  first, always with `COUNT`** (2 requests, ≈ 6 000 bars each, self-heals an empty `index_1d` on every press). The calendar
  shortcut (`market_view.calendar()` → VNINDEX dates outside `holidays.csv`) stays; benchmark contract unchanged.
  **Ops now (SM, before the build lands):** inside the api container `finvest-crawl bars --date 2026-10-24 --only
  VNINDEX,VN30` (2 live requests, `COUNT` bars) — T2 and FE U1 clear on the live DB today.
- **T1**: the ledger rule becomes "a replay never lowers `rows`" (`EXCLUDED.rows >= crawl_sessions.rows`), which also covers
  the earlier `missed` rule (rows 0). The damaged 10-16 row is repaired by hand from the archived manifest (below), no code.
- **T3**: one message map in the `AnalyticsError` handler (`errors.py`), details are already there.
- **Note for fi-ai-architect** (cannot edit `contracts/analytics.md`): §2.4 still shows `benchmarks[].first_available` as a
  date only; platform.md §2.5 v1.8 made it `string | null` (null = benchmark has no bars at all). Please mirror it.

### Order and lanes (M5)
```
BE-4  S-v2-batch → BE-bars-batch              (fixture + cap, then feed batching + indices first)
BE-5  FIX-session-ledger ∥ FIX-whatif-nodata-msg   (start now; disjoint files)
FE-1  FE-fix-crawl-c1-c2-s1                      (start now; FE-crawl-button merged)
```

#### S-v2-batch — spike (T4): how many symbols does V2 `gap-chart` serve per call, and how fast
- Story: S03-BE ; Side: be ; Effort: medium ; Size: ~20 lines (fixture + report, no production code) ; Lead: sonnet
- Files: `services/crawler/tests/fixtures/vci/gap_chart/batch50-1d-8.json.gz` (new, exact bytes, gzip, ≤ 200 KB; only if
  a ≥ 2-name call returns bars), `SPRINT_DIR/3-build.S-v2-batch.md`
- Change (**rev 2, consult 2026-10-24 16:11** — 14 live calls so far: 5 × HTTP 418 at 15:18, then 9 × `200 []` for every
  multi-name body; no 1-name `countBack 8` control and no live-only 2-name call was ever made, so nothing is settled yet):
  - **Fresh cap: ≤ 6 live requests, ≥ 1 s apart, one at a time by hand (no script loop — the 9-call overrun came from one).**
    Same URL/body shape as `_gap_chart` (`source.py`), project UA, `to` = today 23:59:59 VN. Ladder, stop at the first rung
    that returns `[]`/non-200 **after** rung 1 succeeded:
    1. control `["FPT"]`, `countBack 8` — must return 8 bars (if `[]`: retry once with `countBack 60`; if still empty or
       418 → the client is blocked/throttled, report and stop: verdict "blocked, retry on <date>");
    2. `["FPT","VNM"]` (2 live HOSE), `countBack 8`;
    3. `["FPT","SHB"]` (live HOSE + live HNX — the earlier lists always mixed exchanges), `countBack 8`;
    4. `["FPT","VNM","VTS"]` (live + delisted), `countBack 8`;
    5. 50 live HOSE+HNX names from `symbols`, `countBack 8` → **the fixture**;
    6. spare: 8 live names × `countBack 6000` (back-fill shape) — only if 5 worked.
  - Report every call as a citable line: exact body (incl. the `to` epoch), status, bytes, wall time, symbols returned /
    asked, bars per symbol. A `[]` line is a result too. Verdict = the largest rung that returned bars → **cap = 50 / N / 1**;
    plus: delisted names omitted vs empty (rung 4), and whether a 50-name call is slower than the 1-name control.
- Contract: data.md §1.2 V2 (row marked unverified 2026-10-24); platform.md §2.6 v1.11 (cap pending this spike).
- Acceptance: cap ≥ 2 → fixture committed and `parse_bars(fixture)` returns bars for ≥ 48 distinct symbols with exactly 8
  (or fewer, listed) days each; cap = 1 → no fixture, the report's rung-1 line is the citation BE-bars-batch uses; either
  way the report names every number above and `make test-kernel` is unaffected.
- Out of scope: any feed/adapter change; browser-like headers or any other bot-check work-around (SM 15:18); 1m bars.

#### BE-bars-batch — T4 + T2: step 2 fetches indices first with `COUNT`, then symbols in batches; a press finishes in minutes
- Story: S03-BE ; Side: be ; Effort: high ; Size: ~180 lines (≈ 60 prod + 110 tests + 10 docs) ; Lead: opus
- Files: `services/crawler/finvest_crawler/feeds/bars_1d.py`, `services/crawler/finvest_crawler/adapters/vci/source.py`,
  `services/crawler/finvest_crawler/fetch.py` (one line), `packages/market_data/finvest_market_data/domain/ports.py` (one
  method), `services/crawler/tests/test_feed_bars_1d.py`, `services/crawler/tests/test_adapter_vci.py`,
  `services/crawler/tests/test_fetch.py` (one test), `ops/README.md` (one line)
- Change:
  - `feeds/bars_1d.py` `_run`: (1) `INDICES` first, each as today but **always `count=COUNT`** (ignore the `count` arg for
    indices); (2) symbols in batches of `max(1, min(BATCH_MAX, 50_000 // count))`, `BATCH_MAX` a module constant set to the
    cap `S-v2-batch` reports (50 expected; **if the spike reports 1, `BATCH_MAX = 1`, the batching tests below shrink to
    "batches of 1" and the ≈ 40-request figures in `ops/README.md`/§2.6 are replaced by ≈ 1 780 ≈ 15 min at 2 req/s**) via
    `source.bars(batch, "1d", run_date, count)`; per batch: group bars by symbol, symbols with no bars → `no_trades`,
    `PayloadShapeError`/`HTTPError` → every symbol of the batch `skipped` with `_skip_reason(e)`, `SourceBlocked` → the batch
    and all remaining names `skipped("source_blocked")`, `status blocked` (today's rule); upsert + `commit()` per batch;
    `on_progress(names_done, len(names))` after each batch (names, not batches — §2.6 unchanged); the checksum input stays
    the globally sorted per-bar lines (same digest as the one-by-one run on the same bars).
  - `fetched_at` for `upsert_bars_1d_src` stays the archive file's mtime (replays stay idempotent on the
    `(symbol, trading_date, source, fetched_at)` key): the adapter exposes the name it archives under —
    `MarketDataSource.archive_name(symbols: list[str], count: int) -> str` (ports.py), vci returns the existing
    `<key>-1d-<count>` rule (hash for ≥ 4 symbols); the feed stats `fetcher.archive.path(FEED, run_date, source.archive_name(...))`.
  - `assert fetched + len(no_trades) + len(skipped) == len(names)` kept; `symbols_fetched` counts names that returned bars.
  - `fetch.py` `_blocked`: add status **418** (the live 2026-10-24 15:18 answers: 418 after a 30 s hold, 5 in a row — today
    it is a plain `HTTPError`, retried 3× with back-off, so one blocked name costs ≈ 100 s and never trips `SourceBlocked`;
    that, not the bucket, is the likely origin of the 6.7 s/name average). One test in `test_fetch.py`.
  - `ops/README.md`: a press costs ≈ 40 requests (2 index + ⌈names/BATCH_MAX⌉); a full back-fill ≈ 220 and is resumable (archive).
- Contract: platform.md §2.6 v1.10 (step 2: indices first with full history, batching, progress in names); §4 manifest
  invariant unchanged; data.md §1.2 V2 (+ the spike's cap line).
- Acceptance (`test_feed_bars_1d.py`, fake source recording calls):
  - 120 symbols + indices, `count=8` → calls: `index_bars(["VNINDEX"], d, 6000)`, `index_bars(["VN30"], d, 6000)` **first**,
    then `bars(<50>)`, `bars(<50>)`, `bars(<20>)` with `count == 8`; `on_progress` receives `(1,122), (2,122), (52,122),
    (102,122), (122,122)`; manifest `complete`, `symbols_fetched == 122`, `requests == 5`.
  - `count=6000` → symbol batches of 8. `count=8`, `only=["FPT","HPG"]` → one `bars(["FPT","HPG"])` call, indices not fetched
    (`--only` keeps its meaning).
  - A batch whose payload lacks symbol `XYZ` → `symbols_no_trades == ("XYZ",)`; a batch raising `httpx.HTTPError` → its 50
    names `skipped` with the reason, run `partial`, later batches still fetched; `SourceBlocked` on batch 2 → batch 2 + 3
    names skipped `source_blocked`, status `blocked`, indices already upserted.
  - Checksum: the same bars fed through the batched run and the previous one-by-one fixture run give the same
    `checksum` (test keeps the old expected digest).
  - `test_adapter_vci.py`: `parse_bars(batch50 fixture)` → ≥ 48 symbols × 8 bars (skip when the spike reports cap = 1);
    `archive_name(["FPT"], 8) == "FPT-1d-8"`,
    `archive_name(<50>, 8)` equals the file name `_gap_chart` writes (one request through a fake fetcher, path exists).
  - Runner tests (`apps/api/tests/test_jobs.py`) stay green unchanged (the runner's `count` rule and callbacks are untouched).
- Out of scope: the runner (`apps/api`), threads/concurrency, SSI as a second source, 1m bars, dropping delisted symbols
  from the universe, the calendar shortcut in `market_view.py`.

#### FIX-session-ledger — T1: a `crawl_sessions` replay never lowers `rows`
- Story: S03-BE ; Side: be ; Effort: medium ; Size: ~40 lines (≈ 5 prod + 30 tests + 5 docs) ; Lead: opus
- Files: `packages/market_data/finvest_market_data/infrastructure/repositories.py` (`upsert_crawl_session` only),
  `packages/market_data/tests/test_repositories_db.py`, `ops/README.md` (one line)
- Change:
  - `ON CONFLICT (feed, trading_date) DO UPDATE … WHERE EXCLUDED.rows >= crawl_sessions.rows` — replaces the `missed`-only
    clause (a `missed` manifest has `rows = 0`, so it is covered; equal rows still refresh status/checksum/reason).
    Docstring: "the ledger keeps the richest replay; the manifest file on disk is always written".
  - `ops/README.md`: a smaller replay (e.g. `partial/source_no_longer_serves` the morning after) leaves the ledger row alone.
  - **Repair, by hand (BE tester after merge, not code):** `UPDATE crawl_sessions SET status, rows, symbols_fetched,
    symbols_skipped, symbols_no_trades, checksum, reason` from `data/raw/ticks/2026-10-16/manifest.json`
    (`rows = 145184`); write the numbers in the test report.
- Contract: platform.md §4 (manifest, `crawl_sessions` ledger); data.md §3 `crawl_sessions`.
- Acceptance (db tests): row `partial` rows 145 184, then replay manifest `partial` rows 2 578 → row unchanged (rows, fetched,
  checksum); replay `missed` rows 0 → unchanged; replay `complete` rows 145 184 → status becomes `complete`; replay
  `complete` rows 150 000 → all columns replaced; a first insert for a new day with rows 0 → inserted. The existing
  `missed`-does-not-overwrite test keeps passing.
- Out of scope: `crawl_runs` (one row per run, unchanged), the feed code, repairing other days.

#### FIX-whatif-nodata-msg — T3: `POST /api/whatif` errors carry a human message, not the code
- Story: S03-BE ; Side: be ; Effort: medium ; Size: ~35 lines (≈ 12 prod + 23 tests) ; Lead: sonnet
- Files: `apps/api/finvest_api/errors.py`, `apps/api/tests/test_whatif.py`
- Change: in the `AnalyticsError` handler build `message` from `details` with a small template map, falling back to the code
  when a key is missing: `NO_DATA` → `"no data for {symbol} before {first_available}"` (same wording as `routes/scenarios.py`
  RW-U4) or `"no data for {symbol}"` when `first_available` is absent/null; `SYMBOL_UNKNOWN` → `"unknown symbol {symbol}"`;
  `RANGE_TOO_LARGE` → `"range too large: {first_available} to {last_available}"`; `VALIDATION` → `"{field}: {reason}"` when
  present, else the code. `code` and `details` unchanged; the web keeps using `details` (FE-fix-u5-u7 message).
- Contract: platform.md §2.5 v1.10 (`message` wording); §1.3 envelope.
- Acceptance: `POST /whatif` for HLO before its first bar → 422 body `error.code == "NO_DATA"`, `message == "no data for HLO
  before 2024-06-24"`, `details.first_available == "2024-06-24"`; a fake `AnalyticsError("NO_DATA", {})` → 422, `message == "NO_DATA"`
  (fallback, no `KeyError`); `SYMBOL_UNKNOWN` for `ZZZZ` → `"unknown symbol ZZZZ"`; `test_openapi_current` green.
- Out of scope: scenarios routes (already worded), FE strings, new error codes.

#### FE-fix-crawl-c1-c2-s1 — F-034 C1/C2 + shell S1: start failure shows its cause, no double POST, 24 px top-bar targets
- Story: S03-BE ; Side: fe ; Effort: medium ; Size: ~90 lines (≈ 35 prod + 55 tests) ; Lead: sonnet
- Files: `apps/web/src/app/useCrawlJob.ts`, `apps/web/src/components/CrawlButton.tsx`, `apps/web/src/components/CrawlStatus.tsx`,
  `apps/web/src/components/TopBar.tsx` (CSS only: `min-height: 24px; min-width: 24px` on every button/link in the bar),
  `apps/web/src/components/CrawlButton.test.tsx`, `apps/web/src/components/TopBar.test.tsx`, `apps/web/src/i18n/en.json`,
  `apps/web/src/i18n/vi.json` (keys `crawl.start_failed`, `crawl.unreachable`)
- Change:
  - C1: `start.onError` for anything not 409 sets `startError = {code, message}` from the envelope (`error.code`/`message`,
    platform.md §1.3) or `unreachable` when there is no response; `CrawlStatus` renders it in the Error state (UX app-shell.md
    §Crawl button §Error: "Không bắt đầu được: <cause>" / "Could not start: <cause>"; unreachable → "không kết nối được máy chủ" /
    "cannot reach the server"); cleared on the next successful start. Button returns to idle (unchanged).
  - C2: the button is `disabled` while `start.isPending` **and** the click handler ignores clicks when a start is pending or
    the job is running (guard in the handler, not only in the DOM).
  - S1: every interactive top-bar target ≥ 24×24 CSS px (WCAG 2.2 2.5.8), icon-only variant included; no layout change otherwise.
- Contract: platform.md §1.3 envelope, §2.6 (409 unchanged); UX app-shell.md §Crawl button (Error state).
- Acceptance (vitest, MSW): `POST /api/jobs` → 500 `{error:{code:"INTERNAL",message:"boom"}}` → status line contains
  "Could not start" and "boom", `role="status"`; network error → contains "cannot reach the server"; 409 keeps today's
  "already running" message; two `click` events within the same tick → exactly 1 request; TopBar test asserts
  `getComputedStyle(...).minHeight === "24px"` for Menu, VI, EN and the crawl button (jsdom reads inline/class styles the
  dev sets); the BE tester's `crawl-button.mjs` cases "POST 500 INTERNAL" / "POST network down" pass after merge.
- Out of scope: retry/backoff on start, SSE, other a11y findings, the FreshnessChip.
