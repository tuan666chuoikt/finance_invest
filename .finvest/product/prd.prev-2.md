# Finvest — Product Requirements Document (PRD)

Owner: `fi-po`. Status: **Approved v2** (sponsor, 2026-10-15; v1 archived as `prd.prev-1.md`).
Inputs: `product/brief.md`, `product/sponsor-answers.md` (A1–A4, 2026-10-14 21:57; A5–A12, 2026-10-15 18:15),
`knowledge/vn-market.md` (cited as VN§n), `docs/00-kha-thi.md`, `docs/04-lo-trinh-hoc.md` (levels L1–L8).
Anything the sponsor has not confirmed is tagged `[assumed]`. Free data only; anything that costs money is an
open question, never a requirement.

## 1. Problem

The sponsor wants to become a disciplined, knowledgeable investor in the Vietnamese stock market. Free tools
show prices and charts but hide what matters for learning: the real return after lots, fees, tax, T+2 and
corporate actions; whether a "best strategy" would have survived the next week; and what evidence (not
opinion) accompanied a price move. Finvest is a personal learning lab that computes these honestly, shows
every formula and data timestamp, and grows its own fine-grained data store from day one, because free tick
history does not exist before we start crawling. The data exists to **simulate scenarios**, not to monitor or
trade live (A7): the store is built best-effort while the sponsor's machine is on, and every hole is shown.

## 2. Users

- **The sponsor** (single user, Linux desktop, reads Vietnamese and English, UI switchable EN/VI per A8,
  beginner-to-intermediate investor). No other users, no accounts, no sharing.
- **The agent team** (indirect): the PRD is the root of traceability (`PR-###` → `F-###` stories → tasks).

## 3. Learning outcomes (the reason each feature exists)

| Level (docs/04) | After using Finvest the sponsor can… | Features |
|---|---|---|
| L1 Market | Read a price board for one session and explain colour, band, tick, lot, T+2, fee and tax of any row | Price board, rules page |
| L2 Real return | State the gap between "chart return" and real total return for a stock with dividends/bonus shares, and name each drag | What-if |
| L3 Risk | Compare two holdings by volatility, max drawdown and correlation, and choose the one they could hold through | Multi-stock what-if, benchmark |
| L4 Technical analysis | Backtest a rule (MA cross, breakout) and state where it fails | Scenario backtester |
| L5 Validation thinking | Take "best scenario of the last 7 days" and show what it did in the next 7 days; recognise overfitting, look-ahead and survivorship bias | Walk-forward ranking, sensitivity |
| L6 Flows and events | Explain a strong move with dated evidence: market, sector, foreign/proprietary flows, events (news headlines in a later release, A9) | "Why it moved" |
| L7 Fundamentals | (later release) read statements and ratios | Financial data |
| L8 Discipline | (later release) keep a paper-trading journal and review it | Journal |

Principle (docs/04): **every number carries its formula and its data as-of time.** A feature with no learning
outcome in this table is out of scope.

## 4. Goals and measurable metrics

| # | Goal | Metric the sponsor can check | Target |
|---|---|---|---|
| G1 | Own the finest-grain history available for free, **best-effort** (A7: data serves simulation, so no always-on machine is required) | **Tick completeness**: % of trading sessions since crawl start with a complete all-market tick file, and the list of missed sessions (data-quality page) | **0 silent gaps** (every gap listed with its reason); completeness is reported, not targeted, in v1 — the sponsor sets a target after R1 if tick-based features need one |
| G2 | Daily history is complete and adjusted correctly | % of listed symbols with daily OHLCV for every trading day; adjusted-series mismatch vs source adjusted close | ≥ 99.5%; mismatch > 0.1% flagged for 100% of cases |
| G3 | Simulator numbers are right | Golden-case agreement with independent hand/spreadsheet calculation (fees, tax, lots, T+2, cash/stock dividends, rights) | 100% of ≥ 20 golden cases within 1 VND; what-if total return vs adjusted-series return within 0.05% |
| G4 | Fast enough to explore | Time-to-answer: one what-if (10 years daily); compare 5 strategies × 10 symbols × 5 years | < 2 s; < 30 s |
| G5 | Teaches validation, not hindsight | Share of "best over window" rankings shown **with** out-of-sample result | 100% (rankings without OOS are not rendered) |
| G6 | Board is honest about freshness | Watchlist latency during session; staleness badge when data older than threshold | ≤ 5 s median `[assumed source permits]`; badge at > 15 s, 100% of the time |
| G7 | Every figure is explainable | Figures on analysis screens with a visible "how computed + as-of" | 100% |
| G8 | Safe by construction | Real orders placed; broker credentials stored; paid API calls | 0 / 0 / 0 |

