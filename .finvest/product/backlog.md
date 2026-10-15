# Finvest — Product backlog

Owner: `fi-pm`. Source: `product/prd.md` (Approved v2, 2026-10-15), `product/sponsor-answers.md` (A1–A15),
`knowledge/vn-market.md` (cited VN§n). Roadmap and velocity: `product/roadmap.md`. UX specs: `product/ux/`.

Status: **Approved (sponsor 2026-10-15)**.
Changelog: 2026-10-15 — applied sponsor answers A13 (risk-free default 5 %/year, editable) and A14+A15 (default
watchlist = top 30 by 20-session average traded value, refreshed weekly); updated F-018, F-061, F-090.

Conventions
- `F-###` story → `PR-###` requirement. Points 1/2/3/5/8 (nothing above 8). Status: **Ready** (refined,
  can enter a sprint) · **Backlog** (has G/W/T, refine before planning) · **Deferred** (R6, rough points).
- Money criteria carry a worked numeric example. Prices in the examples are **illustrative**, not market data.
  Default fee 0.15 % per side (A6, VN§5), sell tax 0.1 % (VN§5), cash-dividend tax 5 % (VN§5), lot 100 (VN§4).
- Every analysis story states its **decision time** (what data was knowable) so look-ahead is testable.
- Every screen story inherits: EN/VI labels (PR-137), disclaimer on analysis screens (PR-130), "how computed
  + as-of" on every figure from R2 on (PR-110), and the states in its UX spec.

## Summary

| Release | Epics | Stories | Points | Status |
|---|---|---|---|---|
| R1 Data foundation | E1, E2, E3 | 22 | 81 | Ready |
| R2 What-if | E4, E8 | 15 | 53 | Backlog |
| R3 Price board | E5, E8 | 13 | 45 | Backlog |
| R4 Scenarios | E6, E8 | 14 | 48 | Backlog |
| R5 Why it moved | E7, E8 | 7 | 24 | Backlog |
| **R1–R5 (v1)** | | **71** | **251** | |
| R6 Later | E9 | 9 | ~41 (rough) | Deferred |

Traceability: every one of the 61 PR-### maps to at least one story (table at the end). PR-112 (exercises) has
no release in PRD §8; the PM ships each level's exercise with the screen it needs (R2–R5) — a sequencing
choice, not a scope change.

---

## R1 — Data foundation

### E1 Market rules and reference data (L1)

**F-001 Rules module from vn-market.md** · PR-001 · 5 pts · Ready
- Given `knowledge/vn-market.md` §2–§5, When the rules module is generated, Then sessions, bands, tick sizes,
  lots, fees, taxes and settlement each exist as one value with `effective_from` and `verified: yes|no (date, source)`.
- Given HOSE reference 93,500 VND, band ±7 %, tick 100 for prices ≥ 50,000 (VN§3), When ceiling/floor are
  computed, Then raw 100,045 / 86,955 round **inward** to **100,000 / 87,000**.
- Given HNX reference 20,000, band ±10 %, tick 100, Then ceiling/floor = 22,000 / 18,000.
- Given the fee value is changed from 0.15 % to 0.20 % in the module, When a consumer reads it, Then it gets
  0.20 % with the new `effective_from` and older dates still return 0.15 % (PR-001 acceptance).

**F-002 Market rules page (EN/VI)** · PR-001, PR-137 · 3 pts · Ready · UX: `ux/market-rules.md`
- Given the rules module, When the sponsor opens "Market rules", Then every rule shows value, venue,
  `effective_from`, verification status and source section (VN§n).
- Given a rule with `verified: no`, Then it renders in the warning state with a non-colour cue (icon + text "Unverified").
- Given the UI language is switched, Then all labels change language; rule values are unchanged.

**F-003 Trading calendar** · PR-002 · 3 pts · Ready
- Given a calendar table per venue (holidays, bridge days, half sessions) maintained as data, When a date is
  queried, Then it returns trading / holiday (with name) / weekend; nothing is inferred from missing rows (VN§2).
