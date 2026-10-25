# 3-build OPS-fix-testdb-doc
Result: done. Files: Makefile, ops/README.md (~6 lines).
- test-db refuses names not ending in `_test` (make exits 2 = make's code for a failed recipe, message printed); pytest runs with `-rs`.
- Comment and README now say `finvest_<branch>_test`; README notes worktrees have no `.env` (run from main checkout) and skips print.
Checks: `make test-db FINVEST_TEST_DB=finvest_x` -> message, nonzero; `..._x_test` -> 27 passed, 259 deselected. rg `finvest_test_<` finds nothing.
Deviations: none. Outside-set edits: none. Tester: .env was temporarily copied into the worktree for the run and removed.
