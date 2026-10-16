# Sprint 02 — Tech plan (FE/BE)

Owner: `fi-software-architect`, 2026-10-16, plan v1.0 (dag.json dagRev 1). Inputs: `1-sprint-plan.md` (S02-1..S02-4,
F-003, F-019, F-004, F-012; M1–M4), `product/backlog.md`, `contracts/platform.md` v1.4, `data.md`, `codebase.md`,
`sprint-01/5-review.tech.md`, retro R1–R3. Branch `sprint-02` (from sprint-01 head `72e6c8d`).

## Decisions for this sprint

- **All tasks are BE; no `2-tech-plan.ai.md`.** The calendar (F-003) is data (data.md §1.3 VSE notice) plus a lookup, not
  rule semantics, so it stays with the BE side inside the new `packages/market_rules` package that codebase.md §1 reserves.
- **Contract amendments made now (platform.md v1.4, `platform.prev-4.md` archived):** `symbols` feed = `crawl_runs` row +
  archive, no manifest; `bars_1d` feed = manifest + `crawl_sessions` with the ticks keys, bars checksum line, `value` =
  nominal VND from V2 `accumulatedValue` × 1e6, `fetched_at` = archive mtime. data.md §3: `crawl_sessions.symbols_no_trades`,
  `bars_1d_src.value`. ADR-S-009 amended: one timer with two `OnCalendar` lines + `Persistent=true` + a `catchup` command
  replace the separate catch-up unit.
- **F-012 stores the source-adjusted series (`bars_1d_src`, versioned) and `index_1d`, not nominal `bars_1d`.** Nominal
  prices before crawl start need `adj_factors` (F-014/F-015, later sprints; data.md §1.4 (1)); nominal *value* is
  available now from V2 and is stored. Indices limited to `VNINDEX`, `VN30` (the only names confirmed, data.md §5).
- **V2 is called one symbol per request** (`countBack=6000`, ~1,900 calls at 2 req/s ≈ 16 min). Multi-symbol batching is
  uncited for depth and is not needed. Back-fill runs outside 15:00–23:00 VN (shared KBS/VCI budget, 1-sprint-plan risk).
- **F-004 split by evidence (retro R3).** V3 `getAll` (fixture `vci/symbols_getAll/sample`) gives exchange, type, names,
  `icbCode2`, board `DELISTED` — no listing date, no delisting date, no index membership. Listing date comes from S1
  `firstTradingDate` (data.md §1.2 S1, cited). Index membership has **no §1.2 line → spike `S-index-members` first**, then
  `BE-symbols-enrich`. If the spike finds no free endpoint, `BE-symbols-enrich` ships listing dates only and index
  membership becomes a sponsor question (manual VN30 seed) at review — tell the PM then, not now.
- **Delisting date semantics:** the source has none; `delisted_at` = first run date the symbol was seen absent or on board
  `DELISTED`; rows are never deleted (platform.md §4 "Other feeds").
- **`catchup` is the single scheduler entry point** (15:30, 20:00, boot): walk trading days since the last `crawl_sessions`
  row, run `ticks` where status is absent/`partial`/`blocked`/`failed`; `complete` and `missed` are final (K1 serves the
  current session only, data.md §1.2 K1). Today counts only after 15:05 VN (VN§2 put-through ends 15:00).
- **Migrations are a chain** (Alembic `down_revision`): 0002 status column → 0003 symbols → 0004 bars → 0005 index
  membership; the tasks that own them are ordered with `after`. `cli.py` is touched by four tasks and is ordered the same way.
- **Kernel unchanged** (`make test-kernel`: pytest `-m "not db"`, ruff, mypy, import-linter); tasks with a migration or
  repository change run `make test` (`-m db`) before the PR (retro R1). Sizes count prod + test + migration (R3).

Critical path: QA-S01-tests → BE-status-no-trades → BE-calendar → BE-scheduler (M2, Thu 15:30 unattended run) →
BE-symbols-feed → BE-bars-store → BE-bars-backfill (M3). OPS-host-user and S-index-members run beside it.
Total planned size: 1,519 lines over 10 code tasks + 2 manual tasks.

## Tasks

#### QA-S01-tests — land the sprint-01 QA acceptance tests (branch `test/sprint-01/be`)
- Story: — (handoff §3, 1-sprint-plan risk "test worktree not merged") ; Side: be ; Effort: medium ; Size: ~199 lines ; Lead: sonnet
- Files: `services/crawler/tests/test_qa_sprint01.py` (the only file that differs: `git diff origin/sprint-01
  origin/test/sprint-01/be --stat` on code = 1 file, +199)
