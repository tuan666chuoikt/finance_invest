# 4-test.be sprint-04 (RW scope: ledger-rank, smoke-dsn, curve)
Verdict: FAIL-minor (2 bugs, none blocks merge of the code; both are data/doc follow-ups). Worktree test-be-04 @ 5ab2655. No new tests written, no code edited.

| Item | Check | Result |
|---|---|---|
| T5b BE-rw-ledger-rank | `pytest -m db` incl. test_status_rank_is_never_lowered (complete 4_949 then blocked 10_357 stays complete) | PASS, 27 passed |
| T6 db suite runs | `-m db` on throwaway `finvest_be04_test` via host 127.0.0.1:55432 | 27 passed, 0 skipped (db port published: live db shows 127.0.0.1:55432) |
| T5c orphan 10-24 row | smoke (2) weekend rows / crawl_sessions bars_1d | PASS: 0 weekend rows, no 2026-10-24 row; latest is 10-23 blocked 10357 |
| make smoke | runs, 3a/3b output ok | PASS; check (1) VNINDEX ratio returns 4 rows (see B1) |
| AI-rw-curve | services/analytics | PASS 42 passed |
| Kernel | `pytest -m "not db"` | 259 passed, 27 deselected |
| Live api | 127.0.0.1:8001 | up (/health 404, route not present, not tested further) |

## Bugs
- B1 (medium, owner: data fix task / sa decision): VNINDEX index_1d legacy rows 2004-07-02, 2004-07-22, 2004-09-06 (value ~1e14, ratio ~1e10) and 2007-08-16 (value 0) fail smoke check (1). Known from build note; smoke stays red until repaired.
- B2 (low, owner: build OPS-rw-smoke-dsn): Makefile comment suggests `make test-db FINVEST_TEST_DB=finvest_test_<branch>`, but the tests skip unless the db name ENDS with `_test` (test_repositories_db.py:27). Following the suggestion gives "27 skipped" and exit 0 (silent false green; I hit it). Fix the comment to `finvest_<branch>_test` or make skip loud.
Note: a worktree has no .env, so `make test-db` there reads an empty password; run from main checkout or pass PGPASS.
Cleanup: dropped throwaway dbs; no crawl pressed.
