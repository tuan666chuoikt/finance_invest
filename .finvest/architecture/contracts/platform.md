# Finvest — Platform contracts (REST, realtime, crawler → DB)

Owner: `fi-software-architect`. Status: **v1.15, 2026-10-26 S05 BE-ca-recompute consult** (§2.6 recompute set = watermark on `fetched_at`, `reason` adds `, <k> skipped`; v1.14 = `platform.prev-15.md`; v1.14: §2.6 step 3 corporate actions, `symbols_deferred`, `/health.rules_version`; v1.13 = `platform.prev-14.md`; v1.13: §4 wording: `missed` never overwrites `partial`/`complete`, ledger row = richest manifest; v1.12 = `platform.prev-13.md`; v1.12: §2.6 step 2 = indices + S1 snapshot + capped gap fetch, target session, blocked rules and message; §4 live `bars_1d` ledger row, `deferred` skip, ledger repair; v1.11 = `platform.prev-12.md`; v1.11: §2.6 batch cap = `BATCH_MAX`; v1.10: §2.5 `message` wording for `POST /whatif` errors, §2.6 step 2 indices first + batched symbols) — R1 endpoints are normative; R2–R5 sections are shape
previews the owning architect refines at sprint planning. Any deviation found in a PR is a blocker until this file
is updated (CLAUDE.md). The API exports `openapi.json`; TS types are generated from it (codebase.md §6).

## 1. Conventions

### 1.1 Base, versioning, auth
Base URL `http://127.0.0.1:8000/api`. No version prefix in v1 (single user); breaking changes bump `X-Finvest-Api: 1`
→ `2` and this file. No authentication `[assumed, PR-131]`. CORS allows only `http://127.0.0.1:5173` (dev).

### 1.2 Units, time, numbers
- Prices and money: **integer VND** (`58000`), never thousand VND, never floats. Index levels: decimal string
  `"1698.35"`. Ratios/percentages: decimal **strings** (`"0.204"` = 0.204 %) so no float ever crosses the wire.
- Volumes: integer shares. Values: integer VND.
- Timestamps: ISO-8601 with offset in **Asia/Ho_Chi_Minh**: `"2026-10-15T14:45:08.160+07:00"`. Dates: `"2026-10-15"`.
- Every payload that carries data has `as_of` (ISO timestamp, max `fetched_at` of its inputs) and, for computed
  results (R2+), `data_snapshot` + `rules_version`.
- Lists are paginated with `?limit=` (default 100, max 1000) and `?cursor=` (opaque); response has `next_cursor | null`.
- Field names `snake_case`; enums are lower-case strings.

### 1.3 Error envelope
```json
{ "error": { "code": "NOT_TRADING_DAY", "message": "2026-10-18 is a Saturday", "details": {"date": "2026-10-18"} } }
```
HTTP → code: 400 `VALIDATION` · 404 `NOT_FOUND` · 409 `JOB_RUNNING` · 422 `NOT_TRADING_DAY`, `SYMBOL_UNKNOWN`,
`RANGE_TOO_LARGE` · 503 `DB_UNAVAILABLE`, `SOURCE_BLOCKED` · 500 `INTERNAL` (no stack trace in body).
Messages are English; the web maps `code` to EN/VI text (i18n key `error.<code>`).

### 1.4 Session object (embedded wherever freshness matters)
```json
{ "venue": "HOSE", "phase": "continuous", "trading_date": "2026-10-15", "is_trading_day": true,
  "holiday_name": null, "server_time": "2026-10-15T10:02:11+07:00" }
```
`phase ∈ pre_open | ato | continuous | break | atc | post_close | closed | holiday | weekend` (F-005).

## 2. R1 endpoints (normative)

