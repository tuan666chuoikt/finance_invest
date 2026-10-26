# Finvest — Analytics architecture (simulator, backtester, "why it moved", evals)

Owner: `fi-ai-architect`. Status: **v1.4, 2026-10-26** (v1.4: §1.3 recon self-check only against the origin source, S05 BE-recon-s2 consult, v1.3 = `analytics.prev-4.md`; v1.3: §1.3 per-version `last`, v1.2 = `analytics.prev-3.md`; v1.2: §1.3.1 `holding_days` display-only note, S03 review note 3; v1.1 =
`analytics.prev-2.md`; v1 = `analytics.prev-1.md`; inception after `system.md`/`data.md` v1). Inputs: `product/prd.md`
(Approved v2, PR-030…039, PR-070…078, PR-090…095, PR-110), `product/backlog.md` (E4, E6, E7), `knowledge/vn-market.md`
(VN§n, verified 2026-10-15), `architecture/system.md` §2–4, `data.md` §1.3–1.4, §3, `codebase.md` §2–3, ADR-S-001/005/006.
Decisions: `adr/ADR-A-001…006`. Interface: `contracts/analytics.md`. Package: `services/analytics` → `finvest_analytics`
(`sim`, `backtest`, `explain`, `metrics`, `evals`), imported in-process by `apps/api` (system.md §3); never imports
`finvest_crawler`; reads the DB only through the `MarketView` port (§1.1).

Principle: **every number is reproducible from (data_snapshot, rules_version, params) and carries its formula**; the
engine must be able to lie in no way a golden case cannot catch.

## 1. One engine: event-sourced ledger (ADR-A-001)

### 1.1 Ports (domain, pure)
```python
class MarketView(Protocol):                      # read-only; every method takes as_of and returns rows with ts <= as_of
    def calendar(self, venue, start, end) -> list[date]                       # trading days (data.md trading_calendar)
    def bars_1d(self, symbol, start, end, *, as_of) -> list[DailyBar]         # nominal o/h/l/c/v/value, ref, ceiling, floor,
                                                                              #   nominal_kind observed|reconstructed
    def adjusted_close(self, symbol, start, end, *, as_of) -> list[AdjBar]    # ours: nominal × cumulative adj_factors
    def corporate_actions(self, symbol, start, end, *, as_of) -> list[CorporateAction]
    def index_1d(self, index_code, start, end, *, as_of) -> list[IndexBar]
    def flows_1d(self, symbol, start, end, *, as_of) -> list[Flow]           # foreign; prop_net_value nullable (A17)
    def symbols_as_of(self, trading_date) -> list[SymbolRecord]              # listed that day incl. later delisted (PR-075)
    def sector_peers(self, symbol, trading_date) -> list[str]                # same icb_code2, listed that day
    def snapshot(self) -> datetime                                           # max fetched_at of what it will serve = data_snapshot
```
`as_of` is a **date** = close of that trading day (ADR-S-006: dates in Asia/Ho_Chi_Minh). The SQL implementation filters
`fetched_at <= snapshot` so a saved scenario re-run (F-088) sees the same rows; the fixture implementation serves
`tests/fixtures/analytics/*.parquet`.

### 1.2 Simulation loop (`finvest_analytics.sim`)
State: `cash` (int VND), `positions[symbol] = {sellable, pending[(arrival_date, qty)], bonus_pending[(arrival, qty)]}`,
`receivables[(pay_date, amount)]`, `rights_open[...]`, `ledger: list[LedgerRow]`. For each trading day `t` of the
venue calendar from `start` to `end`:
1. **Settle**: pending shares with `arrival_date <= t` become `sellable` (arrival = 2nd trading day after the fill day,
   available for a fill at `close` of that day, VN§5 "before 13:00 T+2"); receivables with `pay_date <= t` → cash
   (`dividend_cash`); sale cash with `settle_date <= t` → cash (or at fill when `cash_advance`, fee rate param, PR-038).