## 5. Constraints: what the data can honestly support

These are requirements on the product's honesty, not footnotes.

- **C1 Tick history starts the day we start crawling and has holes** (VN§8, A7). No free back-fill; a session
  missed because the machine was off is lost for good and is simply listed as a gap. Any tick-based feature
  (session replay, tick-derived 1m bars) states its earliest available date and skips missing sessions
  visibly. The crawler is still the first deliverable (R1, PR-013) so the store starts growing early.
- **C11 Data is for scenario simulation, not live trading or monitoring** (A7). "Finest grain" therefore
  means: daily + 1m bars (C2, C3) are the backbone every simulator and backtest must work on; ticks are a
  bonus layer that improves replay and reconciliation when present. No feature may *require* a complete
  tick history, no always-on machine is required, and the live board (R3) is a learning tool for reading a
  board, not a monitoring tool.
- **C2 1-minute bars** exist only for a short recent window per source (VN§8); back-fill as far as allowed,
  then grow daily. Features show the boundary where 1m data begins.
- **C3 Daily OHLCV** is available for many years and is the backbone of what-if and backtests.
- **C4 "Best scenario of the last 7 days" is hindsight** unless tested on the following window. Every
  ranking is paired with its walk-forward result (PR-073).
- **C5 "Why it moved" yields evidence, not causes.** The product decomposes and lists co-occurring factors
  with their estimated contribution; it never asserts causality (PR-093). No LLM (A4): rules and
  statistics only.
- **C6 Free, unofficial endpoints can change or block at any time** (docs/00 §2). Every source sits behind
  an adapter with fixtures; the UI shows stale-data states; the product degrades, it does not lie.
- **C7 Market rules are drafts marked [verify]** in VN§2–5. Values live in one rules module with
  `effective_from`; the rules page shows the verification status of each rule.
- **C8 Live coverage of ~1,600 symbols at seconds-level refresh is not possible on public endpoints**
  (docs/00 §1): the board is a watchlist refreshed fast plus a full-market snapshot refreshed slowly (A5).
- **C9 Units**: sources quote thousand VND and sometimes 10-share volume units (VN§3). Adapters convert and
  document; all stored prices are in VND, volumes in shares.
- **C10 No margin (A3), no broker account (A2), no paid data, no real orders.**

## 6. Scope

**In scope (v1 = releases R1–R5):** data foundation (daily, corporate actions, tick, 1m, flows), trading
calendar and rules, what-if simulator, price board with watchlist, candlestick charts, scenario backtester
with walk-forward, "why it moved" evidence view, learning layer (formulas, glossary, exercises).

