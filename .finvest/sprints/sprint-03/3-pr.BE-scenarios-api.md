# PR review: BE-scenarios-api (F-055)

## Round 1 — fi-tech-lead (BE), 2026-10-18 — CHANGES_REQUIRED

Reviewed head H = `60b46a6a84e90fd93fe88a61a5e15306f4691425` (task `d59046c` + clean sync merge of origin/sprint-03 `5f90edc`, pushed).
Size: 8 files, +212 / -1 (plan ~230, within 1.5x). File set = plan block exactly; no outside-set edits.

### Files reviewed
- migrations/versions/0006_scenarios.py — DDL matches data.md §3 `scenarios` verbatim (identity PK, CHECKs on name/style/amount); downgrade drops it.
- finvest_api/scenarios/tables.py — own MetaData; SQLite Integer variant for the PK only (Postgres uses the migration). OK.
- finvest_api/scenarios/schemas.py — `ScenarioIn`/`Scenario` match platform.md §2.5: name strip 1–60, symbol strip+upper 1–12,
  style literal, `amount_vnd` strict int 1..100_000_000_000 (floats incl. `1e7` and strings rejected), `sell_date >= buy_date`
  field validator → `details.field == "sell_date"`.
- routes/scenarios.py — GET newest first (`created_at desc, id desc`), POST 201, PUT 200 full replace + `updated_at`, DELETE 204;
  404 `NOT_FOUND`; 422 `SYMBOL_UNKNOWN` `details.symbol` (delisted accepted); bound params only; UTC stored, `vn_iso` +07:00 (ADR-S-006).
- main.py, tests/conftest.py — include_router, create_all scenarios metadata. OK.
- tests/test_scenarios.py — every acceptance bullet covered; all fail without the change (new routes).

Extra probes (temporary test, removed): amount 100_000_000_000 → 201; `" fpt "` → `FPT`; name `"   "`, style `x`, 13-char symbol,
`10000000.0` → 400 with the right `details.field`; PUT unknown id → 404. All as contract says.

### Must-fix
1. **Destructive db test has no `_test` database guard** — `apps/api/tests/test_scenarios.py:51-63` (`test_migration_round_trip`).
   `downgrade -1` drops `scenarios` (the sponsor's saved user data) on whatever `FINVEST_DATABASE_URL` points at; the host `.env`
   points it at the real `finvest` db. Every other destructive db test in the repo skips unless the db name ends in `_test`
   (`apps/api/tests/test_market_view_db.py:16`, `services/crawler/tests/test_feed_symbols.py:79`). Add the same skipif
   (`make_url(URL).database.endswith("_test")`). Proof: the test is skipped with a `..._/finvest` URL and still passes against
   compose `finvest_test` (`uv run pytest -m db apps/api/tests/test_scenarios.py`).

### Nits (optional)
- Same test: `downgrade(cfg, "-1")` only exercises 0006 while 0006 is head; `downgrade(cfg, "0005")` keeps it pinned after 0007 lands.
- PUT with unknown id and unknown symbol returns 422 before 404 (contract silent; fine either way).
- `updated_at > a["updated_at"]` compares ms-precision strings; a same-millisecond PUT would flake (very unlikely after 3 requests).
- Path `id` beyond BIGINT reaches Postgres and returns a FastAPI 500 (pre-existing envelope gap noted in 3-pr.BE-api-symbols-bars.md).

### Checks on H
- Kernel `make test-kernel` (q.sh): exit 0 — `152 passed, 20 deselected, 4 warnings`; ruff "All checks passed!"; mypy "Success: no issues
  found in 5 source files"; lint-imports "Contracts: 5 kept, 0 broken".
- db: `uv run pytest -m db apps/api/tests/test_scenarios.py` against compose `finvest_test` (alembic at 0005) → `1 passed, 3 deselected`
  (upgrade 0006 → downgrade → upgrade round-trip on Postgres).
- Contract exactness: no drift found vs platform.md §1.3/§2.5, data.md §3, ADR-S-006.

Verdict: CHANGES_REQUIRED (1 must-fix). Not merged.

## Round 2 — fi-tech-lead (BE), 2026-10-18 — APPROVE

Reviewed head H = `e3ac60fa8fcb9e13582f9656a4d59ca5a663bf4c` (fix `e3ac60f` on top of sync `64ca82b`; `git merge origin/sprint-03` → already up to date).
Size: 8 files, +217 / -1 vs origin/sprint-03 (plan ~230, within 1.5x). File set unchanged = plan block.

### Files reviewed (delta since round 1)
- tests/test_scenarios.py — must-fix 1 done: module `URL` + skipif `make_url(URL).database.endswith("_test")`, same form as
  test_market_view_db.py:16-19. Alembic env.py reads the same `FINVEST_DATABASE_URL`, so the guard covers what the migration hits.
  Nit taken: downgrade pinned to `"0005"`.
- Other files: unchanged since round 1 review.

### Must-fix
None. Round-1 nits 2–4 (422-before-404 order, ms-precision updated_at compare, BIGINT overflow 500) remain optional/pre-existing.

### Checks on H
- Kernel `make test-kernel` (q.sh): exit 0 — `152 passed, 20 deselected, 4 warnings`; ruff "All checks passed!"; mypy "Success: no issues
  found in 5 source files"; lint-imports "Contracts: 5 kept, 0 broken."
- Guard: `-m db test_scenarios.py` with a `.../finvest` URL → `1 skipped, 3 deselected`.
- db: same against compose `finvest_test` → `1 passed, 3 deselected` (finvest_test alembic now at 0006).

Verdict: APPROVE.

Merge sha: `ae11587598e8e79a2ce5745acb8aa1bc5ea4d048` (into sprint-03, base 5f90edc).