2. **Corporate actions with `ex_date == t`** (VN§6), applied to shares *held at close of t−1* (sellable + pending +
   bonus_pending, i.e. economic ownership):
   - `cash_dividend`: gross = qty × cash_per_share; tax = round_half_up(gross × 5 %); receivable net on `pay_date`
     (or ex_date + 30 calendar days if pay_date unknown → flag `pay_date_assumed`). `dividend_mode = cash | reinvest`:
     reinvest = a buy order on the pay date at the declared fill rule, whole lots only (F-043).
   - `stock_dividend | bonus`: new = floor(qty × b / a) (default `round_down_cancel`, VN§6), enters `bonus_pending`
     with arrival = record_date + 30 calendar days `[assumed]`, **valued from ex_date** at the nominal close.
   - `rights a:b @ S`: entitlement = floor(qty × b / a); policy `exercise_if_cash | lapse | exercise` (A10 default first):
     cash −= entitlement × S on ex_date (simplification: payment window ignored, flagged); shares pending like bonus.
   - `split | merge`: qty × ratio, nominal cost basis unchanged. `delisting`: forced sale at the last nominal close with
     flag `delisted_exit` (PR-075).
3. **Decide** (`strategy.signal(as_of=t, view)`): what-if is the trivial strategy "buy on N, sell on M". Only
   `view.*(…, as_of=t)` is reachable → look-ahead impossible by construction, and tested (§5).
4. **Fill** at the declared rule (ADR-A-002): `close_t` (default what-if) · `next_open` (default backtest: order on t,
   fill at `open(t+1)`, booked on t+1) · `vwap_t` = value/volume of the bar · `limit(p)`: fills at `p` only if
   `low <= p <= high`, else "no fill" with reason (F-042). Buy quantity = `floor(cash / (p × lot × (1 + fee))) × lot`;
   `fee = round_half_up(qty × p × fee_rate)`; sell `tax = round_half_up(qty × p × 0.1 %)`; bonus-share sales add
   `round_half_up(min(p, 10_000) × bonus_qty_sold × 5 %)` (VN§5, A19). Never fills outside `[low, high]`; a day with
   `volume == 0` does not fill (flag `no_liquidity`).
5. **Mark to market** at nominal `close_t`: `equity_t = cash + Σ qty_all × close + Σ receivables`. Appends to the
   equity curve (int VND).
Every step writes a `LedgerRow(date, kind, cash_delta, shares_delta, price, note, how)`; the result is **derived from
the ledger** (F-049) so the CSV export and the screen cannot disagree.

### 1.3 Nominal vs adjusted, and A18
The simulator replays **nominal** bars + events; charts/indicators/decomposition use **our adjusted series**
(`adjusted_close`, data.md §1.4). Agreement test (F-046): fractional, fee-free replay total return == adjusted-series
return within 0.05 % over ≥ 3 years for 10 dividend payers. Pre-crawl dates carry `nominal_kind = reconstructed`
(A18-A): the result gets `flags += [reconstructed_nominal]` and "how computed" states the ± 1 tick rounding error.
Reconstruction inverts each `bars_1d_src` row with the factors of ex-dates **≤ the last date of that row's own fetch
version** (`AdjBar.last`), never the newest date across versions: a full-history pull plus short per-press pulls mix
versions, and a global cut-off re-divides pre-pull rows by a factor the source never applied (S05 BE-ca-recompute consult,
tech plan R6a, G13). Until the what-if's `source_adjusted` basis (§1.3.1) reads ours (`adjusted_close`), it is exposed to
the same mix at the window boundary.
Reconciliation (tech plan R7) checks a reconstructed row's 1-VND self-consistency only against the source it was inverted from
(V2); against a cross-check source (S2, 10-VND resolution) it is an ordinary row: `G_v = 1` → exact, else 0.1 % (S05 BE-recon-s2 consult).
**If A18-B**: `what-if` rejects `buy_date < first_observed_date(symbol)` with error `NOMINAL_UNAVAILABLE`; backtests
then run in `price_mode = adjusted` (no lot rounding, fees on adjusted value, no CA events) and show "approximate".

