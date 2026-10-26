# 3-pr BE-observed-bar (F-013), lead: BE (opus)

## Round 1 (2026-10-26): APPROVE

Reviewed head H = f900046 (63080b3 + clean merge of origin/sprint-05 a87190a, no conflicts).
Size: 10 files, +113/-19 vs plan ~190: within the stop.

Files reviewed: models.py (`Bar.ref` last field, default None), ssi/payloads.py (`refPrice`), ssi/source.py
(0/absent -> None), feeds/bars_1d.py (snapshot unit -> `upsert_bars_1d(observed, fetched_at=archive mtime, ref)`;
V2 units unchanged), jobs/runner.py (`_stock_days` = UNION of both tables for `_count`/`_sessions`;
`symbols_deferred` = count of `deferred` skips), market_view.py (newest src rows + observed rows for dates absent
from src, bounded by `min(end, as_of)` = no look-ahead; `_served` moves; `first_bar_date` min over both), and the
four test files.

Contract: platform.md v1.14 §2.6 `summary.bars_1d.symbols_deferred` = count of `deferred` skips: exact.
data.md §1.4 (1) board bar -> `nominal_kind='observed'`; §3 `bars_1d.ref` = S1 refPrice, NULL when absent: exact.
Units: VND integers (BigInteger columns, `to_vnd(.., "vnd")` like the other board prices); AAA ref 7000 checked
against the fixture in test_adapter_ssi. Money stays int; no SQL string building; no new dependency; no secrets.

Acceptance -> tests: fixture AAA ref = 7000 (adapter); board bars land observed + ref, none in src, replay = same rows
and checksum (feed); stale board -> gaps (existing tests); deferred count (test_jobs); bars_1d-only day served,
src wins on overlap, snapshot moves, first_bar_date (db test, ran green below).

Must-fix: none.

Nits / for the architect (not blocking):
1. Feed acceptance uses stub board bars (ref=100), not the hose fixture end to end; the fixture is covered in the
   adapter test, so together the criterion holds.
2. `repositories.last_bar_dates` and `daily_coverage` still read `bars_1d_src` only (outside the file set): a name
   seen only on the board ranks as an older gap and is not counted in coverage. Gaps exclude names on today's board,
   so no extra request in a normal press; worth a plan line (sa) before step 3 / BE-market-view-ca.
3. Served observed rows are nominal under `price_basis="source_adjusted"`: the planned `# shortcut:` is in place;
   BE-market-view-ca must remove it.

Checks on H:
- kernel (`make test-kernel` via q.sh): exit 0 in 11 s, 297 passed, 31 deselected; ruff clean; mypy no issues
  (5 files); lint-imports 5 kept, 0 broken.
- `pytest -m db -rs` on throwaway db finvest_lead_obsbar_test (compose db, dropped after): exit 0, 31 passed,
  297 deselected, 0 skipped (includes test_a_day_only_in_bars_1d_is_served_and_moves_the_snapshot, which the dev
  could not run).

Merged: f6a6c673 (--no-ff of f900046 into sprint-05, base a87190a), pushed.
