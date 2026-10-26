# 3-build BE-fix-ca-budget
Result: done. `ca_budget` 40 -> 28; `ca_symbols_in_order` now `ORDER BY tier, ca_checked_at NULLS FIRST, symbol` (CASE WHEN tier = 2 dropped), docstring cites data.md 1.2 V5 v1.8.
Files: services/crawler/finvest_crawler/settings.py, packages/market_data/finvest_market_data/infrastructure/repositories.py, services/crawler/tests/test_feed_corporate_actions.py (asserts Settings().ca_budget == 28 in the budget test, which still defers the rest), packages/market_data/tests/test_repositories_db.py (second VN30 name never checked: order [VN30N, VN30M, SCEN, NULLS, OLD, NEW]).
Checks: crawler tests 176 passed, 24 skipped; market_data test_repositories_db (real db finvest_ca_budget_test) 30 passed.
Deviations: none. Outside-set edits: the db test file (the acceptance order test lives there). Tester note: the venv resolves packages from the main checkout; run with PYTHONPATH set to the worktree's services/crawler and packages/*.

## Fix round 1
Must-fix 1 (E501 at test_repositories_db.py:414): trailing comment moved to its own line. ruff check services packages rc checked above; merged origin/sprint-05; head d9620e3.