### 1.3.1 S03: `price_basis = source_adjusted` (sprint-03 slice, before F-014/F-015/F-043)
Until nominal `bars_1d` + `corporate_actions` exist, the engine runs on the newest `bars_1d_src` version per
(symbol, trading_date) and `index_1d`. Consequences, all declared on the result (contracts/analytics.md §1.4, §2.4):
lots are bought at adjusted closes (share counts can differ from the real day), no CA step (§1.2 step 2 is skipped), no
dividends, no T+2 bookkeeping needed because the end is a valuation. `approximate = true` on every such result and
`flags ∋ approximate` — a kernel test computes a result from a `bars_1d_src`-shaped fixture and asserts both. Everything
else (§1.2 step 4 lot/fee/tax arithmetic, decision time, flags, Figures) is the final code path; switching to nominal later
changes the `MarketView` adapter and clears the flag, not the arithmetic.
`returns.holding_days` is **display-only**: calendar days from the first fill to the valuation day. It feeds `cagr_pct`
for `lump_sum` only (one cash flow); for `dca` `cagr_pct` is `null` and a future money-weighted return (XIRR, F-047/§1.4)
takes each contribution date from `contributions[].date`, never `holding_days` (S03 review note 3; S04-RW AI-3).

### 1.4 Return breakdown (F-047, PR-033) — an identity, tested to 1 VND
With `A` = amount, `P_N` = fill price, `P_M` = exit price, `Q` = shares bought, `B` = bonus shares received:
| Term | Formula |
|---|---|
| chart return | `A × (P_M − P_N) / P_N` (nominal; what the price chart suggests) |
| lot rounding / residual cash | `(Q × P_N − A) × (P_M − P_N) / P_N` (uninvested cash earns 0) |
| corporate actions | `B × P_M + Σ net cash dividends − Σ rights cash paid` (nominal `P_M` already reflects the drop) |
| buy fee / sell fee / sell tax | ledger sums (negative) |
| timing (fill rule vs close) | `Q × (close_N − P_N) − Q × (close_M − P_M)`, 0 for `close` fills |
| **real return** | `final_cash − A` = sum of the terms (test asserts equality) |
Benchmarks (F-048): same `A`, same dates, VN-Index price-only (fractional units, no fees, labelled "non-investable"),
E1VFVN30 `[assumed, A20]` through the same engine (ETF tick 10 đ, VN§3).

## 2. Backtester (`finvest_analytics.backtest`, R4)
- `Strategy` protocol: `signal(as_of, view, state) -> list[Order]` + `describe() -> {vi, en, params}` (PR-070). v1 library:
  `BuyAndHold`, `DCA(amount, period, day)`, `MACross(fast, slow)`, `Breakout(n)` (close_t > max(high[t−n…t−1])),
  overlays `StopLoss(pct) | TakeProfit(pct) | TrailingStop(pct)` evaluated on `close_t`, exit at next open (or `close`
  when `fill_rule=close`, flagged *optimistic*). Indicators run on **adjusted** closes; fills on nominal bars.
- Default fill `next_open` (PR-071 `[assumed]`; ADR-A-002 explains why `close` is optimistic for rule strategies).
- **Universe** (PR-075): `symbols_as_of(start)` incl. later-delisted; delisting → forced exit + warning.
- **Metrics** (ADR-A-006, `finvest_analytics.metrics`, on the daily equity curve): total return, CAGR
  (`(E/A)^(365/days) − 1`), annualised vol (`std × √250`), max drawdown + duration + time under water, Sharpe
  (`(mean_daily_excess × 250) / vol`, rf default 5 %/y A13, daily rf = `(1+rf)^(1/250) − 1`), Sortino, win rate
  (round trips), exposure (days with position / days), turnover (traded value / mean equity / years), fees + tax paid.
  Statistics in float64 numpy; money stays int; outputs as decimal strings (platform.md §1.2).
