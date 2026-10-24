# 3-pr FIX-sessions-repair — round 1 (fi-tech-lead, BE, opus)

**Verdict: APPROVE** — reviewed head H = 10ab70f85ef1b5ce7c235138eb80e61e57db4b90 (3fe45e8 + sync merge of origin/sprint-03 8c7716e, no conflicts).

Files reviewed: `repositories.py` (+`repair_crawl_sessions_from_ticks`), `migrations/versions/0008_repair_ticks_sessions.py`, `test_repositories_db.py` (+1 test), `ops/README.md` (+1 line). Size 64 insertions vs ~45 estimate (limit 67): OK, no consult needed.

- Plan/file set: exactly the 4 planned files; SQL is the plan's statement verbatim, `text()` with no string building, no inserts.
- Contract: platform.md §4 v1.12 ledger repair (rows < COUNT(*) per VN day → rows/symbols_fetched from table, checksum NULL, status/reason stay) — exact. data.md §3 `crawl_sessions` columns match; `ticks.ts` is `timestamptz` (0001), so `AT TIME ZONE 'Asia/Ho_Chi_Minh'` gives the VN wall time and `::date` the VN day.
- Hand check: 3 symbols × 2 ticks = 6 rows, 3 distinct; 2026-10-15 17:30 UTC = 2026-10-16 00:30 VN, 2026-10-16 08:59 UTC = 15:59 VN → both 10-16 → rows 6, symbols_fetched 3. Matches the test.
- Layering: migration (apps/api) imports a packages function; `finvest-market-data` is already an api dependency; import-linter 5 kept, 0 broken.
- Tests fail without the change: function absent → ImportError; mutation `s.rows < t.n` → `TRUE` makes the test FAIL (second call returns 1), restored after. `feed = 'ticks'` filter proven by the bars_1d row (would make the return 2). VN-day cast proven (UTC date would give n=3).

Must-fix: none.

Nits (no action required):
1. test_repositories_db.py:286 — the "ledger row with rows 6 already → untouched" case is seeded on 10-15 where there are no ticks, so it tests "no ticks day" rather than "rows == count"; the equal-count guard is covered by the second call instead. "Ticks day with no ledger row → no insert" has no seeded day of its own (structurally impossible for an UPDATE; `len(after) == 3` asserts it).
2. downgrade() is a no-op by design (data repair) — consistent with the plan.

Checks on H:
- `pytest -m db packages/market_data/tests/test_repositories_db.py services/crawler/tests` against compose `finvest_test` (172.20.0.2): **23 passed, 142 deselected** (alembic upgrade to 0008 inside the fixture).
- `make test-kernel`: **238 passed, 25 deselected**; ruff clean; mypy no issues; import-linter 5 kept / 0 broken.
- Production figure (2026-10-16 ticks row → rows 145184, symbols_fetched 911, checksum NULL) is the SM/tester post-merge step, not verified here.

Merged: a50e58b1e9b91a2bb75f3695e0eac851d24c3ca8 into sprint-03 (base 8c7716e, head 10ab70f). Worktree removed.
