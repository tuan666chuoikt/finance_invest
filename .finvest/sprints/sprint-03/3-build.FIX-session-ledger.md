# 3-build FIX-session-ledger
Result: done. `upsert_crawl_session` now uses `WHERE EXCLUDED.rows >= crawl_sessions.rows` (covers `missed`, rows 0); `or_` import dropped.
Files: repositories.py (upsert_crawl_session), tests/test_repositories_db.py (+2 tests), ops/README.md (+1 line).
Checks: market_data pytest with a throwaway timescaledb container (db finvest_test): 27 passed; ruff clean. ~20 lines diff.
Contract: platform.md §4, data.md §3 honored. Existing missed-does-not-overwrite test passes.
Deviations/outside-set edits: none.
Tester: repair 2026-10-16 by hand after merge from data/raw/ticks/2026-10-16/manifest.json (rows 145184); record numbers in the test report.
