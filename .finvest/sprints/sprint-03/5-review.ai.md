# 5-review AI/quant — sprint-03 (fi-ai-architect)

**Verdict: PASS** (0 blockers, 3 notes). Reviewed `origin/sprint-03` @ 2b34322: `services/analytics/finvest_analytics/sim/{whatif,dca,benchmark,dates,figures}.py`,
`domain/money.py`, goldens 001–010, `apps/web/src/features/scenarios/{ScenarioCard,HowComputed,result}.ts(x)`.
Suite: `pytest services/analytics` 40 passed (worktree test-be-03 @ 2236c1e = origin/sprint-03 merged).

## Correctness of money / returns (independent recomputation)
| Case | Hand result | Engine | |
|---|---|---|---|
| Golden 001 FPT 10M @93,500 → 100,000 (lot 100, 0.15 %, tax 0.1 %) | qty 100, fee 14,025, cash 635,975, liquidation 10,610,975, pl_pct 6.1098 | same | PASS |
| VN-Index benchmark, FPT 2024-02-15 → 2026-10-23 (tester, live DB) | 10,000,000 × 1774.15 / 1202.50 = 14,753,846.15 → 14,753,846 | 14,753,846 | PASS |
| Testers' oracle (4-test.be.prev-1) 4 lump-sum cases + goldens 005–007 DCA | 8/8 | 8/8 | PASS |
| Golden 008/009/010 (index lump, index DCA, ETF through engine + n/a) | hand-checked by lead, recomputed by me from the `hand` block | match | PASS |

Formulas match contracts/analytics.md §2.4: `max_qty` floors whole lots then fixes up for the rounded fee; `fee`, `sell_tax`,
`liquidation = cash + mv − fee − tax`; DCA `pl_pct` ÷ total contributed, `cagr` null; percent 4 dp ROUND_HALF_UP; VN-Index
`Σ amount_i × idx(sell)/idx(fill_i)` on the **actual fill dates** (shifted), price-only, no lots.

## Honesty rules
- No look-ahead: every priced read is `as_of = t` (fill at close of `t`), index `at(d)` with `as_of = d`, sell/curve `as_of = m`;
  `resolve_sell` never reads past `view.snapshot()`. The only `as_of = date.max` read is the validation/bar-alignment list
  (`bar_days`), which feeds no number — acceptable (a schedule, not a signal).
- Approximate: `envelope()` sets `approximate = price_basis != "nominal"` and adds the flag; golden 001 asserts both; FE shows it
  on card, table and how-computed panel (`approximate.source_adjusted` i18n key, flag only from the engine) — matches §1.4.
- Benchmarks never show a zero: any gap → `available: false, first_available` (`null` when the index has no bars at all);
  FE `result.ts` types it `string | null`, `ScenarioCard` renders n/a without a date. Contract mirrored (below).
- How-computed panel: `how.inputs` names every number; cost cites `VN§5`, lots `VN§4`, benchmarks `PR-034`.

## Notes (no action needed this sprint; carry to S04 plan)
1. `whatif.py` curve loop starts with `i = -1` and `states[i]` would read the **last** state if the first calendar day had no
   fill row; today impossible (first calendar day == first fill), so a latent trap, not a bug. Add an assert or start at 0.
2. ETF benchmark is n/a whenever the ETF's fill/sell dates differ from the stock's (conservative by design, §2.4); the card
   wording "n/a since <first>" then names a date even though the cause is a mid-range gap — a UX note for the PM, not math.
3. `holding_days` for DCA = first fill → valuation; fine for the display, but a future money-weighted return (XIRR) must not
   reuse it. Already excluded from `cagr` (null).

## Contract change mirrored
`contracts/analytics.md` v1.2 (archived v1.1 → `analytics.prev-2.md`): §2.4 `benchmarks[].first_available: string | null`,
null when the benchmark has no bars at all — same wording as platform.md v1.8 §2.5. No code change needed; engine and web
already comply (`benchmark._na`, `result.ts`).
