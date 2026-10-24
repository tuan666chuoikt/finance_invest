# 3-build BE-crawl-hooks (F-034)
Result: done. `run_bars_1d(count=COUNT, on_progress=None)` and `run_ticks(on_progress=None)`.
Files: services/crawler/finvest_crawler/feeds/{bars_1d,ticks}.py, tests/test_feed_{bars_1d,ticks}.py (+ `**kw` passthrough in test `run` helpers).
Changes: `count` used in adapter calls and archive name `-1d-{count}`; `on_progress(done,total)` after each name (fetched/skipped/no_trades) in bars, after each symbol of `todo` in ticks (a blocked/missed break is not reported, so a blocked run stops at the last handled index).
Contract: platform.md 2.6 Progress; manifest unchanged (count=7 run has the same status/rows/checksum as COUNT run on the fixture).
Checks: kernel (pytest -m "not db", ruff, mypy, lint-imports) exit 0: 212 passed, ruff and mypy clean. Diff +50/-11 (size ~70).
Deviations: none. Outside-set edits: none.
Tester notes: ticks test serves the FPT fixture for A32 (no A32 fixture file exists). CLI unchanged.
