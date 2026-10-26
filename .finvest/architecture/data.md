# Finvest — Data design (sources, schemas, storage tiers, crawl schedule)

Owner: `fi-software-architect`. Status: **v1.6, 2026-10-26** (§1.2 S2 **10 VND resolution** + §1.4 recon slack for S2, from the BE-recon-s2 consult; v1.5 = `data.prev-6.md`; v1.5: §1.4 (4) source-version invariant: every row is divided by the G of its *own* version, from the BE-ca-recompute consult; §5 `adj_*` BIGINT note; v1.4 = `data.prev-5.md`; v1.4: S05 M0 spike: V5 field names + `toDate` rule, S2 re-probed, `bars_1d.ref`, `symbols.ca_checked_at`; v1.3 = `data.prev-4.md`; v1.3: V2 cap = 1 per S-v2-batch, 418 hold; v1.2 = `data.prev-3.md`; v1.2: V2 `accumulatedValue` mixed unit, S02 B2; v1.1 = `data.prev-1.md`). Units: all stored prices **VND integer**,
volumes **shares**, timestamps **TIMESTAMPTZ (UTC)**, trading dates **DATE in Asia/Ho_Chi_Minh**. Rules cited as VN§n
(`knowledge/vn-market.md`). Decisions: ADR-S-001 (storage), ADR-S-002 (sources), ADR-S-005 (money), ADR-S-008
(tick idempotence/manifest).

## 1. What the free sources actually provide — verified 2026-10-15

Method: live HTTP probes from the sponsor's Ubuntu machine (curl, personal user-agent) + reading the vnstock 4.x
adapter source on GitHub (the package is only a wrapper over these endpoints). Re-verify at every release; these are
unofficial broker endpoints (C6) and can change without notice.

### 1.1 The vnstock package (what the proposal assumed)

| Fact (2026-10-15) | Source |
|---|---|
| Current generation ("Gen 5", v4.0.8, 2026-09-15) is **pre-compiled, not open source**, installed from vnstock's own index (`--extra-index-url https://vnstocks.com/api/packages`); PyPI shows the project **quarantined** since 2026-09-24 ("cannot be installed… until a security review is complete"); `pip download vnstock` fails on this machine | pypi.org/project/vnstock, github.com/thinh-vu/vnstock README |
| Licence `license-2026.09`: custom, source-available; **Community tier free for personal/learning use**; needs account registration (`vnstock register`); grants **no rights to third-party data** | vnstocks.com/onboard/giay-phep-su-dung |
| Tiers: Guest 20 calls/min (no `trades()`), Community 60 calls/min (free registration), Sponsor 180–600 calls/min (paid) | PyPI page |
| Wrapper caps (Community): 1m history **180 days**, daily **2,920 days**, `trades()` **5,000 most recent per call, current session only**, order book / foreign flow / proprietary flow **Sponsor only** | vnstocks.com/docs/vnstock-data/du-lieu-giao-dich |

Conclusion: vnstock is **not** a dependency we can build on (compiled binary from a non-PyPI index, account bound,
caps far below what the underlying endpoints serve). We write our own thin adapters to the same public endpoints
(ADR-S-002) and keep the vnstock 4.x source only as reference documentation of those endpoints.

### 1.2 Endpoints probed (all anonymous, no key, no cookie)

