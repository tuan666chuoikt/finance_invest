# Build: BE-scenarios-api (F-055)

Result: done. `scenarios` table (migration 0006, raw DDL per data.md §3) and GET/POST/PUT/DELETE `/api/scenarios`.

Files: migrations/versions/0006_scenarios.py, finvest_api/scenarios/{__init__,tables,schemas}.py,
routes/scenarios.py, main.py (include_router), tests/conftest.py (create_all scenarios metadata), tests/test_scenarios.py.

Contract: platform.md §2.5. 400 VALIDATION with details.field (name, amount_vnd strict int 1..1e11, sell_date >= buy_date),
422 SYMBOL_UNKNOWN (delisted accepted), 404 NOT_FOUND, timestamps UTC stored, serialised +07:00 via vn_iso.
List order: created_at desc, id desc (tie-break).

Checks: ruff clean; `pytest apps/api`: 10 passed, 1 skipped (db round-trip test skipped, no FINVEST_DATABASE_URL here).
Diff: 212 insertions (plan ~230).

Deviations: none. Outside-set edits: none.
Tester notes: run the `db`-marked test_migration_round_trip against the compose db; SQLite tests use an Integer id variant.
