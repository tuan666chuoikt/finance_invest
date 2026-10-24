# 3-build.BE-bars-batch: DONE

Result: step 2 of the bars feed fetches `VN30`, `VNINDEX` first (always `count=6000`), then symbols in batches. Spike S-v2-batch reported cap = 1 (`3-build.S-v2-batch.md`), so `BATCH_MAX = 1`: batches of 1, ~1 780 requests ~ 15 min at 2 req/s (not the ~40 in the card).
Branch `task/sprint-03/BE-bars-batch`.

## Files / changes
- `feeds/bars_1d.py` `_run`: units = one per index, then `max(1, min(BATCH_MAX, 50_000 // count))` symbols each; per unit: group bars by name, empty names -> `no_trades`, `PayloadShapeError`/`HTTPError` -> whole unit `skipped(_skip_reason)`, `SourceBlocked` -> this and all remaining names `skipped(source_blocked)`, `blocked`; upsert + `commit()` per unit; `on_progress(names_done, total)` per unit. `fetched_at` = mtime of `archive.path(FEED, date, source.archive_name(unit, count))`. Checksum: indices' lines are held and fed into the digest when the sorted symbol stream passes their name, so the digest equals the old one-by-one one (pinned `OLD_DIGEST`, computed with the pre-change code on `origin/sprint-03`, indices interleaved between FPT and VNM). Memory stays per-batch.
- `adapters/vci/source.py`: `archive_name(symbols, count)` (old `<key>-1d-<count>` rule, hash for >= 4), used by `_gap_chart`.
- `domain/ports.py`: `MarketDataSource.archive_name`.
- `fetch.py` `_blocked`: 418 added (3x 418 -> `SourceBlocked`, no 100 s back-off per name).
- `ops/README.md`: one paragraph with the real figures.

## Contract
platform.md §2.6 (indices first with full history, batches, progress in names), §4 manifest invariants unchanged (assert kept).

## Checks
- `make test-kernel`: 233 passed, 24 deselected; ruff clean; mypy clean (5 files); lint-imports green. `apps/api/tests/test_jobs.py` unchanged and green.
- New tests: indices-first + batches 50/50/20 with progress (1,122)(2,122)(52,122)(102,122)(122,122) and `requests == 5` (BATCH_MAX monkeypatched to 50, because production value is 1); default batches of 1; `--only` no indices; `count=6000` -> batches of 8; gap -> `no_trades`; HTTP 503 batch -> 50 skipped, `partial`, later batches fetched; blocked batch 2 -> `blocked`, indices already stored; checksum independent of batch size and equal to pre-change digest; 418 -> `SourceBlocked`; `archive_name` equals the file `_gap_chart` writes.
- Skipped per card: `parse_bars(batch50 fixture)` test (no fixture, cap = 1).
- Size: see diff stat in PR (prod ~ 60, tests ~ 110 as planned).

## Deviations / notes for the tester
- Batching tests use a monkeypatched `BATCH_MAX = 50`; shipped value is 1.
- `kbs`/`ssi` sources do not implement `archive_name` (not used on the bars path, mypy does not cover them); add if either becomes a bars source.
- A name without bars inside a multi-name batch is `no_trades` (cannot distinguish delisted-omitted from empty; not measured by the spike).
- Outside-set edits: none.
