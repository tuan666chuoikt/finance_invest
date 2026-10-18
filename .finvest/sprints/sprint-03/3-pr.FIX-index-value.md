# 3-pr FIX-index-value — round 1 (BE lead, opus)

**Verdict: APPROVE.** Reviewed head H = 1b53a9eca9d6a3d64544710c72ee33ab7189b6a5 (task 0c0783c + clean sync merge of origin/sprint-03 58156bb, no conflicts).

## Files reviewed
- services/crawler/finvest_crawler/adapters/vci/source.py — `_value_vnd` matches platform.md §4 v1.6 exactly (stocks: ×1 vs ×1e6 by log distance to v×c; indices / v=0: ≥1e9 VND else ×1e6; outside [0, 2**63−1] → None + warning naming raw path, bar kept). Decimal throughout (float only inside the log comparison, never in the stored value).
- services/crawler/finvest_crawler/adapters/vci/payloads.py — docstring + field comment: mixed unit with both live values (data.md §1.2 V2 v1.2).
- services/crawler/tests/test_adapter_vci.py, tests/test_feed_bars_1d.py, fixture gap_chart/VN30-1d.json.gz (59 bars, both eras, envelope kept).
- File set = plan; feeds/bars_1d.py unchanged. Size +80/−11 (excl. fixture) vs plan ~110: within.

## Checks (synced head)
- `make test-kernel`: 203 passed, 20 deselected; ruff clean; mypy 5 files clean; import-linter 5 kept, 0 broken.
- Affected: test_adapter_vci.py + test_feed_bars_1d.py: 32 passed.
- Fail-without-change: old source.py swapped in → 6 new tests fail (index raw-VND, stock raw-VND, BIGINT ×2, fixture, feed), restored.
- Hand recompute: 6,618,016 × 65,000 = 430,171,040,000; 474,963,630,000 / that = 1.104 (picks million reading). VN30 2026-10-16 6386472.73202 × 1e6 = 6,386,472,732,020 ✓. Fixture value/v (avg VND per share) spans 16,170 (2015-03-31) .. 51,627 (2021-06-23) across both unit eras: no 1e6 jump.

## Must-fix
None.

## Nits / notes
1. Plan acceptance example "av = 1e13, v = 1, c = 1 → None" contradicts the plan's own closest-to-1 rule (raw 1e13 is chosen and fits BIGINT). Dev's substitute (v=1e9, c=1e8, av=1e19 and av=−5) proves the intent. SA: correct the example in 2-tech-plan.md.
2. test_adapter_vci.py comment "million reading 1e19 > 2**63 − 1": the chosen reading is the raw one (1e19); wording only.
3. Index rule assumes raw-VND index days are ≥ 1e9 VND; VNINDEX pre-2012 is not in any fixture. BE tester live check: add `SELECT count(*) FROM index_1d WHERE v > 0 AND value IS NOT NULL AND (value / v < 100 OR value / v > 10000000)` = 0 next to the bars_1d_src check.
4. Contract says "never raised": a chosen value ≥ 1e28 would raise Decimal InvalidOperation in to_vnd (28-digit context). Unrealistic for real data; no action.

## Merge
Merged into sprint-03: merge e0402afd96d78f12f8c6f9ec7611ac0b840539b8 (base 97056f8, head 1b53a9e). Base moved after the sync by FE-scenario-cards only (apps/web, 9 files, disjoint from services/crawler); the merge had no conflicts, so the BE checks still apply.
