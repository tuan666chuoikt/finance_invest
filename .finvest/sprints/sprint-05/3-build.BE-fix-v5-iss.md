# Build BE-fix-v5-iss (B-05-1) — DONE

Branch `task/sprint-05/BE-fix-v5-iss`, head d5bee8058b47630769e5f8c9cac134c9d2d3809e (branch-only, no gh).

## What changed
- `adapters/vci/events.py` `_map` ISS branch (NFC+casefold title): "quyền mua" -> rights (price regex unchanged);
  "cổ tức bằng cổ phiếu" / "thưởng" -> stock_dividend; cbcnv, esop, riêng lẻ, trái phiếu chuyển đổi, sáp nhập,
  đấu giá -> listing_change; generic "phát hành thêm" -> rights stays last. Docstring cites VN§6.
  `parse_events`: listing_change without `exrightDate` is stored with ex_date NULL and no unmapped anomaly;
  every other kind without it stays unmapped. DIV branch untouched.
- Tests: `test_adapter_vci_events.py` (HPG fixture, title-order cases), `test_feed_corporate_actions.py`
  (db re-run test), new fixture `fixtures/vci/events/HPG-2026.json` (gunzip of the captured page, unedited).

## Contract honored
data.md §1.2 V5, §3 corporate_actions (ex_date nullable in 0010 / tables.py), VN§6 v1.2, ai answer Q1/Q2.

## Checks
- HPG fixture: 30 rows = 14 stock_dividend "Trả Cổ tức bằng Cổ phiếu" + 2 "Cổ phiếu thưởng" + 1 rights (2017-06-16 5:1,
  price NULL, 1 amount_missing) + 3 listing_change (1 with ex_date NULL) + 10 cash; 0 unmapped. FPT fixture unchanged.
- New tests fail on the old mapper (3 failed: 2 unit, 1 db) and pass now.
- `make test-kernel` via q.sh: 339 passed; ruff 1 error = `services/analytics/tests/test_recon.py:118` (B-05-4, AI-fix-lint, not mine);
  mypy and lint-imports clean.
- db (own db `finvest_befixv5iss_test` on the live compose server, port 55432): services/crawler + packages/market_data 54 db tests passed;
  whole crawler suite with db 200 passed.
- Re-run path: run 1 with an old-behaviour `_map` -> 16 rows, nominal 2026-05-22 = 23,955; run 2 (fixed mapper, same run date) -> 0 requests
  (archive replay), changed_symbols == ["HPG"], +14 rows, adj_factors = [(2026-05-25, 0.909090909091)], nominal 2026-05-22 in {26,350, 26,351}
  (hand 23,955 x 1.1 = 26,350.5).

## Outside-set edits (mechanical)
- `packages/market_data/.../domain/models.py`: `CorporateAction.ex_date: date | None` (the column was already nullable).
- `services/crawler/finvest_crawler/feeds/recompute.py` `_one`: `if a.ex_date` filter, else a NULL-ex_date listing_change
  would be a None key in `events_by_ex_date` and break `sorted()`.

## Notes for the tester
- Size: 131 insertions / 13 deletions excl. fixture (plan ~110, 1.5x = 165).
- Other readers of ex_date (market_view SQL range filters) drop NULL rows naturally; analytics `fixtures.py` is test-only.
- After deploy, a re-press must replay from archive or re-fetch so the 147 dropped events (26 names) land; then `recompute_press` fills adj_factors.
