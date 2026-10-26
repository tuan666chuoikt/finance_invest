# 3-pr BE-mig-0010 (F-013/F-014)

## Round 1 — 2026-10-26, fi-tech-lead (BE, opus) — CHANGES_REQUIRED

Reviewed head H = 2b39274 (d316ea6 + sync merge of origin/sprint-05 0950502, no conflicts, pushed).
Size: 4 files, +234/-1 (plan ~200, stop 300) — OK.

Files reviewed: `apps/api/migrations/versions/0010_corporate_actions_bars_1d.py`, `.../infrastructure/tables.py`,
`.../infrastructure/repositories.py` (`upsert_bars_1d`, `move_ssi_board_rows`, `restore_ssi_board_rows`),
`packages/market_data/tests/test_repositories_db.py`.

What is right: the five tables + `symbols.ca_checked_at` match data.md §3 column by column (types: prices BIGINT,
`factor NUMERIC(20,12)`, `diff_pct NUMERIC(8,4)`, `nominal_kind` CHECK, `UNIQUE(source, source_event_id)`, `public_date`,
`title`); the conflict guard `WHERE bars_1d.nominal_kind <> 'observed' OR excluded.nominal_kind = 'observed'` is exactly
the plan's; the move keeps the newest `fetched_at` per (symbol, trading_date) via `DISTINCT ON … ORDER BY fetched_at DESC`;
downgrade restores observed ssi rows before dropping. Every acceptance criterion has a db test (2 ssi + 1 vci move,
down/up/down/up, G9 93,499 over 93,500, observed over reconstructed, heads == 0010). Hand check of G9: reconstructed
93,499 vs observed 93,500 -> guard false -> row untouched, 0 returned; test asserts (93,500, observed, 93,000). PASS.

### Must-fix
1. `apps/api/migrations/versions/0010_corporate_actions_bars_1d.py:9,17,23,33` — the migration builds its DDL from the
   live `tables.py` metadata (`t.bars_1d.create(conn)` …) instead of `op.create_table` with its own columns, as the plan
   says and as 0001–0008 do. A migration must be frozen: the first later change to one of these tables in `tables.py`
   plus its own `0011 op.add_column(...)` makes a fresh `alembic upgrade head` fail (0010 already created the column),
   which breaks the db fixture (`downgrade base` -> `upgrade head`) for every db test. The build note's mitigation
   ("later migrations must alter") is exactly the case that breaks. Fix: write the five tables inline with
   `op.create_table("bars_1d", sa.Column(...), ..., sa.CheckConstraint(...), sa.UniqueConstraint(...))` (same names,
   types, nullability, constraint names as `tables.py`), downgrade with `op.drop_table` in reverse order, and drop the
   `tables` import. Keep the `repositories` import for the move (plan-mandated, same as 0009). Proof:
   `test_migration_0010_moves_ssi_rows_and_round_trips` and the whole `-m db` file stay green, and
   `rg -n 'infrastructure import tables' apps/api/migrations` has no match. Expected size after fix ~+290 (under 300).

### Nits (optional)
- none.

### Checks on H (throwaway db finvest_lead_mig0010_test, dropped after)
- `pytest -m db`: 30 passed, 260 deselected
- kernel `pytest -m "not db"`: 260 passed, 30 deselected
- ruff: All checks passed; lint-imports: exit 0

## Round 2 — 2026-10-26, fi-tech-lead (BE, opus) — APPROVE

Reviewed head H = c98afab (745e591 fix + sync merge of origin/sprint-05 80d47cb, no conflicts, pushed).
Size: 4 files, +293/-1 (plan ~200, stop 300) — OK.

Files reviewed: `apps/api/migrations/versions/0010_corporate_actions_bars_1d.py` (fix commit 745e591 touches only this
file); `tables.py`, `repositories.py`, `test_repositories_db.py` unchanged since round 1 (PASS there).

Must-fix 1 (round 1): DONE. 0010 now has frozen inline `op.create_table` for bars_1d, corporate_actions,
corporate_action_log, adj_factors, recon_mismatches + `op.add_column("symbols", ca_checked_at)`; compared column by
column with `tables.py`: names, types (BIGINT prices, NUMERIC(20,12), NUMERIC(8,4), TIMESTAMPTZ), nullability, Identity,
PKs, `bars_1d_nominal_kind_check`, `corporate_actions_source_event_key` all identical. Downgrade restores observed ssi
rows first, then drops the column and tables in reverse order. `rg 'infrastructure import tables' apps/api/migrations`:
no match.

### Must-fix
- none.

### Nits (optional)
- none.

### Checks on H (throwaway db finvest_lead_mig0010_r2_test, dropped after)
- `pytest -m db`: 30 passed, 280 deselected
- kernel `pytest -m "not db"`: 280 passed, 30 deselected
- ruff: All checks passed; mypy (project config): no issues in 5 files; lint-imports: exit 0
- `alembic heads`: 0010 (head)

Merged: f5bb4dd (sm.sh merge, base 80d47cb, head c98afab). Worktree removed.
