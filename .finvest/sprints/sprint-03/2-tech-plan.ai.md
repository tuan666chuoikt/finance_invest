# Sprint 03 — Tech plan (AI side: what-if engine, `services/analytics`)

Owner: `fi-ai-architect`, 2026-10-18, plan v1.2 (v1.1 = lumpsum size; v1.2 = DCA actual + benchmarks re-estimate). Inputs: `1-sprint-plan.md` (M1 F-006; M2 F-040/F-041/F-057; M4 F-048/F-051),
`product/backlog.md` (S03 slice), `product/ux/scenario-dashboard.md`, `architecture/analytics.md` v1.1 (§1.2 step 4, §1.3.1,
§5), `contracts/analytics.md` v1.1 (§1.1 Figure, §1.4 envelope, §2.3, **§2.4 normative for S03**), `knowledge/vn-market.md`
VN§4–§5, sprint-02 `2-tech-plan.md` BE-bars-store / BE-bars-backfill, `data.md` §1.2 V2, §3. The software architect merges
these blocks into `dag.json` and adds the FE/API tasks.

## Decisions for this sprint

- **Contract amended now** (`contracts/analytics.md` v1.1, `analytics.prev-1.md` archived): envelope carries `price_basis`
  + `approximate`; §2.4 defines `style = lump_sum | dca`, valuation (`value.liquidation_vnd`), `returns`, `benchmarks`,
  `contributions`, `missing_sessions`, `equity_curve`. `architecture/analytics.md` v1.1 §1.3.1 states the source-adjusted
  mode. The full R2 shapes (§2.1 fills/breakdown/ledger/risk) are untouched and come in later sprints.
- **The engine is pure and fixture-driven.** `finvest_analytics` never touches SQLAlchemy; it receives a `MarketView`
  (analytics.md §1.1, reduced to `calendar`, `bars_1d`, `index_1d`, `snapshot`, `first_bar_date`). The SQL adapter over
  `bars_1d_src` (newest `fetched_at` per symbol/date) and `index_1d` is a **BE task for the software architect** (note N1).
  Therefore no AI task has an `after` on sprint-02 bar tasks; only the API/SQL task does.
- **Approximate flag is test-enforced** (analytics.md §1.3.1): every result built from a `bars_1d_src`-shaped view has
  `price_basis == "source_adjusted"`, `approximate is True`, `"approximate" in flags`; the `how`-walker test asserts every
  Figure has `how` (G7, contracts §1.1).
- **Golden cases are JSON** (`tests/golden/sim/NNN-<name>.json`, stdlib — analytics.md §5), each with a `hand` list of the
  computation lines quoted in this plan, so the tester's spreadsheet (`docs/golden/`) can be checked line by line.
- **Money arithmetic**: integer VND, `Decimal` for rates, `round_half_up` (ADR-S-005). Lot rule `qty = floor(cash /
  (price × lot × (1 + fee_rate))) × lot` is loop-free and never overspends: `qty×price + round_half_up(qty×price×fee) ≤ cash`
  because the exact total ≤ cash and rounding adds < 0.5 to an integer comparison — a Hypothesis property test proves it.
- **Fixture calendar = weekdays** in the fixture views (no holidays) so golden dates are deterministic; production uses
  `finvest_rules.calendar.trading_days` (F-003). Golden cases use illustrative prices (backlog convention), not market data.
- **Effort/lead**: every block below is money math → `Effort: high`, `Lead: opus` (owner.md), except the scaffold.
- **Sizes** count prod + test (+ fixture JSON lines) (retro R3). Total AI side ≈ 900 lines over 5 tasks.

Order (file sets overlap in `services/analytics/**` → serial): BE-rules-costs ∥ AI-analytics-scaffold → AI-whatif-lumpsum
→ AI-whatif-dca → AI-whatif-benchmarks. M2 = lumpsum + dca merged; M4 = benchmarks merged + API/FE.

## Tasks

#### BE-rules-costs — F-006: trading-cost rules v1 with `effective_from`, `verified`, `RULES_VERSION`
- Story: F-006 ; Side: be ; Effort: high ; Size: ~90 lines ; Lead: opus
- Files: `packages/market_rules/finvest_rules/costs.py`, `packages/market_rules/finvest_rules/__init__.py` (export),
  `packages/market_rules/tests/test_costs.py`