- Given 2026-09-02 (National Day) is a holiday in the table and no crawl ran, Then it is **not** reported as a gap.
- Given a weekday trading date with no crawl, Then it **is** reported as a gap.

**F-004 Symbol master (all exchanges, delisted kept)** · PR-003 · 5 pts · Ready
- Given the free source's listings for HOSE, HNX, UPCoM stocks and ETFs (A1), When the daily refresh runs, Then
  each symbol has exchange, listing date, delisting date, ICB sector, and index-membership history (VN30 etc.).
- Given a symbol disappears from the source listing, Then it is kept with a delisting date, never deleted.
- Given the refresh runs twice the same day, Then the table is unchanged (idempotent).

**F-005 Session-phase service** · PR-004 · 3 pts · Ready
- Given the session table VN§2 and the calendar, When asked at 2026-10-15 09:10 Asia/Ho_Chi_Minh, Then HOSE =
  ATO, HNX = continuous, UPCoM = continuous.
- Given 11:45, Then HOSE = break; given 14:35, Then HOSE = ATC, UPCoM = continuous (no ATC on UPCoM).
- Given a holiday from F-003, Then every venue = holiday; given 16:00 on a trading day, Then = closed.

### E2 Data foundation: crawler and store

**F-010 MarketDataSource adapter with fixtures and unit conversion** · PR-016, C9 · 5 pts · Ready
- Given a source that quotes 93.5 (thousand VND) and volume in units of 10 shares, When the adapter
  normalises, Then the stored price is 93,500 VND and volume 10 × the quoted unit; the unit rule is documented in the adapter.
- Given recorded fixtures, When the core test suite runs with networking disabled, Then it passes (offline).
- Given a second adapter implementing daily OHLCV, When it is configured instead of the first, Then no core code changes.

**F-011 Rate limits, caching, backoff, stop on block** · PR-135 · 3 pts · Ready
- Given a per-source request budget, When a crawl runs, Then it never exceeds the budget and every response is cached.
- Given the source returns HTTP 429/403 three times in a row, Then backoff is exponential and the crawl stops
  and records "source blocked" instead of retrying indefinitely.
- Given any request, Then the user-agent identifies a personal tool.

**F-012 Daily OHLCV back-fill** · PR-010 · 5 pts · Ready
- Given the symbol master and all indices, When back-fill runs, Then daily OHLCV + matched value is stored for
  all years the source provides, nominal, in VND (C9).
- Given the back-fill is interrupted, When re-run, Then it resumes without duplicates.
- Given back-fill completes, Then coverage % per exchange is computed for G2 (target ≥ 99.5 %).

**F-013 Daily incremental update** · PR-010 · 2 pts · Ready
- Given a completed trading session, When the after-close job runs, Then that day's bar is added for every listed symbol and index.
- Given the job runs twice for the same date, Then the result is identical (idempotent).

**F-014 Corporate-actions table with diff log** · PR-011 · 5 pts · Ready
- Given the source's events, When refreshed daily, Then each row has symbol, type (cash dividend, stock
  dividend/bonus, rights, split/merge, listing change), ex-date, record date, pay date, ratio/amount/price,
  source, fetched-at (VN§6).
- Given a past event's ex-date changes at the source, Then the row is updated and a diff-log entry records old/new value and time.

**F-015 Adjusted price series** · PR-012 · 5 pts · Ready
- Decision time: adjusted series are retroactive by design (VN§6) and are for charts/indicators only; the
  simulator uses nominal prices + events.
- Given nominal closes D−2 = 51,000, D−1 = 50,000 and a cash dividend 1,000/share ex on D, When adjusted,
  Then factor = (50,000 − 1,000) / 50,000 = 0.98 and adjusted closes are D−1 = 49,000, D−2 = 49,980.
- Given a bonus issue 10:3 ex on D with D−1 close 93,500, Then factor = 10/13 and adjusted D−1 = 71,923.08.
- Given both events, Then factors multiply; re-running yields byte-identical output (reproducible).

