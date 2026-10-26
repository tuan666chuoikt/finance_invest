# Sprint 05 — Tech plan (AI side: adjustment factors, adjusted/reconstructed series, reconciliation rules, `data_snapshot`)

Owner: `fi-ai-architect`, 2026-10-26, plan v1. Inputs: `1-sprint-plan.md` (F-015, F-016, F-023; M2), `product/backlog.md`
F-013–F-016/F-023 worked examples, `knowledge/vn-market.md` **v1.1** (§3 reference price, **§6 incl. the new combined-event
formula + inversion, source S7**), `architecture/data.md` §1.2 V2/S1/S2/V5, §1.4, §3 (`bars_1d`, `bars_1d_src`, `adj_factors`,
`corporate_actions`, `recon_mismatches`), `architecture/analytics.md` §1.1 (`adjusted_close`, `snapshot`), §1.3,
`contracts/analytics.md` §1.4, ADR-S-005 (integer VND, `round_half_up`), `finvest_rules/costs.py` (`RULES_VERSION`, hash test).
The software architect merges the three blocks below into `dag.json` and owns the data-side tasks in §"SA-owned".

## Correctness rules (each one is a test; cite VN§ in the code)

R1 **Pre-ex close P** = nominal close of the latest stored `bars_1d` row with `trading_date < ex_date` (VN§3: reference =
   close of the latest trading day). No such row → no factor, `data_anomalies` rule `adj_factor_no_pre_close`, never guessed.
R2 **Single-event factor** (VN§6): cash c → `(P − c)/P`; bonus/stock dividend a:b → `a/(a+b)` (independent of P); rights a:b at S
   → `(P·a + S·b)/((a+b)·P)`, and **1 when S ≥ P** (VN§3/§6); `split|merge` a:b (a old → b new) → `a/b` [practice, no VN30 case
   expected this sprint]; `listing_change` → 1. Validation: cash → `0 < c < P`; ratios → `a, b ≥ 1`; else anomaly
   `adj_factor_invalid_input` and no factor row. NULL `cash_per_share` / `issue_price` (F-014 unparsed) → anomaly, no row.
R3 **Several events on one ex-date combine in one formula** (VN§6 S7): `P_adj = (P − c + S·r_r)/(1 + r_s + r_r)`, `r = b/a`;
   `factor = P_adj/P`. Cash + bonus equals the product of single factors; **cash + rights does not** (R3 golden below).
   One `adj_factors` row per `(symbol, ex_date)`; `ca_id` = the lowest id of the group. Different ex-dates **multiply**.
R4 **Precision**: factors `Decimal`, 12 places `ROUND_HALF_UP`, stored `NUMERIC(20,12)`; cumulative product computed on the
   12-place rows (not re-derived) so DB and engine agree byte for byte. Adjusted close = `Decimal` 2 places half-up (the sources
   also carry 2 decimals: FPT 65,182.47, data.md §1.2). Reconstructed nominal = integer VND half-up (ADR-S-005), **no tick
   snapping** (A18-A: "± 1 tick" is stated in "how computed", not hidden).
R5 **Adjusted series as of `as_of`**: `adj(d) = nominal(d) × Π f_e` over ex-dates `d < e ≤ as_of`. An ex-date after `as_of`
   is not applied (retroactive by design, charts only — the simulator never reads it this sprint, analytics.md §1.3.1).
R6 **Reconstruction** (A18-A, data.md §1.4, VN§6 inversion), per symbol, walking **backwards** from the newest
   `bars_1d_src` version (`fetched_at` max; `last = max trading_date` of that version): `G(d) = Π f_e` over `d < e ≤ last`
   (events the source could not know are **not** applied); at each ex-date D the pre-ex nominal is
   `P = A(D−1)/G(D) · (1 + r_s + r_r) − S·r_r + c` (rights term dropped and P recomputed when `S ≥ P`); then `f_D` from R2/R3
   with that P; `nominal(d) = round_half_up(A(d)/G(d))` for every d without an observed bar. Rows get `nominal_kind =
   reconstructed`; **an `observed` row is never overwritten** (F-015 last criterion; a test writes both and re-runs).
R7 **Reconciliation** (F-016): `ours(d) = nominal(d) × G(d)` vs `theirs(d) = A(d)` of the newest source version.
   Observed overlap: `diff_pct = |ours − theirs| / theirs × 100`, 4 places; `> 0.1000` → `recon_mismatches` row; a run deletes
   the symbol's old rows first (re-run idempotent). With **no ex-date between d and `last`**, `G = 1` and ours must equal theirs
   **exactly** (0 VND) — any diff there is a unit/adapter bug, not a factor bug. Pre-crawl dates: self-consistency
   `|round(A/G) × G − A| ≤ 1 VND` (holds by construction for `G ≤ 1`; `G > 1` only after a merge). Report per symbol: days
   checked, mismatches, **first mismatching date** (a mismatch streak that starts at date X means a missing or wrong event
   with ex-date X+1 — the data-quality hint F-014 needs). VN30 members from `symbol_index_membership`; report "30/30, k mismatches".
