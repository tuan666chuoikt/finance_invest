# 3-build BE-whatif-api
Result: done. Branch task/sprint-03/BE-whatif-api.
Files: apps/api/finvest_api/routes/whatif.py (new), errors.py (AnalyticsError handler), main.py (include_router),
apps/api/tests/test_whatif_api.py (new), packages/contracts/openapi.json + apps/web/src/api/types.ts (regenerated).
What changed: `get_market_view(engine)` yields a per-request `SqlMarketView`; `POST /api/whatif` takes `WhatIfRequest`,
returns `run_whatif(req, view)` unchanged. `AnalyticsError` -> VALIDATION 400; SYMBOL_UNKNOWN / NO_DATA / RANGE_TOO_LARGE 422;
`details` passed through (body shape platform.md 1.3, message = code). Pydantic errors keep the generic 400 handler.
Contract honored: analytics.md 2.1/2.3/2.4; platform.md 1.3, 2.5 (POST /whatif row + mapping).
Checks: `make test-kernel` exit 0, 183 passed, ruff + mypy clean; `export_openapi --check` clean after regenerate.
6 new tests: golden 001 (liquidation_vnd.value "10610975", approximate True), amount 0 -> 400, fill_rule open -> 400,
unknown symbol -> 422 SYMBOL_UNKNOWN, buy before first bar -> 422 NO_DATA with details.first_available "2026-10-01".
N2 budget: 20 requests, constant series 2016-01-04..2026-01-04, 10-year range, FixtureView: **0.170 s total** (limit 2 s).
Note: budget is on the fixture view; it excludes SQL latency of SqlMarketView on Postgres (needs a db-marked measurement).
Deviations: no `make contracts` target exists (BE-contracts-ts note: OPS-web-compose adds it); regenerated with
`python -m finvest_api.export_openapi` then `npm --prefix apps/web run gen`. Response schema is an untyped object (route
returns the engine dict as-is), so types.ts has the request type only.
Outside-set edits: none.
Notes for tester: error body `message` equals the code (AnalyticsError carries no text). Other unmerged branches that
change routes make openapi.json stale after merge; rerun the export on sprint-03.
