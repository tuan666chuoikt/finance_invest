# Finvest — Analytics contracts (Python interface + REST, R2/R4/R5)

Owner: `fi-ai-architect`. Status: **v1.3, 2026-10-26** (v1.3: §2.3 `shifts[].field` adds `contribution`, as built in S05; v1.2: §2.4 `benchmarks[].first_available` nullable, mirrors platform.md v1.8;
v1.1 = `analytics.prev-2.md`, v1 = `analytics.prev-1.md`). §1–§2 normative for R2 (what-if); §3–§4 shape preview, normative at
R4/R5 planning. Conventions from `contracts/platform.md` §1 apply (integer VND, decimal strings for ratios, ISO times in
Asia/Ho_Chi_Minh, error envelope, `as_of`, `data_snapshot`, `rules_version`). Semantics: `architecture/analytics.md`.

## 1. Common shapes

### 1.1 Figure (every number on an analysis screen, F-051 / PR-110)
```json
{ "value": "610975", "unit": "vnd",
  "how": { "formula": "final_cash - amount", "inputs": {"final_cash": "10610975", "amount": "10000000"},
           "as_of": "2026-10-15T15:30:02+07:00", "rules_version": "2026.10.15", "cite": "VN§5" } }
```
`unit ∈ vnd | pct | ratio | shares | days`. `value` is a decimal string (int for vnd/shares). A test asserts every leaf
figure in a result has `how` (G7). Omitting `how` is a schema error, not a warning.

### 1.2 Ledger row (F-049)
```json
{ "date": "2026-10-12", "kind": "buy", "symbol": "FPT", "qty": 100, "price": 93500, "cash_delta": -9350000,
  "shares_delta": 100, "available_from": "2026-10-14", "note": "fill close_t", "how": {…} }
```
`kind ∈ buy | buy_fee | sell | sell_fee | sell_tax | bonus_tax | shares_arrive | cash_settle | dividend_receivable |
dividend_cash | bonus_pending | bonus_arrive | rights_exercise | rights_lapse | split | delisted_exit | mark`.

### 1.3 Flags (array of lower-case strings on every result)
`reconstructed_nominal` (A18) · `fill_shifted` (F-042) · `no_fill_limit` · `no_liquidity` · `pay_date_assumed` ·
`arrival_assumed` · `delisted_exit` · `optimistic_close_fill` · `insufficient_history` · `small_sample` ·
`prop_flow_unavailable` (A17) · `rules_unverified:<rule_id>` (C7).

### 1.4 Result envelope
```json
{ "params": {…echo of the request…}, "data_snapshot": "2026-10-15T16:45:00+07:00", "rules_version": "2026.10.15",
  "price_basis": "source_adjusted", "approximate": true, "flags": ["approximate"], "disclaimer": "educational", "result": {…} }
```
`price_basis ∈ nominal | source_adjusted`; `approximate == (price_basis != "nominal")` and then `flags` contains
`approximate` (F-040; a test asserts both on every result computed from `bars_1d_src`). `data_snapshot` = max `fetched_at`
of the bars used. Reproducibility: same `params` + `data_snapshot` + `rules_version` ⇒ byte-identical `result` (F-088).

## 2. What-if (R2, normative)

