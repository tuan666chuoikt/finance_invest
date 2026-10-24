# 3-build BE-ssi-snapshot (sprint-03)

Result: DONE. Branch task/sprint-03/BE-ssi-snapshot.

## Files
- ssi/payloads.py: SsiRow gains tradingDate, openPrice, highest, lowest, matchedPrice, nmTotalTradedQty, nmTotalTradedValue (optional, VND; docstring cites hose.json.gz 2026-10-16 AAA).
- ssi/source.py: pure `parse_snapshot(payload, session, raw_path, exchange)` and `SsiSource.snapshot_bars(session)`.
- domain/ports.py: `snapshot_bars` on the port; kbs/vci raise Unsupported (one method each, as the card says).
- registry.py role literal "snapshot"; settings.py `source_snapshot = "ssi"`.
- tests: test_adapter_ssi.py (7 new), test_registry.py (snapshot assert + kbs/vci Unsupported).

## Behaviour
- Board date from the first row != session -> SourceNoLongerServes(EXCHANGE, served_date); nothing archived.
- qty 0/None or open 0/None -> name in second list. h < max(o,c), l > min(o,c), None/<=0 price -> PayloadShapeError.
- ts = session 00:00 VN as UTC; source "ssi"; prices to_vnd(x, "vnd"); value to_vnd(value, "vnd").
- Archive: feed bars_1d, name board-{hose,hnx,upcom}, written only after the parse accepted it; replay = 0 requests.

## Checks
- `make test-kernel`: 241 passed, ruff clean, mypy clean (5 source files), import-linter ok.
- Fixture: AAA o7090 h7190 l7020 c7100 v684300 value 4855893000, ts 2026-10-15T17:00Z; 41 bars + 5 no-trade = 46 s|e rows.
- Size: 140 insertions across 9 files vs ~95 planned (limit 1.5x = 142).

## Deviations / notes
- Fixture has only stockType "s" rows; CW/bond exclusion is tested with synthetic rows.
- Empty board (no rows) returns ([], []) without a date check (nothing to compare); the caller decides.
- Outside-set edits: none beyond the files named on the card (kbs/vci one-liners are on the card).
- Tester: a board with tradingDate matching but rows frozen (holiday) cannot be told apart here.

## Fix round 1
- Must-fix 1: source.py snapshot value is None when nmTotalTradedValue is None (was 0 VND); new test test_snapshot_unknown_turnover_stays_none.
- Nits taken: list[Bar]/list[str] annotations, += accumulation. origin/sprint-03 already merged (up to date).
- Checks: q.sh kernel make test-kernel exit 0, 247 passed, ruff and mypy clean. Head c5f40ef.