- Change:
  - `Rule(value: Decimal | int, effective_from: date, verified: bool, verified_on: date | None, source: str, cite: str)`
    frozen dataclass; `RULES: dict[str, list[Rule]]` with exactly one v1 entry each: `buy_fee_rate 0.0015` (sponsor A6,
    `verified=False`, cite VN§5), `sell_fee_rate 0.0015` (A6), `sell_tax_rate 0.001` (verified 2026-10-15, Law 109/2025 +
    Decree 253/2026, VN§5), `board_lot 100` (verified S1/S2 2026-10-15, VN§4), `settlement_days 2` (verified S3, VN§5).
    `effective_from = 2006-01-01` for all five (earliest daily bar, data.md §1.2 V2 2006-12-13) — the date we *apply* the
    rule from, not when the law started; stated in a docstring.
  - `rule(name, on: date) -> Rule`: the entry with the latest `effective_from <= on`; none → `RuleNotEffective(name, on)`.
    Convenience `costs(on) -> Costs(buy_fee_rate, sell_fee_rate, sell_tax_rate, lot, settlement_days)`.
  - `RULES_VERSION = "2026.10.16"`; a test asserts it equals `max(r.effective_from … , verified_on …)`-based bump discipline:
    changing any rule value requires bumping it (test compares a hash of `RULES` with a stored constant; message tells the
    developer to bump `RULES_VERSION`).
- Contract: contracts/analytics.md §1.1 (`rules_version`, `cite`), §1.4; vn-market.md VN§4, VN§5; ADR-S-005.
- Acceptance:
  - `costs(date(2026,10,12))` → `0.0015 / 0.0015 / 0.001 / 100 / 2`; `rule("sell_tax_rate", …).verified is True`,
    `rule("buy_fee_rate", …).verified is False`.
  - Appending `Rule(Decimal("0.0020"), date(2027,1,1), …)` to `buy_fee_rate` (test-local copy): `rule(…, date(2026,12,31))`
    → 0.0015, `rule(…, date(2027,1,1))` → 0.0020 (F-006 criterion 2). `rule("board_lot", date(2005,1,1))` → `RuleNotEffective`.
  - Changing a rule value without bumping `RULES_VERSION` fails the hash test.
- Out of scope: price bands/ticks (F-001), odd-lot mode, bonus-share tax (A19), cash-dividend tax (F-043), rules CLI generation.

#### AI-analytics-scaffold — `services/analytics` package: domain types, ports, fixture view, money helpers
- Story: F-040 ; Side: ai ; Effort: medium ; Size: ~190 lines ; Lead: sonnet
- Files: `services/analytics/pyproject.toml`, `services/analytics/finvest_analytics/__init__.py`,
  `services/analytics/finvest_analytics/domain/__init__.py`, `…/domain/models.py`, `…/domain/ports.py`, `…/domain/money.py`,
  `services/analytics/finvest_analytics/fixtures.py`, `services/analytics/tests/test_money.py`,
  `services/analytics/tests/conftest.py`, `pyproject.toml` (root: workspace member `services/analytics`, `finvest-analytics`
  dependency + source, importlinter `root_packages` + contract "finvest_analytics imports no finvest_crawler/finvest_api")