- Change:
  - From a task branch off `sprint-02`, `git merge origin/test/sprint-01/be` (or cherry-pick `872de2e`, `7ef36c8`).
  - Resolve nothing else: `.finvest/**`, `CLAUDE.md` must stay as on `sprint-02` (the test branch is behind on docs);
    `git diff origin/sprint-02...HEAD --stat` must list only `services/crawler/tests/test_qa_sprint01.py`.
  - No production code change. If a test fails on `sprint-02` head, do not edit product code: mark it in `3-build` and
    consult; the known case is the `no_ticks` skip reason, which BE-status-no-trades renames (that task fixes the assert).
- Contract: platform.md §4 (status rule v1.3 — tests written against v1.2 may assert `no_ticks`).
- Acceptance: `make test-kernel` green on the task branch except tests that assert the v1.2 `no_ticks` skip (list them in
  `3-build`; they are rewritten by BE-status-no-trades); diff vs `origin/sprint-02` = exactly one test file.
- Out of scope: any change under `services/crawler/finvest_crawler/**`.

#### BE-status-no-trades — S02-1: `symbols_no_trades` in manifest + `crawl_sessions`; `complete` when no real skip
- Story: S02-1 ; Side: be ; Effort: high ; Size: ~120 lines ; Lead: opus
- Files: `packages/market_data/finvest_market_data/domain/manifest.py`, `packages/market_data/finvest_market_data/infrastructure/tables.py`,
  `packages/market_data/finvest_market_data/infrastructure/repositories.py` (`upsert_crawl_session` only),
  `apps/api/migrations/versions/0002_crawl_sessions_no_trades.py`, `services/crawler/finvest_crawler/feeds/ticks.py`,
  `packages/market_data/tests/test_manifest.py`, `packages/market_data/tests/test_repositories_db.py`,
  `services/crawler/tests/test_feed_ticks.py`, `services/crawler/tests/test_qa_sprint01.py` (asserts only)
- Change:
  - `Manifest.symbols_no_trades: tuple[str, ...] = ()` (sorted); `to_dict` emits it after `symbols_fetched`, before
    `symbols_skipped` (key set = platform.md §4 example).
  - `feeds/ticks.py`: today + empty tape (`SourceNoLongerServes` with `served_date is None` and `trading_date == today`)
    → append to `no_trades`, not `skipped`; drop the `no_ticks` reason. Status: `complete` iff `skipped` is empty after the
    loop (unchanged code path, now correct because no-trade is not a skip). Invariant asserted in code:
    `fetched + len(no_trades) + len(skipped) == len(names)`.
  - Migration 0002: `ALTER TABLE crawl_sessions ADD COLUMN symbols_no_trades INT`; `tables.py` + `upsert_crawl_session`
    write `len(m.symbols_no_trades)`.
- Contract: platform.md §4 (manifest JSON, status rule v1.3, invariant); data.md §3 `crawl_sessions`.
- Acceptance:
  - Fixture run (2-symbol universe, FPT tape + `kbs/trade_history/empty` for VNM, `today == trading_date`) → `status ==
    "complete"`, `symbols_fetched == 1`, `symbols_no_trades == ("VNM",)`, `symbols_skipped == ()`; manifest keys exactly
    `feed, trading_date, source, started_at, finished_at, status, reason, requests, rows, checksum, symbols_fetched,
    symbols_no_trades, symbols_skipped, universe`.
  - Same fixtures with `trading_date < today` → unchanged v1.2 behaviour: `partial`/`source_no_longer_serves`.
  - One `payload_shape` skip + one no-trade → `partial`, `symbols_skipped == (("X","payload_shape"),)`, no-trade listed.
  - `@pytest.mark.db`: `crawl_sessions.symbols_no_trades == 1` after the fixture run; `alembic upgrade head` then
    `downgrade -1` round-trips.
  - Worked example (10-16 live manifest, re-run by QA-S02-live): 911 fetched + 629 no-trade + 0 skipped = 1540 → `complete`.
- Out of scope: F-012 cross-check of no-trade vs daily volume; API endpoints; the 10-15 re-manifest (OPS-cleanup-1015).

#### OPS-host-user — S02-2: compose services run as the host UID/GID; one documented chown
- Story: S02-2 ; Side: be ; Effort: medium ; Size: ~30 lines ; Lead: opus
- Files: `docker-compose.yml`, `Makefile`, `.env.example`, `ops/README.md`
- Change:
  - `docker-compose.yml`: `user: "${FINVEST_UID:-1000}:${FINVEST_GID:-1000}"` on `api` and `crawler` (not `db`: the
    postgres image manages `data/pg` itself). `HOME=/tmp` in the shared env so python/httpx never try to write under `/`.
  - `Makefile`: `export FINVEST_UID ?= $(shell id -u)` / `FINVEST_GID ?= $(shell id -g)` at the top so `make up`/`make crawl`
    pass them; `.env.example` documents both (compose also reads `.env`).
  - `ops/README.md`: the one-time command `sudo chown -R $(id -u):$(id -g) data/raw data/exports` and why `data/pg` stays
    root/postgres-owned.