**F-016 Adjusted-series reconciliation** · PR-012 · 3 pts · Ready
- Given our adjusted close 49,000 and the source's 48,900, Then mismatch = 0.204 % > 0.1 % and it is listed on the data-quality page.
- Given 49,000 vs 48,980 (0.041 %), Then it is not listed.
- Given the VN30 constituents, Then a reconciliation run covers all 30 (R1 release criterion).

**F-017 Tick crawl after close with manifest** · PR-013, C1 · 8 pts · Ready
- Given a trading day, When the after-close crawl runs, Then for each symbol it stores time, price, volume,
  side where given; the raw payload is archived and normalised rows are compressed.
- Given the crawl finishes, Then a per-session manifest lists symbols fetched, rows, checksum, skipped symbols with reason.
- Given the crawl is re-run for the same date, Then rows and checksum are unchanged (idempotent).
- Given the machine was off and the source no longer serves that day, Then the manifest reads "session
  missed: machine off / source no longer serves" — never silently absent (0 silent gaps, G1).

**F-018 Tick crawl priority order** · PR-013 · 3 pts · Ready
- Given the source's rate limit does not allow a full-market pass in the evening, When the crawl runs, Then the
  order is watchlist → VN30 → HOSE → HNX → UPCoM and the manifest lists every skipped symbol.
- Given the default watchlist is not yet computable (no stored sessions yet), Then the order starts at VN30
  until the first weekly watchlist refresh (F-061, A14/A15).

**F-019 Best-effort scheduler** · PR-020 · 3 pts · Ready
- Given a systemd user timer (or equivalent), When a trading day reaches 15:30, Then the crawl starts with no manual action; retry at 20:00 if it failed.
- Given the machine was off at 15:30 and 20:00, When it boots, Then the catch-up job runs once and either
  fetches (if served) or records the gap.
- Given the command `crawl --date 2026-10-14`, Then that date is (re)crawled manually.
- Given non-trading days (F-003), Then nothing runs.

**F-020 Data folder under the repo, git-ignored** · PR-132 · 1 pt · Ready
- Given a fresh checkout, When the app starts, Then all data is written under `finance_invest/data/` (A12)
  and `git status` shows nothing from it (git-ignored).
- Given retention config, Then the default is "keep everything".

**F-021 Data-quality page: feeds, gaps, completeness, storage** · PR-017, PR-132, PR-136 · 5 pts · Ready · UX: `ux/data-quality.md`
- Given each feed (daily, corporate actions, ticks, symbols), Then the page shows last success time, sessions
  covered, completeness % and the list of missed sessions each with its reason (G1).
- Given 20 trading sessions since crawl start, 17 complete, 3 missed, Then tick completeness = 85.0 % and the 3 dates are listed.
- Given storage per feed, Then it shows size on disk (e.g. "Ticks: 412 MB"); and "No backup configured" (PR-136) until one exists.

**F-022 Data-quality anomalies** · PR-017 · 3 pts · Ready
- Given a stored price outside that day's [floor, ceiling] (F-001), or zero volume on a trading day, or a
  duplicate tick (same time, price, volume, sequence), Then each is listed with symbol, date and rule.
- Given an anomaly is fixed by a re-crawl, Then it disappears from the list on the next check.

**F-023 Data snapshot and rules version on results** · PR-133 · 3 pts · Ready
- Given any computed result, Then it carries `data_snapshot` (max fetched-at of inputs) and `rules_version`.
- Given the same snapshot and rules version, When recomputed, Then numbers are identical.

### E3 Platform and guardrails

**F-030 Local docker compose, one-command start and crawl** · PR-131 · 3 pts · Ready
- Given Ubuntu with Docker, When the sponsor runs one documented command, Then the app starts bound to
  127.0.0.1 only (not reachable from another host).
- Given one documented command with a date, Then that date is crawled.

**F-031 App shell with EN/VI switch** · PR-137 · 3 pts · Ready · UX: `ux/app-shell.md`
- Given the app shell, When the sponsor picks VI or EN, Then every label switches and the choice survives a reload (stored locally).
- Given a translation key missing in either language, Then the test suite fails.
- Given technical docs, Then they stay English (not translated).