| Method, path | Purpose | Story |
|---|---|---|
| `GET /health` | `{status:"ok", db:"ok", version, rules_version}`; 503 `DB_UNAVAILABLE` otherwise | F-030 |
| `GET /session?venue=HOSE&at=` | session object (§1.4) for `at` (default now) | F-005 |
| `GET /calendar?from=&to=&venue=` | `[{trading_date, venue, is_open, kind, name}]` | F-003 |
| `GET /rules?venue=&group=&unverified=true` | §2.1 | F-001, F-002 |
| `GET /rules/example?venue=HOSE&ref_price=93500` | `{ceiling:100000, floor:87000, band:"7", tick:100}` live from the module | F-002 |
| `GET /symbols?exchange=&type=&include_delisted=false&q=` | `[{symbol, exchange, type, name_vi, name_en, icb_code2, icb_name_vi, listed_at, delisted_at}]` | F-004 |
| `GET /symbols/{symbol}` | one record + `index_memberships:[{index_code, valid_from, valid_to}]` | F-004 |
| `GET /bars/1d?symbol=&from=&to=&series=nominal|adjusted` | §2.2 | F-012, F-015 |
| `GET /corporate-actions?symbol=&from=&to=` | `[{id, symbol, type, ex_date, record_date, pay_date, ratio_a, ratio_b, cash_per_share, issue_price, source, fetched_at}]` | F-014 |
| `GET /corporate-actions/log?symbol=&since=` | `[{ca_id, changed_at, field, old, new}]` | F-014 |
| `GET /data-quality/summary` | §2.3 | F-021 |
| `GET /data-quality/feeds` | §2.3 | F-021 |
| `GET /data-quality/sessions?feed=ticks&month=2026-10` | §2.4 tick calendar | F-021 |
| `GET /data-quality/sessions/{feed}/{date}` | the manifest (§4) | F-017 |
| `GET /data-quality/gaps?feed=` | `[{trading_date, feed, status, reason}]` with `status ∈ missed|partial|blocked|failed` | F-021 |
| `GET /data-quality/mismatches?symbol=&from=` | `[{symbol, trading_date, ours, theirs, diff_pct, checked_at}]` (diff_pct > "0.1" only) | F-016 |
| `GET /data-quality/anomalies?rule=&symbol=&open=true` | `[{id, symbol, trading_date, rule, value, detected_at, resolved_at}]`; `rule ∈ outside_band|zero_volume_trading_day|duplicate_tick|bar_mismatch_1m` | F-022 |
| `POST /jobs` | §2.6 (v1.8: body `{kind:"crawl"}` only; the server picks the dates) | F-034 |
| `GET /jobs/current` · `GET /jobs/{id}` | §2.6 Job object | F-034 |

### 2.1 Rules payload
```json
{ "rules_version": "2026.10.15-3", "generated_at": "2026-10-15T09:00:00+07:00", "counts": {"verified": 18, "unverified": 9},
  "rules": [ { "key": "hose.band.stock", "group": "bands", "venue": "HOSE", "value": "7", "unit": "pct",
               "effective_from": "2010-01-01", "verified": false, "verified_at": null, "verified_source": null,
               "source_section": "VN§3", "history": [ {"value": "5", "effective_from": "2008-01-01", "effective_to": "2009-12-31"} ] } ] }
```
Units: `pct` (decimal string), `vnd`, `shares`, `time_range` (`"09:00–09:15"`), `days` (T+2 → `"2"`).

### 2.2 Daily bars payload
```json
{ "symbol": "FPT", "series": "nominal", "as_of": "2026-10-15T15:31:02+07:00",
  "bars": [ { "trading_date": "2026-10-15", "o": 57500, "h": 58200, "l": 57300, "c": 58000, "v": 4964400,
              "value": 287054530000, "ref_price": 57100, "ceiling": 61000, "floor": 53200,
              "nominal_kind": "observed" } ] }
```
`series=adjusted` returns Finvest's adjusted series (integers, rounded half-up to 1 VND) with `factors:[{ex_date,
factor, ca_id}]` and `nominal_kind` omitted. `RANGE_TOO_LARGE` above 30 years. Missing trading days are **absent
rows**, never zero bars.

### 2.3 Data-quality summary and feeds
```json
{ "as_of": "...", "daily_coverage_pct": "99.7", "daily_coverage_target_pct": "99.5",
  "tick_completeness": {"pct": "85.0", "complete": 17, "sessions": 20, "since": "2026-10-20"},
  "mismatches": 3, "anomalies_open": 12, "storage_bytes": {"total": 4500000000, "by_feed": {"ticks": 412000000, "raw": 220000000, "bars_1m": 0, "bars_1d": 31000000}},
  "backup": {"configured": false}, "last_success": {"ticks": "2026-10-15T15:52:00+07:00", "...": "..."},
  "sessions_since_last_success": 0 }
