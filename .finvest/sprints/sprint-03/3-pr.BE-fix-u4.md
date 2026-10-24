# 3-pr BE-fix-u4

## Round 1 (fi-tech-lead, BE, opus), 2026-10-24
Verdict: **APPROVE**. Reviewed head H = `7161e6e` (already up to date with `origin/sprint-03` at `4c5037e`; no sync commit).

### Files reviewed
- `apps/api/finvest_api/routes/scenarios.py`: `_check_first_bar` = `MIN(bars_1d_src.trading_date)` per symbol, the same query as
  `SqlMarketView.first_bar_date` (what-if uses it, so save and compute agree on the first bar). `None` → pass (platform.md §2.5
  v1.8 "no bars at all is not refused"). Called after `_check_symbol` in POST and PUT, inside the same transaction, before the
  write. Error: 422 `NO_DATA`, details `{field:"buy_date", symbol (upper-cased), first_available ISO}` exactly as §2.5 v1.8.
  Bound parameters only (SQLAlchemy core), no string SQL.
- `apps/api/tests/conftest.py`: one seed bar FPT 2025-01-02 (bars_1d_src only, as planned).
- `apps/api/tests/test_scenarios.py`: `test_buy_date_before_first_bar` covers every acceptance line: 2020-01-02 → 422 + exact
  details + list empty; 2025-01-02 (boundary) → 201; VNM no bars → 201; PUT bad date → 422 and the row unchanged. Fails
  without the change (first POST would be 201).
- `apps/api/tests/test_symbols.py` (outside the file set, 1 line): expected `bars_1d.first` moves to 2025-01-02 because of the
  planned seed bar. Mechanical consequence, accepted.

### Plan / size
+29 / -4 over 4 files vs plan ~80: within budget. No schema change (`test_openapi_current` green in kernel).

### Must-fix
None.

### Nits (no action required)
1. `_check_first_bar` duplicates `SqlMarketView.first_bar_date`'s query; fine at this size, merge them if a third caller appears.
2. Contract wording (architect, sa): §2.5 v1.8 says the details are "the same `POST /whatif` returns", but what-if returns only
   `{first_available}`; scenarios return the superset `{field, symbol, first_available}`. The web reads `first_available` from
   both, so no behaviour gap; tidy the sentence on the next contract revision.
3. `buy_date` parameter is untyped (`date`); mypy is clean, cosmetic.

### Checks on H
- `make test-kernel` via q.sh: exit 0, **211 passed, 22 deselected**; ruff "All checks passed!"; mypy "no issues"; import-linter
  contracts KEPT.
- `uv run pytest -m db -q apps/api/tests` against compose `finvest_test` (container IP; container started for the run and
  stopped after): **2 passed, 26 deselected**.

### Merge
`sm.sh merge BE-fix-u4 7161e6e` → merge sha **`b61e76c`** into `sprint-03` (base had moved to `7b0411e` = FE-fix-u1: 6 files
outside `apps/api`/`services`/`packages`, so BE checks on H still hold). Worktree removed.