R8 **Independent check on observed ex-dates** (VN§6 S7): `round_to_tick(f × P)` vs the exchange's own **reference price on
   the board** (`S1 ref`) within 1 tick, for every ex-date ≥ crawl start. Needs `ref` on the observed bar (SA-owned, below);
   until stored, the tester reads the board by eye for any VN30 ex-date in 27–29/10.
R9 **`data_snapshot`** = max `fetched_at` over the inputs **actually used**: bar rows served (`bars_1d` and/or `bars_1d_src`)
   + the `corporate_actions` rows whose factors were applied (`ex_date ≤ as_of`; an unapplied future event does not move the
   snapshot). Same inputs + snapshot + `rules_version` → byte-identical JSON. `adj_factors.rules_version = RULES_VERSION`;
   the factor formulas are rules → `RULES_VERSION` bumps to the merge date (the hash test in `test_costs.py` forces it).
   shortcut: `adj_factors` is in place (PK symbol, ex_date); a later CA correction changes past results and moves their
   snapshot (newer `fetched_at`), so a saved scenario's re-check reports `reproducible: false` (contracts §4) — honest, not
   silent; versioned factors come with F-088.

## Golden cases (hand lines go into the JSON `hand` list; tester checks each with a calculator)

| # | Case | Expected |
|---|---|---|
| G1 | cash 1,000, P = 50,000 (D−1), D−2 = 51,000 | f = 0.980000000000; adj D−1 = 49,000.00, D−2 = 49,980.00 |
| G2 | bonus 10:3, P = 93,500 | f = 10/13 = 0.769230769231; adj = 71,923.08 |
| G3 | rights 10:2 at 10,000, P = 50,000 | P_adj = 520,000/12 = 43,333.33; f = 0.866666666667 |
| G3b | rights 10:2 at 50,000 (S ≥ P) | f = 1.000000000000, adj = 50,000.00 |
| G4 | cash 1,000 **and** rights 10:2 at 10,000, same ex-date, P = 50,000 | P_adj = (50,000 − 1,000 + 2,000)/1.2 = 42,500.00; f = 0.850000000000 (**not** 0.98 × 0.866667 = 42,466.67) |
| G5 | cash 1,000 and bonus 10:3, same ex-date, P = 93,500 | (92,500)/1.3 = 71,153.85 = product 0.989304812834 × 0.769230769231 × 93,500 |
| G6 | two ex-dates D1 (G1) < D2 (G2): d < D1 nominal 51,000 | adj(d) = 51,000 × 0.98 × 10/13 = 38,446.15; as_of between D1 and D2 → 49,980.00 |
| G7 | reconstruction: source A(D−1) = 49,000, G = 1, cash 1,000 ex D | P = 50,000 (`reconstructed`); f = 0.98 → matches G1 |
| G7b | source A = 42,500, cash 1,000 + rights 10:2 at 10,000 | P = 42,500 × 1.2 − 2,000 + 1,000 = 50,000 (inverts G4) |
| G8 | G6 chain from source: A(d) = 38,446 (integer-stored), G = 0.753846153846 | nominal = round(50,999.80) = 51,000; self-check 51,000 × G = 38,446.15 → diff 0.15 ≤ 1 VND |
| G9 | observed 2026-10-14 close 93,500 with `nominal_kind = observed`; reconstruction would give 93,499 | row unchanged, kind stays `observed` |
| G10 | recon 49,000 vs 48,900 → 0.2045 % row; 49,000 vs 48,980 → 0.0408 % no row; G = 1 and 93,500 vs 93,500 → 0.0000 | `recon_mismatches` exactly one row |
| G11 | snapshot: bars fetched 2026-10-26T16:14+07, CA fetched 2026-10-27T16:22+07 with ex_date ≤ as_of | `data_snapshot = 2026-10-27T16:22:00+07:00`; same CA with ex_date > as_of → 2026-10-26T16:14 |
| G12 | real data (fixture `services/crawler/tests/fixtures/` FPT V2 rows around the 10 % bonus ex 2026-09-21) | f = 10/11; reconstructed 2026-09-18 close = round(65,182.47 × 1.1) = 71,701 ± 1 VND; tester compares with a public nominal history page by eye and records the value in `4-test.be.md` |