**F-032 Guardrail banner and audit** · PR-130 · 2 pts · Ready
- Given any analysis route, Then the banner shows both "Mô phỏng để học, không phải lời khuyên đầu tư" and
  "Educational simulation, not investment advice"; a test enumerates routes and asserts it.
- Given the dependency tree, Then an audit test finds no broker SDK and no order-placement endpoint.

---

## R2 — What-if (L2)

### E4 What-if simulator

**F-040 Lump-sum buy: lots, fee, residual cash** · PR-030 · 5 pts · Backlog
- Decision time: close of day N (default fill rule F-042); only data ≤ N is used for the buy.
- Given 10,000,000 VND into FPT on Mon 2026-10-12 at an illustrative close of 93,500, lot 100, buy fee 0.15 %,
  When simulated, Then shares = 100 (200 would need 18,728,050), cost 9,350,000 + fee 14,025 = 9,364,025,
  **cash left 635,975 VND**.
- Given 5,000,000 VND and price 93,500, Then 0 shares are bought and the result says "amount below one board lot (9,364,025 VND)".

**F-041 Sale: fee, tax, T+2, total return, CAGR** · PR-030 · 3 pts · Backlog
- Given F-040's 100 shares bought Mon 2026-10-12, When a sale is requested Tue 2026-10-13, Then it is refused
  ("shares arrive T+2: Wed 2026-10-14", VN§5).
- Given a sale on day M at an illustrative 100,000: value 10,000,000, fee 15,000, tax 10,000, Then net
  9,975,000; final cash 635,975 + 9,975,000 = **10,610,975**; total return **610,975 VND = 6.11 %**.
- Given a holding period of exactly 365 days, Then CAGR = total return; otherwise CAGR = (end/start)^(365/days) − 1, formula shown.

**F-042 Declared fill rule and non-trading-day shift** · PR-031 · 3 pts · Backlog
- Given fill rules close-of-N (default), next open, VWAP-of-N, limit-within-[low, high], Then the chosen rule is shown on the result.
- Given N = Sat 2026-10-17, Then N shifts to Mon 2026-10-19 and the shift is displayed.
- Given a limit price of 95,000 when that day's high is 94,800, Then it does not fill and says why (VN§4).

**F-043 Cash dividend event** · PR-032 · 3 pts · Backlog
- Given 100 shares held on the ex-date and a cash dividend of 2,000 VND/share, Then gross 200,000, tax 5 %
  10,000, **net 190,000 VND** credited on the pay date (not the ex-date).
- Given option "reinvest" and net cash 190,000 < one lot (100 × price), Then it stays as cash and the result says so.

**F-044 Stock dividend / bonus shares** · PR-032 · 3 pts · Backlog
- Given 100 shares, ratio 10:3, close before ex 93,500, Then 30 new shares count from the ex-date; adjusted
  reference = 93,500 × 10 / 13 = 71,923.08; value at ex reference = 130 × 71,923.08 ≈ 9,350,000 (continuity).
- Given 105 shares at 10:3 (31.5 new), Then fractional handling follows the rules module (default round down, `[verify]` VN§6).

**F-045 Rights issue: exercise or lapse** · PR-032, A10 · 3 pts · Backlog
- Given 100 shares, rights 10:2 at 10,000, close before ex 50,000, Then adjusted reference = (50,000 × 10 + 10,000 × 2) / 12 = 43,333.33.
- Given cash 635,975 ≥ 20 × 10,000 = 200,000 and default policy, Then exercise: cash 435,975, shares 120.
- Given cash 150,000 < 200,000, Then rights lapse and the result says so; the user can force "lapse" with enough cash.

**F-046 What-if vs adjusted-series agreement** · PR-032, G3 · 3 pts · Backlog
- Given 10 dividend-paying stocks over ≥ 3 years, When what-if total return (fractional, no lots/fees for this
  test) is compared with adjusted-series return, Then each differs by ≤ 0.05 %.

