# 3-build BE-fix-u4
Result: POST/PUT /api/scenarios return 422 NO_DATA when buy_date < MIN(bars_1d_src.trading_date) of the symbol; no bars = pass.
Files: apps/api/finvest_api/routes/scenarios.py (`_check_first_bar`, called after `_check_symbol` in create and replace), tests/test_scenarios.py (new test), tests/conftest.py (seed FPT bar 2025-01-02).
Contract: platform.md 2.5 v1.8; details {field, symbol, first_available}. No schema change.
Checks: pytest -m "not db" 211 passed; ruff, mypy, lint-imports clean. Diff +29/-4 (plan ~80).
Outside-set edit: tests/test_symbols.py one line (bars_1d first now 2025-01-02 because of the new seed bar).
Not run: db-marked tests (no Postgres here); test_openapi_current is in the kernel set and passed.