- **Walk-forward** (PR-073, ADR-A-003): `rank(scenarios, window=[t−W+1, t])` **always** returns the paired OOS block
  `[t+1, t+W']` plus `k` rolling pairs and Spearman ρ per pair; the response schema makes `oos` required, so a ranking
  without OOS cannot be rendered (G5). Multiple-testing note: with `n` scenarios the best in-sample is expected to beat
  the median by chance; the payload carries `n`, the OOS rank distribution and the fixed sentence (VI/EN).
- **Sensitivity** (PR-074): grid → metric matrix; `fragile_optimum = metric_best − median(neighbours) > 0.5 × (metric_best − median(grid))`.
- **Bootstrap** (PR-076, Could): resample round-trip returns with replacement, 1,000 paths, drawdown distribution.
- Performance: signals vectorised over the whole adjusted series once, then the ledger loop runs only on signal days;
  10 y daily ≈ 2,500 iterations ≪ 2 s (N2); compare 5 × 10 × 5 y = 50 runs, `concurrent.futures` process pool → N3.

## 3. "Why it moved" (`finvest_analytics.explain`, R5, ADR-A-004)
Input: symbol, window `[t0, t1]` (default last 7 sessions), `as_of = t1`. Returns **evidence**, never a cause (PR-093).
- **Decomposition** (PR-090, F-101), on adjusted daily simple returns; estimation window = 250 sessions ending `t0 − 1`
  (min 120, else `insufficient_history`): `β_m` = OLS slope of stock on its venue index (VN-Index / HNX-Index /
  UPCoM-Index); sector series = equal-weight mean of ICB-2 peers' returns excluding the stock; `β_s` = OLS slope of the
  sector on the index. Window returns compounded. Two methods shown side by side:
  - *relative*: market = `R_idx`, sector = `R_sec − R_idx`, idiosyncratic = `R_stock − R_sec`;
  - *beta*: market = `β_m × R_idx`, sector = `R_sec − β_s × R_idx`, idiosyncratic = `R_stock − market − sector`
    (F-101: 1.2 × 4 % = 4.8 %, sector 2.0 %, idio 3.2 %).
  Uncertainty: market term ± `1.96 × SE(β_m) × |R_idx|`; idiosyncratic ± `1.96 × σ_resid × √days`. Both printed.
- **Evidence items** (PR-091, F-102), each `{date, kind, value, baseline, source, as_of}`: volume / 20-session mean
  (flag ≥ 2×); ceiling/floor closes (`close == ceiling|floor` from `bars_1d`); gap `|open − prev_close| ≥ band/2`;
  foreign net value per day + cumulative (`flows_1d`); proprietary flow → item `unavailable` (A17-A; with A17-B it
  reads `flows_1d.prop_net_value` filled by a manual CSV import, same item shape); corporate actions with ex_date in
  `[t0 − 5, t1 + 5]`; earnings proximity = `t1` within 20–45 calendar days after a quarter end (heuristic, labelled);
  index/ETF rebalance dates from a manual calendar table; order-book imbalance from R3 snapshots where present.
- **Event study** (PR-094): abnormal return `r_stock − r_idx` aligned t−5…t+5 over all events of a type for the symbol
  and its sector; mean, standard error, `n`; `n < 10` → "small sample" badge.
- **Digest** (PR-095): top movers, breadth, ceiling/floor counts, foreign net, events — SQL over `bars_1d`/`flows_1d`.
- **Wording**: titles "Các yếu tố đi kèm / Co-occurring factors"; a test rejects the PM's causal-verb list (F-103).
- **LLM**: none in v1 (A4, C5). `explain.to_markdown(result)` exports the evidence for pasting into a Claude Code chat;
  a local-model summariser (Ollama) can be added behind `Summariser` port later without touching the evidence code.

