# 3-build AI-analytics-scaffold
Result: done. New workspace package services/analytics (finvest_analytics): domain/{models,ports,money}.py, fixtures.py, tests (golden, hypothesis max_qty property, as_of guard property). Root pyproject: workspace member, dependency, source, hypothesis dev dep, importlinter root + contract.
Contract: Figure/How per analytics.md 1.1, WhatIfRequest per 2.4; MarketView per plan block (reduced S03 port).
Checks: make test-kernel exit 0 (133 passed, ruff, mypy, lint-imports 5 kept); services/analytics 4 passed.
Deviations: max_qty starts from the floor formula then adjusts by whole lots, because the booked fee is rounded half-up (a pure floor can overshoot cash by 1 VND). Added Ctx(as_of, rules_version) for figure(). AnalyticsError lives in money.py (no errors file in the set). Not under mypy strict (config scoped to market_data).
Outside-set edits: uv.lock regenerated.
