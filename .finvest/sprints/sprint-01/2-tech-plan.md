# Sprint 01 — Tech plan (FE/BE)

Owner: `fi-software-architect`. Status: v1.0, 2026-10-15. Input: `1-sprint-plan.md` (F-020, F-030, F-010, F-011,
F-017; goal "ticks are being collected every evening"). Base branch for every task: `sprint-01`.

## Decisions for this sprint

- **All eight tasks are BE.** No FE story is committed (F-031 shell is S02) and no story touches market-rule
  semantics (calendar/session/bands are F-003/F-005, S02), so there is **no `2-tech-plan.ai.md`** and no AI
  architect run. `packages/market_rules`, `services/analytics`, `apps/web`, `packages/contracts` are not created.
- **PM call 1 (F-017 universe from VCI `symbols/getAll` at run time) — accepted.** The ticks feed calls
  `vci.symbols()` (V3), keeps `STOCK|ETF`, drops CW and delisted, archives the payload under
  `data/raw/symbols/<date>/getAll.json.gz`, and writes `universe.source = "vci:symbols/getAll"` into the manifest
  (platform.md §4). `--only A,B,C` replaces the universe with `source = "cli:--only"`. F-004 (S02) swaps the
  universe provider, not the feed.
- **PM call 2 (past date → manifest `missed`, `source_no_longer_serves`) — accepted, mechanism pinned.** K1 ignores
  `?date=` and always returns the current session, so the KBS adapter compares the `t` date of the returned rows
  with the requested `trading_date`; a mismatch or an empty tape raises `SourceNoLongerServes`. The feed probes
  **one** symbol first; on that exception it writes a `missed` manifest and `crawl_sessions` row and exits 0
  without touching the other ~1,540 symbols. A re-run for a date whose payloads are already archived replays the
  archive (ADR-S-008) and stays `complete` — the probe reads the archive first like every other call.
- **Overrides of my own docs (S01 only):** (a) system.md §5 says compose starts `db, api, web`; S01 compose has
  `db, api, crawler` — `web` arrives with F-031. (b) `source_health` (data.md §3) is deferred to F-021; "blocked"
  is recorded in `crawl_sessions.status/reason` and `crawl_runs`. (c) Weekends: without F-003 the CLI refuses
  Saturday/Sunday dates (exit 0, message, no manifest); holidays are unknown until S02 and will produce a
  `missed` manifest on a holiday run — acceptable, F-003 fixes the reason to `holiday`.
- **Contract clarification made:** platform.md §4 now pins `universe.source` values and the checksum canonical
  line format (`platform.prev-1.md` archived).
- **Kernel for S01** (`make test-kernel`): pytest offline (`pytest-socket`, `-m "not db"`), ruff, mypy strict on
  `finvest_market_data/domain`, import-linter. `make test` adds the `db` marker against the compose `db`.
- **Fixtures are recorded once by the developer** on the sponsor's machine with the `curl` given in each block,
  trimmed to ≤ 50 rows keeping the JSON envelope, gzipped, committed under
  `services/crawler/tests/fixtures/<source>/<endpoint>/<case>.json.gz` (≤ 20 KB each).

Critical path: BE-scaffold → BE-domain → BE-schema → BE-feed-ticks (M3). BE-fetcher and the two adapter tasks
run beside it on lane BE-2.

## Tasks

#### BE-scaffold — uv workspace, package skeletons, settings, kernel tooling, `/health`
- Story: F-020 ; Side: be ; Effort: medium ; Size: ~180 lines ; Lead: opus
- Files: `pyproject.toml`, `uv.lock`, `Makefile`, `README.md` (run section only), `.env.example`,
  `packages/market_data/pyproject.toml`, `packages/market_data/finvest_market_data/__init__.py`,
  `packages/market_data/finvest_market_data/{domain,application,infrastructure}/__init__.py`,
  `services/crawler/pyproject.toml`, `services/crawler/finvest_crawler/__init__.py`,
  `services/crawler/finvest_crawler/settings.py`, `services/crawler/finvest_crawler/cli.py`,
  `services/crawler/finvest_crawler/{adapters,feeds}/__init__.py`, `services/crawler/tests/conftest.py`,
  `apps/api/pyproject.toml`, `apps/api/finvest_api/__init__.py`, `apps/api/finvest_api/main.py`,
  `apps/api/tests/test_health.py`
