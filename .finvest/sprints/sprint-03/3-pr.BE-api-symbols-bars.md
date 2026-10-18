# 3-pr BE-api-symbols-bars (F-055 / F-031 support)

## Round 1 — APPROVE (lead BE, opus, 2026-10-18)

Reviewed head H = f69d413222ec7d35ef6ab7036a64e98f9d3bc3ec (= dev commit 3b33527 + clean merge of origin/sprint-03
4bc626c, no conflicts, no behaviour change).
Size: 10 files, +246 / -10 (plan ~200; 1.5x = 300) — within limit.

Files reviewed: `apps/api/finvest_api/{deps,errors,main}.py`, `routes/{__init__,symbols,bars}.py`,
`apps/api/tests/{conftest,test_symbols,test_bars_status,test_health}.py`. File set matches the plan block exactly.

### What is right
- Contract §2.5 rows 1–3: field names, `limit=20` default / 1–200, `include_delisted=false`, symbol asc, `bars_1d`
  `{first,last,as_of} | null`, 404 `NOT_FOUND` envelope (§1.3), status `{last_trading_date, as_of, source:"vci", symbols}`
  with `max/max/count(distinct)` over `bars_1d_src`, empty → nulls + 0.
- 400 `VALIDATION` with `details.field = loc[-1]` (plan). `%`/`_`/`\` escaped in `q`; all values bound, no SQL string
  building. Postgres compile checked: `symbol LIKE %(p)s ESCAPE '\' OR name_vi ILIKE … ESCAPE '\'`, `is_delisted IS false`.
- Time (ADR-S-006, §1.2): `vn_iso` → `+07:00` with ms. Hand check: max fetched_at 2026-10-17T03:00Z → `2026-10-17T10:00:00.000+07:00`
  = test expectation; the latest of two fetched_at for 2026-10-16 wins.
- Every acceptance criterion has a test that fails without the change (new routes 404 otherwise). Fixture has 4 bar rows
  (plan said 3, but 3 dates + a duplicate fetched_at needs 4 — correct). Layering: apps/api → infrastructure allowed (codebase §3).
- No money/return code, no analytics read (no look-ahead surface), no secrets, no network.

### Must-fix
None.

### Nits / follow-ups (not blocking)
1. (for sa) `type` is returned as stored, `STOCK|ETF` (data.md §3), while platform.md §1.2 says "enums are lower-case
   strings". Confirm the casing in §2.5 before BE-contracts-ts exports the OpenAPI types (a one-line change either way).
2. DB failures and unknown routes still return FastAPI defaults (`500 Internal Server Error` text, `{"detail": …}`), not the
   §1.3 envelope (`503 DB_UNAVAILABLE`, `500 INTERNAL`). Outside this plan block; suggest a small follow-up in errors.py.
3. `{symbol}` path param has no length/charset check (safe: bound parameter; 404 for junk). Could reuse the 1–12 rule
   from ScenarioIn later.
4. SQLite `lower()` is ASCII-only, so the `sữa` test passes via ASCII `S`; real Vietnamese case-folding is Postgres ILIKE,
   untested here (no `db` mark per plan).

### Checks (synced head f69d413)
- `make test-kernel` via q.sh: exit 0 in 3s — 138 passed, 18 deselected; ruff clean; mypy ok (5 files); import-linter 5 kept, 0 broken.

### Merge
Merged H f69d413 into sprint-03 (base 4bc626c): merge sha 9a141e09a8bc9f9e253461110bd17b48672efc2a.
