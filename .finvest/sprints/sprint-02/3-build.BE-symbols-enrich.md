# 3-build BE-symbols-enrich

Result: done. Spike found endpoints, so membership (0005) is included. Branch task/sprint-02/BE-symbols-enrich.

## What changed
- Port: `index_members(index_code, as_of) -> list[str]`; kbs and ssi raise `Unsupported`; vci implements V6 `getByGroup` (archived under feed `index_members/<as_of>/<IDX>`).
- `SsiSource.symbols(as_of)`: 3 S1 calls (hose|hnx|upcom, archive `symbols/<as_of>/<ex>.json.gz`), STOCK/ETF rows, `firstTradingDate` yyyymmdd -> `listed_at`; "0", missing or garbage -> None.
- Migration 0005 `symbol_index_membership` + table in tables.py.
- Repos: `upsert_listed_at` (only where NULL), `sync_index_membership` (open/close intervals, rerun writes nothing, empty members = no-op).
- `run_symbols`: step 2 S1 listing dates for symbols also in V3; step 3 VN30 and HNX30 membership (via the symbols source, vci).

## Checks
- kernel: 123 passed; ruff, mypy, lint-imports clean.
- db (compose `finvest_test`): 18 passed, incl. 0005 round trip, A[d1,d2] B[d1,inf) C[d2,inf), rerun no change, upsert_listed_at keeps non-NULL.
- Feed on fixtures: first run 6 requests (1 V3 + 3 S1 + 2 indexes), replay 0 requests / 6 replays; 60 open membership rows.
- Size: ~122 non-test lines added (plan ~200 incl. tests).

## Deviations / notes for tester
- Indexes: VN30 and HNX30 (spike confirmed both; VN100 also works, not added). No history before crawl start.
- Only the hose S1 fixture exists; hnx/upcom return `{"data": []}` in the feed test. Fixture has 5 dated rows of 46; real data has ~25 of 409 dated, so most `listed_at` stay NULL.
- S1 `stockType` mapping s->STOCK, e->ETF is assumed (only 's' seen in fixture); other types dropped.
- `ssi` bucket must exist in `rate_per_s` (it does, 1/s).
- Not run live. Outside-set edits: kbs/source.py (one Unsupported stub), vci/payloads.py (VciMember model).