- Contract: system.md §5 (compose, loopback); codebase.md §6 "Crawl one date".
- Acceptance (manual, recorded in `3-build` with real output): after `make up && make crawl DATE=<today> ` (or `--only FPT`),
  `find data/raw -newer docker-compose.yml ! -user $(id -u) | wc -l` prints `0`; `docker compose run --rm crawler --help`
  exits 0 as the mapped user (`id -u` inside = host uid); `make up` still serves `GET 127.0.0.1:8000/health` 200.
- Out of scope: systemd units (BE-scheduler); deleting the 1,186 stale tapes (OPS-cleanup-1015).

#### BE-calendar — F-003: `finvest_rules` package with the trading calendar as data; CLI refuses non-trading days
- Story: F-003 ; Side: be ; Effort: medium ; Size: ~150 lines ; Lead: sonnet
- Files: `packages/market_rules/pyproject.toml`, `packages/market_rules/finvest_rules/__init__.py`,
  `packages/market_rules/finvest_rules/calendar.py`, `packages/market_rules/finvest_rules/holidays.csv`,
  `packages/market_rules/tests/test_calendar.py`, `pyproject.toml` (workspace member, import-linter contract
  `finvest_rules` imports nothing of ours), `uv.lock`, `services/crawler/pyproject.toml` (dependency),
  `services/crawler/finvest_crawler/cli.py` (replace the weekend guard), `services/crawler/tests/test_cli.py`
- Change:
  - `holidays.csv` columns `date,kind,name,source` (`kind ∈ holiday|half`), one row per closed weekday, 2025-01-01 →
    2026-12-31. 2026 rows from data.md §1.3 (VSE notice 1403/SGDVN-THHC: 01/01; Tết 16–20/02; 27/04; 30/04–01/05;
    31/08–02/09; Sat 22/08 not a trading day). 2025 rows from the HOSE notice the developer finds (cite the URL in `source`).
  - `calendar.py` (pure, no I/O beyond reading the packaged CSV once): `@dataclass(frozen=True) CalendarDay(trading_date,
    venue, is_open, kind, name)`; `day(d: date, venue: str = "HOSE") -> CalendarDay` → weekend → `kind="weekend"`, CSV row →
    its kind/name, else `trading`; `trading_days(start: date, end: date, venue="HOSE") -> list[date]` (inclusive). Dates
    outside the CSV's year range raise `CalendarNotMaintained(year)` — never infer (VN§2, backlog F-003 "nothing is inferred").
    `shortcut: one holiday list for all venues (venue is accepted and echoed), split when a venue-specific closure appears`.
  - `cli.py` `ticks`: replace the Saturday/Sunday guard with `day(date).is_open`; closed → print
    `{"skipped": "<kind>", "name": ...}` and exit 0, no manifest, no DB row (S01 decision (c) kept; data.md §4 last line).
- Contract: data.md §1.3 (calendar row), §4 ("Non-trading days per trading_calendar → exits immediately"); platform.md §2
  `GET /calendar` payload fields (the dataclass mirrors them; the endpoint itself is F-021/F-005 work); VN§2.
- Acceptance:
  - `day(date(2026,9,2)).kind == "holiday"` with name containing "Quốc khánh"; `day(date(2026,8,22)).is_open is False`;
    `day(date(2026,10,16)).kind == "trading"`; `day(date(2026,10,18)).kind == "weekend"`.
  - `trading_days(2026-08-28, 2026-09-03) == [08-28, 09-03]`; `day(date(2027,1,4))` raises `CalendarNotMaintained`.
  - CLI: `finvest-crawl ticks --date 2026-09-02` exits 0, prints the skip line, writes no `_manifest.json`.
  - `uv run lint-imports` passes with the new contract; `make test-kernel` collects `packages/market_rules/tests`.
- Out of scope: `trading_calendar` DB table and `GET /calendar` (arrive with the first API reader, F-021/F-005); session
  phases (F-005); gap reporting (F-021 — the gap record itself is the `missed` manifest written by BE-scheduler).

#### BE-scheduler — F-019: `catchup` command + systemd user timer (15:30, 20:00, boot) + `make install-timers`
- Story: F-019 ; Side: be ; Effort: medium ; Size: ~200 lines ; Lead: opus
- Files: `services/crawler/finvest_crawler/feeds/catchup.py`, `services/crawler/finvest_crawler/cli.py` (add `catchup`
  sub-command), `packages/market_data/finvest_market_data/infrastructure/repositories.py` (add `last_session_date(conn,
  feed) -> date | None` only), `ops/systemd/finvest-crawl.service`, `ops/systemd/finvest-crawl.timer`, `Makefile`
  (`install-timers`, `uninstall-timers`), `ops/README.md`, `services/crawler/tests/test_catchup.py`,
  `services/crawler/tests/test_cli.py`
