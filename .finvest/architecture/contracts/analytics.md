# Finvest — Analytics contracts (Python interface + REST, R2/R4/R5)

Owner: `fi-ai-architect`. Status: **v1, 2026-10-15**. §1–§2 normative for R2 (what-if); §3–§4 shape preview, normative at
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
  "flags": [], "disclaimer": "educational", "result": {…} }
```
Reproducibility: same `params` + `data_snapshot` + `rules_version` ⇒ byte-identical `result` (F-088).

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