- Change:
  - Root `pyproject.toml`: uv workspace with members `packages/market_data`, `services/crawler`, `apps/api`
    (codebase.md §1; the other two packages are created in later sprints). Python 3.12. Dev deps: pytest,
    pytest-socket, ruff (line 110), mypy, import-linter, httpx, respx-free (use `httpx.MockTransport`).
  - `[tool.importlinter]` contracts for the dependency rule in codebase.md §3: `finvest_market_data.domain` imports
    nothing from `application|infrastructure|finvest_crawler|finvest_api`; `finvest_market_data.application` never
    imports `infrastructure` or `finvest_crawler`.
  - `[tool.pytest.ini_options]`: `addopts = "--disable-socket --allow-unix-socket"`, marker `db` ("needs the
    compose db; excluded from the kernel"). `[tool.mypy]` strict for `finvest_market_data.domain` only.
  - `finvest_crawler/settings.py`: `pydantic-settings` class `Settings` read from `.env` with `data_dir: Path =
    "data"` (raw archive at `data_dir/raw`, F-020/A12), `database_url`, `source_ticks: str = "kbs"`,
    `source_symbols: str = "vci"`, `source_bars: str = "vci"`, `user_agent: str = "finvest-personal/0.1
    (+learning tool, single user)"`, `retention_days: int | None = None` (None = keep everything, F-020),
    `rate_per_s: dict[str,float] = {"kbs":2,"vci":2,"ssi":1}`. Never printed.
  - `finvest_crawler/cli.py`: `argparse` entry point `finvest-crawl` (console script) with sub-command `ticks
    --date YYYY-MM-DD --only SYM,SYM` that imports `finvest_crawler.feeds.ticks` lazily and exits 3 "not
    implemented" until BE-feed-ticks lands; `--date` defaults to today in `Asia/Ho_Chi_Minh`.
  - `finvest_api/main.py`: FastAPI app, `GET /health` → `{status:"ok", db:"ok", version, rules_version:null}`;
    `db` via `SELECT 1` with SQLAlchemy Core + psycopg 3; on DB error 503 with the envelope `{"error":{"code":
    "DB_UNAVAILABLE", ...}}` (platform.md §1.3, §2). `rules_version` is null until F-001.
  - `Makefile`: `test-kernel` (`uv run pytest -m "not db" -q && uv run ruff check . && uv run mypy && uv run
    lint-imports`), `test` (kernel + `uv run pytest -m db -q`), `lint`. `up`/`crawl` targets are added by BE-compose.
  - `.gitignore` already ignores `data/` and `.env`; add `data/.gitkeep` is **not** needed (compose creates it).
- Contract: platform.md §1.3 (error envelope), §2 (`GET /health`); codebase.md §1, §3, §4, §5.
- Acceptance:
  - `uv sync && make test-kernel` passes offline (one placeholder test per package is enough; `test_health.py`
    uses `TestClient` with the DB engine replaced by a stub raising → asserts 503 envelope, and a stub returning 1 →
    200 body shape).
  - `uv run lint-imports` reports the three contracts kept.
  - `uv run finvest-crawl ticks --date 2026-10-18` prints "not a trading day (weekend)" and exits 0;
    `--date 2026-10-16` exits 3 "not implemented".
  - `git status` shows nothing under `data/` after creating `data/raw/x` by hand.
- Out of scope: Docker, compose, Alembic, any adapter or domain type, `packages/market_rules`, `apps/web`.

#### BE-domain — market-data domain: Tick/Bar/Symbol value objects, `MarketDataSource` port, units, manifest checksum
- Story: F-010 ; Side: be ; Effort: high ; Size: ~170 lines ; Lead: opus
- Files: `packages/market_data/finvest_market_data/domain/models.py`,
  `packages/market_data/finvest_market_data/domain/ports.py`,
  `packages/market_data/finvest_market_data/domain/units.py`,
  `packages/market_data/finvest_market_data/domain/manifest.py`,
  `packages/market_data/tests/test_units.py`, `packages/market_data/tests/test_manifest.py`
- Change:
  - `models.py` (frozen dataclasses, `slots=True`, no I/O, no pandas): `Tick(symbol, ts: datetime[UTC-aware],
    seq: int, price: int, volume: int, side: Literal["B","S"] | None, source: str)`; `Bar(symbol, ts, o, h, l, c,
    v, value: int | None, source)`; `SymbolRecord(symbol, exchange: Literal["HOSE","HNX","UPCOM"], type:
    Literal["STOCK","ETF"], name_vi, name_en, icb_code2: str | None, is_delisted: bool, source)`. Prices are `int`
    VND (ADR-S-005); `__post_init__` rejects non-UTC `ts`, negative volume, price ≤ 0.
  - `ports.py`: the `MarketDataSource` Protocol exactly as codebase.md §3 but **only** `name`, `symbols()`,
    `ticks(symbol, trading_date)`, `bars(symbols, grain, to, count)` for S01 (the other methods are added by the
    sprint that needs them). Exceptions: `SourceError(Exception)` base; `Unsupported`, `SourceNoLongerServes`
    (source cannot serve the requested session), `PayloadShapeError` (Pydantic validation failed; carries the
    raw bytes path). `SourceBlocked` lives in the fetcher (BE-fetcher), not here.
  - `units.py`: `to_vnd(value: Decimal | int | str, unit: Literal["vnd","thousand_vnd"]) -> int` (Decimal,
    `ROUND_HALF_UP` to 1 VND; VCI adjusted floats like `65182.47` → `65182`), `to_shares(qty, lot_unit: int) -> int`.
  - `manifest.py`: `canonical_line(tick) -> str` and `checksum(ticks: Iterable[Tick]) -> str` ("sha256:<hex>")
    per platform.md §4 (sorted bytewise, `\n`-joined, trailing `\n`, `ts` as `%Y-%m-%dT%H:%M:%S.%f+00:00`);
    `dedupe(ticks) -> tuple[list[Tick], list[Tick]]` keeps the **last** row per `(symbol, ts, seq)` and returns the
    displaced ones (ADR-S-008 `duplicate_tick`); `Manifest` dataclass with the §4 fields and `to_dict()` that
    produces exactly the §4 JSON keys (`started_at/finished_at` as `+07:00` ISO).
- Contract: platform.md §1.2 (units), §4 (manifest JSON, checksum line); ADR-S-005; ADR-S-006; ADR-S-008;
  codebase.md §3 (port), §4.
- Acceptance (worked examples the tests must contain):
  - `to_vnd("93.5","thousand_vnd") == 93500`; `to_vnd("65182.47","vnd") == 65182`; `to_vnd("65182.5","vnd") ==
    65183`; `to_shares(10, 10) == 100` (F-010 G/W/T 1).
  - Two ticks `FPT 2026-10-15T07:45:08.160000Z seq 1234500 price 58000 vol 100 side None` and `… seq 1234600 …`
    → `checksum` equals the sha256 of the two sorted lines `FPT,2026-10-15T07:45:08.160000+00:00,1234500,58000,100,\n…`
    computed independently in the test; order of input does not change it.
  - `dedupe` on three ticks where two share the key → 2 kept (the later one), 1 displaced.
  - `Tick(ts=naive datetime)` raises `ValueError`; mypy strict passes on `domain/`.
- Out of scope: repositories, SQL, HTTP, any adapter, `close_snapshot`/`corporate_actions`/`board` port methods.

#### BE-fetcher — rate-limited archiving HTTP fetcher: token bucket, backoff, stop on block, raw archive as cache
- Story: F-011 ; Side: be ; Effort: medium ; Size: ~210 lines ; Lead: sonnet
- Files: `services/crawler/finvest_crawler/ratelimit.py`, `services/crawler/finvest_crawler/archive.py`,
  `services/crawler/finvest_crawler/fetch.py`, `services/crawler/tests/test_fetch.py`,
  `services/crawler/tests/test_archive.py`
- Change:
  - `ratelimit.py`: `TokenBucket(rate_per_s, burst=1)` with injectable `clock` and `sleep` (so tests run in
    0 s); one bucket per source name, built from `Settings.rate_per_s` (KBS 2, VCI 2, SSI 1 — data.md §1.2).
  - `archive.py`: `Archive(root=Settings.data_dir/"raw")` with `path(feed, trading_date, name) ->
    data/raw/<feed>/<YYYY-MM-DD>/<name>.json.gz`, `read(...) -> bytes | None`, `write(..., payload: bytes)` (gzip the
    bytes **exactly as received**, atomic rename), `write_manifest(feed, trading_date, dict)` → `_manifest.json`
    (indent 2, sorted keys). Creates directories; never deletes (platform.md §4).
  - `fetch.py`: `class SourceBlocked(Exception)`; `Fetcher(client: httpx.Client, buckets, archive, user_agent,
    sleep)` with `get(source, url, *, feed, trading_date, name, method="GET", json=None) -> bytes`: 1) return
    `archive.read` hit without any HTTP call (ADR-S-008 "archive doubles as cache"); 2) `bucket.take()`; 3) request
    with `User-Agent` from settings (F-011 G/W/T 3), timeout 20 s; 4) on 429/403, or 200 whose body starts with
    `<` / contains `Just a moment` (Cloudflare challenge, data.md §1.2 T1), back off 1→2→4→8 s and retry; after
    **3 consecutive** such responses raise `SourceBlocked(source, last_status)`; a non-blocked response resets the
    counter; 5) 5xx/timeout: same backoff, max 3 tries, then raise `httpx.HTTPError`; 6) on 200 archive then return.
    Counters `requests` (HTTP calls) and `replays` (archive hits) exposed for the manifest.
  - Hosts allow-list check: `url` host must be one of `kbbuddywts.kbsec.com.vn`, `trading.vietcap.com.vn`,
    `iboard-api.ssi.com.vn`, `iboard-query.ssi.com.vn`, `iq.vietcap.com.vn` (codebase.md §5 guardrail audit);
    anything else raises `ValueError` before any call.
