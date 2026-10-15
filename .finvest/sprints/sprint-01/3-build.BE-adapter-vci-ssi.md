# 3-build.BE-adapter-vci-ssi

## Result
DONE. VCI (symbols V3 + daily bars V2), SSI (daily bars S2) adapters and `registry.py` built on `task/sprint-01/BE-adapter-vci-ssi` (base: sprint-01 incl. merged BE-domain, BE-fetcher, BE-adapter-kbs).

## Files
`services/crawler/finvest_crawler/adapters/{vci,ssi}/{__init__,payloads,source}.py`, `adapters/registry.py`; fixtures `tests/fixtures/vci/symbols_getAll/sample.json.gz` (41 rows), `vci/gap_chart/FPT-1d.json.gz` (50 bars), `ssi/history/FPT-1d.json.gz` (50 bars), all recorded live 2026-10-15; tests `test_adapter_vci.py`, `test_adapter_ssi.py`, `test_registry.py`. Production code 253 lines (plan ~230).

## What changed
- `VciSource.symbols()`: GET getAll, archived `symbols/<today VN>/getAll`; keeps `board in HSX|HNX|UPCOM` and `type in STOCK|ETF`; `HSX -> HOSE`; null names -> `""`, `icbCode2` null -> `None`.
- `VciSource.bars()`: one POST for all symbols, archived `bars_1d/<to>/<symbols>-1d-<count>` (hashed above 3 symbols). `ts` = trading-day 00:00 Asia/Ho_Chi_Minh in UTC.
- `SsiSource.bars()`: one GET per symbol, archived `bars_1d_ssi/<to>/<sym>-1d-<count>`, window `count*7//5+10` calendar days, newest `count` bars kept (marked `shortcut:`).
- Prices parse as `Decimal` (never float) and go through `to_vnd` (`vnd` for VCI, `thousand_vnd` for SSI). `Bar.value` is `None` (VCI `accumulatedValue` unit is unstated).
- `ticks()` and 1m bars raise `Unsupported`. Shape drift or bad values raise `PayloadShapeError` naming the archived raw path.
- `registry.make_source` / `source_for`: only place names are resolved; unknown name -> `ValueError("... known: kbs, vci, ssi")`.

## [verify] result: V3 field names (also in `vci/payloads.py` docstring)
No `delisted` field exists. `board` is `HSX|HNX|UPCOM|DELISTED|BOND`, `type` is `STOCK|ETF|CW|BOND|FU|UNIT_TRUST|DEBENTURE`; names `organName`/`enOrganName`; `icbCode2` null on ~52 %. V2 `t` is epoch seconds as a string at 00:00 UTC of the trading day; S2 `t` is an int, same convention.

## Contract honored
platform.md 1.2 (integer VND), data.md 1.2 V2/V3/S2, 1.4 (half-up), ADR-S-005, codebase.md 3 layering (import-linter 3 kept).

## Checks
- `make test-kernel`: `63 passed` (new: 29 across the 3 test files), ruff `All checks passed!`, mypy `Success: no issues found in 5 source files`, import-linter `3 kept, 0 broken`.
- Hand-computed: fixture has 27 STOCK/ETF on live boards (8 HSX + 3 ETF + 8 HNX + 8 UPCOM); `65182.47 -> 65182`, `65182.5 -> 65183`, `58000 -> 58000`; SSI `58 -> 58000`, `58.1 -> 58100`, `58.0005 -> 58001`.

## Deviations / notes
- Delisted symbols are dropped as the task card says, but data.md 1.2 V3 says they are "kept -> survivorship (PR-075)". `SymbolRecord.exchange` has no DELISTED value, so S02 (F-004) will need to decide how to store them; flag for the architect.
- `ssi/source.py` imports `validate` from `vci/payloads.py` (shared error wrapper); a cross-adapter import, small.
- Fixtures were recorded with the project User-Agent; plain curl without it also worked. Responses are gzip-encoded (httpx handles it).

## Outside-set edits
None.

## Notes for the tester
Network is disabled in tests; run `uv run pytest services/crawler/tests/test_adapter_vci.py test_adapter_ssi.py test_registry.py`. A live smoke is one `VciSource(fetcher).bars(["FPT"], "1d", today, 5)`.