## Tasks (`services/analytics/**` + `packages/market_rules/**`; serial — `after` chain)

#### AI-ca-factors — F-015: corporate-action factor rules (single, combined, inversion) in `finvest_rules`
- Story: F-015 ; Side: ai ; Effort: high ; Size: ~170 lines (≈ 70 prod + 100 tests) ; Lead: opus
- Files: `packages/market_rules/finvest_rules/corporate_actions.py` (new), `packages/market_rules/finvest_rules/__init__.py`
  (export), `packages/market_rules/finvest_rules/costs.py` (`RULES_VERSION` bump + 1 hash line), `packages/market_rules/tests/test_corporate_actions.py`
  (new), `packages/market_rules/tests/test_costs.py` (hash constant)
- Change:
  - `CaEvent(type, ratio_a: int|None, ratio_b: int|None, cash_per_share: int|None, issue_price: int|None)` frozen dataclass
    (types as data.md §3 `corporate_actions.type`).
  - `factor(events: list[CaEvent], pre_close: int) -> Decimal` — R2/R3 combined formula, 12 places; raises
    `InvalidCorporateAction(reason)` on R2 validation failures (caller writes the anomaly).
  - `pre_close_from_adjusted(adj_pre_close: Decimal, events) -> int` — R6 inversion incl. the `S ≥ P` branch; docstring cites
    VN§6 S7 and the "no circularity" argument.
  - `RULES_VERSION = "2026.10.28"` (or the merge date), one new `RULES` entry `ca_adjustment = "VN§6 v1.1"` with
    `verified=False` (practice S7) so the rules page shows it.
- Contract: knowledge/vn-market.md VN§3 (reference price), VN§6 (formulas, combined formula, inversion); ADR-S-005.
- Acceptance: G1–G5, G3b, G7, G7b exactly; `factor` of cash 50,000 at P 50,000 → `InvalidCorporateAction`; a Hypothesis
  property: for random valid events and P, `pre_close_from_adjusted(P × factor, events) == P` (round-trip to 1 VND);
  changing a formula without bumping `RULES_VERSION` fails the hash test.
- Out of scope: DB, V5 parsing, split handling beyond `a/b`, tick snapping.

#### AI-adjust-series — F-015: adjusted series, reconstruction and the `MarketView` additions (pure, fixture-driven)
- Story: F-015, F-023 ; Side: ai ; Effort: high ; Size: ~220 lines (≈ 90 prod + 110 tests + 20 golden JSON) ; Lead: opus
- Files: `services/analytics/finvest_analytics/adjust/__init__.py`, `services/analytics/finvest_analytics/adjust/series.py` (new),
  `services/analytics/finvest_analytics/domain/models.py` (`AdjBar`, `NominalBar` with `nominal_kind`, `Factor`),
  `services/analytics/finvest_analytics/domain/ports.py` (`corporate_actions(symbol, as_of)`, `adjusted_close(...)` per analytics.md §1.1),
  `services/analytics/finvest_analytics/fixtures.py` (fixture view gains CA rows and the R9 snapshot rule),
  `services/analytics/tests/test_adjust_series.py` (new), `services/analytics/tests/golden/adjust/001-…-012-*.json` (G1–G12 data)
- Change:
  - `cumulative(factors, d, upto) -> Decimal` (R5/R6 `G`), `adjusted(nominal_bars, factors, as_of) -> list[AdjBar]` (R5, 2 dp),
    `reconstruct(src_bars, events_by_ex_date, observed_dates) -> (list[NominalBar], list[Factor])` (R6: backward walk, factors
    derived from inverted pre-closes before crawl start and from observed P after it; skips observed dates).
  - Pure functions over sorted lists; no SQL, no I/O (analytics.md "engine is fixture-driven"); deterministic ordering →
    byte-identical output (R4, R9).
  - Fixture `MarketView.snapshot()` = max `fetched_at` over bars served **and** CA rows applied (R9, G11); the Figure
    `how` text for a reconstructed input states "giá danh nghĩa tái dựng, sai số ± 1 bước giá" (A18-A).
- Contract: analytics.md §1.1, §1.3; contracts/analytics.md §1.4 (`data_snapshot`); data.md §1.4; VN§6.
- Acceptance: G1–G9, G11 from the golden JSON (same loader style as `tests/golden/sim`); re-running on the same fixture gives
  identical `json.dumps(sort_keys=True)` bytes; a factor with `ex_date > as_of` leaves the series and the snapshot untouched.
- Out of scope: SQL adapter (SA task BE-market-view-ca), scenario engine switching to nominal (F-043/F-044, R2), charts.

