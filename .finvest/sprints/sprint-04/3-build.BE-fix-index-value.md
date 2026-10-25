# 3-build BE-fix-index-value (sprint-04, B1)

Result: DONE. Branch task/sprint-04/BE-fix-index-value, diff vs origin/sprint-04: 5 files, +76/-5 (budget ~90).

## What changed
- `adapters/vci/source.py`: `INDEX_VALUE_PER_UNIT = (100, 10_000_000)`; `_value_vnd` gets `vol` (default 0), and for index bars (`ref is None`)
  returns None + `log.warning("vci index value dropped ...")` when value == 0, vol == 0 or value/vol is outside the band. Bar o/h/l/c/v kept. Stocks path unchanged.
- `repositories.py`: `repair_index_1d_value(conn) -> int` (SQLAlchemy core UPDATE ... SET value NULL, all index codes, returns rowcount).
- Migration `0009_repair_index_1d_value` (revises 0008): upgrade calls the repair and prints the count; downgrade no-op.
- Tests: `test_index_value_outside_ratio_band_is_dropped_and_bar_kept` (ratio 1e10 -> None with c kept, ratio 5e4 kept, value 0 -> None, stock untouched);
  db test `test_repair_index_1d_value_nulls_out_of_band_rows_only` (3 rows -> returns 2, good row unchanged, rerun returns 0).

## Contract
data.md §1.2 (index `value` nullable VND): honored; no API change.

## Checks
- `pytest -m "not db"` (whole repo, includes services/analytics benchmark tests): 260 passed, 28 deselected.
- ruff + mypy + lint-imports: pass.
- `pytest -m db` on a throwaway db (finvest_be_fix_index_value_test, dropped after): 28 passed (includes the migration round trip to head = 0009).
- Live db (read-only SELECT, not modified): 8 `index_1d` rows currently match the repair predicate; they are nulled on the next `make up` (alembic upgrade head).

## Deviations
- Spec says drop when `v > 0 and ratio out of band` or `value == 0`; the adapter also drops when `vol == 0`, so it agrees with the repair (`v = 0`) and
  smoke check (1); otherwise a re-crawl would restore what the repair nulled.
- Two existing tests (`test_index_bars_keep_two_decimals`, `test_index_value_unit_is_mixed`) used v=10 which gives an out-of-band ratio; their volumes were raised
  (2_000_000 and 10**7) so they still test what they name.

## Outside-set edits
None. (A temporary .env copy in the worktree for the db run was removed; git-ignored.)

## Notes for the tester
`make up` then `make smoke`: check (1) must print 0 rows. `docker compose up` log shows `0009: index_1d.value nulled on N rows`. N was 8 on the live db at 2026-10-25 17:42.