- Change:
  - `models.py` (frozen dataclasses, Pydantic only for the request): `DailyBar(symbol, trading_date, o, h, l, c: int, v: int,
    price_basis: str, fetched_at: datetime)`, `IndexBar(index_code, trading_date, c: Decimal)`, `Figure(value: str, unit,
    how: How)`, `How(formula, inputs: dict[str, str], as_of: str, rules_version, cite: str | None)`, `WhatIfRequest`
    (Pydantic: `symbol, amount_vnd: int ≥ 1, buy_date, sell_date: date | None, style: Literal["lump_sum","dca"] = "lump_sum",
    fill_rule: Literal["close"] = "close", fee_rate: Decimal | None`). `figure(value, unit, formula, inputs, ctx, cite=None)`
    helper formats ints as str and `Decimal` pct with 4 dp `ROUND_HALF_UP`.
  - `ports.py`: `MarketView(Protocol)` with `calendar(start, end) -> list[date]`, `bars_1d(symbol, start, end, *, as_of) ->
    list[DailyBar]` (rows with `trading_date <= as_of` only), `first_bar_date(symbol) -> date | None`, `index_1d(code, start,
    end, *, as_of) -> list[IndexBar]`, `snapshot() -> datetime`, `price_basis() -> str`.
  - `fixtures.py`: `FixtureView(bars: dict[str, list[DailyBar]], index: dict[str, list[IndexBar]], snapshot, price_basis=
    "source_adjusted")`; calendar = weekdays; `bars_1d` enforces `as_of` (a bar after `as_of` is never returned — this is
    the look-ahead guard the tests rely on). Helper `constant_series(symbol, start, end, close, *, last_close=None)`.
  - `money.py`: `round_half_up(Decimal) -> int`, `fee(qty, price, rate) -> int`, `max_qty(cash, price, lot, rate) -> int`
    (the floor formula), `lot_cost_min(price, lot, rate) -> int` (= `ceil(price × lot × (1 + rate))`, the F-040 "below one
    lot" amount), `pct(num, den) -> Decimal` (4 dp half-up, `den == 0` → raises).
  - Errors: `AnalyticsError(code, details)` with codes `SYMBOL_UNKNOWN | NO_DATA | VALIDATION | RANGE_TOO_LARGE`.
- Contract: contracts/analytics.md §1.1 Figure, §1.4 envelope fields, §2.3 purity, §2.4 lot/fee formulas; analytics.md §1.1
  ports, §1.3.1; codebase.md §2 (`finvest_analytics` never imports `finvest_crawler`), §4 (int VND); ADR-S-005.
- Acceptance:
  - `max_qty(10_000_000, 93_500, 100, Decimal("0.0015")) == 100`, `fee(100, 93_500, 0.0015) == 14_025`, `lot_cost_min(93_500,
    100, 0.0015) == 9_364_025`; `max_qty(5_000_000, 93_500, …) == 0`; `round_half_up(Decimal("2.5")) == 3`, `("2.4") == 2`.
  - Hypothesis property (cash 1…10^11, price 100…10^7 step 10, rate 0…0.0045): `q = max_qty(…)`; `q % lot == 0`;
    `q×price + fee(q, price, rate) ≤ cash`; `(q + lot)×price + fee(q + lot, …) > cash`.
  - `FixtureView.bars_1d(…, as_of=t)` never returns a bar dated after `t` (property over random ranges).
  - `uv run import-linter` passes with the new contract; `make test-kernel` collects `services/analytics/tests`.
- Out of scope: any simulation logic, SQL adapter (N1), TS export of the Pydantic models (`packages/contracts`, later).

#### AI-whatif-lumpsum — F-040 + F-041: lump-sum buy at close of N, valuation at M, P/L, CAGR, Figures, approximate flag
- Story: F-040 ; Side: ai ; Effort: high ; Size: ~600 lines (planned ~250; actual +613 accepted in 3-consult answer: ~350 code incl. mandatory Figure `how`, ~260 tests + golden JSON) ; Lead: opus
- Files: `services/analytics/finvest_analytics/sim/__init__.py`, `services/analytics/finvest_analytics/sim/whatif.py`,
  `services/analytics/finvest_analytics/sim/dates.py`, `services/analytics/finvest_analytics/sim/figures.py`,
  `services/analytics/tests/test_whatif_lumpsum.py`, `services/analytics/tests/golden/sim/001-lump-sum-fpt.json`,
  `…/002-below-one-lot.json`, `…/003-date-shift.json`, `…/004-cagr-730-days.json`, `services/analytics/tests/test_golden.py`
  (generic runner: load JSON → `run_whatif` → compare `expected` leaf values; shared by the next two tasks)
- Change:
  - `dates.py`: `shift_forward(d, calendar)` (buy / contribution: next trading day, F-040), `shift_back(d, calendar)`
    (sell: previous trading day, F-041), `resolve_sell(sell_date | None, view)` → latest bar ≤ sell (or last bar); each
    shift appends `{"field", "from", "to", "reason": "non_trading"}` to `dates.shifts` and `flags += [fill_shifted]`.
  - `whatif.py` `run_whatif(req, view, rules=finvest_rules.costs) -> dict` (the §1.4 envelope as a plain dict, JSON-ready):
    validate (`VALIDATION`: sell < buy, `fill_rule != close`; `NO_DATA` with `details.first_available` when `buy <
    first_bar_date`; `VALIDATION` with `details.last_available` when `buy >` last bar; `SYMBOL_UNKNOWN` when no bars at all);
    buy at `close(N)` with `as_of = N`: `qty = max_qty(amount, close, lot, buy_fee_rate)`, `fee`, `cash`; `qty == 0` →
    `flags += [below_one_lot]`, `details.min_amount`; one `contributions` row (contracts §2.4).
  - Valuation at M (contracts §2.4 `value`): `market_value = qty × close(M)`, `sell_fee`, `sell_tax`, `liquidation`;
    `returns`: `pl_vnd`, `pl_pct = pct(pl, invested)`, `holding_days = (M − N).days`, `cagr_pct` (Decimal `ln/exp` or float
    pow then 4 dp — tolerance in tests) or `null` + `cagr_note` when `holding_days == 0`.
  - `equity_curve`: every trading day in `[N, M]` (contract §2.4; the earlier "calendar day" wording was wrong), `market_value = cash + qty × close` (carry last close forward when the
    day has no bar → `missing_sessions`, `flags += [missing_sessions]`), `invested = amount`.
  - `figures.py`: builds every Figure with `how` (`formula`, `inputs`, `as_of = snapshot`, `rules_version`, `cite`); envelope
    `price_basis = view.price_basis()`, `approximate = price_basis != "nominal"`, `flags` sorted + deduplicated,
    `data_snapshot`, `params` = request echo, `benchmarks: []` (filled by AI-whatif-benchmarks), `disclaimer: "educational"`.
  - `test_golden.py`: walks `expected` paths (`position.shares.value`, `value.liquidation_vnd.value`, …) and compares as
    strings; tolerance key `"approx": {"returns.cagr_pct.value": "0.0001"}`.
- Contract: contracts/analytics.md §1.1, §1.4, §2.1 errors, **§2.4** (all bullets except `benchmarks`); analytics.md §1.2
  steps 3–5, §1.3.1, §4 rows "No look-ahead", "Reproducibility"; VN§4 lot, VN§5 fee/tax; backlog F-040, F-041.
- Acceptance (hand computations, also the `hand` lines in the JSON):
  - **001**: 10,000,000 VND, FPT, N = 2026-10-12 close 93,500, M = 2026-10-15 close 100,000 (constant 93,500 until M).
    `lot cost = 100 × 93,500 × 1.0015 = 9,364,025 → qty = floor(10,000,000 / 9,364,025) = 1 lot = 100`;
    `fee = 100 × 93,500 × 0.0015 = 14,025`; `cash = 10,000,000 − 9,350,000 − 14,025 = 635,975`;
    `market_value = 100 × 100,000 = 10,000,000`; `sell_fee = 15,000`; `sell_tax = 10,000`;
    `liquidation = 635,975 + 10,000,000 − 15,000 − 10,000 = 10,610,975`; `pl = 610,975`; `pl_pct = 6.1098`;
    `holding_days = 3`; `equity_curve[0].market_value = 635,975 + 9,350,000 = 9,985,975`; envelope `approximate: true`,
    `"approximate" in flags`, `price_basis == "source_adjusted"`.
  - **002**: 5,000,000 at 93,500 → `shares 0`, `cash 5,000,000`, `liquidation 5,000,000`, `pl 0`, `pl_pct 0.0000`, flags
    contain `below_one_lot`, `details.min_amount == 9,364,025`.
  - **003**: buy Sat 2026-10-17 → `dates.buy == 2026-10-19`, shift row `buy_date 2026-10-17 → 2026-10-19`; sell Sun
    2026-10-25 → `dates.sell == 2026-10-23`; `holding_days == 4`; `fill_shifted` in flags. Buy before the first bar →
    `NO_DATA` with `first_available`; sell `None` → `dates.sell` = last fixture bar.
  - **004**: case 001 prices but M = N + 730 days: `cagr = (1.0610975)^(365/730) − 1 = 3.0096 %` (± 0.0001); M = N + 365
    days → `cagr_pct == pl_pct`; M = N → `cagr_pct is None`, `cagr_note.how` present.
  - No look-ahead: perturb every bar with `trading_date > N` (× 1.3) → identical `contributions`, `position.shares`,
    `position.cash` (backlog F-040 criterion 1). Reproducibility: two runs → identical `json.dumps(sort_keys=True)` bytes.
  - `how` walker: every dict with keys `value` + `unit` in the result has a non-empty `how.formula` and `how.inputs` (G7);
    `how.cite == "VN§5"` on `sell_fee_vnd`/`sell_tax_vnd`/`contributions[].fee_vnd` figures, `"VN§4"` on `position.shares`.
  - Gap: remove the 2026-10-14 bar from the fixture → `missing_sessions == ["2026-10-14"]`, curve for that day carries
    93,500, flag `missing_sessions`.
- Out of scope: DCA (`style = dca` → `VALIDATION` until AI-whatif-dca), benchmarks, other fill rules (F-042), T+2 refusal
  (F-053), ledger/CSV (F-049), breakdown (F-047), risk metrics (F-090), SQL view (N1), API route (N2).

#### AI-whatif-dca — F-057: monthly contributions on the start day-of-month, whole lots, carried cash
- Story: F-057 ; Side: ai ; Effort: high ; Size: ~410 lines (planned ~200 + ~15 D4; actual +410 accepted in 3-consult answer: ~175 code incl. schedule + Figure `how`, ~235 tests + 5 golden JSON) ; Lead: opus
- Files: `services/analytics/finvest_analytics/sim/dca.py`, `services/analytics/finvest_analytics/sim/whatif.py` (dispatch
  on `style`, shared valuation), `services/analytics/tests/test_whatif_dca.py`, `services/analytics/tests/golden/sim/005-dca-fpt.json`,
  `…/006-dca-day-31.json`, `…/007-dca-carried-cash.json`
- Change:
  - `dca.py` `schedule(start, end, calendar) -> list[tuple[requested, actual]]`: contribution day = `start.day`; for each
    month from `start` to `end`: `min(day, days_in_month)` (day 31 in a 30-day month → last day), shift forward to a trading
    day; drop a contribution whose shifted date `> end` (note in `dates.shifts` with `reason: "after_end"`); each actual
    shift ≠ requested appends a shift row (`field: "contribution"`).
  - Loop per contribution date `t` (decision time = close of `t`, `as_of = t`): `cash += amount`; `qty = max_qty(cash, close_t,
    lot, buy_fee)`; `fee`; `cash −= qty × close + fee`; `shares += qty`; append `contributions` row with `cash_after`.
  - `invested_vnd = Σ amount` over actual contributions; valuation and `returns` reuse the lump-sum code; `pl_pct = pl /
    invested` (UX "P/L % formula for DCA"); `cagr_pct = null` with `cagr_note` "not defined for multiple contributions
    (S03: no IRR)"; `equity_curve[].invested` = cumulative contributions up to that day (step line).
  - `dates.buy` = first actual contribution; `holding_days` from it.
  - D4 follow-up from AI-whatif-lumpsum: emit `flags += [rules_unverified:<rule_id>]` (contracts §1.3, C7) for every
    `finvest_rules.Rule` with `verified == false` used by `costs()`; applies to lump-sum and DCA paths (shared valuation code).
- Contract: contracts/analytics.md §2.4 (`contributions`, `returns.pl_pct` DCA rule, `cagr_pct null`, `equity_curve.invested`);
  analytics.md §1.2 step 3 (decision time), §1.3.1; backlog F-057; UX scenario-dashboard.md "DCA card line", "Mini curve".
- Acceptance:
  - **005** (F-057 example): 2,000,000 monthly from 2026-01-15, constant close 93,500, end 2026-06-30 close 100,000.
    Contributions 15/01, 16/02 (Sun 15/02 → Mon), 16/03 (Sun → Mon), 15/04, 15/05, 15/06 (weekday calendar).
    `cash after months 1–4 = 2,000,000 / 4,000,000 / 6,000,000 / 8,000,000, qty 0 each (< 9,364,025)`;
    `month 5: cash 10,000,000 → qty 100, fee 14,025, cash 635,975`; `month 6: cash 2,635,975 → qty 0`.
    `invested = 12,000,000`; `shares 100`; `market_value 10,000,000`; `sell_fee 15,000`; `sell_tax 10,000`;
    `liquidation = 2,635,975 + 10,000,000 − 25,000 = 12,610,975`; `pl = 610,975`; `pl_pct = 610,975 / 12,000,000 = 5.0915`;
    `cagr_pct is None`. (End 2026-05-29 instead → 5 contributions, invested 10,000,000, liquidation 10,610,975, pl_pct 6.1098
    — the backlog's number; both variants in the file.)
  - **006**: start Sat 2026-01-31 → first contribution Mon 2026-02-02 (shift row); Feb → day 28 Sat → Mon 2026-03-02;
    Mar → Tue 2026-03-31; Apr → Thu 2026-04-30; end Sat 2026-05-30 → `dates.sell` Fri 2026-05-29; May 31 (Sun) → Jun 1 > end
    → dropped (`after_end`). Exactly 4 contributions, `invested = 4 × amount`.
  - **007** (carried cash, varying price): 2,000,000 monthly, closes 10,000 (month 1), 12,000 (month 2), end close 11,000.
    `m1: lot cost 1,001,500 → qty 100, fee 1,500, cash 998,500`; `m2: cash 2,998,500, lot cost 1,201,800 → qty 200, fee 3,600,
    cash 594,900`; `shares 300`; `market_value 3,300,000`; `sell_fee 4,950`; `sell_tax 3,300`;
    `liquidation = 594,900 + 3,300,000 − 8,250 = 3,886,650`; `pl = −113,350`; `pl_pct = −2.8338`.
  - No look-ahead per contribution: perturb bars after each `t_i` → identical `contributions[i]`. `equity_curve.invested`
    steps on contribution dates only. Reproducibility bytes identical.
- Out of scope: contribution periods other than monthly, IRR/money-weighted return, DCA with dividends, backtester
  `DCA` strategy wrapper (F-081, reuses `schedule`).

#### AI-whatif-benchmarks — F-048: VN-Index price-only and E1VFVN30 through the engine, pp difference, n/a handling
- Story: F-048 ; Side: ai ; Effort: high ; Size: ~340 lines (re-estimated after the lumpsum/DCA size stops: ~140 code incl. Figure `how`, ~200 tests + 3 golden JSON; 1.5x stop = 510) ; Lead: opus
- Files: `services/analytics/finvest_analytics/sim/benchmark.py`, `services/analytics/finvest_analytics/sim/whatif.py`
  (fill `benchmarks`), `services/analytics/tests/test_benchmarks.py`, `services/analytics/tests/golden/sim/008-vnindex-lump.json`,
  `…/009-vnindex-dca.json`, `…/010-etf-engine-and-na.json`
- Change:
  - `vnindex(contributions, sell_date, view)`: `value = round_half_up(Σ amount_i × idx(sell) / idx(date_i))` with `idx` =
    `index_1d("VNINDEX").c` (Decimal, 2 dp); `pl_pct = pct(value − invested, invested)`; `diff_pp = scenario.pl_pct −
    pl_pct` (4 dp); `investable: false`. Missing index bar on any `date_i` or on `sell` → `available: false,
    first_available` = first index bar date.
  - `etf(req, view)`: re-run `run_whatif` with `symbol = "E1VFVN30"`, same style/amount/dates, `benchmarks` disabled
    (no recursion); copy `value.liquidation_vnd` → `value_vnd`, `returns.pl_pct`, `diff_pp`; `investable: true`. `NO_DATA` /
    no bar on a contribution date / on `sell` → `available: false, first_available` (never a zero; backlog F-048 criterion 4).
    Shifts inside the ETF run are not surfaced (its dates are the scenario's).
  - Figures carry `how` (formula with the index levels / the ETF liquidation inputs, `cite: "PR-034"`, `investable`).
- Contract: contracts/analytics.md §2.4 `benchmarks` bullet; analytics.md §1.4 "Benchmarks (F-048)"; data.md §1.2 V2
  (`VNINDEX` since 2004-01-05, points) and §3 `index_1d` (NUMERIC(12,2)); sponsor A20-A; backlog F-048.
- Acceptance:
  - **008**: case 001 scenario (`pl_pct 6.1098`), index 1,200.00 on N and 1,260.00 on M → `value_vnd 10,500,000`,
    `pl_pct 5.0000`, `diff_pp 1.1098` (backlog: "+1,11 điểm %").
  - **009**: case 007 scenario (`pl_pct −2.8338`), index 1,000.00 (m1), 1,250.00 (m2), 1,100.00 (sell):
    `value = 2,000,000 × 1.1 + 2,000,000 × 0.88 = 2,200,000 + 1,760,000 = 3,960,000`; `pl_pct −1.0000`; `diff_pp −1.8338`.
  - **010**: case 001 scenario; E1VFVN30 close 20,000 on N, 21,000 on M: `lot cost 2,003,000 → qty 400, fee 12,000, cash
    1,988,000`; `market_value 8,400,000, sell_fee 12,600, sell_tax 8,400`; `liquidation 10,367,000`; `pl_pct 3.6700`;
    `diff_pp 2.4398`; `investable: true`. Same case with the ETF series starting after N → `available: false`,
    `first_available` = that first date, no `value_vnd` key; VN-Index with no index bars → `available: false`.
  - Index decimals: idx 1,234.56 → 1,234.57 moves the value by the exact ratio (no float drift; Decimal end to end).
  - The ETF run's `approximate` flag does not leak into the scenario flags twice (flags stay deduplicated); `how` walker
    passes on the benchmark Figures; reproducibility bytes identical.
- Out of scope: configurable `benchmark_etf` (A20-B), benchmark equity curves on the card, FUEVFVND, HNX/UPCoM indices.

## Notes for the software architect (BE/FE/API tasks, dag.json)

- **N1 `SqlMarketView`** (BE, suggested `packages/market_data/finvest_market_data/infrastructure/analytics_view.py`,
  ~120 lines, `after: BE-bars-store, BE-bars-backfill` of sprint-02 — both merged on the `sprint-02` head, so in dag.json
  they are satisfied by `base`): `bars_1d(symbol, start, end, as_of)` = newest `fetched_at` per `(symbol, trading_date)` from
  `bars_1d_src` (`DISTINCT ON … ORDER BY fetched_at DESC`), `adj_c` → `c`, `price_basis = "source_adjusted"`;
  `index_1d` from `index_1d`; `calendar` = `finvest_rules.calendar.trading_days`; `snapshot()` = max `fetched_at` of the
  rows served (contracts §1.4); `first_bar_date` = min `trading_date`. Live-source assumptions it rests on are cited in
  BE-bars-store (fixture `vci/gap_chart/FPT-1d`: integer VND after half-up rounding; data.md §1.2 V2 indices).
- **N2 `POST /api/whatif`** (BE, `apps/api`, `after: AI-whatif-lumpsum, N1`): Pydantic `WhatIfRequest` from
  `finvest_analytics.domain.models`; `AnalyticsError` → platform.md §1 error envelope; `sell_date: null` = today. F-055
  saved scenarios recompute by calling `run_whatif` per row (20 × 10 y pure-Python loops ≈ 2,500 iterations each, well
  under 2 s; measure in the API test).
- **N3 E1VFVN30 coverage is uncited** (retro R3): `vci/symbols_getAll/sample` has no `E1VFVN30` row and data.md §1.2 V2
  does not mention ETFs. Suggested spike `S-etf-bars` (BE, ~30 lines: one recorded V2 payload for `E1VFVN30` + a check that
  V3 `getAll` lists it with its `type`). The engine does not block on it — a missing ETF renders "n/a — data from …" by
  contract — but F-048's investable half of the acceptance depends on the back-fill including the ETF.
- **N4 FE**: `approximate` text is the i18n key `approximate.source_adjusted` (contracts §2.4); `pl_pct` arrives with 4
  decimals and the FE formats `6,11 %`; `diff_pp` → "+1,11 điểm % / pp"; `benchmarks[].available == false` → n/a cell with
  `first_available`.
- **N5 kernel**: `make test-kernel` must collect `services/analytics/tests` (root `pyproject.toml` `testpaths` already lists
  `services`); Hypothesis becomes a dev dependency in AI-analytics-scaffold (`uv add --dev hypothesis`).
