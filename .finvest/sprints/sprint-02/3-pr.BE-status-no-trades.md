# 3-pr BE-status-no-trades (S02-1) — round 1

Verdict: **APPROVE**. Reviewed head H = `e15d4d051bd6fa182cfe4622034018a35c8f9568` (task 694ed61 + sync merge of origin/sprint-02 0bddb4b, clean, no conflicts).

## Files reviewed (git diff origin/sprint-02...H; 8 files, +59/-12, plan ~120 -> within 1.5x)
- apps/api/migrations/versions/0002_crawl_sessions_no_trades.py: ADD/DROP COLUMN symbols_no_trades INT; revises 0001. OK.
- domain/manifest.py: field `symbols_no_trades: tuple[str, ...] = ()` (declared after symbols_skipped to keep positional
  callers; JSON order is what the contract fixes); to_dict emits it between symbols_fetched and symbols_skipped. Matches platform.md §4 example.
- infrastructure/tables.py, repositories.upsert_crawl_session: len(symbols_no_trades). Matches data.md §3.
- feeds/ticks.py: today + empty tape -> no_trades (names sorted, so list sorted); `no_ticks` gone (rg: 0 hits); status rule
  unchanged; invariant assert. Past-date / other-session path untouched.
- tests: test_manifest (key order + value), test_repositories_db (column value 1, 0002 downgrade -1 / upgrade head),
  test_feed_ticks (today no-trade -> complete + on-disk keys + not archived; no-trade + payload_shape -> partial; db column 0).

## Acceptance -> test
- 2-symbol today, VNM empty -> complete, fetched 1, no_trades (VNM,), skipped (): test_empty_tape_today_is_no_trades_and_complete.
- Same fixtures, trading_date < today -> partial/source_no_longer_serves: existing test_past_date_empty_tape_after_good_one_is_partial (green).
- payload_shape + no-trade -> partial: test_no_trade_next_to_a_real_skip_is_partial.
- db column == 1 and migration round-trip: test_crawl_session_upsert_and_status, test_migration_round_trip_and_timescale.
- New tests reference symbols_no_trades / assert complete, so they fail on the base.
- Worked example 911 + 629 + 0 = 1540 -> complete: left to QA-S02-live as planned.

## Must-fix
None.

## Nits (no action required in this task)
1. ticks.py invariant exempts `status == "missed"` (v1.2: a missed run lists no symbols); platform.md §4 states the
   invariant without that exception. SA may add "(except missed)" to the contract text next revision.
2. Every name empty "today" (run before the open, or an unflagged holiday) now yields `complete` with 0 rows. Contract
   caveat covers it; F-003 calendar / F-019 schedule (15:35) / F-012 volume cross-check should guard it.

## Checks on H
- kernel `make test-kernel`: 100 passed, 8 deselected; ruff all checks passed; mypy no issues; lint-imports green (exit 0).
- `pytest -m db` on throwaway timescale/timescaledb:2.17.2-pg16 (finvest_test, removed after): 8 passed.

## Merge
- Merged into sprint-02: `a203568dc005220116843c8dc19ac2bfd69012da` (base 0bddb4b, head e15d4d0), pushed.
