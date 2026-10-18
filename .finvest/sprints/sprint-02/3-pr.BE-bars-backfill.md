# 3-pr BE-bars-backfill (round 1, fi-tech-lead)

**Verdict: APPROVE.** Reviewed head H = f14d9c1eb0154fb97abd82b8d4245ba37805254e (origin/sprint-02 already merged, "Already up to date").

## Files reviewed (13)
Makefile; domain/ports.py; kbs/ssi/vci `source.py`; vci/payloads.py; cli.py; feeds/bars_1d.py (new); test_feed_bars_1d.py, test_cli.py, test_adapter_vci.py; fixtures FPT/ZZZ.

## Findings
- Contract: manifest keys, checksum line `symbol,trading_date,source,o,h,l,c,v,value` (per-name sorted, names sorted => globally sorted; value empty when null), `requests` excludes replays, exit 2 on blocked, `fetched_at` = archive mtime, universe.source: all as platform.md §4 / ADR-S-008. Indices go through `upsert_index_1d` at 2 dp (IndexBar).
- Layering: lint-imports 4 kept, 0 broken. No new dependency. Port gains `index_bars`; kbs/ssi raise `Unsupported` (mechanical).
- Acceptance: first run complete/1/("ZZZ",)/50/2 requests; replay identical checksum, 0 requests; interrupt then resume = uninterrupted rows, 1 request; blocked on symbol 2 keeps symbol 1, exit 2. All asserted by tests in this diff.
- Size: shortstat 325 lines incl. tests/fixtures; ~190 non-test vs plan ~200 (1.5x = 300): OK. Outside-file-set edits (ports, 3 adapters, vci payloads/tests) are declared in 3-build and needed.
- VCI relaxation (null accumulatedValue -> value None; placeholder v=0/o,h,l,c<=0 skipped; zero-close traded day dropped with a warning instead of PayloadShapeError): declared, tested (`test_bar_with_zero_close_is_dropped_not_fatal`), not a contract change (data.md V2 silent). Non-blocking: the architect should confirm the relaxation of the S01 "bad bar = shape error" rule.

## Must-fix
None.

## Nits (no action required now)
1. Dropped zero-close days are only logged, not listed in the manifest; an audit of history gaps (G2 coverage) will not see them. Consider a counter in a later task.
2. `bars_1d.py` imports private `_fetcher`, `_skip_reason` from `feeds.ticks`; promote to a shared module when a third feed needs them.

## Checks (synced head f14d9c1)
- `make test-kernel` via q.sh: exit 0; 129 passed, 18 deselected; ruff clean; mypy no issues (5 files); lint-imports 4 kept.
- Affected tests alone (test_feed_bars_1d, test_cli, test_adapter_vci): 32 passed.
- `-m db` not required: no migration/repository/SQL change in this diff (repo functions were db-tested in BE-bars-store).
- Live M3 back-fill (>=1,500 symbols, FPT 2006-12-13, coverage >= 99.5 %) is NOT run yet, pending outside the 15:00-23:00 VN window; it belongs to the tester/M3 step, not to this merge.

Merged into sprint-02: merge sha 50dce1404a523a5963710db3f9400aad3a070ad8
