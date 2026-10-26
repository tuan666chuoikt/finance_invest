# PR BE-fix-v5-iss (B-05-1) — lead review

## Round 1 — 2026-10-26 — fi-tech-lead (BE, opus) — **APPROVE**

Reviewed head H = `ee9ab33f342111ad89d710dd02d25304a538ec84` (dev d5bee80 + clean merge of origin/sprint-05 70a16d5, no conflict).

### Files reviewed
- `services/crawler/finvest_crawler/adapters/vci/events.py` — `_map` ISS order: "quyền mua" guard first, then
  "cổ tức bằng cổ phiếu"/"thưởng" → stock_dividend, `_NON_ADJUSTING` → listing_change, "phát hành thêm" → rights last.
  `parse_events`: listing_change without `exrightDate` kept with ex_date NULL, no anomaly; adjusting kinds without it stay unmapped. DIV untouched.
- `packages/market_data/.../domain/models.py` — `ex_date: date | None` (outside set, mechanical; column already nullable in 0010/tables.py).
- `services/crawler/finvest_crawler/feeds/recompute.py` — `if a.ex_date` filter (outside set, needed: a None key would break `sorted(events)`;
  covered by the db test, whose HPG CBCNV row has no exrightDate).
- `services/crawler/tests/test_adapter_vci_events.py`, `tests/test_feed_corporate_actions.py`, `tests/fixtures/vci/events/HPG-2026.json`
  (`cmp` against gunzip of `test-be-05/.../HPG-p0.json.gz`: identical, unedited).

### Plan / contract
- File set as planned + 2 mechanical one-liners, explained in the build note. Size 132+/10- (fixture 1 line) vs ~110 → 1.2×, under 1.5×.
- data.md §1.2 V5 kinds, VN§6 v1.2, consult answer Q1/Q2 honoured. ex_date NULL (plan) vs "exrightDate or listingDate" (ai answer):
  the plan chose NULL; followed.
- Title-order risk checked on all 26 captured payloads: 612 ISS titles, each hits exactly one keyword
  (155 cbcnv, 147 cổ tức bằng cổ phiếu, 102 riêng lẻ, 80 thưởng, 63 trái phiếu chuyển đổi, 46 quyền mua, 16 sáp nhập, 3 đấu giá); 0 ambiguous, 0 unmatched.
- Other ex_date readers: market_view SQL range filters drop NULL; repo ordering puts NULL last; anomaly insert gets ex_date via `ex.get`
  (nullable). analytics `fixtures.py` is test-only.

### Money check (by hand)
- factor 10:1 = 10/11 → 0.909090909091 (12 places half-up); nominal 2026-05-22 = 23,955 / 0.909090909091 = 26,350.49999… → 26,350 VND
  (test accepts 26,350 or 26,351; old mapper left 23,955). Ratios 10%→10:1, 20%→5:1, 30%→10:3, 35%→20:7 correct.

### Tests fail without the change
- Old `events.py` restored temporarily: 2 new unit tests FAILED (HPG fixture, title order); restored, tree clean. Dev reports the db test fails too (old `_map` path is its own run 1).

### Checks on H (real numbers)
- `make test-kernel` (q.sh lead-v5iss-kernel): exit 0, 341 passed, 61 deselected; ruff clean; mypy no issues; import-linter contracts KEPT.
- `pytest -m db -rs services/crawler packages/market_data` on throwaway db `finvest_lead_v5iss_test` (finvest-live-db-1, dropped after)
  (q.sh lead-v5iss-db): exit 0, 54 passed, 0 skipped (includes `test_b05_1_a_rerun_over_the_archive_maps_the_stock_dividends`).

### Must-fix
- None.

### Nits (not blocking)
1. `events.py` `_map` docstring says listing_change is "never in adj_factors"; with an ex_date it still enters `events_by_ex_date`
   and writes a factor-1 row (ai plan: `listing_change` → 1) and, before the first V2 bar, an `adj_factor_no_pre_close` anomaly.
   Numbers are unaffected; ~336 listing_change rows will add factor-1 rows / anomaly noise. For the architects: decide whether
   recompute should skip `listing_change` entirely (one filter in `recompute._one`).
2. `test_feed_corporate_actions.py`: `monkeypatch.undo()` also undoes the `conn` fixture's setenv; harmless now (conn already open),
   `monkeypatch.setattr(events, "_map", real)` would be tighter.

### Merge
- merge sha: `85efde3432d31cb2148fe0094f967c5106ada2aa` (base 70a16d5, pushed to origin/sprint-05); worktree removed.