- Contract: platform.md §4 (archive path, rate limiting, `SourceBlocked`); data.md §1.2 rate policy; ADR-S-002;
  ADR-S-008.
- Acceptance (all with `httpx.MockTransport`, network disabled, fake clock/sleep):
  - 3 × 429 → `SourceBlocked` raised after exactly 3 requests; recorded sleeps are `[1, 2]` s (backoff before the
    2nd and 3rd attempt); 429, 429, 200 → returns body, 3 requests, counter reset.
  - 200 with body `<!DOCTYPE html>…Just a moment…` counts as blocked.
  - At `rate_per_s=2`, 5 immediate calls to one source accumulate ≥ 2.0 s of simulated sleep; calls to a second
    source do not wait on the first bucket.
  - Second `get` for the same `(feed, date, name)` makes **zero** HTTP calls and returns identical bytes; the
    archive file's gunzipped bytes equal the response body byte-for-byte.
  - `User-Agent` header on every request equals `Settings.user_agent`; a URL outside the allow-list raises before
    any request.
- Out of scope: parsing payloads, any adapter, DB writes, manifest content (only the file write helper here).

#### BE-schema — Alembic + migration 0001 (ticks hypertable, crawl_runs, crawl_sessions, data_anomalies) + repositories
- Story: F-017 ; Side: be ; Effort: high ; Size: ~200 lines ; Lead: opus
- Files: `apps/api/alembic.ini`, `apps/api/migrations/env.py`, `apps/api/migrations/script.py.mako`,
  `apps/api/migrations/versions/0001_market_data_ticks.py`,
  `packages/market_data/finvest_market_data/infrastructure/tables.py`,
  `packages/market_data/finvest_market_data/infrastructure/repositories.py`,
  `packages/market_data/tests/test_repositories_db.py`
