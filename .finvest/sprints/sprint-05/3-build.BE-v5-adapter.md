# 3-build BE-v5-adapter (F-014)

Result: V5 events adapter built; fixture parses to 4 rows. Branch task/sprint-05/BE-v5-adapter.

## Files
- `services/crawler/finvest_crawler/adapters/vci/events.py` (new): `parse_events`, `fetch_events`.
- `services/crawler/finvest_crawler/adapters/vci/payloads.py`: `VciEvent`, `VciEventsData`, `VciEventsPage` (envelope `data.{content,last}`).
- `packages/market_data/finvest_market_data/domain/models.py`: `CorporateAction` (data.md §3 fields minus `id`/`fetched_at` + `public_date`, `title`).
- `services/crawler/tests/fixtures/vci/events/FPT-2026.json` (copy of spike v5-call4.json), `services/crawler/tests/test_adapter_vci_events.py` (8 tests).

## What changed / contract
- Mapping exactly as the task card (data.md §1.2 V5, VN§6). Ratio: `Fraction(exerciseRatio).limit_denominator(1000)` -> (a, b) = (den, num): 0.1 -> 10:1, 0.15 -> 20:3.
- `fetch_events`: fromDate=20100101, toDate=run_date+400d (YYYYMMDD, always in the URL), size=50, pages 0.. until `last` (guard MAX_PAGES=40), bucket `vci_iq`,
  feed `corporate_actions`, name `<SYM>-p<page>`; returns (rows, anomalies, requests made = Fetcher.requests delta, archive replays count 0).
- A page is archived only after it parsed (Fetcher `archive=False`, then `archive.write`): an HTTP-200 body with `status 400` ("Invalid datetime") is a PayloadShapeError and is not cached.
- 418 x TRIES(3) -> `SourceBlocked` (Fetcher, tested).

## Checks
- adapter tests: 8 passed; BE kernel `pytest -m "not db"`: 268 passed, 28 deselected; ruff clean; mypy clean; lint-imports clean.
- Diff vs origin/sprint-05 (no fixture): 257 lines added incl. 8 tests (~150 of code), fixture excluded.

## Decisions where the card was silent (please confirm in review)
1. `DIV` with neither `valuePerShare` nor the stock-dividend title -> stored as `cash_dividend` with `cash_per_share` NULL + `corporate_action_amount_missing` (card: "NULL + anomaly").
2. `stock_dividend`/`rights` with no usable `exerciseRatio` -> row stored, ratio NULL, same `corporate_action_amount_missing` rule (no new rule invented). `listing_change` ratio is informational, never flagged.
3. Event without `exrightDate` -> not stored + `corporate_action_unmapped` (`ex_date` is the key of `adj_factors`).
4. `DIV` + `valuePerShare` wins over a stock-dividend title.

## Deviations / outside-set edits
- None. Not done (other tasks): `vci_iq` entry in `Settings.rate_per_s` (the press step must add `"vci_iq": 1`; `Fetcher.buckets["vci_iq"]` raises KeyError without it), DB writes, budget B=40.

## Notes for the tester
- `toDate` check = request URL contains `toDate=<run_date+400d>`; archive name stays `<SYM>-p<n>` (dated dir = run_date).
- ESOP ratios of the live fixture (0.00135, 0.00499) become 741:1 and 200:1; irrelevant for `listing_change`.

## Fix round 1
- Must-fix 1 (size stop skipped): wrote `3-consult.BE-v5-adapter.md` (258 lines vs stop 225; source 144 on estimate, tests 113). Recommendation: waive. Awaiting architect answer; no code change, head unchanged f223cc5 (already merged with origin/sprint-05, no new sprint commits).

## Fix round 2
- Must-fix 1 closed: architect answer `3-consult.BE-v5-adapter.answer.sa.md` = **waive** (plan Size re-estimated to ~260, dag size 260). No code or test change.
- Merged origin/sprint-05 (web-only commits, no conflicts) -> head 4cb33a6, pushed. Kernel re-run: 268 passed, ruff clean, mypy clean (8 s).