### 2.1 `POST /api/whatif` (F-040…F-049, F-053)
Request:
```json
{ "symbol": "FPT", "amount_vnd": 10000000, "buy_date": "2026-10-12", "sell_date": "2026-10-15",
  "fill_rule": "close", "limit_price": null, "fee_rate": "0.0015", "dividend_mode": "cash",
  "rights_policy": "exercise_if_cash", "lot_mode": "board", "cash_advance": false, "benchmark_etf": "E1VFVN30" }
```
`fill_rule ∈ close | next_open | vwap | limit` (limit needs `limit_price`); `dividend_mode ∈ cash | reinvest`;
`rights_policy ∈ exercise_if_cash | exercise | lapse`; `lot_mode ∈ board | odd_lot_allowed`. `sell_date` default = last
trading day with data. Validation: `amount_vnd ≥ 1`; dates are trading days or shift forward (`fill_shifted`).
Errors: `SYMBOL_UNKNOWN`, `NOT_TRADING_DAY` (only when shifting is impossible: beyond last data), `RANGE_TOO_LARGE`
(> 30 y), `NO_DATA` (symbol has no bar on/after `buy_date`, `details.first_available`), `NOMINAL_UNAVAILABLE` (A18-B only),
`BELOW_ONE_LOT` is **not** an error: result with `shares = 0` and `flags += [below_one_lot]`, `details.min_amount`.
Response `result`:
```json
{ "fills": [{"date":"2026-10-12","side":"buy","rule":"close","price":93500,"qty":100}, …],
  "position": {"shares": 100, "cash": 635975, "market_value": 10000000, "equity": 10635975},
  "returns": {"total_vnd": <Figure>, "total_pct": <Figure>, "cagr_pct": <Figure>, "holding_days": <Figure>},
  "breakdown": {"chart_return": <Figure>, "lot_residual": <Figure>, "corporate_actions": <Figure>,
                "buy_fee": <Figure>, "sell_fee": <Figure>, "sell_tax": <Figure>, "timing": <Figure>, "real_return": <Figure>},
  "risk": {"volatility_pct": <Figure>, "max_drawdown_pct": <Figure>, "max_drawdown_days": <Figure>,
           "sharpe": <Figure>, "time_under_water_pct": <Figure>, "risk_free_pct": "5"},
  "benchmarks": [{"name": "VN-Index", "investable": false, "total_pct": <Figure>}, {"name": "E1VFVN30", "investable": true, "total_pct": <Figure>, "equity": …}],
  "events": [{"type": "cash_dividend", "ex_date": "...", "pay_date": "...", "cash_per_share": 2000, "applied": true}],
  "ledger": [<LedgerRow>…], "equity_curve": [{"date": "2026-10-12", "equity": 9985975}, …] }
```
Invariant tests: `breakdown.real_return == returns.total_vnd == position.equity_at_end − amount_vnd`;
`Σ ledger.cash_delta == cash − amount_vnd`.

### 2.2 `GET /api/whatif/{id}/ledger.csv` — same rows as `ledger`, UTF-8, header row, `;`-free (F-092); `id` from
`POST /api/scenarios` (§4). Without saving: `POST /api/whatif?format=csv` streams the ledger instead of JSON.

### 2.3 Python interface (used by the API and by tests)
```python
def run_whatif(req: WhatIfRequest, view: MarketView, rules: MarketRules) -> WhatIfResult
def simulate(strategy: Strategy, universe: list[str], start: date, end: date, params: SimParams,
             view: MarketView, rules: MarketRules) -> SimResult          # ledger, equity curve, fills, flags
```
Pure functions; no I/O; `view.snapshot()` is copied into the result. `WhatIfRequest`/`SimParams` are Pydantic models
shared with the API schema (`packages/contracts` exports them to TS).