- Change:
  - `catchup(settings, *, now_vn: datetime, conn, repo, run=run_ticks) -> list[Manifest]`: `start = last_session_date("ticks")
    + 1 day` or `now_vn.date()` if none; `end = now_vn.date()` if `now_vn.time() >= 15:05` else the day before; for each
    `trading_days(start, end)` (BE-calendar): status = `repo.session_status(conn, "ticks", d)`; skip when `complete` or
    `missed`; else `run_ticks(settings, d, None, ...)`. Catch `SystemExit`/exceptions per day: log, continue, and exit non-zero
    at the end if any day ended `blocked`/`failed` (so the 20:00 timer shows red; platform.md §4 "exit non-zero").
  - A past day runs `ticks` once and lands as `missed/source_no_longer_serves` (data.md §1.2 K1; 1-sprint-plan note 1) and
    is then final; a holiday is never visited (F-003 criterion 2); a weekday trading date with no session gets its `missed`
    manifest (F-003 criterion 3 — this is the gap record).
  - `ops/systemd/finvest-crawl.timer`: `OnCalendar=Mon..Fri *-*-* 15:30:00 Asia/Ho_Chi_Minh` and `…20:00:00…`,
    `Persistent=true`, `[Install] WantedBy=timers.target`. `finvest-crawl.service`: `Type=oneshot`,
    `WorkingDirectory=__FI_ROOT__`, `ExecStartPre=/bin/sh -c 'for i in $(seq 36); do docker info >/dev/null 2>&1 && exit 0;
    sleep 5; done; exit 1'`, `ExecStart=/usr/bin/docker compose run --rm crawler catchup`, `Environment=FINVEST_UID=… GID=…`
    via `EnvironmentFile=-%h/.config/finvest/env` written by `make install-timers`.
  - `make install-timers`: sed `__FI_ROOT__` → `$(CURDIR)`, copy to `~/.config/systemd/user/`, write the env file,
    `systemctl --user daemon-reload && systemctl --user enable --now finvest-crawl.timer`, `loginctl enable-linger $$USER`;
    prints `systemctl --user list-timers finvest-crawl.timer`. `make uninstall-timers` reverses it.
  - `ops/README.md`: install, verify (`list-timers`, `journalctl --user -u finvest-crawl.service`), manual re-run stays
    `make crawl DATE=`.
- Contract: ADR-S-009 incl. 2026-10-16 amendment; data.md §4 (catch-up paragraph); platform.md §4 (status/reason enums,
  exit non-zero on blocked); system.md §5 (systemd user units, linger); VN§2 (15:00 close → 15:05 cut-off).
- Acceptance:
  - Unit (fake repo + fake `run`): last session 2026-08-27, `now_vn = 2026-09-03 15:30` → runs exactly 08-28 and 09-03
    (09-02 holiday, 08-29/30 weekend, 08-31/09-01 holidays); `now_vn = 2026-09-03 09:00` → runs 08-28 only.
  - Statuses: `complete` and `missed` days are skipped; `partial`/`blocked`/`failed`/`None` days run; a day whose run raises
    is logged and the others still run; process exit 2 if any day ended `blocked`.
  - No session rows at all → only today is considered (no silent back-walk into history).
  - `finvest-crawl catchup --help` exits 0; `make install-timers` on the sponsor's machine lists the timer with the next
    elapse at 15:30 VN (recorded in `3-build`).
  - Live (M2, not a PR gate; owner sm): Thu 2026-10-22 15:30 manifest written with no manual action (`journalctl --user -u
    finvest-crawl.service` shows the run).
- Out of scope: `POST /jobs` API (platform.md §2, later), `close_snapshot`/other feeds in the timer (`catchup` runs `ticks`
  only; add feeds when they exist), priority order F-018, back-fill scheduling (manual, BE-bars-backfill).

#### BE-symbols-feed — F-004 core: `symbols` table + daily `symbols` feed from V3 (delisted kept, idempotent)
- Story: F-004 ; Side: be ; Effort: high ; Size: ~230 lines ; Lead: sonnet
- Files: `apps/api/migrations/versions/0003_symbols.py`, `packages/market_data/finvest_market_data/domain/models.py`
  (`SymbolRecord` gains `listed_at: date | None = None`, `delisted_at: date | None = None`),
  `packages/market_data/finvest_market_data/infrastructure/tables.py`, `…/infrastructure/repositories.py`
  (`upsert_symbols`, `mark_delisted`, `list_symbols`), `services/crawler/finvest_crawler/adapters/vci/source.py`
  (`parse_symbols(payload, raw_path, include_delisted=False)`), `services/crawler/finvest_crawler/feeds/symbols.py`,
  `services/crawler/finvest_crawler/cli.py` (add `symbols` sub-command), `packages/market_data/tests/test_repositories_db.py`,
  `services/crawler/tests/test_adapter_vci.py`, `services/crawler/tests/test_feed_symbols.py`, `services/crawler/tests/test_cli.py`
