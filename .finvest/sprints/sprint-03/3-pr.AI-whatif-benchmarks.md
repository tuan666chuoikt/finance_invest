# PR review: AI-whatif-benchmarks (F-048)

## Round 1 (fi-tech-lead, BE, 2026-10-18): APPROVE

Reviewed head H = `8d4b18c3c34f17d14e3d4013654a997f2072058d` (task head 30a8760/c2c1ecb + clean sync merge of
origin/sprint-03 c4c97ad, no conflicts).

### Files reviewed (git diff origin/sprint-03...HEAD, +286/-5, plan Size ~340, stop 510: within)
- `services/analytics/finvest_analytics/sim/benchmark.py` (new, 124)
- `services/analytics/finvest_analytics/sim/whatif.py` (+11/-1: `with_benchmarks` kw, fills `benchmarks`)
- `services/analytics/tests/test_benchmarks.py` (8 tests), goldens `008-vnindex-lump`, `009-vnindex-dca`, `010-etf-engine-and-na`
- `services/analytics/tests/test_golden.py` (outside the file set, reported: runner gains `index` and `extra` view keys; test infra only)

### Contract / plan check
- contracts/analytics.md §2.4 `benchmarks`: VN-Index `Σ amount_i × idx(sell)/idx(date_i)`, Decimal end to end, half-up to VND,
  `investable false`; E1VFVN30 = same request through `run_whatif` with `with_benchmarks=False` (no recursion);
  `diff_pp = scenario − benchmark` at 4 dp; missing bar on any contribution date or sell ⇒ `available false, first_available`,
  no `value_vnd` key (never a zero). Shape matches the contract example. `benchmark_etf` ignored (S03 fixed list). OK.
- Look-ahead: each index read is `index_1d(VNINDEX, d, d, as_of=d)`; the ETF run is the engine itself (as_of-bounded).
  The n/a path reads index history up to the snapshot for `first_available` only (metadata, no number). OK.
- ETF gaps: an own buy/sell shift in the ETF run (bar gap) makes contribution/sell dates differ ⇒ n/a, not a shifted result. OK.
- Flags: ETF run's flags are not merged into the scenario. Figures carry `how` with `cite PR-034` and `inputs.investable`.
- Layering: import-linter 5 kept, 0 broken. No new dependency, no network, no secrets, no SQL.

### Independent recomputation (python Decimal, ROUND_HALF_UP)
- 008: 10,000,000 × 1260.00/1200.00 = 10,500,000; pl 5.0000; diff 6.1098 − 5.0000 = 1.1098. Matches.
- 009: 2,000,000 × 1100/1000 + 2,000,000 × 1100/1250 = 3,960,000; pl −1.0000; diff −1.8338. Matches.
- 010: qty 400, fee 12,000, cash 1,988,000, liquidation 10,367,000, pl 3.6700, diff 2.4398. Matches.
- 2-dp: 10,000,000 × 1234.57/1234.56 = 10,000,081.0005 → 10,000,081. Matches the test.

### Checks on H
- `q.sh kernel make test-kernel`: exit 0, 188 passed, 20 deselected (db); ruff clean; mypy ok (5 files); import-linter 5 kept / 0 broken.
- Goldens 008-010 fail without the change (their `benchmarks.*` keys do not exist on the base, which returns `[]`).

### Must-fix
None.

### Nits / follow-ups (not blocking)
1. `benchmark.py:102` the ETF run uses the default `finvest_rules.costs`, not the scenario's injected `rules`; only matters for
   tests that inject rules. Pass `rules` through when next touched.
2. `test_benchmarks.py:70` `test_future_index_bar_is_not_used` keeps `sell_date = 2026-10-15`, so the 10-16 bar is outside
   `[d, d]` anyway; it does not prove `as_of`. Stronger: `sell_date: null` with a snapshot before the future bar.
3. `test_benchmarks.py:22` flags are a set, so `count("approximate") == 1` would hold even if ETF flags were merged; assert the
   ETF-only flags (e.g. one the ETF run raises and FPT does not) are absent instead.
4. Contract gap for **sa**: with no index/ETF bars at all the result is `first_available: null` (reported in 3-build). The
   contract example only shows a date, and the FE type `apps/web/src/features/scenarios/result.ts:23` declares
   `first_available: string`. Suggest the contract says `string | null` and FE renders "n/a" without a date.
5. FE fixture `apps/web/src/features/scenarios/fixtures/envelope-001.json:33` uses `unit: "pp"` for `diff_pp`; the contract unit
   list (§1.1) has no `pp` and the engine emits `pct`. FE should align the fixture (label "điểm %" in UI).

### Merge
Merged by `sm.sh merge`: base c4c97ad, head 8d4b18c, merge sha `941572d788a3f13904ae5cfd5eb3107d25de752f` into sprint-03 (pushed). Worktree removed.