```
`GET /data-quality/feeds` → `[{feed, source, status, last_success, sessions_covered, completeness_pct, storage_bytes,
blocked_since}]`, `status ∈ ok | partial | failed | blocked | never`.

### 2.4 Tick sessions calendar
`[{trading_date, kind:"trading"|"weekend"|"holiday", holiday_name, status:"complete"|"partial"|"missed"|"pending"|null,
symbols_skipped, reason}]` for every day of the month; `pending` = trading day not yet crawled (today before 15:30).

### 2.5 S03 endpoints (normative; F-031, F-055, F-056, F-040…F-057)
The web calls the API **same-origin** at `/api` (Vite dev proxy `/api → 127.0.0.1:8000`; prod nginx on `127.0.0.1:8080`
proxies `/api/` to `api:8000`), so §1.1 CORS stays as is and nothing new binds beyond loopback (A23 pending).

| Method, path | Purpose | Story |
|---|---|---|
| `GET /symbols?q=&limit=20&include_delisted=false` | `[{symbol, exchange, type, name_vi, name_en, delisted_at}]`; `q` matches symbol prefix (case-insensitive) or name substring; the row whose `symbol` equals `upper(q)` comes first, the rest symbol asc (LIVE-03 L2) | F-055 form combobox |
| `GET /symbols/{symbol}` | the record + `bars_1d: {first: "2006-12-13", last: "2026-10-17", as_of} \| null` (no bars → `null`); unknown → 404 `NOT_FOUND`. `index_memberships` deferred (F-004 rest) | F-055 form limits |
| `GET /bars/1d/status` | `{last_trading_date: "2026-10-17" \| null, as_of: ISO \| null, source: "vci", symbols: 1612}` over `bars_1d_src` (`max(trading_date)`, `max(fetched_at)`, `count(distinct symbol)`); empty table → nulls and `symbols: 0` → web "No bars yet" state | F-031 chip, F-056 |
| `GET /scenarios` | `[Scenario]` newest first (`created_at desc`), no pagination in S03 (≤ 100 rows, F-055) | F-055 |
| `POST /scenarios` body `ScenarioIn` | 201 `Scenario` | F-055 |
| `PUT /scenarios/{id}` body `ScenarioIn` | 200 `Scenario` (full replace; `updated_at` set); unknown → 404 | F-055 |
| `DELETE /scenarios/{id}` | 204; unknown → 404 | F-055 |
| `POST /whatif` body = analytics.md §2.1 request + §2.4 additions | analytics.md §1.4 envelope; errors below | F-040, F-041, F-057, F-048, F-051 |

```json
ScenarioIn: { "name": "FPT · 10.000.000 ₫ · 12/10/2025", "symbol": "FPT", "style": "lump_sum",
              "amount_vnd": 10000000, "buy_date": "2025-10-12", "sell_date": null }
