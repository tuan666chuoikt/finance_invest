# 3-build BE-fix-runner-now
Result: DONE. B-05-5 fixed.
Files: apps/api/finvest_api/jobs/runner.py (step 2 now `_target(_now())`; `today` for steps 1,3,4 unchanged), apps/api/tests/test_jobs.py (+1 parametrized test: 14:50 then 15:06 -> that day; 14:50 twice -> previous session).
Checks: kernel (not db) 339 passed; ruff clean.
Note: run pytest with PYTHONPATH=<worktree>/apps/api, else the shared venv imports the main checkout's finvest_api.
Deviations / outside-set edits: none.
