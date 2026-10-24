# 3-build FIX-sessions-repair
Result: done. Files: repositories.py (+`repair_crawl_sessions_from_ticks`), migrations/versions/0008_repair_ticks_sessions.py, test_repositories_db.py (+1 test), ops/README.md (+1 line).
Contract: platform.md §4 v1.12; single UPDATE, idempotent, checksum NULL, no inserts.
Checks: db tests 25 passed (against finvest_test, migration 0008 runs in the upgrade); kernel 233 passed; ruff+mypy+lint-imports green.
Deviations/outside-set: none. Tester: after merge `alembic upgrade head` in api container, expect 2026-10-16 ticks row rows 145184, symbols_fetched 911, checksum NULL.