**Out of scope for v1:** order placement of any kind; broker login; margin; derivatives, covered warrants,
bonds (VN§1); LLM/news summarisation (A4); **news headlines and the headline timeline (A9: "developed
later", PR-019/PR-092 kept as Could in R6)**; multi-user, cloud deployment, mobile app; intraday live
strategy execution/alerts/monitoring (A7); fundamentals and journal (deferred to R6, kept as Could).

## 7. Requirements (MoSCoW: M = Must, S = Should, C = Could, W = Won't in v1)

Each requirement: priority · learning outcome (L#) · acceptance the PM turns into Given/When/Then.

### 7.1 Market rules and reference data (L1)

- **PR-001 (M)** Rules module generated from `knowledge/vn-market.md`: sessions, bands, tick sizes, lots,
  fees, taxes, settlement, each with `effective_from` and a `verified: yes/no (date, source)` flag; a
  "Market rules" page renders it. *Acceptance:* changing a value in the module changes simulator output;
  page shows unverified rules in a warning state.
- **PR-002 (M)** Trading calendar table (holidays, bridge days, half sessions) per venue, maintained by data,
  never inferred from missing rows (VN§2). *Acceptance:* a missing crawl on a trading day is reported as a
  gap; a holiday is not.
- **PR-003 (M)** Symbol master for all HOSE/HNX/UPCoM stocks and ETFs (A1): exchange, listing date,
  delisting date, ICB sector, index membership history (VN30 etc.). Delisted symbols are kept (survivorship
  control for PR-075). Refreshed daily.
- **PR-004 (S)** Session-phase service: current phase per venue (pre-open, ATO, continuous, break, ATC,
  post-close, closed, holiday) used by the board and the crawler scheduler.

### 7.2 Data foundation (crawler and store) — release R1

- **PR-010 (M)** Daily OHLCV + matched value, for every symbol and index, back-filled for all years the
  source provides, then incremental after each session. *Acceptance:* G2 coverage; nominal prices stored as
  received, in VND.
- **PR-011 (M)** Corporate-actions table (cash dividend, stock dividend/bonus, rights issue, split/merge,
  listing changes): symbol, type, ex-date, record date, pay date, ratio/amount/price, source, fetched-at
  (VN§6). Refreshed daily; a diff log when a past event changes.
- **PR-012 (M)** Adjusted price series computed by Finvest from nominal prices + PR-011 using VN§6 formulas,
  reproducible, and reconciled against the source's adjusted close; mismatches > 0.1% listed on the
  data-quality page. *Acceptance:* worked example for one stock with a cash dividend and one bonus issue in
  tests.
- **PR-013 (M)** **Tick crawl after close for all symbols, best-effort** (A1, A7): time, price, volume,
  side where given (VN§8). Raw payload archived, normalised rows stored compressed. Runs when the machine
  is on (PR-020); a missed session is recorded as a gap, never back-filled silently. *Acceptance:* a
  per-session manifest (symbols fetched, rows, checksum, skipped symbols, or "session missed: reason");
  re-run is idempotent; 0 silent gaps (G1). `[assumed]` the free endpoint allows a full-market pass within
  the evening at its rate limits; if not, priority order = watchlist → VN30 → HOSE → HNX → UPCoM and the
  manifest records what was skipped.
- **PR-014 (S)** 1-minute bars: back-fill as far as the source allows, then daily; where ticks exist, 1m
  bars are also derived from ticks and the two are reconciled (OHLCV equality) as a data-quality check.
- **PR-015 (S)** Order-book top-3 bid/ask snapshots sampled every 3–5 s during the session for the
  watchlist only (VN§8), stored for session replay (PR-054).
- **PR-016 (M)** Every source behind a `MarketDataSource` adapter with recorded fixtures, unit conversion
  (VN§3), caching, rate limiting and backoff; adding a source does not change the core. *Acceptance:* core
  tests run offline on fixtures; a second adapter can replace the first for daily OHLCV.
- **PR-017 (M)** Data-quality page: per feed last success time, sessions covered, gaps, completeness %,
  anomalies (price outside band, zero volume on a trading day, duplicate ticks), reconciliation mismatches.
  This page is the sponsor's G1/G2 check.
- **PR-018 (S)** Daily market-structure data (VN§7): foreign net buy/sell per symbol and market, proprietary
  (tự doanh) net flow `[assumed available from a free source]`, index constituents and weights, ETF
  rebalance dates (calendar entered manually if no source).
- **PR-019 (C, R6)** News headlines: title, time, URL, tagged symbols, from RSS/public pages whose terms
  allow it. Headline and link only; no article body stored; no summarisation (A4). **Deferred to a later
  release (A9).**
- **PR-020 (S)** Scheduler, best-effort (A7): the after-close crawl runs from a timer (systemd or
  equivalent) at 15:30 with a retry at 20:00; if the machine was off, it runs at next boot and fetches the
  day's ticks only if the source still serves them `[assumed usually not]`, otherwise records the gap. A
  missed or partial run is shown on the data-quality page; manual re-run for a date. No always-on machine,
  no secondary device, no alerting is required.
- **PR-021 (C, R6)** Financial statements and ratios (P/E, P/B, ROE, growth) per symbol, quarterly (L7).

### 7.3 What-if simulator — release R2 (L2, L3)

- **PR-030 (M)** Lump-sum what-if: "X VND into symbol E on day N, value on day M (default today)". Buys whole
  board lots (VN§4), keeps residual cash, applies brokerage fee on buy and sell (default **0.15% per side**, editable, A6) and 0.1% sell tax (VN§5),
  enforces T+2 before a sale (VN§5). Output: shares, cash, market value, total return (VND and %), CAGR.
- **PR-031 (M)** Declared fill rule, shown on the result: `close of N` (default), `next open`, `VWAP of N`,
  or `limit price within [low, high] of N`; never a price outside that day's range (VN§4). If N is not a
  trading day, the next trading day is used and the shift is displayed.
- **PR-032 (M)** Corporate actions replayed as events (VN§6): cash dividend (5% tax, option reinvest or keep
  as cash, cash arrives on pay date), stock dividend/bonus shares (shares count from ex-date, valued at the
  adjusted reference until arrival), rights issue (option: exercise with cash from the portfolio / let
  lapse; default exercise if cash suffices, else lapse — A10). *Acceptance:* the what-if total return equals the
  adjusted-series total return within 0.05% for a dividend-paying stock over ≥ 3 years (G3).
- **PR-033 (M)** Return breakdown on every result: "chart return" (nominal price change) vs real return, with
  contributions of dividends, fees, taxes, lot rounding/residual cash, and timing of fills; each term with
  its formula and inputs (PR-110). *Learning:* L2.
- **PR-034 (M)** Benchmark on the same screen: same X into VN-Index (price-only, non-investable, labelled
  so) and into an investable index ETF with the same fee model `[assumed E1VFVN30]`.
- **PR-035 (S)** Portfolio what-if: several symbols with weights or a cash split; shows per-symbol
  contribution, pairwise correlation and the diversification effect on drawdown (L3).
- **PR-036 (S)** Risk metrics with explanations: annualised volatility, max drawdown and its duration, Sharpe
  (risk-free rate shown and editable, default the 12-month bank deposit rate entered by the sponsor — A11),
  time under water. (L3)
- **PR-037 (M)** Independent verification kit: ≥ 20 golden cases documented as hand calculations (markdown
  or spreadsheet) covering lots, fees, tax, T+2, cash dividend, bonus shares, rights issue, delisting; tests
  fail on any 1-VND deviation. Testers maintain an independent calculator (CLAUDE.md Done rule).
- **PR-038 (C)** Toggles, default off: odd-lot purchases (VN§4) and cash advance on sale proceeds (VN§5).
- **PR-039 (M)** Settlement and cash ledger: a dated ledger of every cash and share movement (buy, fee, tax,
  dividend, settlement) visible under the result, exportable (PR-134).

### 7.4 Price board and charts — release R3 (L1)

- **PR-050 (M)** Watchlist board: reference/ceiling/floor, top-3 bid/ask with volumes, last matched price and
  volume, change and %, total volume/value, foreign buy/sell, colours per VN§3; default watchlist **30
  symbols (up to 100), refresh ≤ 5 s** (A5). Columns match the familiar Vietnamese board layout; labels
  follow the UI language (PR-137, A8). Purpose: learning to read a board, not monitoring (C11).
- **PR-051 (M)** Freshness and session states: as-of time per row, "stale" badge when older than 15 s in
  session, session-phase banner (ATO / continuous / break / ATC / closed / holiday, PR-004), explicit
  "market closed, showing last session" state, and error state when the source fails (C6).
- **PR-052 (S)** Full-market snapshot board for all symbols (A1) refreshed every 30–60 s (A5), with
  sort/filter (exchange, sector, % change, volume, ceiling/floor hits) and add-to-watchlist.
- **PR-053 (S)** Candlestick chart: daily (nominal/adjusted toggle, with the difference explained), 1m where
  available (C2 boundary shown), volume, MA overlays, markers for ex-dates and corporate events.
- **PR-054 (S)** Session replay: play back a past session's ticks and order-book snapshots for a watchlist
  symbol at chosen speed (from our own crawl, so from crawl start only, C1). *Learning:* reading supply and
  demand (L1, docs/04 exercise 1).
- **PR-055 (C)** "Explain this row" overlay: why this colour, how ceiling/floor were rounded to tick, what
  100 shares cost including fee.
- **PR-056 (M)** Indices panel: VN-Index, VN30, HNX-Index, HNX30, UPCoM-Index with change, breadth
  (advancers/decliners/unchanged, ceiling/floor counts) and total value.

### 7.5 Scenario backtester — release R4 (L4, L5)

- **PR-070 (M)** Strategy library v1, all parametrised: buy-and-hold (lump sum), DCA (amount, period,
  weekday/day-of-month), MA crossover (fast/slow), breakout (N-day high), stop-loss / take-profit / trailing
  stop overlays, and benchmark hold. Each strategy page states its rule in plain Vietnamese and English.
- **PR-071 (M)** One engine for what-if and backtests: the same cost, lot, T+2 and corporate-action model
  (PR-030–032). Signals use only data with timestamp ≤ decision time (`as_of` on every function); fills at
  the declared rule (next open default `[assumed]`, or same close), never outside [low, high]. *Acceptance:*
  a look-ahead test (future data perturbed → signal unchanged) is in the kernel.
- **PR-072 (M)** Comparison screen: N scenarios × M symbols × one period, table of total return, CAGR, max
  drawdown, Sharpe, trades, fees+tax paid, win rate, exposure; overlaid equity curves; benchmark row.
- **PR-073 (M)** **Walk-forward ranking**: any "best over window W" (e.g. last 7 days) shows, next to it, the
  same scenarios over the following window W' (and over k rolling windows), rank stability (e.g. Spearman
  across windows) and the plain statement "in-sample rank ≠ future rank". A ranking without an OOS column is
  not rendered (G5). *Learning:* L5, docs/04 exercise 5.
- **PR-074 (S)** Parameter sensitivity: results over a parameter grid (heatmap/table); flags optima whose
  neighbours perform much worse (overfitting lesson).
- **PR-075 (S)** Survivorship control: the universe for a backtest is the set listed at the start date
  (PR-003), including later-delisted symbols; a delisting is handled as a forced exit at the last price with
  a warning.
- **PR-076 (C)** Bootstrap of trade sequences to show the distribution of drawdowns, not one path.
- **PR-077 (C, R6)** Rule builder (simple composable conditions) for custom strategies.
- **PR-078 (S)** Scenario journal: save a scenario run with parameters, data snapshot version (PR-133), and
  the sponsor's note ("what I expected / what happened"); re-run reproduces identical numbers.

### 7.6 "Why it moved" — release R5 (L6)

- **PR-090 (M)** Return decomposition for symbol E over a window (default 7 sessions): market component
  (index), sector component (ICB peers or sector index), idiosyncratic residual; method shown (relative
  return and beta-based variants, with the estimation window), rules and statistics only (A4).
- **PR-091 (M)** Evidence panel, each item dated and sourced: volume vs 20-day average, ceiling/floor hits,
  foreign net flow, proprietary flow, ex-dates and corporate events (PR-011), earnings-report proximity, index
  / ETF rebalance dates, unusual order-book imbalance from our snapshots (PR-015 where available).
- **PR-092 (C, R6)** Headline timeline aligned with the price chart (needs PR-019); headline + link only.
  Deferred with PR-019 (A9).
- **PR-093 (M)** Honesty rules: the view is titled as evidence ("Các yếu tố đi kèm"), each factor shows an
  estimated contribution and its uncertainty, no causal claim, and the educational disclaimer (PR-130).
- **PR-094 (S)** Event study: for an event type (ex-dividend, earnings, rebalance) show the symbol's and
  sector's average historical reaction (t−5…t+5) with sample size.
- **PR-095 (C)** Daily market digest after close: top movers, breadth, flows, ceiling/floor counts, events
  of the day, generated from data (no LLM).

### 7.7 Learning layer (all levels)

- **PR-110 (M)** Every figure on what-if, backtest and why-it-moved screens has an expandable "how
  computed": formula, inputs with their values, data as-of time, rule versions used (PR-001). (G7)
- **PR-111 (M)** Glossary VN/EN (trần, sàn, tham chiếu, GDKHQ, T+2, lô chẵn, phí, thuế, drawdown, Sharpe,
  walk-forward…) linked from terms in the UI, each entry showing both languages regardless of the UI
  language (PR-137); content sourced from `vn-market.md` and docs/04.
- **PR-112 (S)** Exercises: each screen offers the docs/04 exercise for its level (e.g. "explain the colour
  of 10 symbols", "compare chart return vs real return for 5 high-dividend stocks") with a notes field saved
  locally.
- **PR-113 (C, R6)** Paper-trading journal with entry/exit rules and monthly self-review (L8).
- **PR-114 (C)** Learning progress view: levels L1–L8 with completed exercises.

### 7.8 Platform and guardrails (non-functional, product-visible)

- **PR-130 (M)** Guardrails: no order placement UI or API, ever; no broker credentials anywhere; no paid
  API; every analysis screen shows "Mô phỏng để học, không phải lời khuyên đầu tư" (educational, not
  investment advice). *Acceptance:* a test asserts the banner on every analysis route; a dependency audit
  shows no broker SDKs.
- **PR-131 (M)** Runs locally on the sponsor's Ubuntu machine with `docker compose`, bound to localhost
  `[assumed no login needed]`; one command to start, one to crawl a date.
- **PR-132 (M)** Storage: all data lives under the repo folder, `finance_invest/data/` (git-ignored, A12);
  ticks compressed; storage used per feed shown on the data-quality page; retention configurable, default
  **keep everything** (A12; docs/00 §3 estimates tens of MB per day, ~10–20 GB/year).
- **PR-133 (M)** Reproducibility: every result references the data snapshot (max fetched-at) and rules
  version; re-running with the same snapshot yields identical numbers.
- **PR-134 (S)** CSV export of any table and ledger.
- **PR-135 (M)** Respect source rate limits and terms: per-source request budget, caching of every fetch,
  exponential backoff, user-agent identified as a personal tool; crawling stops (and reports) rather than
  hammering a blocked endpoint.
- **PR-136 (C)** Backup to a **different disk or device** the sponsor names; restore procedure tested once
  per release. Plainly: `finance_invest/data/` (A12) is the live store, not a backup — a copy on the same
  disk dies with it, and git ignores it. Downgraded from Should to Could because the data is best-effort
  anyway (A7, C11): losing it costs history, not money. The data-quality page states "no backup
  configured" until one is.
- **PR-137 (M)** UI language switch **EN/VI** (A8): every label, message, state text and rule page exists in
  both languages; the choice is saved locally; one missing translation key fails a test. The disclaimer
  (PR-130) and the glossary (PR-111) show both languages. Technical docs stay in English.

### Count

61 requirements: 34 Must, 16 Should, 11 Could; Won't items are listed in §6, not as PR-###.
(v1→v2: PR-020 M→S, PR-092 S→C, PR-136 S→C, PR-137 added as M; PR-019/092 moved to R6.)

## 8. Releases and release criteria

| Release | Content (PR) | Learning | Release criteria |
|---|---|---|---|
| **R1 Data foundation** (first; start the tick crawl as early as possible, C1) | 001–004, 010–013, 016, 017, 020, 130–133, 135, 137 | L1 (raw data, adjusted prices) | Tick manifests for ≥ 5 sessions (need not be consecutive) with 0 silent gaps and every missed session listed with a reason; daily OHLCV ≥ 99.5% coverage; adjusted series reconciled for VN30 with mismatches listed; rules page shows verification status; timer ran for a week with no manual start on days the machine was on; UI switches EN/VI |
| **R2 What-if** | 030–034, 037, 039, 110, 111 | L2 | All golden cases pass (1 VND); what-if vs adjusted-series return within 0.05% on 10 dividend stocks; benchmark shown; "how computed" on every figure; disclaimer on screen |
| **R3 Price board** | 050, 051, 056, 053, 014, 015, 052, 054, 055 | L1 | Watchlist ≤ 5 s median in session, stale badge verified by cutting the source; all states (empty, loading, error, stale, closed, holiday) have UX specs and tests; colours match VN§3 for ceiling/floor/reference cases |
| **R4 Scenarios** | 070–073, 075, 078, 035, 036, 074, 134 | L3, L4, L5 | Look-ahead test passes; same engine as R2 (shared tests); every ranking renders with OOS column; a documented walk-forward example on "best of last 7 days" |
| **R5 Why it moved** | 018, 090, 091, 093, 094, 095 | L6 | Decomposition reproducible with method shown; evidence items dated and sourced; no causal wording (reviewed by PM); disclaimer present |
| **R6 Later** | 019, 092 (news, A9), 021, 077, 113, 114, 038, 076, 136 | L6 (news), L7, L8 | Defined after R5 retro |

Common Done criteria (every release): numbers verified against an independent calculation; data correctness
(adjusted prices, dividends, fees, tax) covered by tests; guardrail PR-130 holds; touched docs updated.

## 9. Risks (product view)

| Risk | Mitigation in requirements |
|---|---|
| Free endpoint changes/blocks | PR-016 adapters + fixtures, PR-017 visibility, PR-051 stale states, PR-135 backoff; second source as a follow-up |
| Wrong return math | PR-037 golden cases, PR-012 reconciliation, PR-032 agreement test, opus-reviewed PRs for money math |
| Learning the wrong lesson (hindsight) | PR-073 mandatory OOS, PR-071 `as_of`, PR-074 sensitivity, PR-075 survivorship |
| Missed crawl days = permanent tick holes | Accepted (A7, C11): holes are listed, not hidden (PR-013/017); simulation runs on daily + 1m (C3), never requires ticks; PR-020 timer + boot catch-up; R1 first |
| Data loss (same-disk store, no backup) | PR-136 Could + "no backup configured" notice on the data-quality page; daily/1m can be re-fetched from sources, only ticks are lost |
| Scope creep into "trading tool" | §6 out-of-scope, PR-130 tests |

## Open questions for the sponsor

Answered: A1–A12 (see `product/sponsor-answers.md`; A5, A6, A10, A11 as proposed; A7, A8, A9, A12 applied
above). No new questions — the remaining `[assumed]` tags are technical and the team will settle them in R1;
the next label, if needed, is A13.
