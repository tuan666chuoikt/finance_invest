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
- Story: F-031 ; Side: fe ; Effort: medium ; Size: ~230 lines ; Lead: sonnet
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
- Story: F-055 ; Side: fe ; Effort: medium ; Size: ~250 lines ; Lead: sonnet
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