- Change:
  - Migration 0003: `symbols` as data.md §3 (`exchange CHECK IN ('HOSE','HNX','UPCOM')`, `type`, names, `icb_code2`,
    `listed_at`, `delisted_at`, `is_delisted`, `source`, `fetched_at`). `icb_sectors` deferred (names need V5, F-014).
  - `parse_symbols(..., include_delisted=True)` also returns board `DELISTED` rows with `is_delisted=True`; their `exchange`
    is unknown on V3 → keep the last known exchange from the table when present, else `UPCOM` and anomaly rule
    `delisted_exchange_unknown` (data.md §3 `data_anomalies`). The ticks universe keeps calling the default (`False`) — the
    feed's universe is unchanged (1-sprint-plan note 2).
  - `run_symbols(settings, run_date, *, fetcher, conn, repo) -> int`: `insert_crawl_run("symbols")`; `source.symbols(run_date)`
    with `include_delisted=True` (archive `data/raw/symbols/<run_date>/getAll.json.gz`, shared with the ticks universe —
    same file, replayed); `upsert_symbols` (`ON CONFLICT (symbol) DO UPDATE` names/exchange/type/icb/`is_delisted`/
    `fetched_at`; `delisted_at = COALESCE(delisted_at, run_date)` when `is_delisted`, never cleared on re-listing — log
    anomaly `relisted` instead); `mark_delisted(conn, present: set[str], run_date)` sets `is_delisted=true, delisted_at =
    COALESCE(delisted_at, run_date)` for rows absent from the payload; `finish_crawl_run`. Summary JSON line with counts.
  - `cli.py` `symbols [--date]`: runs the feed; exit 2 on `SourceBlocked`.
- Contract: platform.md §4 "Other feeds" (`symbols` row, delisting semantics); §2 `GET /symbols` fields (table columns
  mirror them); data.md §1.2 V3 (3,683 rows incl. 234 DELISTED), §3 `symbols`, §4 `symbols` feed row; ADR-S-008 archive-first.
- Acceptance:
  - Fixture `vci/symbols_getAll/sample` (41 rows, boards BOND/DELISTED/HNX/HSX/UPCOM): default parse excludes BOND, CW,
    DELISTED (count as today); `include_delisted=True` adds the DELISTED STOCK rows with `is_delisted=True`; BOND still excluded.
  - `@pytest.mark.db`: run twice on the same fixture → identical `SELECT * FROM symbols ORDER BY symbol` (F-004 criterion 3),
    `requests == 1` then `0`; a second fixture with one symbol removed → that row `is_delisted=true`, `delisted_at ==
    run_date`, row count unchanged (criterion 2); third run with it back → `is_delisted=false`, `delisted_at` kept, anomaly
    `relisted` written.
  - Live (`3-build`, after 15:20 any day): `make crawl` unchanged; `docker compose run --rm crawler symbols` → `SELECT
    exchange, is_delisted, count(*)` roughly HOSE ~427, HNX ~299, UPCOM ~815, delisted ~234 (data.md §1.2 V3).
- Out of scope: listing dates, index membership (BE-symbols-enrich); `icb_sectors`; `GET /symbols` endpoint; changing the
  ticks universe source string (`vci:symbols/getAll` stays until the feed reads the table — F-004 follow-up at review).

#### S-index-members — spike: a free index-constituents endpoint (VN30/HNX30/UPCoM) and an S1 listings fixture
- Story: F-004 ; Side: be ; Effort: medium ; Size: ~40 lines ; Lead: sonnet
- Files: `services/crawler/tests/fixtures/vci/index_members/*.json.gz` and/or `services/crawler/tests/fixtures/ssi/index_members/*.json.gz`,
  `services/crawler/tests/fixtures/ssi/exchange/hose.json.gz` (≤ 50 rows, envelope kept), `SPRINT_DIR/3-build.S-index-members.md`
- Change (no production code):
  - Probe, anonymous, ≤ 2 req/s, from the sponsor's machine with `curl`: VCI `GET https://trading.vietcap.com.vn/api/price/symbols/getByGroup?group=VN30`
    (also `HNX30`, `UPCOMLARGE` if `VN30` answers) and SSI `GET https://iboard-query.ssi.com.vn/stock/group/VN30`. Record
    status, row count, the field that carries the symbol, whether the list is the *current* constituents only (expected:
    no history), and the response for an unknown group.
  - Record S1 `GET https://iboard-query.ssi.com.vn/stock/exchange/hose` trimmed to 50 rows: confirm `firstTradingDate`
    is present and its format (data.md §1.2 S1 lists it; the format is unverified).
  - Report in `3-build.S-index-members.md`: one data.md §1.2-style row per endpoint (source, serves, grain, verdict) for the
    architect to paste, plus the fixture paths. If nothing answers, say so — `BE-symbols-enrich` then drops membership.