- Change:
  - `tables.py`: SQLAlchemy Core `MetaData` with `ticks`, `crawl_runs`, `crawl_sessions`, `data_anomalies` exactly
    as data.md §3 (columns, types, PKs). `ticks.side CHAR(1) NULL`. No ORM.
  - Migration 0001 (raw SQL via `op.execute` where Timescale needs it): `CREATE EXTENSION IF NOT EXISTS
    timescaledb`; create the four tables; `SELECT create_hypertable('ticks','ts', chunk_time_interval =>
    interval '1 day')`; `ALTER TABLE ticks SET (timescaledb.compress, timescaledb.compress_segmentby='symbol',
    timescaledb.compress_orderby='ts, seq')`; `SELECT add_compression_policy('ticks', interval '1 day')`
    (ADR-S-001). Downgrade drops the tables.
  - `repositories.py` (functions over an `Engine`/`Connection`, Core only):
    `upsert_ticks(conn, ticks: Sequence[Tick]) -> int` — `INSERT … ON CONFLICT (symbol, ts, seq) DO UPDATE SET
    price, volume, side, source WHERE (ticks.price, ticks.volume, ticks.side) IS DISTINCT FROM (EXCLUDED.price,
    EXCLUDED.volume, EXCLUDED.side)`, in batches of 5,000 rows, returns the number of rows **changed** by the
    update branch (`xmax <> 0` trick via `RETURNING (xmax = 0) AS inserted`) so the feed can log `duplicate_tick`;
    `insert_crawl_run(conn, feed, trading_date, started_at) -> id` and `finish_crawl_run(conn, id, status, reason,
    requests, rows, manifest_path)`; `upsert_crawl_session(conn, Manifest)` on `(feed, trading_date)`;
    `insert_anomaly(conn, symbol, trading_date, rule, value)`; `session_status(conn, feed, trading_date) ->
    str | None`.
  - `engine(database_url)` factory with `pool_pre_ping=True`.