**F-047 Return breakdown: chart return vs real return** · PR-033 · 5 pts · Backlog
- Given F-040/F-041 (10,000,000 VND, 93,500 → 100,000), Then the breakdown shows, summing exactly to the real return:
  chart return 10,000,000 × 6,500 / 93,500 = **695,187.17** · lot/residual cash −45,187.17 · buy fee −14,025 ·
  sell fee −15,000 · sell tax −10,000 · dividends 0 · = **610,975 VND**.
- Given each term, Then "how computed" (F-051) shows formula and inputs.

**F-048 Benchmark on the same screen** · PR-034 · 3 pts · Backlog
- Given the same amount and dates, Then the result shows VN-Index (price-only, labelled "non-investable") and
  E1VFVN30 `[assumed]` with the same fee/lot model and ETF tick 10 VND (VN§3).

**F-049 Cash and share ledger** · PR-039, PR-134 · 3 pts · Backlog
- Given F-040/F-041, Then the ledger lists dated rows: buy −9,350,000; buy fee −14,025; shares +100 (arrive
  T+2); sale +10,000,000; sell fee −15,000; tax −10,000; cash settles T+2; final cash 10,610,975.
- Given "Export CSV", Then the file has the same rows and totals.

**F-050 Golden-case verification kit (≥ 20)** · PR-037, G3 · 5 pts · Backlog
- Given ≥ 20 hand-calculated cases (lots, fees, tax, T+2, cash dividend, bonus, rights, delisting), When tests
  run, Then each matches within 1 VND; F-040–F-045 examples are among them.
- Given the tester's independent calculator, Then it agrees with every case.

**F-051 "How computed" panel** · PR-110, G7 · 3 pts · Backlog
- Given any figure on an analysis screen, When expanded, Then it shows formula, inputs with values, data as-of
  time, rules version (F-023). A test asserts every figure has one.

**F-052 Glossary VN/EN** · PR-111 · 3 pts · Backlog
- Given a glossary term in the UI (trần, sàn, tham chiếu, GDKHQ, T+2, lô chẵn, phí, thuế, drawdown, Sharpe,
  walk-forward…), When clicked, Then the entry shows both languages regardless of UI language, citing VN§n or docs/04.

**F-053 What-if screen** · PR-030–034 · 5 pts · Backlog · UX spec written at R2 planning
- Given symbol, amount, date N, date M (default today), fill rule, dividend option, Then the result shows
  shares, cash, market value, total return (VND, %), CAGR, breakdown, benchmark, ledger, disclaimer.
- Given a symbol with no data on N, Then an empty/partial state explains the earliest available date.

### E8 Learning layer (R2 part)

