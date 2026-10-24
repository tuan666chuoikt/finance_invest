# 3-pr.BE-bars-batch

## Round 1 (fi-tech-lead BE, opus, 2026-10-24): APPROVE

Head H = `3ba7b9c7650c60cc087aef46a5e7d7dfc4e58f7c` (already contains latest `origin/sprint-03` 481a424; no sync commit needed).

Files reviewed: `feeds/bars_1d.py`, `adapters/vci/source.py`, `fetch.py`, `domain/ports.py`, `ops/README.md`,
`tests/test_feed_bars_1d.py`, `tests/test_adapter_vci.py`, `tests/test_fetch.py`. File set = plan block exactly.

Size: 150 insertions + 38 deletions = 188 lines vs plan 190 (dag rev 10) -> within 1.5x.

Contract: platform.md v1.11 §2.6 (indices first with full `COUNT`, batches `max(1, min(BATCH_MAX, 50_000 // count))`,
progress in names, 418 blocked) matches the code. `BATCH_MAX = 1` per spike S-v2-batch verdict (cap = 1); ops/README uses
the card's cap-1 figures (~1 780 requests, ~15 min). §4 manifest invariant assert kept.

Correctness:
- Checksum: indices are fetched first but their lines are held and fed in name order, so the digest equals the one-by-one
  run. Independently verified: the new checksum test (pinned `OLD_DIGEST`) passes against the pre-change code on
  `origin/sprint-03` (temporary detached worktree, removed).
- `fetched_at` = mtime of `archive_name(unit, count)`, the same name `_gap_chart` writes -> replays stay idempotent.
- SourceBlocked skips the current and all remaining units; HTTP/payload errors skip only the unit; progress counts names.

Tests fail without the change: on pre-change code, `test_indices_first_then_symbol_batches`,
`test_batch_size_shrinks_with_count_and_is_one_by_default`, `test_batch_gaps_failures_and_block`,
`test_418_is_blocked_not_retried_as_a_plain_error`, `test_archive_name_matches_the_file_gap_chart_writes` fail (5 failed).
`parse_bars(batch50)` test skipped per card (cap = 1, no fixture).

Checks on H: `make test-kernel` (q.sh) exit 0: 233 passed, 24 deselected; ruff clean; mypy clean (5 files); lint-imports
green. No migration/repository/SQL change, so `-m db` not required.

Must-fix: none.

Nits (no action required now):
1. `bars_1d.py` `by_name.get(..., []).append(b)`: bars for a symbol not in the requested unit are still upserted (the whole
   `bars` list goes to `upsert_*`) but not counted in rows/checksum. Moot at `BATCH_MAX = 1`; filter to `got` names when the
   cap is raised.
2. `kbs`/`ssi` sources do not implement the new `MarketDataSource.archive_name`; add it if either becomes a bars source.
3. A blocked run now digests the indices even when they sort after the block point; blocked digests are not compared, fine.

Security: no secrets, no SQL building, free source only.

Merged: `7e0f4a4da254955ab5379d8f261be08a2149ba68` into `sprint-03` (base 481a424, head 3ba7b9c).
