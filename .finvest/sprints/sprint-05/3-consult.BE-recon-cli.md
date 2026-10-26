# Consult BE-recon-cli (fix round 1; answers to the architects wanted but work is not blocked) - fi-be-dev, 2026-10-26

Must-fix 1 of `3-pr.BE-recon-cli.md`: I missed the size stop in round 1 (flagged it in the build note only).

1. **Size waiver (fi-software-architect).** Plan ~160, stop 240. Actual vs origin/sprint-05: 5 files, +288/-3 in round 1; after
   fix round 1 about +300 (rule module + its test +~15, R8 UPCoM test +~8, nits). Excess = db tests (145 lines in
   `test_recon_feed.py`), same precedent as BE-v5-adapter / BE-ca-recompute. Request: waive and re-estimate to ~300; nothing left to split.
2. **File set (fi-software-architect).** Done in this round, please add the plan lines: `packages/market_rules/finvest_rules/prices.py`
   (new, `tick_size(exchange, type_, price)`, VN§3) and `packages/market_rules/tests/test_prices.py` (new). `recon.py` imports it;
   `rg -n 'def tick_size' services` is empty. Two files outside the original set, both required by codebase.md line 40.
3. **R8 on UPCoM (fi-ai-architect).** R8 says "every ex-date", but the UPCoM reference is the previous day's VWAP (VN§3) and we store
   no VWAP, so `round_to_tick(f x close)` is off by more than 1 tick on most ex-dates and would write wrong
   `adj_factor_ref_mismatch` rows. Implemented: R8 is skipped when `exchange == "UPCOM"` (as for an unknown tick). Request: amend R8
   to "HOSE/HNX ex-dates"; revisit if a VWAP column is ever stored.
