# Answer BE-ca-recompute consult (AI side) — fi-ai-architect, 2026-10-26

**Decision on must-fix 2: option A** (per-version `last`), as the lead recommended. B spends source budget on every ex-date
and C throws away the observed/short rows; A is a rule, not a workaround, and costs ~25 prod lines in AI code.

## Rule (tech plan v1.1 **R6a**, R7 amended; `analytics.md` §1.3; old copies `2-tech-plan.ai.prev-1.md`, `analytics.prev-3.md`)
- A `bars_1d_src` row of version v (one `fetched_at`) carries the source's adjustments for ex-dates `e ≤ last_v` only,
  `last_v` = max `trading_date` of that version. `G_v(d) = Π f_e` over `d < e ≤ last_v`; `nominal(d) = round(A_v(d)/G_v(d))`.
- Pre-ex close at D from the latest bar D−1 of version v: `D ≤ last_v` → invert as today with `G_v`; `last_v < D` → the row is
  already nominal, `P = nominal(D−1)`, no inversion (the lead's test misses this second case: G13b covers it).
- Recon (R7) uses the same `G_v` per theirs row; `recon.py:50` has the same global-`last` bug today.
- Golden G13 (lead's case, must fail on v1 with 51,020) and G13b (press gap, prev row still in V0) added to the plan.

## Who does what
- New AI task **AI-adjust-version** (~90 lines, block in `2-tech-plan.ai.md`; `dag.json` dagRev 3, old copy `dag.prev-2.json`):
  `AdjBar.last: date | None = None` (None → list max, so G1–G12 and every caller stay byte-identical), `series.py` and
  `recon.py` use `b.last or last`. `BE-ca-recompute` and `BE-recon-cli` now wait on it — SA: I touched those two `after`
  lists and the dag `_doc`; please keep them if you re-emit dag.json for item 3.
- BE-ca-recompute round 2 (SA's card): `_one` reads `max(trading_date) OVER (PARTITION BY fetched_at)` into `AdjBar.last`,
  keeps "newest row per date" (any version gives the same nominal once the rule holds). The db test the lead asked for =
  G13 on the db (full F0 before E, short F1 after; assert pre-window rows = 50,000) plus G13b.
- Nit d (BE-market-view-ca, merged): `adjusted_close` is ours (nominal × our factors) → version-free, fine. The S03
  `source_adjusted` path on `bars_1d_src` newest-per-date **is** mixed at the window boundary (a fake f_E step). My
  recommendation to SA: switch that path to `adjusted_close(as_of = today)` as soon as F-015 is merged (small adapter task,
  not this sprint's AI scope); until then the exposure is one f_E step at the boundary, visible in recon.
- Nit c: 0.5 VND lost by BIGINT `adj_c` before dividing by G stays inside the stated ± 1 tick (A18-A); G12 reads 71,700 ± 1.
  Accept this sprint; if SA ever widens `adj_*` to NUMERIC(14,2), R4 already assumes it. Items 3, 4, nits a/b are SA/lead calls.

## Risk, stated
R6a assumes the source re-adjusts **on** the ex-date (data.md §1.4, observed after the fact for FPT 09-21), not the evening
before. A fetch at E−1 evening already adjusted would be mis-labelled `last_v = E−1`; R7's `G_v = 1` exact-equality rule and
R8 (board `ref`) flag it on the first live VN30 ex-date — the tester records that pass/fail in `vn-market.md`'s ledger.
Sponsor not needed.
