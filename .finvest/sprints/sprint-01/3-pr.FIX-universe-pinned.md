# 3-pr FIX-universe-pinned — round 1 (be lead)
**APPROVE** head 216e5b98717ef2a87137d4298a11ce8b37689aea (synced, already up to date with origin/sprint-01).
Files reviewed (11): ports.py, repositories.py, vci/kbs/ssi source.py, feeds/ticks.py, test_adapter_{vci,kbs,ssi}.py, test_feed_ticks.py, test_repositories_db.py. Two extra one-line test edits (kbs/ssi) are necessary for the port change.
Must-fix: none.
Nits: none.
Checks: pytest -m "not db" 82 passed; ruff clean; mypy clean; lint-imports green. The 8 db tests are not run here (no Postgres); test_fail_unfinished_runs read by hand (SQL correct, rowcount 1 then 0). Tester must run pytest -m db.
Merge sha: 09dd6261966630c6dab2621319a9490725ae431a
