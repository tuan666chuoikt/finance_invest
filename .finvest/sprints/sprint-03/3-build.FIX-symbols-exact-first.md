# 3-build FIX-symbols-exact-first
Result: DONE. `list_symbols` orders by exact-symbol match (case-insensitive) then symbol asc when q is non-empty; limit applies after.
Files: apps/api/finvest_api/routes/symbols.py, apps/api/tests/conftest.py (seed FOC), apps/api/tests/test_symbols.py.
Checks: pytest apps/api 23 passed, 2 skipped; ruff check clean.
Deviation: plan says `q=fp` -> ["FPT","FOC"] in Change but ["FOC","FPT"] in Acceptance. No exact match for "fp", so the algorithm and Acceptance give ["FOC","FPT"]; tests use that (with include_delisted: FOC, FPT, FPTX).
Tests added: q=FPT and q=fpt -> [FPT, FOC]; q=FPT&limit=1 -> [FPT].
Outside-set edits: none. Tester: ruff format --check fails repo-wide (pre-existing), not touched.