Scenario:   { "id": 7, …ScenarioIn, "created_at": "2026-10-19T09:00:00+07:00", "updated_at": "2026-10-19T09:00:00+07:00" }
```
- `ScenarioIn` validation (400 `VALIDATION`, `details.field`): `name` 1–60 chars (the web fills the default); `symbol` 1–12
  chars, upper-cased by the server; `style ∈ lump_sum | dca`; `amount_vnd` integer `1 … 100_000_000_000` (UX form); `buy_date`
  a date; `sell_date` null or `≥ buy_date`. `symbol` not in `symbols` (delisted allowed) → 422 `SYMBOL_UNKNOWN`.
  v1.8 (RW-U4): `buy_date` earlier than the symbol's first stored bar in `bars_1d_src` → 422 `NO_DATA`,
  `details {field:"buy_date", symbol, first_available:"2025-01-02"}` — the same code/details `POST /whatif` returns, so the
  web shows one message ("No FPT data before 02/01/2025") on the form field and on an already-saved card. A symbol with no
  bars at all is **not** refused on save (it becomes computable after a back-fill); other date limits stay unenforced.
- The web computes each saved scenario with one `POST /whatif` per row (`sell_date: null` → latest bar); a failing row
  shows its own error card (UX scenario-dashboard.md "Error (one scenario fails)"). No stored results in S03; the
  R4 journal (analytics.md §4) is a different table.
- `POST /whatif` error mapping (adds to §1.3): `AnalyticsError.code` → `VALIDATION` 400 · `SYMBOL_UNKNOWN`, `NO_DATA`,
  `RANGE_TOO_LARGE` 422; `details` passed through (`first_available`, `last_available`, `min_amount`); v1.10: `message` is
  human-readable, built from `details` — `NO_DATA` "no data for {symbol} before {first_available}", `SYMBOL_UNKNOWN`
  "unknown symbol {symbol}", `RANGE_TOO_LARGE` "range too large: {first_available} to {last_available}", the bare code when
  a key is missing. In the result,
  `benchmarks[].first_available` is `string | null` — **null when the benchmark has no bars at all** (live: VNINDEX empty,
  4-test.fe U1); the web renders "n/a" without a date and never crashes (analytics.md §2.4 mirrors this). Calendar years
  outside `finvest_rules` `holidays.csv` are served from VNINDEX bar dates (data.md §1.2 V2), never refused.
- `scenarios` table: data.md §3 (`id BIGINT identity PK, name, symbol, style, amount_vnd BIGINT, buy_date, sell_date,
  created_at, updated_at`), migration `0006_scenarios`.

### 2.6 Manual crawl job (normative v1.8; F-034, A23 — nothing crawls unless this job or the CLI runs)

Routes live in the api process; the crawl runs as a **background thread inside the api container** (same image as the
crawler, `./data` mounted at `/app/data`). One job at a time, enforced by a process-level lock **and** the `jobs` row.
- `POST /jobs` body `{"kind":"crawl"}` → **202** Job (`status:"running"`). While a `crawl` job is `running` → **409**
  `{error:{code:"JOB_RUNNING", message, details:{id, started_at}}}`. Any other `kind` → 400 `VALIDATION`.
- `GET /jobs/current` → the newest `crawl` job of any status, or **404** `NOT_FOUND` if none ever ran (the web reads this
  on load: running → resume the Running state; done/failed → the last-run tooltip / status line).
- `GET /jobs/{id}` → Job; 404 `NOT_FOUND`.
- Job object (`jobs` table, data.md §3, + `progress`, `summary` JSONB):
```json
{ "id": 12, "kind": "crawl", "status": "running",            // running | done | failed
  "created_at": "2026-10-26T16:10:03+07:00", "finished_at": null,
  "progress": { "step": 1, "steps": 2, "label": "ticks", "trading_date": "2026-10-26", "done": 12, "total": 30 },
  "summary": null, "error": null }