| # | Source / endpoint | Serves | Grain, depth, units observed | Verdict |
|---|---|---|---|---|
| K1 | **KBS** `GET https://kbbuddywts.kbsec.com.vn/iis-server/investment/trade/history/{SYM}?page=1&limit=50000` | tick tape of the **current session** | whole day in **one call** (FPT 3,870 rows, HPG 5,107, SHB 10,892, VIX 5,339 on 2026-10-15); fields `t` "2026-10-15 14:45:08:16" (local, centiseconds), `FMP` price **VND**, `FV` match volume (shares), `FCV` price change, `AVO`/`AVA` accumulated volume/value, `LC` side (documented 'B'/'S', **observed empty** in sample → [verify] whether side is ever filled); response 0.2–0.5 s, 68 KB for 3,870 rows; `?date=` ignored → **no past sessions** | **Primary tick source** (R1) |
| V1 | **VCI** `POST https://trading.vietcap.com.vn/api/market-watch/LEData/getAll` `{"symbol","limit","truncTime"}` | tick tape, current session | **100 rows per call** regardless of `limit`; paging backwards with `truncTime`; fields `id` (seq), `truncTime` epoch s, `matchType` b/s/unknown, `matchPrice` VND, `matchVol`; a `truncTime` before today returns `[]` → **no past sessions** | Secondary tick source (watchlist only: ~100 calls/symbol/day) and the only one with trade side |
| V2 | **VCI** `POST https://trading.vietcap.com.vn/api/chart/OHLCChart/gap-chart` `{"timeFrame":"ONE_DAY"|"ONE_MINUTE"|"ONE_HOUR","symbols":[..],"to":epoch,"countBack":n}` | OHLCV history | **daily since 2006-12-13** (FPT 4,943 bars, VND, `v` shares); **1m since 2023-09-11** (FPT 172,520 bars ≈ 3 years); indices (`VNINDEX` since 2004-01-05, points); **one symbol per call** (spike S-v2-batch 2026-10-24: every multi-name body, 2–200 names, answered `200 []`; 1-name bodies answer; `BATCH_MAX = 1`, platform.md §2.6); the host holds ≈ 30 s then answers 418 after ≈ 60–70 calls in a few minutes (block detection: platform.md §4 v1.12); `accumulatedValue` is **nominal** matched value, **unit mixed per row** (S02 B2: VN30 2012-02-06 = 222,242,000,000 raw VND, 2026-10-16 = 6,386,472.73 million VND; rule in platform.md §4) — recent rows in **million VND** (fixture FPT 2026-08: 474,963.63 → 474,963,630,000 VND ÷ 6,618,016 shares = 71,768 ≈ adjusted close 65,000 × 1.1), `accumulatedVolume` = `v`. **Prices are source-adjusted** (FPT 2026-09-18 close 65,182.47 before the 10 % bonus ex-date 2026-09-21; integer VND after) | **Primary daily + 1m + index history** |
| V3 | **VCI** `GET https://trading.vietcap.com.vn/api/price/symbols/getAll` | symbol master | 3,683 rows: HSX 406 stocks + 21 ETF + 328 CW, HNX 299, UPCOM 815, **DELISTED 234 stocks** (kept → survivorship, PR-075), `icbCode2`, names VI/EN | **Primary symbol master** |
| V4 | **VCI** `POST …/api/price/symbols/getList` `{"symbols":[..]}` | board snapshot for a list | per symbol: `listingInfo` (ref/ceiling/floor, `isDelisted`, `listedShare`), `bidAsk` (3 levels), `matchPrice` (last, ATO/ATC, open/high/low, foreign buy/sell volume & value, total room), VND | **Watchlist board (R3)**: 1 call per refresh |
| V5 | **VCI IQ** `GET https://iq.vietcap.com.vn/api/iq-insight-service/v1/events?ticker=FPT&fromDate=YYYYMMDD&toDate=YYYYMMDD&eventCode=DIV,ISS&page=0&size=50` | corporate events | **Spike S05-M0 (2026-10-26, 4 calls, `sprints/sprint-05/spike/v5-call4.json`):** `toDate` is **required** (empty → HTTP 200 body `status 400, exception "Invalid datetime"`; `2026-01-01` form also 400) → always send `YYYYMMDD` both ends; answers in 0.16–0.24 s, gzip; page envelope `data.{content[], totalElements, totalPages, last}` (size 50 honoured; page 0-based). Fields per event: `id` (24-hex, source_event_id), `ticker`, `eventCode` DIV|ISS, `eventTitleVi/En`, `publicDate`, `recordDate`, `exrightDate`, `exerciseRatio`, `category`, cash only: **`valuePerShare`** (1000.0 = 1,000 VND) + **`payoutDate`**; share issues: `listingDate`. FPT 2026: DIV "Trả cổ tức bằng tiền mặt - Đợt 2 2025 - 1,000 VND" ex 2026-05-28 valuePerShare 1000 (exerciseRatio 0.1 = share of par 10,000, **not** a share ratio); ISS "Cổ phiếu thưởng tỉ lệ 10.0%" ex 2026-09-21 exerciseRatio 0.1 (bonus 10:1, the G12 case); ISS "Phát hành cho CBCNV tỉ lệ 0.5%" (ESOP, exerciseRatio 0.00499, listingDate 2029) — **no reference adjustment [assumed, ai-architect to confirm in VN§6]**. **Block behaviour: not observed in 4 calls at ≤ 1 req/s** (budget before a block unknown; same company as V2 whose host holds ≈ 30 s then 418s after ≈ 60–70 calls) → policy: bucket `vci_iq` 1 req/s, **B = 40 requests per press** (same as `GAP_MAX`), 3 blocked/held responses → `SourceBlocked` (fetch.py); raise B only after a press log shows ≥ 60 calls unblocked | **Primary corporate actions**; also `…/v1/sectors/icb-codes` for ICB names |
| S1 | **SSI iBoard** `GET https://iboard-query.ssi.com.vn/stock/exchange/{hose|hnx|upcom}` | full-market snapshot | 409 / 299 / 815 rows in **3 calls**; per row ref/ceiling/floor, open/high/low, matched price+vol, `nmTotalTradedQty/Value`, best 3 bid/ask, **foreign buy/sell qty & value**, `tradingUnit` 100, `parValue`, `corporateEvents`, `firstTradingDate`; VND; `exchangeSession` | **Full-market board (R3, 30–60 s)** and **after-close nominal daily bar + foreign flow for every symbol** |
| S2 | **SSI iBoard** `GET https://iboard-api.ssi.com.vn/statistics/charts/history?resolution=1D|1&symbol=FPT&from=&to=` | OHLCV history | daily since 2010-01-04 (4,183 bars), prices **thousand VND** (58 = 58,000), also source-adjusted; 1m only **~1 month** back (from 2026-09-14) and empty for ranges > ~30 days **Spike S05-M0 (1 call, HPG 2026-09-01→10-26, 0.42 s, `sprints/sprint-05/spike/s2-HPG-1D.json`):** same envelope as the FPT fixture (`code SUCCESS`, `data.{t,o,h,l,c,v}` thousand VND, **2 decimals → 10 VND resolution**: fixture `ssi/history/FPT-1d.json.gz` 2026-09-18 `c` = 65.18 = 65,180 VND where V2 stores 65,182 (65,182.47) → the S2 cross-check compares with `slack_vnd = 10`, never exact); block behaviour **not observed** in 1 call → VN30 cross-check = 30 calls at 1 req/s with the same 3-blocked stop; no earlier S2 block was ever seen (S03 fixture + this) | Cross-check source for daily (reconciliation, F-016) |
| B1 | **KBS** `…/investment/stocks/{SYM}/data_day|data_1P?from=DD-MM-YYYY&to=` | OHLCV | daily only **~3 months** (62 bars), adjusted; 1m **~3 sessions** | Not used for history |
| T1 | **TCBS** `apipubaws.tcbs.com.vn/...` (tick paging, bars, dividends) | — | every call answered by a **Cloudflare JS challenge** ("Just a moment…") → unusable from a script | Rejected |
| N1 | **VNDirect** `finfo-api.vndirect.com.vn/v4/stock_prices` (had nominal + adjusted close), `dchart-api…` | — | connection **timed out** / HTTP 406 | Rejected (re-probe in R1 spike; it would give observed nominal history) |
| C1 | **cafef** `s.cafef.vn/Ajax/PageNew/DataHistory/PriceHistory.ashx` | nominal + adjusted daily (web table) | "symbol is null or empty" with both param spellings → needs the page's exact query; HTML scraping territory | R1 spike only if nominal history before crawl start turns out to matter (see §1.4) |