- Contract: data.md §2 (ticks tier), §3 (DDL); platform.md §4 (upsert rule, no DELETE); ADR-S-001; ADR-S-008.
- Acceptance (`@pytest.mark.db`, needs `FINVEST_DATABASE_URL` → compose `db`; skipped in the kernel):
  - `alembic upgrade head` then `downgrade base` then `upgrade head` succeeds on an empty database;
    `timescaledb_information.hypertables` lists `ticks`; `timescaledb_information.jobs` has the compression policy.
  - `upsert_ticks` with the same 3 rows twice → table has 3 rows, second call returns 0 changed; the same keys with
    one different price → 1 changed and the newer price is stored.
  - `upsert_crawl_session` twice for the same `(feed, date)` → one row with the second status.
  - `ticks.side` accepts NULL and `'B'`; rejects `'X'` (CHECK `side IN ('B','S')`).
- Out of scope: `symbols`, `bars_*`, `source_health`, `jobs`, every other data.md §3 table (added by the story that
  writes them); API endpoints reading these tables (F-021, S02); migration run at API start-up (BE-compose).

#### BE-adapter-kbs — KBS tick-tape adapter (K1) with fixtures: parse, normalise, detect "session not served"
- Story: F-010 ; Side: be ; Effort: high ; Size: ~180 lines ; Lead: sonnet
- Files: `services/crawler/finvest_crawler/adapters/kbs/__init__.py`,
  `services/crawler/finvest_crawler/adapters/kbs/payloads.py`, `services/crawler/finvest_crawler/adapters/kbs/source.py`,
  `services/crawler/tests/fixtures/kbs/trade_history/FPT-2026-10-1x.json.gz` (real date in the name),
  `services/crawler/tests/fixtures/kbs/trade_history/empty.json.gz`, `services/crawler/tests/test_adapter_kbs.py`
