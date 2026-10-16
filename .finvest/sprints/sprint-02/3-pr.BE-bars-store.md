# 3-pr BE-bars-store (F-012 storage) — round 1

Verdict: APPROVE. Reviewed head H=98e581b192eb7719c7dcd3728620069c6f016cea. Synced with origin/sprint-02 (already up to date).
Reviewer: fi-tech-lead (BE).

Files reviewed: migration 0004, infrastructure/tables.py, infrastructure/repositories.py, domain/models.py, domain/units.py
(outside-set, 1 line, justified: unit conversion stays in one place), vci/payloads.py, vci/source.py,
test_repositories_db.py, test_units.py, test_adapter_vci.py.

Size: whole PR +276/-20 (build report said +224; it is 276). Code only +195 vs ~150 = 1.3x, within 1.5x on the
code-only count used for BE-scheduler; tests +81. No size stop.

Contract: bars_1d_src columns/PK match data.md §3 exactly (adj_o/h/l/c, v, value BIGINT, PK symbol,trading_date,source,fetched_at);
index_1d NUMERIC(12,2) + PK(index_code,trading_date) matches. value = accumulatedValue x 1e6 half-up to int VND (platform.md §4
"Other feeds", data.md §1.2 V2). trading_date via Asia/Ho_Chi_Minh (ADR-S-006). Same fetched_at overwrites, later adds a version
(data.md §1.4 (2)). Index levels 2 dp half-up (platform.md §1.2). No SQL string building, no secrets, no new dependency.
Layering: import-linter kept.

Independent recompute (python Decimal, ROUND_HALF_UP): 65818.84/66637.03/64818.83/65000.65 -> 65819/66637/64819/65001;
474963.63 x 1e6 = 474963630000; // 6618016 = 71768; coverage 2/3 = 66.67 -> "66.7". All equal the test assertions.

Tests: every acceptance item has a test that fails without the change (new functions/fields): fixture first bar + value,
value half-up, index 2 dp, missing accumulatedValue = PayloadShapeError, db upsert idempotency/versioning, index latest-wins,
daily_coverage incl. delisted, 0004 downgrade/upgrade round-trip.

Must-fix: none.

Nits (for BE-bars-backfill / later, not blocking):
1. upsert_bars_1d_src / upsert_index_1d: duplicate keys inside one batch raise CardinalityViolation (docstring says keys must be
   unique). The back-fill must dedupe per (symbol, trading_date) before calling.
2. daily_coverage returns Decimal while acceptance text wrote strings; the API layer must serialise with str() to keep "66.7".
3. parse_index_bars is tested on a synthetic payload only; BE-bars-backfill should record a real VNINDEX gap-chart fixture.
4. VN ZoneInfo constant now defined in domain/models.py and vci/source.py; one could import the other.

Checks on H:
- make test-kernel (q.sh): exit 0; 120 passed, 16 deselected; ruff clean; mypy no issues (5 files); lint-imports kept.
- pytest -m db on compose db finvest_test (q.sh): exit 0; 16 passed.
Merge sha: 66d6b999cc12f53bc9f0712785722ebd6d5d7517
