# BE-calendar — build report
Result: DONE. Branch task/sprint-02/BE-calendar.
Files: packages/market_rules/{pyproject.toml,finvest_rules/{__init__,calendar}.py,holidays.csv,tests/test_calendar.py}; root pyproject (member, source, import-linter contract); services/crawler pyproject + cli.py + tests/test_cli.py; uv.lock.
Change: `day()`, `trading_days()`, `CalendarNotMaintained` (years outside 2025-2026 raise); CLI prints `{"skipped": kind, "name": ...}`, exit 0, no manifest.
Checks: `make test-kernel` exit 0: 102 passed, ruff ok, mypy ok, lint-imports ok (new contract). Manual: `finvest-crawl ticks --date 2026-09-02` prints skip line.
## Deviations / data flags (PM/sponsor please verify on hsx.vn)
- 2026-01-02 added as holiday: press (thitruongtaichinhtiente.vn) says HOSE/HNX closed 1/1 AND 2/1/2026 (swapped day); data.md §1.3 lists only 01/01. Remove the row if the notice says otherwise.
- 2025 rows come from press reports of HOSE notices (URLs in `source`); 2025-01-01 and 2025-04-07 (Hùng Kings) are from Labor Code, no HOSE notice found.
- 2025-05-02 and 2025-09-01 are adjacent-day closures per press.
## Outside-set edits: none. Dockerfile already copies packages/.
## Tester notes: 2024 and 2027 dates raise CalendarNotMaintained by design; the CLI will traceback on them (BE-scheduler should handle).

## Fix round 1
Removed unverified 2026-01-02 holiday row (not in data.md 1.3); added assertion day(2026-01-02).kind == "trading". make test-kernel: 102 passed, ruff/mypy ok. PM to add the row once verified on hsx.vn.