- Change:
  - Record the fixture once: `curl -sS -A 'finvest-personal/0.1' 'https://kbbuddywts.kbsec.com.vn/iis-server/
    investment/trade/history/FPT?page=1&limit=50000'`, trim the row array to the first 50 rows keeping the envelope,
    gzip. Module docstring documents the observed shape and **units**: `FMP` price VND, `FV` match volume shares,
    `AVO` accumulated volume (= `seq`), `LC` side `'B'|'S'|''`, `t` local `YYYY-MM-DD HH:MM:SS:cc` (centiseconds,
    Asia/Ho_Chi_Minh) — data.md §1.2 K1.
  - `payloads.py`: Pydantic v2 models for the envelope and row (`extra="allow"` for the envelope, strict types on
    the five fields we use); a validation failure raises `PayloadShapeError` with the archive path (ADR-S-002 "fail
    loudly, keep the raw payload").
  - `source.py`: `class KbsSource` implementing `name="kbs"`, `ticks(symbol, trading_date)`: `fetcher.get("kbs",
    url, feed="ticks", trading_date=…, name=symbol)` → `parse_ticks(payload, symbol, trading_date) -> list[Tick]`
    (pure, also exported for the feed's tests): `ts = VN-local datetime(t) → UTC`, microsecond = cc × 10,000,
    `price = int(FMP)`, `volume = int(FV)`, `seq = int(AVO)`, `side = LC or None`, `source="kbs"`.
    **Session check (PM call 2):** if the tape is empty or any row's local date ≠ `trading_date` → raise
    `SourceNoLongerServes(symbol, served_date)`. `symbols()`/`bars()` raise `Unsupported`.
- Contract: platform.md §4 (normalisation: VND, shares, UTC `ts`, `seq` = AVO, `side` B|S|null); data.md §1.2 K1;
  codebase.md §3 (port); ADR-S-006; ADR-S-008.
- Acceptance (fixtures, network disabled):
  - Fixture row `t="2026-10-15 14:45:08:16"` → `ts == datetime(2026,10,15,7,45,8,160000, tzinfo=UTC)`; a row with
    `FMP=58000, FV=100, AVO=1234500, LC=""` → `Tick(price=58000, volume=100, seq=1234500, side=None)`.
  - `seq` is strictly increasing over the parsed fixture; `len(parse_ticks(fixture)) == 50`.
  - `parse_ticks(fixture, trading_date=date(2026,10,14))` raises `SourceNoLongerServes` with `served_date ==
    date(2026,10,15)`; `empty.json.gz` raises `SourceNoLongerServes` too.
  - A payload with `FMP` renamed raises `PayloadShapeError` naming the archive path.
  - Adapter asks the fetcher for exactly the K1 URL with `limit=50000`.
- Out of scope: writing to DB or manifest, VCI fallback (V1), the 10:00 in-session `LC` sample (optional spike).

#### BE-adapter-vci-ssi — VCI symbols (V3) + daily bars (V2) and SSI daily bars (S2, thousand VND) with fixtures
- Story: F-010 ; Side: be ; Effort: high ; Size: ~230 lines ; Lead: sonnet
- Files: `services/crawler/finvest_crawler/adapters/vci/{__init__,payloads,source}.py`,
  `services/crawler/finvest_crawler/adapters/ssi/{__init__,payloads,source}.py`,
  `services/crawler/finvest_crawler/adapters/registry.py`,
  `services/crawler/tests/fixtures/vci/symbols_getAll/sample.json.gz`,
  `services/crawler/tests/fixtures/vci/gap_chart/FPT-1d.json.gz`,
  `services/crawler/tests/fixtures/ssi/history/FPT-1d.json.gz`, `services/crawler/tests/test_adapter_vci.py`,
  `services/crawler/tests/test_adapter_ssi.py`, `services/crawler/tests/test_registry.py`
- Change:
  - Fixtures (record once, trim to ≤ 50 rows keeping the envelope, gzip): V3 `GET https://trading.vietcap.com.vn/
    api/price/symbols/getAll` — keep a sample that contains at least one of each: HOSE stock, ETF, CW, HNX, UPCOM,
    DELISTED; V2 `POST https://trading.vietcap.com.vn/api/chart/OHLCChart/gap-chart` body
    `{"timeFrame":"ONE_DAY","symbols":["FPT"],"to":<epoch>,"countBack":50}`; S2 `GET https://iboard-api.ssi.com.vn/
    statistics/charts/history?resolution=1D&symbol=FPT&from=<epoch>&to=<epoch>`. Field names for exchange/type/
    delisted on V3 are `[verify]` from the recorded payload — document them in the module docstring.
  - `vci/source.py`: `VciSource(name="vci")`: `symbols()` → `SymbolRecord` list, mapping board `HSX→HOSE`,
    keeping `type ∈ STOCK|ETF`, **excluding CW and delisted** (1-sprint-plan.md note 2), archived as
    `feed="symbols", name="getAll"`; `bars(symbols, "1d", to, count)` → `Bar` list with `to_vnd(x, "vnd")`
    (adjusted floats rounded half-up, data.md §1.4), `v` shares, `ts` = trading-day midnight VN → UTC. `ticks()`
    raises `Unsupported` in S01.
  - `ssi/source.py`: `SsiSource(name="ssi")`: `bars(..., "1d", ...)` with `to_vnd(x, "thousand_vnd")` (S2 quotes
    `58` for 58,000 VND); everything else `Unsupported`. Docstring states the unit rule (F-010 G/W/T 1).
  - `registry.py`: `make_source(name, fetcher) -> MarketDataSource` for `kbs|vci|ssi` and `source_for(role,
    settings, fetcher)` reading `Settings.source_ticks|source_symbols|source_bars` — the only place a source name
    is resolved (F-010 G/W/T 3, codebase.md §3 config swap).
- Contract: platform.md §1.2 (units), §4 (normalisation); data.md §1.2 V2, V3, S2; §1.4; codebase.md §3;
  ADR-S-005.
- Acceptance (fixtures, network disabled):
  - `symbols()` on the V3 fixture returns no CW, no delisted row, exchanges only `HOSE|HNX|UPCOM`, and the count
    equals the hand-counted STOCK+ETF rows of the fixture (state the number in the test).
  - V2 fixture bar with `c=65182.47` → `Bar.c == 65182`; a bar with `c=58000` → `58000`; `v` unchanged.
  - S2 fixture bar with close `58` → `Bar.c == 58000`; `58.1` → `58100`.
  - `source_for("bars", Settings(source_bars="ssi"), f).bars(["FPT"],"1d",…)` and the same with `"vci"` both return
    `list[Bar]` whose first element passes the same shape assertions — no code outside the adapters differs.
  - Unknown source name → `ValueError` listing the three known names.
- Out of scope: writing `symbols`/`bars_1d_src` tables (F-004/F-012, S02), V1 ticks, V4/V5/S1 endpoints,
  1m bars, the `symbols` DB table.

#### BE-compose — docker compose (db, api, crawler on 127.0.0.1), Dockerfile, `make up` / `make crawl`
- Story: F-030 ; Side: be ; Effort: medium ; Size: ~150 lines ; Lead: opus
- Files: `docker-compose.yml`, `Dockerfile`, `.dockerignore`, `Makefile` (targets `up`, `down`, `crawl`, `logs`,
  `db-shell` only — append), `README.md` ("Run" section — rewrite), `ops/README.md`
- Change:
  - `docker-compose.yml`: `db` = `timescale/timescaledb:2.17-pg16`, bind mount `./data/pg:/var/lib/postgresql/data`,
    **no `ports`** (ADR-S-001, system.md §5), healthcheck `pg_isready`, credentials from `.env`
    (`POSTGRES_PASSWORD`; `.env.example` documents it); `api` = this repo's image, command `alembic upgrade head &&
    uvicorn finvest_api.main:app --host 0.0.0.0 --port 8000`, `ports: "127.0.0.1:8000:8000"`, `depends_on: db:
    condition: service_healthy`; `crawler` = same image, `profiles: ["tools"]` (not started by `up`), entrypoint
    `finvest-crawl`, bind mount `./data:/app/data`, env `FINVEST_DATA_DIR=/app/data`, `FINVEST_DATABASE_URL`
    pointing at `db`. No `web` service in S01 (F-031 adds it).
  - `Dockerfile`: `python:3.12-slim`, install `uv`, copy the workspace, `uv sync --frozen --no-dev`; one image for
    api and crawler. `.dockerignore` excludes `data/`, `.git`, `.finvest/`, `node_modules`.
  - `Makefile`: `up` (`docker compose up -d --build`), `down`, `logs`, `crawl` (`docker compose run --rm crawler
    ticks --date $(DATE)`; `DATE` defaults to today in VN time via `TZ=Asia/Ho_Chi_Minh date +%F`),
    `db-shell` (`docker compose exec db psql -U finvest finvest`).
  - `README.md` Run section: the exact two sponsor commands `make up` → `curl http://127.0.0.1:8000/api/health`
    and `make crawl DATE=2026-10-23`; where the data lives (`data/pg`, `data/raw`), that nothing listens on other
    interfaces, how to re-run a date.
  - Engine `/health` must work through the compose network: `FINVEST_DATABASE_URL=postgresql+psycopg://finvest:
    …@db:5432/finvest`.
- Contract: system.md §5 (deployment), §3 (components); codebase.md §6 (full-run paths "Start", "Crawl one
  date"); platform.md §2 (`GET /health`); ADR-S-001; ADR-S-003.
- Acceptance (documented in the PR as a transcript; the lead re-runs it):
  - Fresh clone + `.env` from `.env.example` + `make up` → `curl -s 127.0.0.1:8000/api/health` returns
    `{"status":"ok","db":"ok",…}` within 60 s; `ss -ltn` shows `127.0.0.1:8000` and **no** `0.0.0.0:8000`, no 5432
    published; `data/pg/` exists and `git status --porcelain` is empty (F-020).
  - `make crawl DATE=2026-10-18` prints the weekend message and exits 0 (until BE-feed-ticks merges, a weekday
    date exits 3 "not implemented" — acceptable for this PR; the story's crawl criterion closes with BE-feed-ticks).
  - `docker compose config` validates; `make down && make up` keeps the data (migration already applied, no error).
- Out of scope: systemd timers (F-019), `web` service, nginx, backups, TLS, auth.

#### BE-feed-ticks — ticks feed: universe → archive-first fetch → normalise → upsert → manifest + `crawl_sessions`
- Story: F-017 ; Side: be ; Effort: high ; Size: ~240 lines ; Lead: opus
- Files: `services/crawler/finvest_crawler/feeds/ticks.py`, `services/crawler/finvest_crawler/cli.py` (replace the
  stub body of the `ticks` sub-command only), `services/crawler/tests/test_feed_ticks.py`,
  `services/crawler/tests/fixtures/feeds/ticks/*.json.gz` (two-symbol universe + two K1 tapes, derived from the
  adapter fixtures)
- Change:
  - `run_ticks(settings, trading_date, only: list[str] | None, *, fetcher=None, conn=None) -> Manifest`:
    1. `insert_crawl_run`. 2. Universe: `only` → `universe.source="cli:--only"`; else
       `source_for("symbols").symbols()` → `"vci:symbols/getAll"` with `count` and `as_of`. 3. **Probe** the first
       symbol with `source_for("ticks").ticks(sym, trading_date)`; `SourceNoLongerServes` → manifest
       `status="missed", reason="source_no_longer_serves"`, `symbols_fetched=0`, write manifest + session + run,
       exit 0 (1-sprint-plan.md note 3, platform.md §4 reasons). 4. For every symbol: `ticks()` → `dedupe()` →
       `upsert_ticks()`; displaced duplicates and `changed > 0` → `insert_anomaly(rule="duplicate_tick",
       value=str(n))`; rows accumulate into the checksum (`manifest.checksum` over all kept ticks, streaming
       sha256 over sorted lines is **not** possible → collect canonical lines, sort once at the end; ~2–3 M lines
       ≈ 200 MB, acceptable on one machine; `shortcut: in-memory sort, upgrade to per-symbol sub-checksums if RAM
       hurts`). 5. Per-symbol `PayloadShapeError`/`httpx.HTTPError` → `symbols_skipped += {symbol, reason}` with
       reason `http_<status>` | `payload_shape` | `timeout`, continue. 6. `SourceBlocked` → stop the loop,
       `status="blocked", reason="source_blocked"`, remaining symbols listed as skipped `source_blocked`, write
       manifest/session/run, **exit 2** (platform.md §4: non-zero so the 20:00 retry sees failure). 7. Else
       `status = "complete"` if `symbols_skipped` is empty, else `"partial"`; `requests` = fetcher HTTP calls,
       `rows` = ticks kept; `archive.write_manifest(...)`, `upsert_crawl_session`, `finish_crawl_run`.
  - Structured one-line JSON log per symbol (`symbol, rows, replayed, ms`) and a final summary line to stdout.
  - `cli.py` `ticks` sub-command: weekend guard stays; builds `httpx.Client`, `Fetcher`, engine, calls `run_ticks`,
    exits with 0 / 2 as above; `--only` parsing.
  - The crawl start date is implicit: the first `crawl_sessions` row (1-sprint-plan.md risk "sessions lost before
    S01"); no extra field.
- Contract: platform.md §4 (manifest JSON incl. `universe.source` values, status/reason enums, idempotence check,
  exit on blocked); data.md §3 (`ticks`, `crawl_runs`, `crawl_sessions`, `data_anomalies`), §4 (`ticks` feed row);
  ADR-S-008; codebase.md §6 ("One feed" path).
- Acceptance:
  - Offline (fixture universe of 2 symbols, `MockTransport` serving the two K1 fixtures, `Archive` in `tmp_path`,
    repositories replaced by an in-memory fake implementing the same functions): manifest `status="complete"`,
    `symbols_fetched=2`, `rows=100`, `requests=3` (1 universe + 2 tapes), `universe.source=="vci:symbols/getAll"`,
    `_manifest.json` keys exactly the platform.md §4 set.
  - **Idempotence:** run twice on the same fixtures → identical kept `Tick` lists, identical `checksum`, second
    run `requests=0` (all replayed), `replays=3`.
  - Past date: universe fixture + K1 fixture dated 2026-10-15, `trading_date=2026-10-14` → `status="missed"`,
    `reason="source_no_longer_serves"`, exactly 2 HTTP requests (universe + probe), manifest file written.
  - Blocked: transport returns 429 forever for the second symbol → `status="blocked"`, `symbols_skipped` lists it
    with `source_blocked`, process exit code 2.
  - One symbol's payload with a renamed field → `status="partial"`, skipped reason `payload_shape`, the other
    symbol's rows stored.
  - `@pytest.mark.db` (make test): the same two-symbol run against the compose `db` twice → `SELECT count(*) FROM
    ticks` = 100 both times, one `crawl_sessions` row with `checksum` equal to the manifest's.
  - Live (M3, not a PR gate, recorded in 3-build): `make crawl DATE=<trading day, after 15:30>` finishes in
    < 45 min with `status ∈ complete|partial`, manifest at `data/raw/ticks/<date>/_manifest.json`.
- Out of scope: scheduler/catch-up (F-019), priority order (F-018), holiday calendar (F-003), V1 fallback,
  `source_health`, any API endpoint, `close_snapshot`/`bars` feeds.
