# 3-build BE-contracts-ts
Result: done. Files: apps/api/finvest_api/export_openapi.py, apps/api/tests/test_openapi_current.py, packages/contracts/{openapi.json,README.md}, apps/web/src/api/types.ts (generated).
Contract: codebase.md §1/§6, platform.md §2.5. types.ts has Scenario, ScenarioIn, SymbolOut, BarsStatus.
Checks: export --check exit 0; make test-kernel 166 passed, ruff/mypy clean; web typecheck passes.
Deviations: no `make contracts` target added (plan says OPS-web-compose adds it; Makefile untouched to avoid conflict). Until then: export_openapi then `npm --prefix apps/web run gen`.
Notes for tester/lead: other unmerged task branches that change routes/models (BE-api-symbols-bars, BE-scenarios-api, BE-market-view) will make openapi.json stale after merge; rerun the export on sprint-03 after they land.
Outside-set edits: none.
