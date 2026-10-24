# 3-build FIX-whatif-nodata-msg
Result: DONE. `AnalyticsError` handler builds `message` from a template map (errors.py `_TEMPLATES`/`_message`), falling back to the code when keys are missing. NO_DATA with null/absent first_available -> "no data for {symbol}".
Files: apps/api/finvest_api/errors.py, apps/api/tests/test_whatif_api.py (card said test_whatif.py; real name is test_whatif_api.py).
Checks: pytest -m "not db" 227 passed; ruff, mypy, lint-imports clean.
Deviation / outside-set edits: domain NO_DATA details lacked `symbol`, so the message could not name it. Added `"symbol": sym` to the two NO_DATA raises in services/analytics/finvest_analytics/sim/whatif.py (additive key; details.first_available unchanged) and updated the two pinning asserts in services/analytics/tests/test_whatif_lumpsum.py.
Tester notes: HLO acceptance is covered by FPT-equivalent test (message "no data for FPT before 2026-10-01"); test_openapi_current unaffected (passes).