- Contract: data.md §1.2 (format of a row), §1.3 "Symbol master incl. delisted"; common.md "free sources only, cache everything".
- Acceptance: fixtures committed (≤ 20 KB each, gzip, exact bytes), the report names for each probed URL the HTTP status,
  row count and symbol field; `make test-kernel` unaffected (no tests added).
- Out of scope: any adapter or table code; ICB sector names (V5, F-014).

#### BE-bars-store — F-012 storage: `bars_1d_src` + `index_1d` tables, repositories, V2 `value` and index parsing
- Story: F-012 ; Side: be ; Effort: high ; Size: ~150 lines ; Lead: opus
- Files: `apps/api/migrations/versions/0004_bars_1d_src_index_1d.py`, `packages/market_data/finvest_market_data/infrastructure/tables.py`,
  `…/infrastructure/repositories.py` (`upsert_bars_1d_src`, `upsert_index_1d`, `daily_coverage(conn) -> dict[str, Decimal]`),
  `packages/market_data/finvest_market_data/domain/models.py` (`Bar.trading_date` property or helper; `IndexBar` if the
  developer prefers a separate type — keep `Bar` if `symbol` can carry `VNINDEX`), `services/crawler/finvest_crawler/adapters/vci/payloads.py`
  (`accumulatedValue: list[Decimal]`), `services/crawler/finvest_crawler/adapters/vci/source.py` (`parse_bars` fills `value`),
  `packages/market_data/tests/test_repositories_db.py`, `services/crawler/tests/test_adapter_vci.py`
- Change:
  - Migration 0004: `bars_1d_src` per data.md §3 (+ `value BIGINT`), PK `(symbol, trading_date, source, fetched_at)`;
    `index_1d(index_code, trading_date, o,h,l,c NUMERIC(12,2), v, value, PK(index_code, trading_date))`.
  - `parse_bars`: `value = round_half_up(accumulatedValue[i] × 1_000_000)` as int VND; o/h/l/c rounded half-up to int VND
    (platform.md §2.2 "rounded half-up to 1 VND"); `t` epoch seconds → `trading_date` in VN (ADR-S-006).
  - `upsert_bars_1d_src(conn, bars, fetched_at: datetime)` → `INSERT … ON CONFLICT DO UPDATE` (idempotent for the same
    `fetched_at`); `upsert_index_1d` likewise keyed `(index_code, trading_date)` — index levels keep 2 decimals (platform.md
    §1.2 "index levels decimal").
  - `daily_coverage(conn)`: per exchange, `symbols with ≥ 1 bars_1d_src row / symbols` (delisted included), as decimal
    strings with 1 digit — the number platform.md §2.3 `daily_coverage_pct` will read.
- Contract: platform.md §4 "Other feeds" (`bars_1d`, value unit, fetched_at = archive mtime), §1.2 (integer VND, index
  decimals), §2.2 (rounding); data.md §1.2 V2 (adjusted prices; `accumulatedValue` million VND nominal), §1.4 (2) (versioned
  snapshots), §3 `bars_1d_src`, `index_1d`; ADR-S-005, ADR-S-006.
- Acceptance:
  - Worked example, fixture `vci/gap_chart/FPT-1d` first bar (`t=1785801600`): `o=65819, h=66637, l=64819, c=65001`
    (half-up from 65818.84/66637.03/64818.83/65000.65), `v=6618016`, `value=474963630000`; sanity `value / v == 71768` VND
    ≈ nominal price (adjusted close × 1.1 bonus) — assert `value // v` between `l` and `h × 1.15`.
  - `@pytest.mark.db`: upsert the fixture twice with the same `fetched_at` → row count unchanged; with a later `fetched_at`
    → a second version per bar; `daily_coverage` on a 3-symbol `symbols` table with 2 covered → `{"HOSE": "66.7", …}`.
  - `alembic upgrade head` / `downgrade -1` round-trip on the compose db.
- Out of scope: the back-fill loop and CLI (BE-bars-backfill); nominal `bars_1d` reconstruction (F-015); SSI cross-check (F-016).

#### BE-bars-backfill — F-012 feed: back-fill every symbol (incl. delisted) and VNINDEX/VN30 with resume + coverage %
- Story: F-012 ; Side: be ; Effort: high ; Size: ~200 lines ; Lead: sonnet
- Files: `services/crawler/finvest_crawler/feeds/bars_1d.py`, `services/crawler/finvest_crawler/cli.py` (add `bars`
  sub-command), `services/crawler/tests/test_feed_bars_1d.py`, `services/crawler/tests/fixtures/feeds/bars_1d/*.json.gz`
  (FPT + one zero-bar symbol, derived from `vci/gap_chart/FPT-1d`), `services/crawler/tests/test_cli.py`, `Makefile` (`backfill` target)
