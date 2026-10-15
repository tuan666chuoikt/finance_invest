# 3-pr.BE-adapter-vci-ssi

## Round 1: APPROVE (head e7c98c7d61e34b7cdd64379cbfc441300e2242f4)
Files reviewed: adapters/registry.py, vci/{__init__,payloads,source}.py, ssi/{__init__,payloads,source}.py, 3 test files, 3 fixtures. Branch already synced with origin/sprint-01 (no merge needed). Size 253 prod lines vs ~230 plan (within 1.5x).

Contract: V2/V3/S2 field use and units match; `to_vnd` with "vnd" (VCI) / "thousand_vnd" (SSI), Decimal parsing (no float); ts = trading-day 00:00 Asia/Ho_Chi_Minh in UTC; HSX->HOSE; CW/DELISTED/BOND dropped; ticks/1m Unsupported; unknown source -> ValueError listing kbs, vci, ssi; registry is the only name resolver.
Independent recount of the V3 fixture: 41 rows, 27 STOCK/ETF on HSX|HNX|UPCOM (test asserts 27). V2 fixture has 50 ascending bars incl. 65000.65-style floats; S2 fixture 50 ascending bars (last close 58 -> 58000). Ascending order is what the [-count:] trim in SSI relies on.

Checks (synced head): make test-kernel via q.sh: 63 passed, ruff clean, mypy ok, import-linter 3 kept.

Must-fix: none.
Nits (no action required this sprint):
1. ssi/source.py imports `validate` from vci/payloads.py (cross-adapter); move to a shared module when a 4th adapter appears.
2. Archive replay is keyed by (feed, to, name): a bars call with to=today during a session would replay a partial bar later. Relevant for S02 bar feeds, not S01.
3. Delisted symbols are dropped per the task card, but data.md 1.2 V3 wants them kept for survivorship (PR-075) and SymbolRecord.exchange has no DELISTED value. Flag for software architect before F-004 (S02).
4. mypy config only covers the domain package, so adapters are not type-checked (pre-existing scope).
Merged: 68c94c6a2199444dc76daeef735c9c74e407e4ca
