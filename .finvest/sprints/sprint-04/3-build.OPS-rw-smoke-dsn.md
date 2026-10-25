# 3-build OPS-rw-smoke-dsn
Result: built, 37 lines (plan ~70). Files: Makefile (test-db, smoke; FINVEST_TEST_DB override; password read from .env), docker-compose.yml (db ports 127.0.0.1:55432:5432), .env.example (comment), ops/smoke.sql (new), ops/README.md (test db, repair, Manual fixes), README.md (1 line).
T5c: ran on live db: `DELETE 1` (row was bars_1d 2026-10-24 partial). Logged in ops/README.md.
Smoke on live db: check (2) 0 rows. Check (1) returns 4 rows, NOT 0: VNINDEX 2004-07-02, 2004-07-22, 2004-09-06 (value ~1e14, ratio ~1e10) and 2007-08-16 (value 0). Legacy back-fill data errors; needs a data fix task (decision for lead/sa).
Not verified: `make test-db` 26+1 db tests: the live db container was created before the port mapping; it needs `docker compose up -d db` from the main checkout after merge (recreates db container only, data/pg kept; brief api downtime). `make -n` output checked. Tester: run that first, then make test-db.
Deviations: none. Outside-set edits: none.

## Fix round 1
Merged origin/sprint-04. Must-fix 1: F-030 guard in services/crawler/tests/test_qa_sprint01.py now asserts crawler no ports, db exactly 127.0.0.1:55432, api exactly 127.0.0.1:8001, every published port on 127.0.0.1 (renamed test_f030_compose_publishes_only_loopback). `make test-kernel` green; test fails when db mapping is 0.0.0.0:55432 (checked, reverted).
Outside-set edits: services/crawler/tests/test_qa_sprint01.py (lead-authorized). Nits not done.