Rate limits: **none published** by KBS/VCI/SSI; none hit during ~60 probe calls at ≤ 2 req/s. Policy (PR-135): token
bucket per source, defaults KBS 2 req/s, VCI 2 req/s, SSI 1 req/s, exponential backoff, **stop and record "source
blocked"** after 3 consecutive 429/403/HTML-challenge responses; every response archived (§3) so a re-run never
re-fetches what we already have. A full-market tick pass = ~1,600 KBS calls ≈ **15–30 min**; the evening window
(15:30 → next 09:00) is ample, so the priority order of F-018 only matters under throttling.

Licence/ToS for personal use: the endpoints are the brokers' own web-app APIs; no published API terms for third
parties were found. vnstock's licence explicitly disclaims data rights ("the user must determine the rules of each
source"). Treat as **unofficial, personal, read-only, rate-respecting** use (C6, PR-135) → sponsor question **A16**
in `system.md`.

### 1.3 Grain and depth we can promise (replaces VN§8 "[verify per source]" for these sources)

| Grain | Depth available at crawl start | Grows by |
|---|---|---|
| Ticks (all ~1,520 stocks + 21 ETFs) | **current session only** → store starts 2026-10 (C1) | one KBS pass per session |
| Order-book top 3 | live only (V4/S1 snapshots) | watchlist sampling in session (R3) |
| 1m bars | **~3 years** back (VCI), all symbols | daily VCI pass; also derived from ticks where present (F-067) |
| Daily OHLCV, source-adjusted | **2006/2010 →** (VCI/SSI) | after-close pass |
| Daily **nominal** OHLCV | **observed from crawl start** (S1 snapshot at close); earlier dates **reconstructed** (§1.4) | after-close pass |
| Foreign buy/sell per symbol per day | from crawl start (S1/V4 snapshot); earlier history **not found free** | after-close pass |
| Proprietary (tự doanh) flow | **not found free** (vnstock: Sponsor tier only) → PR-018 item open, **A17** | — |
| Corporate actions | ≥ 10 years (V5) | daily pass over symbols with `exrightDate ≥ today − 7d`, weekly full pass |
| Symbol master incl. delisted | full (V3) | daily pass |
| Trading calendar | manual table from VSE notice 1403/SGDVN-THHC (28/11/2025) for 2026: 01/01; Tết 16–20/02; 27/04 (Hùng Kings, in lieu); 30/04–01/05; 31/08–02/09 (make-up day Sat 22/08 is **not** a trading day for the exchanges [verify on hsx.vn]) | the sponsor/PM adds each year's notice; never inferred (PR-002) |

