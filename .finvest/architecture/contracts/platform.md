# Finvest — Platform contracts (REST, realtime, crawler → DB)

Owner: `fi-software-architect`. Status: **v1.2, 2026-10-16** (§4 clarified after REVIEW-01; v1.1 = `platform.prev-2.md`) — R1 endpoints are normative; R2–R5 sections are shape
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
HTTP → code: 400 `VALIDATION` · 404 `NOT_FOUND` · 409 `JOB_ALREADY_RUNNING` · 422 `NOT_TRADING_DAY`, `SYMBOL_UNKNOWN`,
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
| `POST /jobs` body `{kind:"crawl", feed:"ticks"|"all"|…, trading_date}` → 202 `{id, status:"queued"}`; 409 if the same job runs; 422 `NOT_TRADING_DAY` | manual re-run | F-019 |
| `GET /jobs/{id}` | `{id, kind, args, status, created_at, finished_at, log}` | F-019 |

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
  "symbols_fetched": 1537, "symbols_skipped": [ {"symbol": "ABC", "reason": "http_429"} ],
  "universe": {"source": "symbols table", "as_of": "2026-10-15T15:20:03+07:00", "count": 1541} }
```
  `universe.source ∈ symbols table | vci:symbols/getAll (S01, before F-004) | cli:--only`; `checksum` canonical line =
  `symbol,ts,seq,price,volume,side` with `ts` as `%Y-%m-%dT%H:%M:%S.%f+00:00` (UTC, 6 digits), `side` empty when
  null; lines sorted bytewise, `\n`-joined, trailing `\n`; `requests` counts HTTP calls made (archive replays excluded).
  `status ∈ complete | partial | missed | blocked | failed`; `reason` for `missed` is one of `machine_off`,
  `source_no_longer_serves`, `source_blocked`, `holiday_misconfigured`. `reason` for `partial` is null unless the
  loop stopped early (`source_no_longer_serves`): the untouched symbols are then listed in `symbols_skipped` with
  that reason. Per-symbol skip reasons: `http_<status> | payload_shape | timeout | no_ticks | source_blocked |
  source_no_longer_serves`. K1 serves the current session only, so for a `trading_date` before today (VN) an
  empty or other-session tape is conclusive (`source_no_longer_serves`); for today an empty tape is `no_ticks`.
  A run first closes unfinished `crawl_runs` rows of its `(feed, trading_date)` as `failed`, reason `interrupted`.
  The DB row `crawl_sessions` mirrors the manifest; the manifest file is the audit copy.
- Normalisation (adapter responsibility): price → integer VND (SSI history ×1000; KBS/VCI already VND), volume →
  shares, `ts` → UTC from source-local time, `seq` = KBS accumulated volume after the trade (monotonic within the
  day) or VCI `id`; `side` → `B|S|null`.
- Idempotence check (test): running a feed twice on the same fixture yields identical table rows and checksum.
- Rate limiting: per-source token bucket (data.md §1.2); the adapter raises `SourceBlocked` after 3 consecutive
  429/403/HTML responses; the feed records `blocked` and exits non-zero (systemd shows failure; retry timer at 20:00).