- Change:
  - `run_bars_1d(settings, run_date, *, only, fetcher, conn, repo, today) -> Manifest`: universe = `repo.list_symbols(conn,
    include_delisted=True)` + indices `["VNINDEX", "VN30"]`; `insert_crawl_run("bars_1d")`; per name
    `source.bars([name], "1d", to=run_date, count=6000)` → zero bars → `symbols_no_trades`; `PayloadShapeError`/HTTP →
    `symbols_skipped` with the ticks reasons; `SourceBlocked` → `blocked`, rest skipped, exit 2; else `upsert_bars_1d_src(…,
    fetched_at = archive file mtime)` (indices → `upsert_index_1d`); canonical lines → checksum (platform.md §4 bars line);
    `commit()` per symbol so an interrupt loses at most one symbol.
  - Resume = re-run: every archived payload replays (`requests` excludes replays), unarchived names are fetched; identical
    rows and checksum when nothing changed upstream (ADR-S-008). Manifest `universe.source = "symbols table"`.
  - End: `daily_coverage` printed in the summary line `{"summary": …, "coverage": {"HOSE": "99.8", …}}` and in `3-build`.
  - `cli.py` `bars --date <run_date> [--only]`; `make backfill` → `docker compose run --rm crawler bars`. The developer runs
    it live **outside 15:00–23:00 VN** (shared rate budget, 1-sprint-plan note 3).
- Contract: platform.md §4 (manifest keys, bars checksum line, `requests` excludes replays, exit codes); data.md §1.2 V2
  (daily since 2006-12-13, indices `VNINDEX` since 2004), §4 `bars_1d_src` row; ADR-S-008.
