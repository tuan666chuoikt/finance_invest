# 3-build BE-ca-repo (F-014/F-015/F-016)

## Result
Done. Eleven repository functions added to `packages/market_data/finvest_market_data/infrastructure/repositories.py`; 5 db tests added.
Own diff: 2 files, +179/-4 (plan ~160, stop 240). Branch `task/sprint-05/BE-ca-repo`.

## Dependency note (read before review)
`CorporateAction` (domain/models.py) is created by the unmerged BE-v5-adapter. I merged `origin/task/sprint-05/BE-v5-adapter` (f154482) so my
code type-checks; the PR diff vs `sprint-05` therefore shows that branch's +258 lines too (7 files, +437) until it lands. My own change is the two
files above. If BE-v5-adapter changes the dataclass in its fix round, re-merge. I did not edit models.py.

## What changed
- `upsert_corporate_actions(conn, rows, fetched_at) -> (upserted, changes)`: per row read by `(source, source_event_id)`; new row inserts with no
  log; existing row: one `corporate_action_log` row per differing field of type/ex_date/record_date/pay_date/ratio_a/ratio_b/cash_per_share/issue_price
  (old/new as text, `changed_at = fetched_at`), then update (incl. public_date, title, `fetched_at` always). `changes` = log rows written.
- `ca_symbols_in_order(conn, limit=None)`: one SQL, tier 0 VN30 current (`valid_to IS NULL`), tier 1 `scenarios` symbols (plain SQL, `# shortcut:` comment
  as planned), tier 2 by `ca_checked_at NULLS FIRST`, symbol; tiers 0/1 by symbol; delisted excluded from all tiers. `mark_ca_checked(conn, symbols, at)`.
- `corporate_actions_for` (every requested symbol is a key, `[]` if none; order ex_date, id), `replace_adj_factors`, `adj_factors_for`,
  `replace_recon_mismatches`, `newest_src_bars` (per trading_date newest `fetched_at`, PG `distinct_on`), `nominal_bars`.

## Decisions on points the card left open (no contract change)
- `replace_adj_factors` rows = `(ex_date, factor: Decimal|str, ca_id|None)`; `adj_factors_for` returns the same tuple shape (Decimal back), ordered by ex_date.
- `replace_recon_mismatches` rows = `(trading_date, ours, theirs, diff_pct: Decimal)`; `checked_at` = DB `now()` (card has no time parameter).
- `newest_src_bars` = newest version of each date (not only the newest snapshot).
- The card's recon-row/factor-row shapes are plain tuples so market_data does not import analytics types.

## Checks
- db: `test_repositories_db.py` 30 passed (5 new; `-W error::DeprecationWarning` clean). Per-branch db `finvest_be_ca_repo_test`.
- `make test-kernel`: 288 passed, 35 deselected; ruff clean; mypy no issues (5 files); lint-imports 5 kept / 0 broken.
- Acceptance: ex 2026-11-05 -> 2026-11-07 gives exactly one log row (`ex_date`, `2026-11-05` -> `2026-11-07`), re-run adds none; order test
  `[VN30M, SCEN, NULLS, OLD, NEW]` (+ a delisted name absent, `limit=2`); factor `0.980000000000` stored and read back equal as `Decimal`;
  `replace_recon_mismatches` twice -> 1 row.
- Not run: full db suite beyond this file (only additive code in one module).

## Outside-set edits
None.

## Notes for the tester
Consumers (BE-ca-step3, BE-ca-recompute, recon) pass/read the tuple shapes above. `listing_change` rows are stored like any other; excluding them
from factors is the recompute's job (v5-adapter review nit).
