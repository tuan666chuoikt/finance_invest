# 3-build QA-S01-tests
Result: DONE. Merged origin/test/sprint-01/be into task/sprint-02/QA-S01-tests.
Files: services/crawler/tests/test_qa_sprint01.py (+199), the only diff vs origin/sprint-02.
Checks: make test-kernel exit 0: 99 passed, 8 deselected; ruff, mypy, lint-imports clean.
Tests asserting v1.2 no_ticks: none failed on sprint-02 head (BE-status-no-trades not yet merged; it may need to rewrite them).
Deviations / outside-set edits: none. No production code changed.
