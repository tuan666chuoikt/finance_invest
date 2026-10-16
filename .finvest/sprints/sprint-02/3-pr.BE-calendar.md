# 3-pr BE-calendar, round 1 (lead)
Verdict: CHANGES_REQUIRED. Reviewed head H=44dd869ee29cedf63eb214ac1b6045940b796988 (synced with origin/sprint-02, already up to date).
Files reviewed: all 10 (calendar.py, __init__.py, holidays.csv, pyproject x3, test_calendar.py, cli.py, test_cli.py; uv.lock skipped).
Size: 140+/8- vs ~150 estimate: ok.
Must-fix:
1. packages/market_rules/finvest_rules/holidays.csv:15 (2026-01-02 row): not in the contract (data.md §1.3 / tech-plan list only 01/01 for the New Year; "never inferred", PR-002). The source is a press article and the dev flagged it unverified. A wrong closed row makes the CLI skip a real trading day. Remove the row; PM adds it once verified on hsx.vn. Proof: add an assertion in packages/market_rules/tests/test_calendar.py::test_holiday_weekend_trading that day(date(2026,1,2)).kind == "trading" (or drop it if PM verifies first and records the notice).
Nits: 2025 rows rely on press/Labor Code (flagged by dev; PM to verify, not blocking). CLI traceback on unmaintained years is left to BE-scheduler (dev note). test_cli imports pytest inside the function.
Checks on H: make test-kernel exit 0: 102 passed, ruff ok, mypy ok, lint-imports ok.
Acceptance examples (2026-09-02 holiday, 08-22 closed, 10-16 trading, 10-18 weekend, trading_days 08-28..09-03 = [08-28, 09-03], 2027 raises) verified by reading code + tests.

# 3-pr BE-calendar, round 2 (lead)
Verdict: APPROVE. Reviewed head H=36b76b88488dabaaf6adb1f00e87a29cd277bac2 (clean sync merge of origin/sprint-02, no conflicts).
Must-fix 1 resolved: 2026-01-02 row removed from holidays.csv, test asserts day(2026-01-02).kind == "trading".
Size: 140+/8- vs ~150: ok. Checks on H: make test-kernel exit 0: 103 passed, ruff ok, mypy ok.
Merge sha: 2e8595923ea52e9ec1e5f64447210033de6522f3