- Acceptance:
  - Fixtures (2 symbols + fake `symbols` repo): first run `status == "complete"`, `symbols_fetched == 1`,
    `symbols_no_trades == ("ZZZ",)`, `rows == 50`, `requests == 2`; second run → identical checksum, `requests == 0`.
  - Interrupt test: fake repo raises on the second symbol → `crawl_runs` closed `failed`; re-run completes with
    `requests == 1` and the same row set as an uninterrupted run (F-012 criterion 2).
  - Blocked on symbol 2 → `blocked`, exit code 2, symbol 1 rows kept.
  - Live (M3, `3-build`): `make backfill` finishes; `SELECT count(DISTINCT symbol) FROM bars_1d_src` ≥ 1,500; FPT earliest
    `trading_date = 2006-12-13`; coverage per exchange printed (G2 target ≥ 99.5 %; shortfall listed by symbol in `3-build`,
    criterion 3 is the sprint's first-to-slip item).
- Out of scope: daily incremental update (F-013), 1m bars, nominal reconstruction (F-015), scheduling the back-fill.

#### BE-symbols-enrich — F-004 rest: listing dates from S1, index-membership history from the spike's endpoint
- Story: F-004 ; Side: be ; Effort: medium ; Size: ~200 lines ; Lead: sonnet
- Files: `apps/api/migrations/versions/0005_symbol_index_membership.py`, `packages/market_data/finvest_market_data/domain/ports.py`
  (add `index_members(self, index_code: str, as_of: date) -> list[str]`; `kbs`/`vci`/`ssi` raise `Unsupported` where absent),
  `packages/market_data/finvest_market_data/infrastructure/tables.py`, `…/infrastructure/repositories.py`
  (`upsert_listed_at`, `sync_index_membership`), `services/crawler/finvest_crawler/adapters/ssi/source.py` +
  `…/ssi/payloads.py` (`symbols(as_of)` from the three S1 exchange calls → `SymbolRecord` with `listed_at`),
  `services/crawler/finvest_crawler/adapters/<spike source>/source.py` (`index_members`), `services/crawler/finvest_crawler/feeds/symbols.py`
  (two extra steps), `services/crawler/tests/test_adapter_ssi.py`, `services/crawler/tests/test_feed_symbols.py`,
  `packages/market_data/tests/test_repositories_db.py`
- Change:
  - `SsiSource.symbols(as_of)`: 3 calls (`hose|hnx|upcom`, archive `data/raw/symbols/<as_of>/<exchange>.json.gz`), returns
    `SymbolRecord(..., listed_at=firstTradingDate)` parsed per the spike's fixture format; `run_symbols` step 2:
    `upsert_listed_at` for symbols present in both (`listed_at` only set when NULL — the source value is the truth, ours
    never older).
  - Migration 0005: `symbol_index_membership(index_code, symbol, valid_from, valid_to, PK(index_code, symbol, valid_from))`
    (data.md §3). `sync_index_membership(conn, index_code, members, run_date)`: new symbol → row `valid_from=run_date,
    valid_to=NULL`; open row whose symbol is absent → `valid_to=run_date`; unchanged → no write (idempotent). History
    starts at crawl start (1-sprint-plan note 2).
  - `run_symbols` step 3: for each index the spike confirmed (`VN30` at least) `source.index_members(idx, run_date)` →
    `sync_index_membership`. If the spike found no endpoint: skip step 3, remove `0005`/membership code from this task and
    say so in `3-build` (size then ≈ 110).
- Contract: platform.md §2 `GET /symbols/{symbol}` `index_memberships` shape (table mirrors it), §4 "Other feeds";
  data.md §1.2 S1 (`firstTradingDate`), §3 `symbol_index_membership`; the spike's `3-build.S-index-members.md` for the
  index endpoint and fixture.
- Acceptance:
  - S1 fixture (`ssi/exchange/hose`): every row yields `listed_at` as a `date`; a row without the field → `listed_at=None`,
    no exception.
  - `@pytest.mark.db`: `sync_index_membership("VN30", {A,B}, d1)` then `({B,C}, d2)` → rows `A[d1,d2] B[d1,∞) C[d2,∞)`;
    running `({B,C}, d2)` again changes nothing; `upsert_listed_at` never overwrites a non-NULL value.
  - Feed on fixtures: `run_symbols` makes 1 (V3) + 3 (S1) + n (indices) requests the first time, 0 on replay.
- Out of scope: index history before crawl start; ICB sector names; `GET /symbols` endpoints.

#### QA-S02-live — S02-3: live acceptance re-run (tester): 10-16 checksum unchanged, 10-14 `missed`
- Story: S02-3 ; Side: be ; Effort: medium ; Size: ~0 lines (no code; `4-test.be.md`) ; Lead: sonnet
- Files: `SPRINT_DIR/4-test.be.md` (tester's report; no code)
- Change: manual, by the BE tester after BE-status-no-trades is merged and `make up` rebuilt: `make crawl DATE=2026-10-16`
  → compare `data/raw/ticks/2026-10-16/_manifest.json` against the recorded S01 numbers; `make crawl DATE=2026-10-14`.
- Contract: platform.md §4 (status rule v1.3, `missed/source_no_longer_serves`); ADR-S-008 (replay idempotence).
- Acceptance: 10-16 → `status == "complete"`, `rows == 145184`, checksum identical to the S01 manifest, `symbols_fetched ==
  911`, `len(symbols_no_trades) == 629`, `requests == 629` (no-trade names are asked again; archived tapes replay); 10-14 →
  `status == "missed"`, `reason == "source_no_longer_serves"`, `requests == 2`; `crawl_sessions` rows agree with both files.
- Out of scope: any code change (file a bug in `4-test.be.md` instead).

#### OPS-cleanup-1015 — S02-4: remove the 1,186 stale empty 10-15 tapes without sudo, re-manifest 10-15
- Story: S02-4 ; Side: be ; Effort: medium ; Size: ~0 lines (ops; commands recorded in `3-build.OPS-cleanup-1015.md`) ; Lead: opus
- Files: `data/raw/ticks/2026-10-15/*.json.gz` (data, not code), `SPRINT_DIR/3-build.OPS-cleanup-1015.md`
- Change: manual, by the SM/sponsor after OPS-host-user (ownership) and BE-status-no-trades (status rule) are merged:
  1. `sudo chown -R $(id -u):$(id -g) data/raw` (the one documented command, ops/README.md).
  2. `for f in data/raw/ticks/2026-10-15/*.json.gz; do [ "$(gunzip -c "$f")" = '{"data":[]}' ] && rm "$f"; done` — count
     before/after (expected 1,186 removed; `_manifest.json` untouched by the glob? it is `.json`, not `.json.gz`).
  3. `make crawl DATE=2026-10-15` → archive replays the 354 accepted tapes, the first unarchived symbol returns another
     session → `partial`, `reason source_no_longer_serves`, untouched names listed.
- Contract: platform.md §4 (code never deletes; archive-only-after-accept; `partial/source_no_longer_serves` listing);
  5-review.tech.md "Decisions (architecture)" last bullet.
- Acceptance: `find data/raw -user root | wc -l` = 0; `ls data/raw/ticks/2026-10-15/*.json.gz | wc -l` = 354; new 10-15
  manifest `status == "partial"`, `symbols_fetched == 354`, `len(symbols_skipped) == 1186` all with reason
  `source_no_longer_serves`, `rows` equals the 10-15 tick count in the DB (`SELECT count(*) FROM ticks WHERE ts::date AT TIME
  ZONE 'Asia/Ho_Chi_Minh' = '2026-10-15'`).
- Out of scope: recovering the lost 10-15 ticks (impossible, data.md §1.2 K1); code changes.
