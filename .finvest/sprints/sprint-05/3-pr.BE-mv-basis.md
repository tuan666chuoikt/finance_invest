# 3-pr BE-mv-basis (F-015) — lead review

## Round 1 — APPROVE (fi-tech-lead, BE, 2026-10-26)

Reviewed head H = `888112f5b59c7945843891578a219369fff59c36` (task/sprint-05/BE-mv-basis; already up to date with origin/sprint-05 0d69b8b, no sync commit).

### Files reviewed
- `apps/api/finvest_api/market_view.py` (`SqlMarketView.bars_1d`)
- `apps/api/tests/test_market_view_db.py`

### Plan / size
- File set exactly the plan's two files. Size +57/-18 = 75 lines vs ~80 planned (< 1.5x). No consult needed.

### Contract
- data.md §1.4 (4) last line: simulator basis = `bars_1d` (observed + reconstructed) x our factors, not `bars_1d_src` — honored when the
  symbol has a `reconstructed` row; `bars_1d_src` DISTINCT-ON read kept only as symbol-level fallback (never mixed per date), as the
  plan says, with a `shortcut:` comment naming the S06 removal. R7 `ours` (nominal x Π f over (d, today]) unchanged and now applied to
  every `bars_1d` row. `_served` / G11 unchanged (max fetched_at of served rows + CA rows applied).
- No look-ahead: served rows bounded by `min(end, as_of)`; the reconstructed-row probe is unbounded but only picks the basis, never data.
- No SQL string building; Decimal through `round_vnd`; no new dependency.

### Hand recomputation
- Pre-E day nominal 50,000 (reconstructed rows + observed D1), cash 1,000 ex D, stored f = 0.98: 50,000 x 0.98 = 49,000 on all 5 pre-E
  days. Matches the test. Old code served 50,000 (F0 src, pre-E version) on 4 days and 49,000 on D1 — the step the card describes.

### Tests
- New `test_bars_1d_reads_one_basis_not_mixed_src_versions` fails on the base `market_view.py` (verified: base file restored, 1 failed:
  "(2026-09-28, 50000) != (2026-09-28, 49000)"), passes on H. Covers G11 snapshot and the no-reconstructed-row fallback (VNM 68,000).

### Checks on H (real numbers)
- `make test-kernel` (q.sh lead-mvbasis-kernel): exit 0, 335 passed, 48 deselected; ruff clean; mypy 5 files clean; import-linter green.
- `pytest -m db -rs` on throwaway db `finvest_lead_mvbasis_test` (finvest-live-db-1, dropped after) (q.sh lead-mvbasis-db): exit 0, 48 passed.
  The dev's reported order coupling with `test_migration_round_trip` did not reproduce in a full `-m db` run.

### Must-fix
- None.

### Nits (not blocking; for tester / SA)
1. Once a symbol has any `reconstructed` row, a date present only in `bars_1d_src` (no observed and not yet reconstructed) is not served
   (on base code the test window would also have returned D = 49,000 from src). This is the plan's "never mixed per date" rule; the
   same-press recompute (platform.md §2.6 v1.14 recompute set) reconstructs every newest-src date, so the gap only lasts until the
   recompute runs (e.g. a failed step 3 heals on the next press). Testers: check the latest session is present after a full press.
2. The probe `bars_1d WHERE symbol AND nominal_kind='reconstructed' LIMIT 1` adds one query per call; fine at current scale.

### Merge
Merged into `sprint-05`: merge sha `23a7f8d055a46035971a59634c867d0676eabf9f` (base 0d69b8b, head 888112f). Worktree removed.