### 2.4 S03 slice (F-040, F-041, F-057, F-048, F-051) — normative; amends §2.1 for `price_basis = source_adjusted`
Request additions: `style ∈ lump_sum | dca` (default `lump_sum`); for `dca`, `amount_vnd` is the **monthly** amount and
`buy_date` the first contribution date (day-of-month rule F-057). `sell_date: null` = latest stored bar (the response
echoes the date used). Only `fill_rule = close` is accepted in S03 (`fill_rule` ≠ close → `VALIDATION`). Errors add
`VALIDATION` (`amount_vnd < 1`, non-integer, `sell_date < buy_date`, `buy_date` after last bar → `details.last_available`).
Semantics on `source_adjusted` bars: no corporate actions, no dividends, fills at the adjusted close, lots/fees/tax as
usual (analytics.md §1.3.1). The end is a **valuation**, not a trade: no T+2 refusal, no sell fill row.
```json
"result": {
  "dates": {"buy": "2026-10-19", "sell": "2026-10-23",
            "shifts": [{"field": "buy_date", "from": "2026-10-17", "to": "2026-10-19", "reason": "non_trading"}]},
  "contributions": [{"date": "2026-01-15", "requested": "2026-01-15", "amount_vnd": 2000000, "qty": 0, "price": 93500,
                     "fee_vnd": 0, "cash_after": 2000000}],
  "position": {"shares": <Figure shares>, "cash": <Figure vnd>, "invested_vnd": <Figure vnd>},
  "value": {"market_value_vnd": <Figure>, "sell_fee_vnd": <Figure>, "sell_tax_vnd": <Figure>, "liquidation_vnd": <Figure>},
  "returns": {"pl_vnd": <Figure>, "pl_pct": <Figure>, "cagr_pct": <Figure|null>, "holding_days": <Figure days>},
  "benchmarks": [
    {"name": "VN-Index", "investable": false, "available": true, "value_vnd": <Figure>, "pl_pct": <Figure>, "diff_pp": <Figure>},
    {"name": "E1VFVN30", "investable": true, "available": false, "first_available": "2014-10-06"}],
  "missing_sessions": ["2026-03-04"],
  "equity_curve": [{"date": "2026-10-19", "market_value": 9985975, "invested": 10000000}, …] }
```
- `dates.shifts[]`: `field ∈ buy_date | sell_date | contribution` (`contribution` = a DCA instalment moved from its
  requested day, `reason ∈ non_trading | no_bar | after_end`; `after_end` = instalment dropped, `to` null when no trading day follows; F-057).
- `contributions`: one row per fill day (lump sum = 1 row). `qty = floor(cash / (price × lot × (1 + fee_rate))) × lot`,
  `fee_vnd = round_half_up(qty × price × fee_rate)`, `cash_after = cash − qty × price − fee_vnd` (carried into the next
  contribution for `dca`). `qty = 0` ⇒ `flags += [below_one_lot]`, `details.min_amount = lot × price × (1 + fee_rate)`
  rounded up (F-040: 9,364,025 at 93,500).
- `value`: `market_value = shares × close(sell)`; `sell_fee = round_half_up(market_value × fee_rate)`; `sell_tax =
  round_half_up(market_value × 0.1 %)`; `liquidation = cash + market_value − sell_fee − sell_tax` (F-041, VN§5).
- `returns`: `pl_vnd = liquidation − invested_vnd`; `pl_pct = pl_vnd / invested_vnd × 100` (DCA: ÷ total contributed, F-057);
  `cagr_pct = ((liquidation / invested) ^ (365 / holding_days) − 1) × 100` for `lump_sum` with `holding_days ≥ 1`
  (calendar days buy→sell), else `null` with the `how` on `returns.cagr_note` stating why. Percent Figures are decimal
  strings with 4 decimals, ROUND_HALF_UP ("6.1098" for 610,975 / 10,000,000).
- `benchmarks` (F-048): VN-Index = `Σ amount_i × index(sell) / index(date_i)` over contributions (price-only, no lots, no
  fees, `index_1d.c` 2 decimals, result rounded half-up to VND); E1VFVN30 = the same request on symbol `E1VFVN30` through
  this engine. `diff_pp = scenario.pl_pct − benchmark.pl_pct`. A benchmark lacking a bar on any contribution date or on
  `sell` ⇒ `available: false, first_available: string | null` (never a zero) — **null when the benchmark has no bars at all**
  (live: VNINDEX empty before the first index crawl, 4-test.fe U1; platform.md v1.8 §2.5); the web renders "n/a" without a
  date. The benchmark list is fixed in S03 (`benchmark_etf` ignored).
- `missing_sessions`: calendar trading days in `[buy, sell]` without a bar; the curve carries the last close forward;
  `flags += [missing_sessions]` when non-empty.
- `equity_curve`: every trading day in `[buy, sell]`, `market_value = cash + shares × close` (no sell costs), `invested` =
  cumulative contributions (step line, UX scenario-dashboard.md "Mini curve").
