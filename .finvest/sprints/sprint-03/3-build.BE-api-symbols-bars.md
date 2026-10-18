# 3-build BE-api-symbols-bars
Result: DONE. Branch task/sprint-03/BE-api-symbols-bars.
Files: apps/api/finvest_api/{deps,errors}.py, routes/{__init__,symbols,bars}.py, main.py (router wiring, get_engine moved to deps), tests/{conftest,test_symbols,test_bars_status}.py, test_health.py (import).
Contract: platform.md 1.2/1.3/2.5 rows 1-3; timestamps `+07:00` with ms (ADR-S-006); naive (SQLite) timestamps read as UTC.
Checks: `make test-kernel` green: 134 passed (7 in apps/api), ruff clean, mypy ok, import-linter 4 kept.
Notes: q is matched as symbol prefix (upper-cased) OR ILIKE substring on names; `%`/`_` in q are escaped. Symbol path param is upper-cased. Validation error 400 uses pydantic msg and details.field=loc[-1]. Fixture has 4 FPT bar rows (14, 15, 16 x2 fetched_at). ILIKE on SQLite lowercases ASCII only; Postgres handles Vietnamese case.
Outside-set edits: none.
