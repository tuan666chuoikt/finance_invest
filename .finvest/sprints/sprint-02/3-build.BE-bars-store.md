# 3-build BE-bars-store (F-012 storage)

**Result:** done, PR open. Branch `task/sprint-02/BE-bars-store`.

## Files
- `apps/api/migrations/versions/0004_bars_1d_src_index_1d.py`: `bars_1d_src` (PK symbol, trading_date, source, fetched_at; adj_o/h/l/c, v, value BIGINT), `index_1d` (NUMERIC(12,2) levels).
- `infrastructure/tables.py`, `infrastructure/repositories.py`: `upsert_bars_1d_src(conn, bars, fetched_at)`, `upsert_index_1d(conn, bars)`, `daily_coverage(conn)`.
- `domain/models.py`: `Bar.trading_date` (VN date of `ts`, ADR-S-006); new `IndexBar` (Decimal levels, separate from integer-VND `Bar`).
- `vci/payloads.py`: `accumulatedValue: list[Decimal]` (required; absence is a PayloadShapeError).
- `vci/source.py`: shared `_rows`; `parse_bars` fills `value`; new `parse_index_bars` (2 dp half-up).
- Tests: `test_repositories_db.py`, `test_adapter_vci.py`, `test_units.py`.

## Contract
platform.md §1.2/§2.2 (integer VND, half-up, index 2 dp); data.md §1.2 V2 (million VND), §1.4 (2) versioned snapshots; ADR-S-005/006.
Worked example asserted: FPT first bar o/h/l/c = 65819/66637/64819/65001, v=6618016, value=474963630000, value//v=71768 within [l, h*1.15].

## Checks
- kernel `pytest -m "not db"`: 120 passed. ruff clean. mypy: no issues. lint-imports: kept.
- `pytest -m db` (compose db, `finvest_test`): 16 passed, incl. upsert idempotency (same fetched_at = 2 rows, later = 4), index upsert, coverage 33.3 -> 66.7 / 100.0, and 0004 downgrade/upgrade round-trip.
- Diff size vs origin/sprint-02: +224/-20 incl. ~100 test lines (plan ~150).

## Deviations
- `daily_coverage` returns `dict[str, Decimal]` (the plan signature); acceptance wrote strings. `str(v)` gives "66.7"; the API layer serialises Decimal as a string. Switch to str if the reader prefers.
- `parse_index_bars` is tested on a synthetic payload only; no recorded VNINDEX gap-chart payload exists, so the index response shape is an assumption (same column layout as stocks). BE-bars-backfill should record a fixture.

## Outside-set edits
- `packages/market_data/finvest_market_data/domain/units.py`: `to_vnd` unit `"million_vnd"` (one line; keeps unit conversion in one place) + one assert in `test_units.py`.

## Notes for tester
- DB tests need `FINVEST_DATABASE_URL` ending `_test`; the compose db has no host port, I used the container IP.
