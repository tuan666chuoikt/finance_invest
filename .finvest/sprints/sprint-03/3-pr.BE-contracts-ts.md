# 3-pr BE-contracts-ts — round 1 (fi-tech-lead, BE, opus)
Verdict: APPROVE. Reviewed head H=046f2e2075fb8c5adf346862df6800717a824799 (task 492b222 + sync merge of origin/sprint-03 @ 7b1842d, no conflicts).
Files reviewed: apps/api/finvest_api/export_openapi.py (28), apps/api/tests/test_openapi_current.py (5),
packages/contracts/README.md (6), packages/contracts/openapi.json (generated, 640), apps/web/src/api/types.ts (generated, 468).
Size: 39 hand-written lines vs ~80 estimate (+ generated) — within budget. File set matches the plan block exactly.
Contract: codebase.md §6 "Export contracts" row, system.md packages/contracts row, platform.md §2.5 — paths /api/{health,symbols,
symbols/{symbol},bars/1d/status,scenarios,scenarios/{id}}; schemas Scenario, ScenarioIn, SymbolOut, BarsStatus present in types.ts.
Checks (synced head): export --check exit 0; make test-kernel 177 passed / 20 deselected, ruff clean, mypy clean, lint-imports 5 kept 0 broken;
npm run gen produced no diff (types.ts current); npm run typecheck exit 0.
Acceptance proof: added a field to BarsStatus -> test_openapi_current FAILED and --check exit 1 ("stale (15294 vs 15426 chars)"); reverted -> pass.
Must-fix: none.
Nits: (1) --check prints a size summary, not a diff; fine for now (pytest shows the diff). (2) messages say `make contracts`, which only exists
after OPS-web-compose merges (deviation recorded in 3-build). (3) POST /whatif is not in the schema yet; whichever task adds it must re-export
— the kernel drift test enforces this.
Merged: 8880ba65f18469ed142f7eec28d8f784085137d0 into sprint-03.
