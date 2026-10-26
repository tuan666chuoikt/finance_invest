# 3-build OPS-fix-guards
Result: done. Audit suffixes += .js .jsx .mjs .cjs; test db port 15433 (compose + README line 79).
Files: apps/api/tests/test_no_broker_audit.py (+ mjs probe test), docker-compose.test.yml, README.md. ~9 lines.
Checks: test_no_broker_audit.py 6 passed (main .venv python; worktree `uv run` has no pytest). Compose config: see below.
Deviations/outside-set: none. No unmerged task branch touches these files.

## Fix round 1
E501 fixed: SUFFIXES module constant in test_no_broker_audit.py. make test-kernel exit 0 (342 passed, ruff+mypy clean).
