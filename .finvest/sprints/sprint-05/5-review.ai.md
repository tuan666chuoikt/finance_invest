# Sprint 05 — AI/quant review (fi-ai-architect, 2026-10-26)

Scope: `origin/sprint-05` @ 2df45e4 — `packages/market_rules/finvest_rules/corporate_actions.py`,
`services/analytics/finvest_analytics/adjust/{series,recon}.py`, `services/crawler/finvest_crawler/feeds/recompute.py`,
`adapters/vci/events.py` (B-05-1), `apps/api/finvest_api/market_view.py`; tester report `4-test.be.md` (round 2).
Against plan v1.2 `2-tech-plan.ai.md` R1–R9, goldens G1–G13b. **Verdict: PASS** (follow-ups below, none blocking).

## Rules vs code
| Rule | Where | Finding |
|---|---|---|
| R1 pre-ex close = latest bar `< ex_date`, never guessed | `series.forward_factors`; `recompute._one` anomaly `adj_factor_no_pre_close` for `d <= first` | ok; `reconstruct` skips `e <= first` too |
| R2 single factors + validation | `corporate_actions._terms`/`factor` | ok: cash `0 < c < P`, ratios ≥ 1, rights `S ≥ P` dropped, `split` a/b, `listing_change` 1; `InvalidCorporateAction(reason)` → anomaly `adj_factor_invalid_input` via `recompute._reconstruct` (culprit ex-date dropped, symbol continues) |
| R3 one formula per ex-date | `factor`: `(P − c + ΣS·r_r)/(1 + r_s + Σr_r)/P` | ok; G4 ≠ product, G5 = product (goldens 004/005) |
| R4 Decimal 12 dp half-up, adj 2 dp, nominal int, no tick snap | `_PLACES`, `_PX_PLACES`, `round_vnd`; `cumulative` multiplies the stored 12-place rows | ok; `cumulative` quantizes the product once (12 dp), fine for DB/engine agreement |
| R5 adj as of `as_of`, future ex-dates not applied | `series.adjusted` (`d < e ≤ as_of`), `market_view.adjusted_close` | ok (011b golden) |
| R6/R6a backward walk, per-version `last_v`, observed never overwritten | `series.reconstruct` (three P branches: observed / `last_v < D` no inversion / inversion), `recompute._one` + repo guard | ok; G7, G7b, G8, G9, G13, G13b goldens present; OHLC divided by the same `G_v` |
| R7 recon: self-check ≤ 1 VND, `G = 1` exact, else 0.1 % | `recon.reconcile` branch order reconstructed → G=1 → pct; `_PCT_MAX` cap (lead must-fix, good catch) | ok; `summary` never counts `checked == 0` as pass |
| R8 ref check | `recon.ref_check` helper exists | **not exercised live** (no VN30 ex-date fell in 27–29/10 yet); stays an open check for S06 |
| R9 snapshot = inputs actually used | `market_view._serve` over bars + `corporate_actions` rows with `ex_date ≤ as_of` | ok (G11/G11b) |

## Independent evidence (tester, round 2)
- Fraction oracle over all **1,346 factors / 110 names**: 1,303 equal at 12 dp, **43 differ ≤ 7.4e-5 relative**. That is
  1 VND of P on a ~13,500-VND stock (1/13,500 = 7.4e-5): the inversion returns an integer P (R4), the oracle used the exact
  Fraction. Expected, bounded by 1/P, and the self-check absorbs it: **0 of 292,577** reconstructed × G rows > 1 VND vs V2.
- B-05-1 (ISS stock dividends unmapped): fix is in the title mapper, order `quyền mua` → `cổ tức bằng cổ phiếu|thưởng` →
  non-adjusting → `phát hành thêm`; 612 captured ISS titles hit exactly one keyword. Hand check HPG 10:1 ex 2026-05-25:
  f = 10/11 = 0.909090909091; 23,955 / 0.909090909091 = 26,350.4999… → **26,350** (reported 26,350; ±1 VND by R4). 205 stock
  dividends now carry factors — this was the real money bug of the sprint; without it every pre-2026 HPG/FPT-style return was
  understated by the bonus ratio.
- Idempotence: recompute ×2 → identical bars md5; replay with pinned names → 0 requests, 0 changes (R9 reproducibility holds).

## Deviations and follow-ups (none change numbers)
1. **F-016 "30/30" is 26/30** (B-05-8): VNM, VPB, VPL, VRE have one `vci` row each — a bars backfill gap, not a rule defect.
   Ops: `crawl bars --only VNM,VPB,VPL,VRE` on live, then `crawl recon`. The PM's C1 condition stays open until then.
2. **`listing_change` noise** (lead nit 1, decision requested): plan R2 says factor 1, but a factor-1 row adjusts nothing and
   an early one spawns `adj_factor_no_pre_close` anomalies (~336 rows). Decision: recompute skips `listing_change` entirely
   (one filter in `recompute._one`, `a.ex_date and a.type != "listing_change"`); R2 text updated at the next plan revision. S06, small.
3. **R8 unverified against the board** until an observed VN30 ex-date exists; keep the tester's by-eye step in S06 for the
   first one (ref column is stored, helper is ready).
4. `market_view.bars_1d` applies factors over `(d, today]`, not `(d, as_of]`: correct for a *source-adjusted* basis (the
   source's newest version is adjusted to today), and exactly why the flag below must stay. Not a look-ahead bug while
   `price_basis = source_adjusted`; becomes one the day the simulator claims `nominal` — F-043/F-044 must switch to `as_of`.
5. B-05-9 (unmapped anomalies appended per run): count distinct `(symbol, source_event_id)` in the sentinel; ops, cosmetic.

## "≈ approximate" flag — keep
Yes, still correct and required. `market_view.price_basis()` is the constant `source_adjusted`; the engine still fills at
the adjusted close, with no dividend cash and no event ledger (contracts §2.3). The flag means "returns computed on a
series where cash dividends are netted into price and pre-ex prices are rescaled" — true today for every scenario, whether
the bars come from `bars_1d_src` or from reconstructed nominal × factors. Drop it only when F-043/F-044 land (fills on
nominal, dividends and bonus shares as ledger events); even then a scenario whose window touches `reconstructed` rows keeps
flag `reconstructed_nominal` (contracts §1.3, A18) with "± 1 bước giá" in `how`.

## Contract
`contracts/analytics.md` v1.3: `dates.shifts[].field` now lists `contribution` (DCA instalment shifts, reasons
`non_trading | no_bar | after_end`), as built in `sim/dca.py` / `sim/whatif.py` and rendered by FE-fix-dca-shifts. No other drift found.

Verdict: **PASS** for the AI/quant slice (F-015, F-016 rules). Open: items 1–3 above are S06/ops follow-ups.
