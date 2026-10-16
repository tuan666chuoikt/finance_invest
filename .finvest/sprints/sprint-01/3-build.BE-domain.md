# BE-domain build
Result: DONE. Tick/Bar/SymbolRecord, MarketDataSource port + exceptions, to_vnd/to_shares, canonical_line/checksum/dedupe/Manifest.
Files: packages/market_data/finvest_market_data/domain/{models,ports,units,manifest}.py, packages/market_data/tests/{test_units,test_manifest}.py.
Contract: platform.md 1.2, 4; ADR-S-005/006/008; codebase.md 3 (S01 subset of the port).
Checks: `make test-kernel` exit 0: 13 passed; ruff all passed; mypy strict no issues (5 files); lint-imports kept.
Decisions: Manifest flattens `universe` into universe_source/as_of/count and `symbols_skipped` into (symbol, reason) tuples; to_dict() emits the exact section-4 shape.
`ts` must be UTC (offset 0), so a +07:00 aware datetime is also rejected (ADR-S-006). to_vnd rejects floats by design (callers pass str/Decimal).
Bar also validates ts/prices>0/volume>=0 (not in card; same rule as Tick). dedupe keeps the first-seen key position with the last row's value.
Deviations: none. Outside-set edits: none.
Notes for tester: tests use `# type: ignore[arg-type]` only for the side param helper.