### 1.4 Nominal vs adjusted: the consequence for the model

Every free history endpoint re-adjusts the **whole** series on each ex-date (V2/B1 showed 65,182.47 for FPT
on 2026-09-18 after the 10 % bonus; S2 shows the same value at its 10 VND resolution, 65.18 thousand). Hence:

1. **Nominal is only observable live.** From crawl start we record the nominal daily bar from the closing snapshot
   (S1, 3 calls) → `bars_1d.nominal_kind = 'observed'`. For dates before crawl start we **reconstruct**
   `nominal = source_adjusted / cumulative_factor(after date)` using our own `adj_factors` (VN§6) →
   `nominal_kind = 'reconstructed'`; the what-if shows this flag (PR-110 "how computed") — sponsor question **A18**.
2. **Source-adjusted series are mutable.** Each fetch is stored as a versioned snapshot (`bars_1d_src.fetched_at`);
   a change in a past adjusted close between two fetches = evidence of a new corporate action → listed on the
   data-quality page (F-014 diff log, F-016 reconciliation).
3. **Reconciliation (PR-012)** = ours (`observed nominal` × our factors) vs the newest source-adjusted series, on the
   overlap from crawl start; before crawl start the check is self-consistency only (reconstructed × factors == source).
4. **A version is adjusted only as of its own last date.** A version = one fetch = one `fetched_at` per symbol (the
   archive file's mtime, `feeds/bars_1d.py`); `last_v` = its max `trading_date`. Step 2 pulls the full history once and then
   only the gap window (platform.md §2.6, min 5 sessions), so the "newest row per date" of a symbol is a **mix of versions**:
   old dates come from a fetch that predates later ex-dates. Therefore every consumer of `bars_1d_src` applies the factors
   of **that row's version**: `nominal(d) = A_v(d) / Π f_e` over `d < e ≤ last_v` (R6a in the S05 AI plan), never a
   single `last` for the whole series (S05 lead finding: a 2 % cash dividend made every pre-crawl row +2.04 % wrong).
   Assumed: the source applies an ex-date on that date, not the evening before (consistent with the FPT 2026-09-18 probe);
   the R7 exact-0 check on the newest version flags it if ever false (a mismatch streak starting at a version boundary).
   Exact-0 is a V2 rule (V2 carries 2-decimal VND); a source of coarser resolution passes its resolution as `slack_vnd`
   (S2: 10) and `|ours − theirs| ≤ slack_vnd` counts as equal in every branch — never a percentage, never for V2.
   The simulator basis reads `bars_1d` (observed + reconstructed) × our factors, not `bars_1d_src` (S05 BE-mv-basis).

## 2. Storage tiers (ADR-S-001: PostgreSQL 16 + TimescaleDB, one database `finvest`)

| Tier | Table | Engine | Retention / compression | Volume estimate |
|---|---|---|---|---|
| Raw archive | files `data/raw/<feed>/<YYYY-MM-DD>/<SYMBOL>.json.gz` (+ `_manifest.json`) | filesystem | keep everything (A12); gzip | ticks ≈ 10–20 MB/day (KBS ≈ 17 B/row before gzip, ~2–3 M rows/day market-wide) ≈ 3–5 GB/year |
| Ticks | `ticks` | hypertable, chunk 1 day, **compress after 1 day** (segment by symbol, order by ts) | keep everything | ≈ 60 B/row raw → ~150 MB/day → ~15–25 MB/day compressed ≈ 5–8 GB/year |
| 1m bars | `bars_1m` | hypertable, chunk 7 days, compress after 7 days | keep everything | ~1,500 symbols × 255 bars × 60 B ≈ 23 MB/day raw, ~3 MB compressed; back-fill 3 y ≈ 2–3 GB compressed |
| Daily | `bars_1d`, `bars_1d_src`, `flows_1d` | plain tables | keep | < 300 MB total incl. 20 y history |
| Reference | `symbols`, `symbol_index_membership`, `trading_calendar`, `corporate_actions`, `corporate_action_log`, `adj_factors`, `icb_sectors` | plain | keep | tiny |
| Ops | `crawl_runs`, `crawl_sessions` (manifests), `source_health`, `data_anomalies`, `recon_mismatches`, `jobs` | plain | keep | small |
| Results (R2+) | `sim_runs`, `backtest_runs`, `scenario_journal` | plain, JSONB params/result | keep | small |

Docker volume for Postgres lives at `finance_invest/data/pg/` (bind mount); raw archive at `finance_invest/data/raw/`;
both git-ignored (F-020). Storage per feed for the data-quality page = `pg_total_relation_size()` +
`du` of the raw folder, computed by the API on request and cached 5 min.

## 3. Schemas (DDL sketch; migrations in `apps/api/migrations/` via Alembic)

```sql
-- reference ------------------------------------------------------------
symbols(symbol TEXT PK, exchange TEXT CHECK (exchange IN ('HOSE','HNX','UPCOM')), type TEXT /*STOCK|ETF*/,
        name_vi TEXT, name_en TEXT, icb_code2 TEXT, listed_at DATE, delisted_at DATE, is_delisted BOOL,
        source TEXT, fetched_at TIMESTAMPTZ, ca_checked_at TIMESTAMPTZ /*S05: last V5 read; press order = VN30, scenario symbols, then NULLS FIRST oldest*/);
symbol_index_membership(index_code TEXT, symbol TEXT, valid_from DATE, valid_to DATE, PK(index_code,symbol,valid_from));
trading_calendar(trading_date DATE, venue TEXT, is_open BOOL, kind TEXT /*trading|weekend|holiday|half*/,
        name TEXT, source TEXT, PK(trading_date,venue));
icb_sectors(icb_code TEXT PK, level INT, name_vi TEXT, name_en TEXT);

-- prices ----------------------------------------------------------------
ticks(symbol TEXT, ts TIMESTAMPTZ, seq BIGINT /*accumulated volume after this trade (KBS AVO) — unique & monotonic per day*/,
      price BIGINT /*VND*/, volume BIGINT, side CHAR(1) /*B|S|NULL*/, source TEXT, PK(symbol,ts,seq));
bars_1m(symbol TEXT, ts TIMESTAMPTZ /*bar open, UTC*/, o BIGINT,h BIGINT,l BIGINT,c BIGINT, v BIGINT, value BIGINT,
      source TEXT /*vci|derived_ticks*/, PK(symbol,ts,source));
bars_1d(symbol TEXT, trading_date DATE, o,h,l,c BIGINT /*nominal VND*/, ref BIGINT /*S1 refPrice on the ex-date = exchange reference, R8 check; NULL when reconstructed*/,
      ceiling BIGINT, floor BIGINT, v BIGINT, value BIGINT, nominal_kind TEXT CHECK (nominal_kind IN ('observed','reconstructed')),
      source TEXT /*ssi|vci*/, fetched_at TIMESTAMPTZ, PK(symbol,trading_date));   -- S05 migration 0010: the S1 board bar moves here from bars_1d_src (nominal, never adjusted); an observed row is never overwritten by a reconstruction
bars_1d_src(symbol TEXT, trading_date DATE, source TEXT, adj_c BIGINT, adj_o,adj_h,adj_l BIGINT, v BIGINT, value BIGINT /*nominal VND, V2 accumulatedValue×1e6*/,
      fetched_at TIMESTAMPTZ, PK(symbol,trading_date,source,fetched_at));      -- versioned source-adjusted series; one fetched_at = one version, adjusted as of its own max trading_date (§1.4 (4)); adj_* BIGINT drops the source's 2 dp (≤ 0.5 VND, inside A18-A ± 1 tick; §5)
index_1d(index_code TEXT, trading_date DATE, o,h,l,c NUMERIC(12,2), v BIGINT, value BIGINT, PK(index_code,trading_date));
-- user data (S03) ------------------------------------------------------
scenarios(id BIGINT GENERATED ALWAYS AS IDENTITY PK, name TEXT NOT NULL CHECK (length(name) BETWEEN 1 AND 60), symbol TEXT NOT NULL,
      style TEXT NOT NULL CHECK (style IN ('lump_sum','dca')), amount_vnd BIGINT NOT NULL CHECK (amount_vnd > 0),
      buy_date DATE NOT NULL, sell_date DATE /*NULL = latest bar*/, created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL);
      -- saved what-if inputs only (platform.md §2.5); results are recomputed on read. R4 journal = scenario_journal.
flows_1d(symbol TEXT, trading_date DATE, foreign_buy_v BIGINT, foreign_sell_v BIGINT, foreign_buy_value BIGINT,
      foreign_sell_value BIGINT, total_room BIGINT, current_room BIGINT, source TEXT, PK(symbol,trading_date));

-- corporate actions (VN§6) ----------------------------------------------
corporate_actions(id BIGSERIAL PK, symbol TEXT, type TEXT /*cash_dividend|stock_dividend|rights|split|merge|listing_change*/,
      ex_date DATE, record_date DATE, pay_date DATE, ratio_a INT, ratio_b INT, cash_per_share BIGINT /*VND*/,
      issue_price BIGINT, source TEXT, source_event_id TEXT, fetched_at TIMESTAMPTZ, UNIQUE(source,source_event_id));
corporate_action_log(id BIGSERIAL, ca_id BIGINT, changed_at TIMESTAMPTZ, field TEXT, old TEXT, new TEXT);
adj_factors(symbol TEXT, ex_date DATE, factor NUMERIC(20,12), ca_id BIGINT, rules_version TEXT, PK(symbol,ex_date));

-- operations -------------------------------------------------------------
crawl_runs(id BIGSERIAL PK, feed TEXT, trading_date DATE, started_at, finished_at TIMESTAMPTZ, status TEXT
      /*ok|partial|failed|blocked|missed*/, reason TEXT, requests INT, rows BIGINT, manifest_path TEXT);
crawl_sessions(feed TEXT, trading_date DATE, status TEXT, symbols_fetched INT, symbols_no_trades INT /*S02-1*/, symbols_skipped INT, rows BIGINT,
      checksum TEXT, reason TEXT, PK(feed,trading_date));                     -- one row per (feed, session) = the gap list
source_health(source TEXT PK, last_ok TIMESTAMPTZ, last_error TIMESTAMPTZ, consecutive_errors INT, blocked_since TIMESTAMPTZ);
data_anomalies(id BIGSERIAL, symbol TEXT, trading_date DATE, rule TEXT, value TEXT, detected_at TIMESTAMPTZ, resolved_at TIMESTAMPTZ);
recon_mismatches(symbol TEXT, trading_date DATE, ours BIGINT, theirs BIGINT, diff_pct NUMERIC(8,4), checked_at TIMESTAMPTZ, PK(symbol,trading_date));
jobs(id BIGSERIAL, kind TEXT, args JSONB, status TEXT /*queued|running|done|failed*/, created_at, finished_at TIMESTAMPTZ, log TEXT);
```

Idempotence: every write is `INSERT … ON CONFLICT DO UPDATE` on the natural key; re-crawling a session produces the
same rows and the same manifest checksum (F-017). Unit conversion happens **only** in adapters (F-010); the domain
never sees thousand VND.

## 4. Feeds and crawl schedule (Asia/Ho_Chi_Minh; systemd user timers, ADR-S-009)

| Feed | Source | When | Calls | Writes |
|---|---|---|---|---|
| `symbols` | V3 (+V5 icb names) | 15:20 daily, before the others | 2 | `symbols`, `icb_sectors`; disappeared symbols get `delisted_at` |
| `close_snapshot` | S1 | 15:30 daily (retry 20:00) | 3 | `bars_1d` (observed nominal), `flows_1d`, index breadth |
| `ticks` | K1 (fallback V1 for watchlist) | 15:35 daily (retry 20:00); order watchlist → VN30 → HOSE → HNX → UPCoM | ~1,600 | raw archive, `ticks`, `crawl_sessions` manifest |
| `bars_1m` | V2 ONE_MINUTE | 16:30 daily; one-time back-fill (3 y) in R3 | ~1,600 (several symbols/call → fewer) | `bars_1m` source=vci |
| `bars_1d_src` | V2 ONE_DAY (+S2 cross-check for VN30) | 16:45 daily; back-fill once in R1 | ~200 (batched symbols) | `bars_1d_src`, reconstructed `bars_1d` for pre-crawl dates |
| `corporate_actions` | V5 | 17:00 daily (symbols with events in ±7 d) + Sunday full pass | 50–1,600 | `corporate_actions`, `_log`, recompute `adj_factors` |
| `recon` | local | after `bars_1d_src` | 0 | `recon_mismatches`, `data_anomalies` |
| `board_watchlist` (R3) | V4 | in session, every 3 s, watchlist ≤ 100 symbols | 1 per tick | in-memory latest + `orderbook_snapshots` (PR-015, 3–5 s) |
| `board_market` (R3) | S1 | in session, every 45 s | 3 | in-memory latest |

Catch-up at boot (`Persistent=true`): for every trading day since the last `crawl_sessions` row, run `ticks` once;
K1 serves only the current session, so a past day is recorded as `missed: machine off / source no longer serves`
(F-019). Non-trading days per `trading_calendar` → the job exits immediately with `kind=holiday`.

## 5. Open items for R1 spikes (technical, not sponsor)

- K1 `LC` side field: confirm whether it is filled in-session (sample at 10:00) or always empty; else side comes
  from V1 for the watchlist only and `ticks.side` is NULL elsewhere.
- ~~V5 field names for pay date and cash per share~~ resolved 2026-10-26 (`payoutDate`, `valuePerShare`, §1.2 V5); the title fallback is needed only for rights issue prices.
- Index symbol names on V2 for HNX-Index/HNX30/UPCoM-Index (`VNINDEX`, `VN30` confirmed).
- `bars_1d_src.adj_*` is BIGINT while V2 carries 2 decimals (FPT 65,182.47): each reconstructed row loses ≤ 0.5 VND
  before the division by G (≤ 0.55 VND at G = 0.909; G12 gives 71,700 vs 71,700.47). Inside A18-A's stated ± 1 tick,
  so not changed in S05; candidate migration 0011 `NUMERIC(14,2)` + adapter when R7 wants sub-VND exactness.
- Re-probe N1 (VNDirect) and C1 (cafef) for observed nominal history; if either works, `nominal_kind='observed'`
  can cover history too (A18 then disappears).
