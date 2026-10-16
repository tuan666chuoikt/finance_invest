# 3-build BE-status-no-trades (S02-1)

Result: DONE. `symbols_no_trades` added; an empty tape for today is no-trade, not a skip, so a session with only
no-trade names is `complete`.

## Files
- `domain/manifest.py`: `Manifest.symbols_no_trades: tuple[str, ...] = ()` (placed after `symbols_skipped` so existing positional callers keep working); `to_dict` emits it after `symbols_fetched`, before `symbols_skipped`.
- `infrastructure/tables.py`, `repositories.upsert_crawl_session`: write `len(symbols_no_trades)`.
- `apps/api/migrations/versions/0002_crawl_sessions_no_trades.py`: ADD / DROP COLUMN `symbols_no_trades INT`.
- `feeds/ticks.py`: today + empty tape -> `no_trades` (sorted by loop order = sorted names), `no_ticks` reason removed; status rule unchanged (`partial` iff `skipped`); assert `fetched + no_trades + skipped == len(names)` except `missed` (loop stops with nothing listed, per platform.md §4 v1.2 behaviour).
- Tests: test_manifest, test_repositories_db (value 1 and 0002 downgrade -1 / upgrade), test_feed_ticks (no-trade complete, no-trade + payload_shape partial, MANIFEST_KEYS, db column == 0 on full run).

## Contract honored
platform.md §4 (manifest keys, status rule v1.3, invariant); data.md §3 `crawl_sessions`. Past-date behaviour unchanged (existing partial/missed tests green).

## Checks
- kernel (`pytest -m "not db"`, ruff, mypy, lint-imports): 100 passed, ruff and mypy clean.
- db (throwaway timescale container, `finvest_test`, since removed): 8 passed.
- Diff vs origin/sprint-02: see git; within 1.5x of ~120 lines.

## Deviations / outside-set edits
None. `test_qa_sprint01.py` needed no change (its asserts still hold).

## Notes for the tester
- QA-S02-live: the 10-16 re-run should give 911 + 629 + 0 = 1540 -> `complete`.
- Overlap with `task/sprint-02/BE-calendar`: it edits `cli.py` / `test_cli.py` only, none of my lines.
