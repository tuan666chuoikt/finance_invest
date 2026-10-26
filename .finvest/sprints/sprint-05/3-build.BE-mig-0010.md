# 3-build BE-mig-0010 (F-013/F-014)

Result: DONE. Branch task/sprint-05/BE-mig-0010.

## Files
- `apps/api/migrations/versions/0010_corporate_actions_bars_1d.py` (new): creates bars_1d, corporate_actions,
  corporate_action_log, adj_factors, recon_mismatches from the `tables.py` definitions (`Table.create`), adds
  `symbols.ca_checked_at`, then `move_ssi_board_rows`; prints the count. Downgrade restores observed ssi rows
  into `bars_1d_src` (`restore_ssi_board_rows`), drops the column and the tables.
- `tables.py`: the five tables exactly as data.md §3 (+ `public_date`, `title`; `factor NUMERIC(20,12)`,
  `diff_pct NUMERIC(8,4)`, `nominal_kind` CHECK, `UNIQUE(source, source_event_id)`), `symbols.ca_checked_at`.
- `repositories.py`: `upsert_bars_1d`, `move_ssi_board_rows`, `restore_ssi_board_rows` (helper for the downgrade).
- `test_repositories_db.py`: 2 new db tests; `bars_1d` added to the fixture TRUNCATE list.

## Contract honored
data.md §1.4 (1), §3; ADR-S-001. `upsert_bars_1d` conflict clause:
`WHERE bars_1d.nominal_kind <> 'observed' OR excluded.nominal_kind = 'observed'`.

## Checks (throwaway db finvest_be_mig_0010_test)
- db tests market_data + api scenarios + crawler feed_symbols: 33 passed
- market_data db file: 25 passed; kernel `-m "not db"`: 260 passed, 30 deselected
- ruff: All checks passed; mypy: no issues (5 files); lint-imports: ok
- Acceptance covered: 2 ssi (older version ignored, newest fetched_at kept) + 1 vci -> bars_1d 2 observed rows,
  bars_1d_src keeps vci; up/down/up twice idempotent; reconstructed 93,499 over observed 93,500 leaves 93,500/observed
  (returns 0 rows written); observed over reconstructed wins; `ScriptDirectory.get_heads() == ['0010']`.
- Size: ~245 lines added (plan ~200, limit 300).

## Deviations
- `Table.create(conn)` instead of `op.create_table` (same definitions, no column duplication). Consequence: a later
  edit of `tables.py` changes what 0010 creates on a fresh db; later migrations must alter, not rely on that.
- `upsert_bars_1d` counts via RETURNING (rowcount is -1 for batched inserts). Skipped (observed-protected) rows are
  not counted. ceiling/floor stay NULL (Bar has no such fields).
- Downgrade restores only `observed` `ssi` rows, one version each (the older duplicate versions are gone);
  reconstructed rows are derivable and dropped.
- bars_1d.o/h/l/c/v are NOT NULL (data.md sketch is silent; mirrors bars_1d_src).

## Outside-set edits
None.

## Notes for the tester
Dedicated db was created inside the compose db container (`finvest_be_mig_0010_test`); drop it when done.

## Fix round 1 (2026-10-26)
- Must-fix 1 done: `0010_corporate_actions_bars_1d.py` now uses inline `op.create_table`/`op.add_column` (same names, types, nullability, constraint names as tables.py); downgrade uses `op.drop_table` in reverse order; `tables` import removed (`rg 'infrastructure import tables' apps/api/migrations` no match). `repositories` import kept for the move.
- Checks: `pytest -m db` 30 passed (throwaway db, dropped after); ruff, mypy, lint-imports green. No sprint-05 merge conflicts.