- `how.cite` on cost figures is `VN§5`, on lots `VN§4`; `how.inputs` names every number in the formula (UX "How computed
  panel" example). Approximate texts are FE i18n keys (`approximate.source_adjusted`), the engine sends the flag only.
- Deferred to R2 full (unchanged in §2.1): `fills`, `breakdown`, `risk`, `events`, `ledger`, other fill rules, dividends.

## 3. Backtester (R4, preview)
- `POST /api/backtest/compare` `{scenarios: [{strategy, params, fill_rule}], symbols: [...], start, end, fee_rate, rf_pct}`
  → `rows: [{scenario, symbol, metrics: {total_pct, cagr_pct, max_drawdown_pct, sharpe, sortino, trades, fees_tax_vnd,
  win_rate_pct, exposure_pct, turnover}: Figure…}]`, `curves: [{scenario, symbol, points: [...]}]`, `benchmark_row`.
  Limits: `len(scenarios) × len(symbols) ≤ 100` else `RANGE_TOO_LARGE`.
- `POST /api/backtest/walk-forward` `{…compare request…, window_sessions: 7, oos_sessions: 7, rolling: 12, metric: "total_pct"}`
  → `{in_sample: [...ranked rows...], oos: [...same rows, OOS window...], pairs: [{is_window, oos_window, spearman}],
  n_scenarios, statement: {vi, en}}`. **`oos` and `pairs` are required** in the response schema (G5).
- `POST /api/backtest/sensitivity` `{strategy, symbol, start, end, grid: {fast: [5,10,20], slow: [50,100,200]}, metric}`
  → `{cells: [{params, metric: Figure}], fragile_optima: [{params, reason}]}`.
- Strategy ids: `buy_and_hold | dca | ma_cross | breakout`; overlays `stop_loss | take_profit | trailing_stop` as
  `overlays: [{type, pct}]`. `GET /api/backtest/strategies` returns `describe()` for each (VI/EN rule text, params schema).

## 4. Scenario journal (R4, preview) — the only write endpoints besides `POST /api/jobs`
`POST /api/scenarios {kind: whatif|compare|walk_forward, request, note}` → `{id, data_snapshot, rules_version}`;
`GET /api/scenarios?limit&cursor`; `GET /api/scenarios/{id}` → saved request + stored result; `POST /api/scenarios/{id}/rerun`
→ recomputes with the **saved** `data_snapshot` and asserts byte equality (`reproducible: true|false`, diff path on false).

## 5. Why it moved (R5, preview)
- `GET /api/explain/{symbol}?from=2026-10-06&to=2026-10-15&method=beta|relative` →
  `{window, stock_return_pct, decomposition: {market, sector, idiosyncratic}: {value: Figure, ci_low, ci_high},
  estimation: {window_start, window_end, sessions, beta_m, beta_m_se, beta_s, index_code, sector_code, peers_n},
  evidence: [{date, kind, value, baseline, unit, source, as_of}], title: {vi: "Các yếu tố đi kèm", en: "Co-occurring factors"}}`.
  `kind ∈ volume_ratio | ceiling_close | floor_close | gap | foreign_net | prop_net | corporate_action | earnings_window |
  rebalance | orderbook_imbalance`. Missing data → the item is present with `value: null` and a flag, never dropped silently.
- `GET /api/explain/event-study?symbol=FPT&event=cash_dividend` → `{points: [{offset: -5…5, mean_pct, se_pct}], n, sector: {…}}`.
- `GET /api/digest/{date}` → `{movers_up, movers_down, breadth: {up, down, flat}, ceiling_count, floor_count,
  foreign_net_value, events: [...]}`, every figure a `Figure`.

## 6. Compatibility rules
Adding a field or flag is non-breaking; renaming/removing one, changing a default (`fill_rule`, `fee_rate`,
`dividend_mode`) or a formula bumps `rules_version`/`X-Finvest-Api` and this file; saved scenarios keep the version they
were computed with and `rerun` reports a version mismatch instead of silently recomputing.
