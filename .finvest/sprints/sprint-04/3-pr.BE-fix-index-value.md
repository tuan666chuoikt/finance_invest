# 3-pr BE-fix-index-value — round 1 (fi-tech-lead, BE, 2026-10-25)

Verdict: APPROVE
Reviewed head H: d424189 (38f33ae + chore merge of origin/sprint-04 860af49, no conflicts)

## Files reviewed
- services/crawler/finvest_crawler/adapters/vci/source.py: band constant + index-only drop; stocks always pass ref = v*c (0, not None), so the
  stock path cannot reach the new branch. o/h/l/c/v kept.
- packages/market_data/.../repositories.py: `repair_index_1d_value` via SQLAlchemy core; compiles to `value / CAST(v AS NUMERIC)` (true division,
  no integer truncation); idempotent (`value IS NOT NULL`).
- apps/api/migrations/versions/0009_repair_index_1d_value.py: same pattern as 0008; downgrade no-op.
- services/crawler/tests/test_adapter_vci.py, packages/market_data/tests/test_repositories_db.py: cover acceptance (1) and (2); both fail without
  the change (ratio 1e10 kept / function missing). Two existing tests got realistic volumes so they stay in band — fine.

## Checks
- Plan/file set: exactly the 5 planned files. Size +76/-5 vs ~90 (within 1.5x).
- Contract data.md §1.2 (index value nullable VND): honored, no API change.
- Hand recompute: 20000.5 million VND = 20_000_500_000; /2 = 1.0e10 (out), /400_000 = 50_001 (in). Matches tests.
- Lead probe on throwaway db: rows (v=0,value=5), (v=1,value=10_000_001), (v=1,value=10_000_000), (v=2,value=199) -> repair returns 3, only the
  1e7 edge row kept; no division-by-zero on v=0; edges inclusive like the adapter.
- `make test-kernel`: 260 passed, 28 deselected; ruff all checks passed; mypy no issues; lint-imports pass.
- `pytest -m db` (finvest_lead_be_fix_index_value_test, dropped after): 28 passed.
- Acceptance (3) (`make smoke` on live db after `make up`) is the tester's.

## Deviation accepted
- Adapter also drops when vol == 0, matching the repair's `v = 0` and smoke check (1); otherwise a re-crawl would restore nulled values.

## Must-fix
None.

## Nits (not blocking)
1. repositories.py: `.values(value=None)` is dedented relative to the chain; cosmetic.

## Merge
- Merged by sm.sh: merge 7894e44d5da8ca0bc2a5070c7f5754f37c688af8 into sprint-04 (base 696ee6d). The base gained FE-fix-table and FE-fix-shell
  (apps/web only, 13 files) after the sync; no overlap with this diff's BE files, so the BE checks above still hold.
