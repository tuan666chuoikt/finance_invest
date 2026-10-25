# 3-pr OPS-fix-testdb-doc — round 1 (fi-tech-lead, BE, opus)
Verdict: APPROVE. Reviewed head H=95ce7c326e3debb9b5141f12585d5c1604bbbbe9 (synced with origin/sprint-04: already up to date).
Files reviewed: Makefile, ops/README.md. Size: 5+/4- vs ~12 estimate (within 1.5x). File set exactly as planned; no contract drift
(ops/README.md text matches the plan block).
Acceptance (run in worktree, COMPOSE_PROJECT_NAME=finance_invest, PGPASS passed from main .env, `make -s` so the URL is not echoed):
1. `make test-db FINVEST_TEST_DB=finvest_x` -> prints "FINVEST_TEST_DB must end in _test (tests drop all tables)", recipe exit 1 (make exit 2). PASS.
2. `make test-db FINVEST_TEST_DB=finvest_opsfix_test` -> 27 passed, 259 deselected, 0 skipped (`-rs` active). PASS.
3. `rg -n 'finvest_test_<branch>' Makefile ops/README.md` -> no match. PASS.
Kernel (`make test-kernel`): 259 passed, 27 deselected; ruff clean; mypy clean; import-linter contracts KEPT.
Must-fix: none.
Nits (no action needed in this task):
- Plan acceptance says "exits 1"; make reports 2 for a failed recipe. Wording only; the guard works.
- Pre-existing: the test-db pytest line has no `@`, so make echoes the URL with the password; worth an `@` in a later ops task.
- Pre-existing: run from a worktree, `docker compose exec` uses the worktree's project name, so createdb fails quietly (`|| true`); the README's
  "run from the main checkout" note covers it.
Merged: 860af496f5bf87cc4221deb7c779d9730d4eee69 into sprint-04 (base 931ce32).