**F-054 Exercise framework + L2 exercise** · PR-112 · 3 pts · Backlog
- Given the what-if screen, Then it offers the docs/04 L2 exercise ("chart return vs real return for 5
  high-dividend stocks") with a notes field saved locally and restored on reload.

---

## R3 — Price board (L1)

### E5 Board and charts

**F-060 Watchlist board** · PR-050 · 8 pts · Backlog
- Given the watchlist in session, Then each row shows reference/ceiling/floor, top-3 bid/ask with volumes, last
  price/volume, change and %, total volume/value, foreign buy/sell; median refresh ≤ 5 s (G6).
- Given HOSE reference 93,500 and last 100,000 (= ceiling), Then the price is purple **and** carries a "▲ CE" cue;
  floor cyan + "▼ FL"; reference yellow + "="; above green "▲"; below red "▼" (VN§3).

**F-061 Watchlist management** · PR-050, A5 · 2 pts · Backlog
- Given first start, Then the default watchlist has 30 symbols (A14/A15); the sponsor can add/remove up to 100; the 101st is refused with a message.
- Given the stored daily data, When the default is computed, Then it is the top 30 symbols by **average traded
  value** (shares × price, summed per session) over the last 20 sessions, all exchanges; e.g. a symbol trading
  2,000,000 shares/session at an illustrative 93,500 averages 187,000,000,000 VND/session. Decision time: close of
  the last of the 20 sessions.
- Given fewer than 20 sessions are stored, Then the average uses the sessions available and the screen says
  "based on N sessions"; with none stored, the VN30 basket is the stand-in.
- Given a week has passed since the last refresh, Then the default is recomputed weekly (as-of date shown);
  symbols the sponsor added or removed by hand stay as the sponsor set them.

**F-062 Freshness and session states** · PR-051 · 3 pts · Backlog
- Given a row older than 15 s during continuous session, Then a "stale" badge shows (100 %, G6); verified by cutting the source.
- Given phase from F-005, Then a banner shows ATO / continuous / break / ATC / closed / holiday; when closed it says "market closed, showing last session (date)".

**F-063 Indices panel** · PR-056 · 3 pts · Backlog
- Given VN-Index, VN30, HNX-Index, HNX30, UPCoM-Index, Then each shows level, change, breadth (up/down/unchanged, ceiling/floor counts) and total value.

**F-064 Daily candlestick chart** · PR-053 · 5 pts · Backlog
- Given a symbol, Then daily candles with volume, MA overlays, ex-date/corporate-event markers; a nominal/adjusted toggle explains the difference (F-015).

**F-065 1-minute chart with data boundary** · PR-053, C2 · 3 pts · Backlog
- Given 1m bars that start on date B, Then the chart marks "1-minute data from B" and does not draw earlier.

**F-066 1-minute bars: back-fill and daily crawl** · PR-014 · 3 pts · Backlog
- Given the source's 1m window, Then back-fill as far as allowed, then add each session (idempotent).

**F-067 1m vs tick reconciliation** · PR-014 · 2 pts · Backlog
- Given a session with ticks, Then 1m bars derived from ticks equal source 1m OHLCV; mismatches appear on the data-quality page.

**F-068 Order-book snapshots for the watchlist** · PR-015 · 3 pts · Backlog
- Given the session, Then top-3 bid/ask is sampled every 3–5 s for watchlist symbols only and stored with timestamps.

**F-069 Full-market snapshot board** · PR-052 · 5 pts · Backlog
- Given all symbols (A1), Then refresh every 30–60 s (A5) with sort/filter by exchange, sector, % change, volume, ceiling/floor hits, and add-to-watchlist.

**F-070 Session replay** · PR-054, C1 · 5 pts · Backlog
- Given a past session with ticks and snapshots, Then playback at 1×/10×/60×; sessions before crawl start or missed are listed as unavailable, not hidden.

**F-071 "Explain this row"** · PR-055 · 2 pts · Backlog
- Given reference 93,500 on HOSE, Then the overlay shows ceiling 100,000 / floor 87,000 with the inward rounding and "100 shares cost 9,350,000 + fee 14,025 = 9,364,025 VND".

**F-072 L1 exercise** · PR-112 · 1 pt · Backlog
- Given the board, Then the L1 exercise "explain the colour of 10 symbols" is offered with saved notes (F-054).

---

## R4 — Scenarios (L3, L4, L5)

### E6 Backtester

**F-080 One engine with `as_of` and a look-ahead test** · PR-071 · 5 pts · Backlog
- Decision time: a signal on day t uses only bars with timestamp ≤ close of t; fill at next open t+1 (default `[assumed]`) or same close.
- Given data after t is perturbed, Then the signal at t is unchanged (kernel test).
- Given the F-040/F-041 example run through the backtester, Then numbers equal the what-if (shared tests).

**F-081 Buy-and-hold and DCA** · PR-070 · 3 pts · Backlog
- Given DCA 2,000,000 VND on day 15 of each month into a symbol at a constant illustrative 93,500, Then months
  1–4 buy 0 shares (cash 2,000,000 … 8,000,000 < one lot incl. fee 9,364,025) and month 5 (cash 10,000,000)
  buys 100 shares, cash left 635,975.
- Given each strategy page, Then its rule is stated in VI and EN.

**F-082 MA crossover and breakout** · PR-070 · 3 pts · Backlog
- Given fast/slow MA parameters, Then a buy signal at the close of t where fast crosses above slow is filled at t+1 open; breakout = close > N-day high of the prior N days (excludes t).

**F-083 Stop-loss / take-profit / trailing overlays** · PR-070 · 3 pts · Backlog
- Given a stop at −8 % from entry 93,500, Then the trigger level is 86,020 and the exit fills by the declared rule, never outside [low, high].

**F-084 Comparison screen** · PR-072 · 5 pts · Backlog
- Given N scenarios × M symbols × one period, Then a table of total return, CAGR, max drawdown, Sharpe, trades, fees+tax, win rate, exposure, overlaid equity curves and a benchmark row.

**F-085 Walk-forward ranking with OOS column** · PR-073, G5 · 5 pts · Backlog
- Decision time: the ranking uses window W ending at close of t; the OOS column uses W' starting t+1.
- Given "best of last 7 sessions", Then each row shows the next-7-session result and the statement "in-sample rank ≠ future rank"; a ranking without OOS is not rendered (test).

**F-086 Rolling windows and rank stability** · PR-073 · 3 pts · Backlog
- Given k rolling windows, Then Spearman rank correlation between consecutive in-sample and OOS ranks is shown per window; the R4 documented example uses "best of last 7 days".

**F-087 Survivorship-controlled universe** · PR-075 · 3 pts · Backlog
- Given a start date, Then the universe = symbols listed that day (F-004), including later-delisted; a delisting forces an exit at the last price with a warning.

**F-088 Scenario journal** · PR-078, PR-133 · 3 pts · Backlog
- Given a saved run with parameters, data snapshot and note, When re-run, Then numbers are identical.

**F-089 Portfolio what-if** · PR-035 · 5 pts · Backlog
- Given 10,000,000 split 50/50 across two symbols, Then each leg buys whole lots independently, residual cash is shown per leg, and per-symbol contribution, pairwise correlation and drawdown vs single holdings are shown.

**F-090 Risk metrics** · PR-036, A11 · 3 pts · Backlog
- Given daily returns, Then annualised volatility, max drawdown and duration, Sharpe and time under water are
  shown with formulas; the risk-free rate is editable and defaults to **5 %/year** (A13); e.g. annualised return 12 %,
  volatility 20 % → Sharpe (12 % − 5 %) / 20 % = 0.35.

**F-091 Parameter sensitivity** · PR-074 · 3 pts · Backlog
- Given a parameter grid, Then a heatmap/table shows results and flags an optimum whose neighbours are worse by a stated threshold.

**F-092 CSV export** · PR-134 · 2 pts · Backlog
- Given any table or ledger, Then "Export CSV" produces the same rows and totals.

**F-093 L3/L4/L5 exercises** · PR-112 · 2 pts · Backlog
- Given the scenario screens, Then the docs/04 L3, L4, L5 exercises are offered with saved notes.

---

## R5 — Why it moved (L6)

### E7 Evidence view

**F-100 Market-structure data** · PR-018 · 5 pts · Backlog
- Given each session, Then foreign net buy/sell per symbol and market, proprietary flow `[assumed free source]`,
  index constituents/weights and ETF rebalance dates (manual calendar if no source) are stored with source and fetched-at.

**F-101 Return decomposition** · PR-090 · 5 pts · Backlog
- Decision time: window ends at close of t; beta is estimated on a window that ends before the analysed window starts.
- Given a 7-session return of +10 %, index +4 %, beta 1.2, sector residual +2 %, Then market = 4.8 %, sector 2.0 %, idiosyncratic 3.2 %, method and estimation window shown.

**F-102 Evidence panel** · PR-091 · 5 pts · Backlog
- Given the window, Then dated, sourced items: volume vs 20-day average, ceiling/floor hits, foreign and proprietary flow, ex-dates/events, earnings proximity, rebalance dates, order-book imbalance where snapshots exist.

**F-103 Honesty rules** · PR-093 · 2 pts · Backlog
- Given the view, Then its title is "Các yếu tố đi kèm / Co-occurring factors", each factor shows contribution ± uncertainty, the disclaimer is present, and a wording test rejects causal verbs (list owned by PM).

**F-104 Event study** · PR-094 · 3 pts · Backlog
- Given an event type, Then the average symbol and sector reaction t−5…t+5 is shown with sample size n.

**F-105 Daily market digest** · PR-095 · 3 pts · Backlog
- Given a closed session, Then top movers, breadth, flows, ceiling/floor counts and the day's events are generated from data (no LLM, A4).

**F-106 L6 exercise** · PR-112 · 1 pt · Backlog
- Given the view, Then "explain the 3 strongest sessions of the month with evidence" is offered with saved notes.

---

## R6 — Later (Deferred, rough points, refine after the R5 retro)

### E9 Later

| Story | PR | Pts | One-line acceptance |
|---|---|---|---|
| F-120 News headlines | PR-019 (A9) | 5 | Headline, time, URL, tagged symbols from terms-allowed RSS; no body, no summary |
| F-121 Headline timeline | PR-092 | 3 | Headlines aligned on the price chart, link only |
| F-122 Financial statements and ratios | PR-021 | 8 | Quarterly P/E, P/B, ROE, growth per symbol with as-of |
| F-123 Rule builder | PR-077 | 8 | Composable conditions run through the F-080 engine and look-ahead test |
| F-124 Paper-trading journal | PR-113 | 5 | Entry/exit rules, monthly self-review |
| F-125 Learning progress | PR-114 | 3 | L1–L8 with completed exercises |
| F-126 Odd-lot and cash-advance toggles | PR-038 | 3 | Default off; odd lot buys 1–99 shares (VN§4) |
| F-127 Trade-sequence bootstrap | PR-076 | 3 | Drawdown distribution, not one path |
| F-128 Backup to another disk | PR-136 | 3 | Restore tested once per release; F-021 notice clears |

---

## Traceability PR → F

| PR | Stories | PR | Stories | PR | Stories |
|---|---|---|---|---|---|
| 001 | F-001, F-002 | 033 | F-047 | 074 | F-091 |
| 002 | F-003 | 034 | F-048 | 075 | F-087 |
| 003 | F-004 | 035 | F-089 | 076 | F-127 |
| 004 | F-005 | 036 | F-090 | 077 | F-123 |
| 010 | F-012, F-013 | 037 | F-050 | 078 | F-088 |
| 011 | F-014 | 038 | F-126 | 090 | F-101 |
| 012 | F-015, F-016 | 039 | F-049 | 091 | F-102 |
| 013 | F-017, F-018 | 050 | F-060, F-061 | 092 | F-121 |
| 014 | F-066, F-067 | 051 | F-062 | 093 | F-103 |
| 015 | F-068 | 052 | F-069 | 094 | F-104 |
| 016 | F-010 | 053 | F-064, F-065 | 095 | F-105 |
| 017 | F-021, F-022 | 054 | F-070 | 110 | F-051 |
| 018 | F-100 | 055 | F-071 | 111 | F-052 |
| 019 | F-120 | 056 | F-063 | 112 | F-054, F-072, F-093, F-106 |
| 020 | F-019 | 070 | F-081, F-082, F-083 | 113 | F-124 |
| 021 | F-122 | 071 | F-080 | 114 | F-125 |
| 030 | F-040, F-041, F-053 | 072 | F-084 | 130 | F-032 |
| 031 | F-042 | 073 | F-085, F-086 | 131 | F-030 |
| 032 | F-043–F-046 | | | 132 | F-020, F-021 |
| | | | | 133 | F-023, F-088 |
| | | | | 134 | F-049, F-092 |
| | | | | 135 | F-011 |
| | | | | 136 | F-021 (notice), F-128 |
| | | | | 137 | F-002, F-031 |

## Open questions for the sponsor

Answered: A13–A15 (2026-10-15) — A13 risk-free default 5 %/year, editable (F-090); A14+A15 default watchlist =
top 30 by average traded value (shares × price), last 20 sessions, refreshed weekly, not VN30 (F-061, F-018).