## 4. Honesty rules → tests (each is a kernel test, codebase.md §5)
| Rule | Test |
|---|---|
| No look-ahead | perturb all bars with date > t (×1.3, shuffled) → `signal(as_of=t)` byte-identical (Hypothesis, every strategy) |
| Fill inside the day | property: fill price ∈ [low, high] or no fill, for random bars/rules |
| T+2 | sell order on t+1 of a buy → `SETTLEMENT_PENDING`; on t+2 `close` fill → OK; `next_open` on t+2 → shifts to t+3 open |
| Ledger identity | breakdown terms sum to `final_cash − A` exactly; equity curve last point == final cash after flattening |
| Nominal/adjusted agreement | F-046 on 10 fixture symbols ≤ 0.05 % |
| Walk-forward | schema: `oos` required; `rank()` without an OOS window raises |
| Survivorship | fixture with a 2024 delisting: universe at 2023-01-02 includes it; result has `delisted_exit` |
| Causal wording | regex list over all `explain` strings VI/EN |
| Reproducibility | same `(params, data_snapshot, rules_version)` → identical JSON bytes (F-088, N6) |

## 5. Evals (`finvest_analytics.evals`, fixtures under `tests/fixtures/analytics/`) (ADR-A-005)
- **Golden cases** (F-050, ≥ 20): `golden/sim/NNN-<name>.json` (stdlib, no YAML dep) = inputs + `hand` (list of computation lines) + expected
  ledger and figures; F-040…F-045 are cases 001–008 (10,000,000 → 100 FPT @93,500, cash 635,975; sale 100,000 → 10,610,975;
  dividend 2,000 → 190,000 on pay date; 10:3 bonus → 30 shares, ref 71,923; rights 10:2 @10,000 → exercise 435,975 /
  lapse). Testers keep the independent calculator (spreadsheet) in `docs/golden/`.
- **Synthetic series** with known answers: linear trend + sine → MA cross dates known analytically; step series →
  breakout day known; constant price with one bonus → total return 0 and shares ×1.3.
- **Attribution**: synthetic stock `= 1.2 × index + 0.5 × sector_excess + ε` → recovered β within CI 95 % of runs;
  5 hand-labelled real windows (fixture) whose expected top evidence item (e.g. ex-date, floor streak) must appear.
- Each eval has a `[verify]`-free data path: fixtures only, offline, < 30 s total (part of N10).

## 6. Sponsor-question impact (A16–A18, system.md)
| If the sponsor picks … | Engine impact |
|---|---|
| A16-B (vnstock Community only) | `MarketView` unchanged; daily depth 8 y → backtests cap at 8 y with a notice; 1m 180 d; **no foreign flow** → evidence item `unavailable`; walk-forward windows unaffected |
| A17-B (manual proprietary flow) | add nullable `flows_1d.prop_net_value` + CSV import job; evidence item appears only on dates present, `source = manual` |
| A18-B (no reconstructed nominal) | what-if start ≥ first observed date (`NOMINAL_UNAVAILABLE`); backtests before that date run in `price_mode = adjusted`, flagged approximate; golden cases unchanged |

## Open questions for the sponsor (new; A13–A18 see backlog/system)
- **A19 — Thuế 5 % khi bán cổ phiếu thưởng / cổ tức bằng cổ phiếu.** Luật giữ nguyên tắc "nộp khi bán" (xác minh
  15/10/2026), nhưng cơ sở tính (mệnh giá 10.000 đ hay giá bán) chưa xác minh được trong Nghị định 253/2026.
  **Khuyến nghị A19-A:** mô phỏng khấu trừ 5 % × min(giá bán, 10.000 đ) × số cổ phiếu thưởng bán ra, hiển thị cờ
  "[verify]" trong "cách tính"; A19-B: bỏ qua khoản thuế này trong v1 (kết quả lệch vài phần nghìn, dễ hiểu hơn).
- **A20 — ETF chuẩn so sánh.** PRD giả định E1VFVN30 (VN30, phí thấp, lịch sử từ 2014). **Khuyến nghị A20-A:**
  E1VFVN30; A20-B: FUEVFVND (VNDiamond) hoặc cho chọn trong màn hình (thêm 1 tham số, ~0 chi phí kỹ thuật).
- **A21 — Cổ tức tiền mặt mặc định.** **Khuyến nghị A21-A:** giữ tiền (đúng thực tế: tiền về tài khoản, mua lại cần
  đủ lô 100); A21-B: tái đầu tư tự động vào ngày trả cổ tức (chỉ khi đủ 1 lô).
