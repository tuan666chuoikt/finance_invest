# 3-pr BE-whatif-api — round 1 (fi-tech-lead, BE, opus)

**Verdict: APPROVE**. Reviewed head H = 413855d37e129bb7a082ab85253714a83c1d7622 (ae4d770 + clean sync merge of origin/sprint-03 at 3b4bf5c, no conflicts).

Files reviewed: apps/api/finvest_api/routes/whatif.py, errors.py, main.py, apps/api/tests/test_whatif_api.py;
packages/contracts/openapi.json + apps/web/src/api/types.ts (generated, checked by regenerate only).
Size: 97 hand-written lines (+185 generated) vs ~160 estimate — within budget.

Checks
- Plan/file set: exactly the plan's set; no outside-set edits.
- Contract: platform.md §2.5 mapping VALIDATION 400 / SYMBOL_UNKNOWN, NO_DATA, RANGE_TOO_LARGE 422, `details` passed through;
  §1.3 envelope shape. The status map is total: `AnalyticsError.__init__` asserts code ∈ CODES (same four), so no KeyError → 500.
  Pydantic errors keep the generic 400 handler. Response is the engine dict unchanged (analytics.md §1.4 envelope).
- Money (hand recompute, golden 001): qty = floor(10,000,000 / (93,500×100×1.0015)) ×100 = 100; buy fee 14,025; cash 635,975;
  MV 10,000,000; sell fee 15,000; tax 10,000; liquidation 10,610,975; pl_pct 6.1098 — matches the live response.
- No floats on the wire: walked the full golden-001 JSON response, 0 float values; data_snapshot "2026-10-15T15:30:00+07:00".
- Extra probes: sell<buy → 400 VALIDATION {reason: sell_before_buy}; buy after last bar → 400 VALIDATION {last_available} (analytics.md §2.4).
- Layering: lint-imports 5 kept, 0 broken. Security: no secrets, SQL via SQLAlchemy Core (existing SqlMarketView), body validated by Pydantic.
- Tests: the five acceptance cases + N2 budget each present and would fail without the route/handler.

Results on H
- `make test-kernel`: exit 0 — 194 passed, 20 deselected; ruff clean; mypy clean; import-linter 5 kept.
- `pytest apps/api/tests/test_whatif_api.py -s`: 6 passed; **N2 budget: 20 requests in 0.107 s** (limit 2 s, FixtureView).
- `make contracts` after sync: tree clean (no drift).

Must-fix: none.

Nits (not blocking)
1. errors.py:27 `message` = code ("VALIDATION"); §1.3 wants an English message. Fine while the web maps `code`; a short
   text on AnalyticsError would be nicer later.
2. test_whatif_api.py:31 asserts `approximate is True` but not `"approximate" in flags` (§1.4 asks both); engine tests cover it.
3. N2 is measured on FixtureView only; SqlMarketView latency on Postgres is unmeasured (tester: a `-m db` timing would close it).

Merged: 58156bbda09c77f7ba8077c53cd5caf6455450cb into sprint-03 (base 3b4bf5c, head 413855d).
