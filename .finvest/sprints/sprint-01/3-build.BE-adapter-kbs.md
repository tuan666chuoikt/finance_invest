# BE-adapter-kbs build
Result: DONE. KbsSource (name="kbs", ticks only) + pure parse_ticks + pydantic payload models + real FPT fixture.
Files: services/crawler/finvest_crawler/adapters/kbs/{__init__,payloads,source}.py, tests/fixtures/kbs/trade_history/{FPT-2026-10-15,empty}.json.gz, tests/test_adapter_kbs.py (~200 lines incl. tests).
Contract: data.md 1.2 K1, platform.md 4 (VND, shares, UTC ts, seq=AVO, side B|S|null), PM call 2 (SourceNoLongerServes on empty or date mismatch), ADR-S-002 (PayloadShapeError names the archive path).
Checks: `make test-kernel` exit 0: 34 passed (12 new), ruff ok, mypy ok (domain scope), lint-imports 3 kept. No network in tests (MockTransport).
Live findings (fixture recorded 2026-10-15 21:56 from FPT, 3,870 rows, trimmed to the first 50 = newest 50):
- Array is NEWEST FIRST and rows sharing one `t` are in arbitrary order, so parse_ticks sorts by seq (AVO). AVO is unique and equals the running sum of FV in chronological order for the whole 3,870 rows (verified), so it is a safe seq.
- LC IS filled in the evening sample (S 2239, B 1629, "" 2: the ATO/ATC prints). The data.md [verify] about LC is answered: side is filled.
- Empty tape is `{"data":[]}` HTTP 200 (checked with a bogus symbol).
Deviations:
- Card example `t="2026-10-15 14:45:08:16"` is not in the real fixture (newest row is `14:45:07:44`); the fixture test asserts the real row and a synthetic row test asserts the card's 14:45:08:16 / FMP 58000 / FV 100 / AVO 1234500 / LC "" values.
- `parse_ticks` has an optional 4th arg `raw_path` (default `<unarchived>`) so the pure function can name the archive path in PayloadShapeError; KbsSource passes `fetcher.archive.path("ticks", date, symbol)`.
- Row validation is stricter than the card: FMP > 0, FV/AVO >= 0, `t` pattern, LC in B|S|"" (bad values become PayloadShapeError instead of a ValueError from Tick).
Outside-set edits: packages/market_data/finvest_market_data/domain/ports.py: SourceNoLongerServes now takes (symbol, served_date=None) and exposes both attributes (the acceptance needs `.served_date`; BE-domain had a bare class). Backwards compatible; BE-feed-ticks can rely on `.served_date`.
Notes for tester/feed: mypy config covers only packages/market_data domain, so the crawler adapter is not type-checked by the kernel (checked by hand: only import-untyped noise).