#### AI-recon-rules — F-016: reconciliation rules and run report (pure)
- Story: F-016 ; Side: ai ; Effort: high ; Size: ~130 lines (≈ 50 prod + 80 tests) ; Lead: opus
- Files: `services/analytics/finvest_analytics/adjust/recon.py` (new), `services/analytics/tests/test_recon.py` (new)
- Change:
  - `reconcile(nominal_bars, factors, src_bars, *, threshold=Decimal("0.1")) -> ReconResult(mismatches: list[Mismatch],
    checked: int, exact_days: int, first_mismatch: date|None)` per R7; `Mismatch(symbol, date, ours, theirs, diff_pct)` with
    `diff_pct` 4 places half-up (fits `NUMERIC(8,4)`).
  - `summary(results: dict[symbol, ReconResult], expected: set[str]) -> str` → "30/30, k mismatches; first mismatch FPT 2026-09-18"
    (missing symbols listed, never counted as pass).
  - R8 helper `ref_check(f, pre_close, board_ref, tick) -> bool` (`|round_to_tick(f·P) − ref| ≤ tick`), used by the SA's recon CLI
    when `ref` is stored.
- Contract: data.md §1.4 (3), §3 `recon_mismatches`; backlog F-016 examples; VN§6 S7 (R8).
- Acceptance: G10; the G = 1 exact-equality rule (a 1-VND diff with no ex-date between → mismatch flagged as `unit_or_adapter`
  in the message); pre-crawl self-consistency passes on G8 and fails on a hand-broken A; `summary` with 29 of 30 symbols
  → "29/30" and the missing name.
- Out of scope: S2 cross-check fetching (SA), writing to the DB, the F-021 page.

Order: AI-ca-factors → AI-adjust-series → AI-recon-rules (series imports factors; recon imports series). All three can
start before F-014's table lands (pure + fixtures); the SA glue tasks come after F-014 and AI-adjust-series. Total ≈ 520
lines.

## SA-owned data-side tasks (software architect writes these blocks; the AI side only states what they must satisfy)

- **Migration 0010** per data.md §3: `corporate_actions`, `corporate_action_log`, `adj_factors`, **`bars_1d` (nominal, with
  `nominal_kind`, `source`, `fetched_at` and a `ref BIGINT` column for R8)**, `recon_mismatches`. Today the SSI board bar is
  written into `bars_1d_src` with `source='ssi'` (`feeds/bars_1d.py` kind `snapshot`, `upsert_bars_1d_src`): the observed
  nominal must move to `bars_1d` (`observed`), otherwise `SqlMarketView.bars_1d`'s "newest `fetched_at` per date" mixes a nominal
  SSI row with adjusted VCI rows (harmless today, wrong on the first ex-date after crawl start — flag for F-013's acceptance).
- **F-014 step 3** (V5 adapter, diff log, budget) and the per-press recompute: for every symbol whose CA rows changed, run
  `reconstruct` + upsert `adj_factors` / reconstructed `bars_1d` rows (never over `observed`), anomalies for R1/R2 failures.
- **BE-market-view-ca**: `SqlMarketView.corporate_actions`, `adjusted_close`, snapshot per R9 (CA `fetched_at` joins `_served`),
  `GET /api/health` returns `rules_version` (F-023), and the F-023 reproducibility test on the SQL view (`db` marker).
- **`crawl recon` CLI** (0 source calls): VN30 + saved-scenario symbols, writes `recon_mismatches`, prints `summary`; records
  a `crawl_runs` row `feed='recon'`. **S2 cross-check** (30 calls, thousand VND × 1000 in the adapter, data.md §1.2 S2) as a
  second `theirs` — first to slip per the sprint plan; its block behaviour needs the M0 spike line.
- Fixture for G12: record FPT V2 rows 2026-09-15…2026-09-25 and the V5 event (ex 2026-09-21, `exerciseRatio` 0.1) in
  `services/crawler/tests/fixtures/` during the M0 spike (≤ 2 calls).

## Honesty notes for review
- Adjusted series are retroactive: a result's numbers legitimately change when a new ex-date passes or a CA is corrected; the
  change is visible through `data_snapshot` (R9) — the review checks that no test "freezes" factors by stubbing `as_of` away.
- Reconstructed nominal is a model, not an observation (A18-A): flags + "how computed" text are test-asserted, not optional.
- Formulas in VN§6 are exchange practice (S1 principle, S7 broker pages); R8 against the board `ref` is the only primary
  verification we can run for free. Record the first real pass/fail in the verification ledger of `vn-market.md` at review.