```
  Finished: `summary = { "ticks": {"trading_date", "status", "symbols_fetched", "rows", "symbols_skipped", "partial_until"} | null,
  "bars_1d": {"sessions_added", "symbols_fetched", "symbols_skipped"}, "no_session_today": bool, "duration_s": 221 }`.
  `symbols_skipped` is a count (v1.9). `sessions_added` is not in any manifest: it is
  `COUNT(DISTINCT trading_date)` of `bars_1d_src` after step 2 minus the same count before it (v1.9);
  failed: `error = {"code": "PermissionError" | "SourceBlocked" | "HTTPError" | …, "message", "path"?, "source"?, "http_status"?}`
  (always the cause **and** the path or source, UX app-shell.md §Crawl button) and `summary` keeps whatever steps finished.
- What the job does (VN time): step 1 — if today is a trading day (`finvest_rules` calendar, VN§sessions) run
  `run_ticks(today)`; before 15:00 the manifest is `partial` (platform.md §4) and `summary.ticks.partial_until` = now; a
  non-trading day skips step 1 and sets `no_session_today: true`. Step 2 — `run_bars_1d(today, count = trading days since the
  older of the two table maxima MAX(trading_date) of `bars_1d_src` and `index_1d` + 2, min 5; an empty table is ignored,
  `COUNT` only when both are empty — v1.9)`: catches up daily bars for every symbol and index (F-012 resume
  semantics, idempotent upserts). v1.10: step 2 fetches the **indices first, always with the full `COUNT` history** (2
  requests; an empty `index_1d` heals on any press), then the symbols in **batches** of `max(1, min(BATCH_MAX, 50_000 // count))`
  names per V2 request (one request failing marks that batch `skipped`, the run goes on; `source_blocked` stops it —
  v1.11: HTTP 418 counts as blocked). `BATCH_MAX` = the cap spike S-v2-batch records (data.md §1.2 V2); 50 → a normal
  press ≈ 40 requests, an empty-table back-fill ≈ 220; 1 → ≈ 1 780 requests ≈ 15 min at 2 req/s. Both resumable from the archive. A `CatchupFailed`-style partial result is `failed` with the error of the raising step.
  **v1.12 (supersedes the per-name catch-up above):** step 2 runs on the **target session** = the last trading day whose
  close has passed (`now ≥ 15:05 VN`, else the previous trading day; `progress.trading_date` and the `bars_1d` ledger row
  carry it). Units, in order, each committed: (1) indices with `COUNT` (2 V2 requests); (2) the **S1 full-market snapshot**
  (data.md §1.2 S1: 3 SSI requests, 1 req/s bucket) → one `source = ssi` bar per listed name that traded, no-trade names
  recorded, used only when the board's `tradingDate` equals the target (otherwise dropped, logged, nothing marked);
  (3) **gaps**: names not covered by (2) whose newest bar is older than the target, oldest first, `GAP_MAX = 40` names per
  press via V2 (batches as above); the rest are skipped `deferred` (status `partial`) and taken by the next presses. A
  catch-up press (`count < COUNT`) excludes delisted names; a full back-fill (`make backfill`, no cap) includes them.
  Normal press ≈ 5–45 requests. **Blocked**: a timeout counts as a blocked response in the fetcher (3 consecutive → `SourceBlocked`);
  3 consecutive skipped units (any reason, `FAIL_RUN`) end the run `blocked`; no request follows; the job is `failed`,
  `error.code = "SourceBlocked"`, `error.message = "nguồn <source> đang chặn tạm, thử lại sau ~1 giờ"`, `http_status` 0 = timed out.
- Progress: `done/total` are symbols in step 1 and names in step 2 (advanced per batch); the runner updates the row at most every 2 s.
  **v1.14 (S05, F-013/F-014/F-023):** `progress.steps = 3`; step 3 `label = "corporate_actions"`, `done/total` = symbols read
  this press. `summary.bars_1d` gains `symbols_deferred` (count of names skipped `deferred` by `GAP_MAX`). New
  `summary.corporate_actions = {"status": "ok"|"partial"|"blocked", "symbols_checked", "events_upserted", "changes",
  "symbols_deferred"} | null` (null when step 3 did not start): `changes` = `corporate_action_log` rows written this press,
  `symbols_deferred` = listed names not read this press (budget B = 40 requests, data.md §1.2 V5; order VN30 → saved-scenario
  symbols → `symbols.ca_checked_at` NULLS FIRST, oldest first). Step 3 runs after step 2 even when step 2 ended `partial`; a
  blocked step 3 → job `failed`, `error.code = "SourceBlocked"`, `error.source = "vci_iq"`, `summary` keeps steps 1–2 and the
  partial step 3 counts. After step 3, the **recompute set** = `changed_symbols` ∪ every symbol whose newest `bars_1d_src`
  (vci) `fetched_at` is newer than its newest `reconstructed` `bars_1d.fetched_at` (or that has no reconstructed row), restricted
  to `symbols.ca_checked_at IS NOT NULL` (the rest are *skipped*); a watermark, not "this press", so a replay, a blocked step 2
  or a failed step 3 heal on the next press. Factors and reconstructed `bars_1d` rows are recomputed in the same job (F-015;
  0 requests; `crawl_runs` feed `corporate_actions` carries `rows` = events, `reason` = "recompute: <n> symbols, <k> skipped";
  v1.15 — a prior `reason` is kept: "<prior>; recompute: …"). `GET /api/health.rules_version` = `finvest_rules.costs.RULES_VERSION` (string, never null).
  After the recompute the job runs the local reconciliation (F-016, 0 requests) on VN30 + saved-scenario symbols and sets
  `summary.recon = {"symbols", "checked", "mismatches"} | null` (null when step 3 did not run).
- Crash safety: on api start-up every `running` job is set `failed`, `error.code = "interrupted"` (the thread died with the
  container). The crawler's own `crawl_runs`/`crawl_sessions` rows are written as before (§4); the job row is additional.
- CLI parity: `make crawl DATE=…` / `make backfill` still work and share nothing with the api lock — the sponsor is told
  (README) not to run both at once; the source rate budget (data.md) is the only shared resource.

## 3. R3 board (shape preview; normative at R3 planning)

- `GET /board/watchlist` → `{session, as_of, rows:[{symbol, ref_price, ceiling, floor, bid:[{price,volume}×3],
  ask:[…×3], last_price, last_volume, change, change_pct, total_volume, total_value, foreign_buy_v, foreign_sell_v,
  open, high, low, as_of, stale}]}`; `stale = now − as_of > 15 s` computed server-side (F-062).
  Polling: the web refetches every 3 s in session, 60 s when `phase ∈ closed|holiday|weekend` (ADR-S-004).
  `GET /board/market?exchange=&sort=&filter=` same row shape for all symbols (45 s source refresh).
  `GET /board/indices` → `[{index_code, level, change, change_pct, advancers, decliners, unchanged, ceiling_hits,
  floor_hits, total_value, as_of}]`. `PUT /watchlist` body `{symbols:[…≤100]}` → 422 `WATCHLIST_LIMIT` at 101.
- `GET /bars/1m?symbol=&from=&to=` → same shape as §2.2 with `ts` instead of `trading_date` and `boundary:
  {first_available:"2023-09-11"}` (F-065). `GET /ticks?symbol=&date=` paginated `[{ts, seq, price, volume, side}]`.
- Realtime upgrade path (only if polling misses N4): `GET /board/stream` SSE, event `board`, same row shape, one
  event per source refresh; no other change.

## 4. Crawler → DB and manifest contract (normative, R1)

- Tables and natural keys: `architecture/data.md` §3. Writes are `INSERT … ON CONFLICT (natural key) DO UPDATE`
  and set `fetched_at` where the table has it (`ticks` has none: last write wins, ADR-S-008); no `DELETE` except by an explicit `jobs` kind `purge` (not in v1).
- Raw archive path: `data/raw/<feed>/<YYYY-MM-DD>/<SYMBOL>.json.gz` (payload bytes exactly as received, gzip) and
  — written **only after the adapter accepted the payload as that session's data** (an empty or other-session tape
  is never archived under the requested date; REVIEW-01 QA-BUG-2). The universe is archived as
  `data/raw/symbols/<trading_date>/getAll.json.gz`, keyed by the feed's `trading_date`, so a re-run replays the
  same list (QA-BUG-3) —
  `data/raw/<feed>/<YYYY-MM-DD>/_manifest.json`:
```json
{ "feed": "ticks", "trading_date": "2026-10-15", "source": "kbs", "started_at": "...", "finished_at": "...",
  "status": "complete", "reason": null, "requests": 1541, "rows": 2314567,
  "checksum": "sha256:<hex of canonical rows: symbol,ts,seq,price,volume,side sorted, one per line>",
  "symbols_fetched": 1537, "symbols_no_trades": ["XYZ"], "symbols_skipped": [ {"symbol": "ABC", "reason": "http_429"} ],
  "universe": {"source": "symbols table", "as_of": "2026-10-15T15:20:03+07:00", "count": 1541} }
```
  `universe.source ∈ symbols table | vci:symbols/getAll (S01, before F-004) | cli:--only`; `checksum` canonical line =
  `symbol,ts,seq,price,volume,side` with `ts` as `%Y-%m-%dT%H:%M:%S.%f+00:00` (UTC, 6 digits), `side` empty when
  null; lines sorted bytewise, `\n`-joined, trailing `\n`; `requests` counts HTTP calls made (archive replays excluded).
  `status ∈ complete | partial | missed | blocked | failed`; `reason` for `missed` is one of `machine_off`,
  `source_no_longer_serves`, `source_blocked`, `holiday_misconfigured`. `reason` for `partial` is null unless the
  loop stopped early (`source_no_longer_serves`): the untouched symbols are then listed in `symbols_skipped` with
  that reason. Per-symbol skip reasons: `http_<status> | payload_shape | timeout | source_blocked |
  source_no_longer_serves`. An **other-session** tape is conclusive (`source_no_longer_serves`, stop). An **empty**
  tape is never conclusive on its own (B1, S02: A32 had no trades on 2026-10-16 while K1 still served that day two days
  later): for `trading_date` before today (VN) the run first probes `PROBE_SYMBOLS = (FPT, HPG, VNM)`; if none of
  them returns a tape for `trading_date` the session is `missed` / `source_no_longer_serves` (≤ 3 requests, nothing
  overwritten: a `missed` manifest never replaces a stored `partial` or `complete` row); otherwise the day is still served and an empty tape, today
  or past, is **no trades**: the symbol goes to `symbols_no_trades` (sorted list, not a skip, contributes no rows,
  never archived so a re-run asks again). A probe tape that is fetched counts once (not re-fetched in the loop). Status rule: `complete` = every symbol in the universe is fetched or no-trade; `partial` = at least one
  symbol in `symbols_skipped`; `symbols_fetched + len(symbols_no_trades) + len(symbols_skipped) = universe.count`
  (except `--only`, where it equals the list given). S02-1 (v1.3): `no_ticks` was a skip reason and turned every
  session with an illiquid name into `partial`. Caveat: "no trades" and "source answered empty by mistake" look
  the same on the tape; cross-check against daily volume once F-012 lands.
  A run first closes unfinished `crawl_runs` rows of its `(feed, trading_date)` as `failed`, reason `interrupted`.
  The DB row `crawl_sessions` mirrors the **richest** manifest for the day (`rows` never lowered, FIX-session-ledger; a repair may set `checksum NULL`); the manifest file on disk is the audit copy of the last run.
  v1.12: `blocked` is also the status after `FAIL_RUN = 3` consecutive skipped names/units (own reasons kept, the rest
  `source_blocked`). Ledger repair (migration 0008, re-runnable): a `ticks` row whose `rows` is below `COUNT(*)` of the
  `ticks` table for that VN day takes `rows`/`symbols_fetched` from the table and `checksum = NULL`; status/reason stay.
- Normalisation (adapter responsibility): price → integer VND (SSI history ×1000; KBS/VCI already VND), volume →
  shares, `ts` → UTC from source-local time, `seq` = KBS accumulated volume after the trade (monotonic within the
  day) or VCI `id`; `side` → `B|S|null`.
- Idempotence check (test): running a feed twice on the same fixture yields identical table rows and checksum.
- Other feeds (S02). `symbols` (F-004): one `crawl_runs` row per run (feed `symbols`, `trading_date` = run date VN), raw
  archive `data/raw/symbols/<date>/getAll.json.gz` (already the ticks universe file) + `data/raw/symbols/<date>/<exchange>.json.gz`
  for S1 listings; no manifest (nothing per-session to gap-list). A symbol absent from V3 or on board `DELISTED` gets
  `is_delisted=true`, `delisted_at` = first run date it was observed so (never deleted; the source has no date).
  `bars_1d` back-fill (F-012): manifest + `crawl_sessions` row with feed `bars_1d`, `trading_date` = run date (v1.12: the target session when the job runs it; the row is refreshed after every committed unit as `partial`/`running` with `checksum ""`, the final manifest replaces it; skip reason `deferred` = gap name left for the next press; `symbols_fetched` = names whose bar for that date is in the table after the run), the same
  JSON keys as ticks; `rows` = bars written, `symbols_no_trades` = symbols the source answered with zero bars, checksum
  canonical line `symbol,trading_date,source,adj_o,adj_h,adj_l,adj_c,v,value` (ints, `value` empty when null). Prices
  from V2 are source-adjusted decimals → rounded half-up to integer VND into `bars_1d_src`; `value` is **nominal**
  matched value in VND. V2 `accumulatedValue` is **mixed-unit** (B2, S02: VN30 2012-02-06 = 222,242,000,000 raw VND,
  2026-10-16 = 6,386,472.73 million VND): stocks pick the scale (×1 or ×1e6) closest to `v × c`; indices treat
  `accumulatedValue ≥ 1e9` as VND, else × 1e6 (fixtures `vci/gap_chart/FPT-1d`, `vci/gap_chart/VN30-1d`). A value that
  would not fit BIGINT is stored NULL with a warning, never raised. `bars_1d_src.fetched_at`
  = archive file mtime, so a replay rewrites the same version and a fresh fetch adds a new one (data.md §1.4 (2)).
- Rate limiting: per-source token bucket (data.md §1.2); the adapter raises `SourceBlocked` after 3 consecutive
  429/403/HTML responses; the feed records `blocked` and exits non-zero (systemd shows failure; retry timer at 20:00).
