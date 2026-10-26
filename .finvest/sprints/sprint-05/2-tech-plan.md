# Sprint 05 — Tech plan (BE / FE / ops; AI blocks of `2-tech-plan.ai.md` merged into dag.json)

Owner: `fi-software-architect`, 2026-10-26, plan v1.3 (v1.2 = `2-tech-plan.prev-4.md`; v1.3 = BE-recon-s2 round 2: no slack, aligned with the AI answer — `self_check=(source == "vci")`, after AI-recon-xsrc, crawler file set only, size ~90; v1.1 = `2-tech-plan.prev-3.md`; v1.2 = BE-recon-s2 per the consult: `reconcile(slack_vnd)` (withdrawn in v1.3); v1.0 = `2-tech-plan.prev-2.md`; v1.1 = BE-ca-recompute round 2 per the consult: per-version `last`, watermark recompute set, queries in the repo, size ~340; new BE-mv-basis; v0 = `2-tech-plan.prev-1.md`). Inputs: `1-sprint-plan.md`, `2-tech-plan.ai.md` (3 AI tasks + the
"SA-owned" list), `product/backlog.md` F-013/F-014/F-015/F-016/F-023/F-033, `architecture/data.md` **v1.4** (§1.2 V5/S2 spike
lines, §1.4, §3), `contracts/platform.md` **v1.14** (§2.6 step 3), `product/ux/app-shell.md` §Crawl button,
`product/ux/visual-design.md` §4/§6.3/§6.4/§9, `sprints/sprint-04/6-retro.md` R1–R5, branch `sprint-05` = main `0de35b7`.

## M0 spike (done at planning, 5 calls by hand, `sprints/sprint-05/spike/`)
- **V5:** `toDate` is required and both dates are `YYYYMMDD` (3 other forms → body `status 400 "Invalid datetime"`); cash
  events carry **`valuePerShare`** (VND) and **`payoutDate`**; share issues carry `exerciseRatio` (bonus 10 % = 0.1) and
  `listingDate`; ESOP issues ("Phát hành cho CBCNV") are `ISS` with tiny ratios; page envelope `data.{content, totalPages, last}`.
  Block behaviour **not observed** in 4 calls → budget **B = 40 requests per press** at 1 req/s, 3 blocked → `SourceBlocked`
  (data.md §1.2 V5). Fixture for G12 and the adapter tests: `spike/v5-call4.json` (FPT 2026: bonus ex 2026-09-21, cash
  1,000 ex 2026-05-28, 2 ESOP).
- **S2:** HPG 1D answered in 0.42 s, thousand VND, same envelope as `services/crawler/tests/fixtures/ssi/history/FPT-1d.json.gz`;
  no block seen (data.md §1.2 S2). V2 rows for G12 already exist in `fixtures/vci/gap_chart/FPT-1d.json.gz`
  (2026-09-18 close 65,182.47; 2026-09-21 66,400).
- `[assumed]` ESOP issues do not move the exchange reference price → stored as `listing_change` (factor 1), anomaly-free;
  the AI architect confirms or corrects in VN§6 at review (no sponsor question: data rule, not scope).

## Decisions for this sprint
- **Nominal lives in `bars_1d`, adjusted in `bars_1d_src`.** Migration 0010 creates `bars_1d` (data.md §3, with `ref` and
  `nominal_kind`) and **moves** today's `source='ssi'` board rows out of `bars_1d_src` (they are nominal; a VN30 ex-date after
  crawl start would otherwise poison the newest-version pick in `SqlMarketView.bars_1d`). From then on `bars_1d_src.source='ssi'`
  means S2 history (cross-check), `'vci'` = V2.
- **What the simulator reads this sprint (unchanged basis, `price_basis = "source_adjusted"`):** `bars_1d_src` newest version
  ∪ observed `bars_1d` rows for dates the source has no row for, each observed close × Π factors over ex-dates in
  `(d, today]` (R7 `ours`), rounded half-up to integer VND. Until BE-market-view-ca lands, BE-observed-bar serves the observed
  rows unscaled (`shortcut:` comment; correct while no VN30 ex-date lies inside the ~2-week observed overlap — the recon run
  would show it). Charts' true adjusted series (R5, `adjusted_close`) comes with BE-market-view-ca; the engine does not switch
  to nominal (F-043/F-044, R2).
- **Step 3 budget and order** (platform.md §2.6 v1.14): B = 40 V5 requests/press; symbols in order VN30 → saved-scenario
  symbols → `symbols.ca_checked_at NULLS FIRST, oldest first`; every read is a full pull (`fromDate=20100101`,
  `toDate=run_date+400d`, pages until `last`) so the diff log sees corrections to old events; a symbol costs
  `ceil(totalElements/50)` requests (FPT ≈ 1–2). ~1,600 names ≈ 40 presses to the first full coverage; VN30 on press 1.
- **Recompute set per press** (v1.1, platform.md §2.6 v1.15) = `changed_symbols` ∪ names whose newest vci `bars_1d_src.fetched_at`
  is newer than their newest `reconstructed` `bars_1d.fetched_at` (or that have no reconstructed row), restricted to
  `ca_checked_at IS NOT NULL` (a name V5 never read would otherwise get `reconstructed = adjusted`, silently wrong). A watermark,
  not "wrote this press": `fetched_at` is the archive mtime, so a replay, a blocked step 2 or a failed step 3 would otherwise lose
  names until gap rotation (~40 presses). Reconstructed rows carry the newest src `fetched_at`, so the set empties itself.
- **Source versions mix** (data.md §1.4 (4)): after the first full pull, step 2 adds ~5-row versions; "newest row per date" is
  therefore a mix of versions and each row must be divided by the G of its own version (`last_v` = max `trading_date` of the
  row's `fetched_at` group; AI plan R6a, task AI-adjust-version). The simulator basis must stop reading `bars_1d_src` (BE-mv-basis).
- **Crawler imports `finvest_analytics.adjust`** (pure functions) — allowed by the import-linter contracts (only
  analytics → crawler/api is forbidden). No new package, no new dependency.
- **Compose isolation** (tester.md §8): live stack = project `finvest-live` on 8080/8001; tests use `docker-compose.test.yml`
  (OPS-guards) with another project name and ports 18080/18001/15432. Nobody stops `gw-app@finance_invest`.
- **Sizes** count prod + tests (A24-D1 open). Shared-line rule (retro R4): `runner.py`, `market_view.py`, `repositories.py`,
  `cli.py`, `i18n/*.json`, `setup.ts` edits are ordered with `after` below; no two concurrent tasks touch the same file.
- UI build notes attach a 1280 light shot (retro R3, dev.md step 6); `apps/web/e2e/` reaches the sprint branch first
  (FE-e2e-carry) so devs can run `screens.mjs`.

## Order and lanes

```
BE-1  BE-mig-0010 → BE-observed-bar → BE-ca-recompute (after AI-adjust-series, AI-adjust-version) → BE-recon-cli (after AI-recon-rules) → BE-recon-s2 (after AI-recon-xsrc)
BE-2  BE-v5-adapter → BE-ca-repo (after BE-mig-0010) → BE-ca-step3 (after BE-observed-bar) → BE-market-view-ca (after AI-adjust-series) → BE-mv-basis (after BE-ca-recompute) → OPS-guards (any time)
AI-1  AI-ca-factors → AI-adjust-series → AI-recon-rules → AI-adjust-version → AI-recon-xsrc   (2-tech-plan.ai.md v1.2)
FE-1  FE-e2e-carry → FE-crawl-step3 → FE-rw → FE-shots (tester, manual)
```
Milestones: M1 = BE-mig-0010, BE-observed-bar, BE-v5-adapter, BE-ca-repo, BE-ca-step3, OPS-guards, AI-ca-factors, FE-e2e-carry,
FE-crawl-step3, FE-rw · M2 = AI-adjust-series, AI-recon-rules, AI-adjust-version, BE-ca-recompute, BE-market-view-ca, BE-mv-basis, BE-recon-cli, BE-recon-s2 ·
M3 = FE-shots. M0 was done by the architect at planning (no dag task). L1–L3 are sm/sponsor clock milestones.
**Slip order:** BE-recon-s2, then FE-rw, then BE-mv-basis (v1.1; slipping it leaves the simulator on mixed src versions — PM/sponsor call). Never: BE-ca-step3, BE-ca-recompute.

## Tasks

#### BE-mig-0010 — F-013/F-014: migration 0010 (CA tables, `adj_factors`, nominal `bars_1d`, `recon_mismatches`) and the SSI row move
- Story: F-013, F-014 ; Side: be ; Effort: high ; Size: ~200 lines ; Lead: opus
- Files: `apps/api/migrations/versions/0010_corporate_actions_bars_1d.py` (new), `packages/market_data/finvest_market_data/infrastructure/tables.py`,
  `packages/market_data/finvest_market_data/infrastructure/repositories.py` (only `upsert_bars_1d`, `move_ssi_board_rows`),
  `packages/market_data/tests/test_repositories_db.py`
- Change:
  - `tables.py`: `bars_1d`, `corporate_actions` (+ `public_date DATE`, `title TEXT` for the raw `eventTitleVi`), `corporate_action_log`,
    `adj_factors`, `recon_mismatches` exactly as data.md §3; `symbols.ca_checked_at TIMESTAMPTZ`. Types: prices BIGINT, `factor NUMERIC(20,12)`,
    `diff_pct NUMERIC(8,4)`, `nominal_kind` CHECK, `UNIQUE(source, source_event_id)`.
  - Migration 0010 (style of 0009): create the tables/column with `op.create_table` from the same definitions, then
    `move_ssi_board_rows(conn)`: `INSERT INTO bars_1d` the newest `fetched_at` row per `(symbol, trading_date)` of `bars_1d_src WHERE source='ssi'`
    (`nominal_kind='observed'`, `ref NULL`, `source='ssi'`), then delete those `bars_1d_src` rows; print the count. Downgrade reverses the move
    and drops the tables (observed rows must not be lost on downgrade).
  - `upsert_bars_1d(conn, bars, *, nominal_kind, fetched_at, ref: dict[str, int] | None = None) -> int`: `ON CONFLICT (symbol, trading_date) DO UPDATE …
    WHERE bars_1d.nominal_kind <> 'observed' OR excluded.nominal_kind = 'observed'` — an observed row is never replaced by a reconstruction
    (F-015 last criterion); returns rows written.
- Contract: data.md §1.4 (1), §3; ADR-S-001.
- Acceptance (`db` marker): migrate up on a throwaway db with 2 `ssi` + 1 `vci` row in `bars_1d_src` → `bars_1d` has the 2 observed rows,
  `bars_1d_src` keeps only `vci`; down then up again is idempotent; `upsert_bars_1d` of a `reconstructed` 93,499 over an `observed` 93,500 leaves
  93,500 / `observed` (G9); an `observed` over `reconstructed` wins; `alembic heads` = 0010.
- Out of scope: writing the board bar into `bars_1d` from the feed (BE-observed-bar), CA/factor/recon repo functions (BE-ca-repo), any read path.

#### BE-observed-bar — F-013: the S1 board bar lands in `bars_1d` (observed, with `ref`); deferred count; read path keeps serving the day
- Story: F-013 ; Side: be ; Effort: high ; Size: ~190 lines ; Lead: opus
- Files: `packages/market_data/finvest_market_data/domain/models.py` (`Bar.ref: int | None = None`, last field), `services/crawler/finvest_crawler/adapters/ssi/payloads.py`
  (`refPrice`), `services/crawler/finvest_crawler/adapters/ssi/source.py` (`parse_snapshot` fills `ref`), `services/crawler/finvest_crawler/feeds/bars_1d.py`,
  `apps/api/finvest_api/jobs/runner.py` (`symbols_deferred`), `apps/api/finvest_api/market_view.py`, `services/crawler/tests/test_feed_bars_1d.py`,
  `services/crawler/tests/test_adapter_ssi.py`, `apps/api/tests/test_market_view_db.py`, `apps/api/tests/test_jobs.py`
- Change:
  - `feeds/bars_1d.py` snapshot unit → `repo.upsert_bars_1d(conn, kept, nominal_kind="observed", fetched_at=<archive mtime>)`; V2 units unchanged
    (`upsert_bars_1d_src`). Manifest lines keep the same canonical columns (checksum unchanged for V2 units; the snapshot line gains nothing).
    `Manifest` already lists `deferred` skips → `run_bars_1d` exposes their count; runner writes `summary.bars_1d.symbols_deferred`.
  - `_count` / `_sessions` in `runner.py` now take `MAX(trading_date)` over `bars_1d` ∪ `bars_1d_src` (the board day no longer appears in `bars_1d_src`).
  - `SqlMarketView.bars_1d`: newest-version `bars_1d_src` rows ∪ `bars_1d` observed rows for dates absent from the source rows, unscaled —
    `# shortcut: observed close served as adjusted; BE-market-view-ca multiplies by the cumulative factor` — and `_served` includes
    their `fetched_at`. `first_bar_date` = min over both tables.
- Contract: platform.md §2.6 v1.12–v1.14 (step 2 units, `symbols_deferred`), §4 ledger row; data.md §1.2 S1 (`refPrice`), §1.4 (1).
- Acceptance: feed test with the `ssi/exchange/hose.json.gz` fixture → rows in `bars_1d` (`observed`, `ref` = the fixture's `refPrice`, e.g. AAA 7,000),
  none in `bars_1d_src`; running the same date twice → identical rows and manifest checksum; board `tradingDate` ≠ target → `SourceNoLongerServes`,
  the names become V2 gaps and the missed day is in the run (backlog F-013 case 3); `GAP_MAX` overflow → `symbols_deferred` = the count in the job
  summary; market-view db test: a day present only in `bars_1d` is served with its close and moves `snapshot()`.
- Out of scope: factors on the read path, step 3, reconstructed rows.

#### BE-v5-adapter — F-014: VCI IQ events adapter (pure parse + fetch), fixture from the spike
- Story: F-014 ; Side: be ; Effort: high ; Size: ~260 lines (re-estimated 2026-10-26 at consult: source ~145 + 8 acceptance tests ~115; was ~150) ; Lead: sonnet
- Files: `services/crawler/finvest_crawler/adapters/vci/events.py` (new), `services/crawler/finvest_crawler/adapters/vci/payloads.py` (`VciEvent`, `VciEventsPage`),
  `packages/market_data/finvest_market_data/domain/models.py` (`CorporateAction` dataclass: fields of data.md §3 + `public_date`, `title`),
  `services/crawler/tests/fixtures/vci/events/FPT-2026.json` (copy of `.finvest/sprints/sprint-05/spike/v5-call4.json`), `services/crawler/tests/test_adapter_vci_events.py` (new)
- Change:
  - `parse_events(payload, raw_path) -> tuple[list[CorporateAction], list[tuple[str, str]], bool]` → (rows, `(source_event_id, anomaly_rule)` for
    unmapped/unparsed, `last` page flag). Mapping (data.md §1.2 V5; VN§6 types): `DIV` + `valuePerShare` → `cash_dividend`, `cash_per_share = int(valuePerShare)`,
    `pay_date = payoutDate`; `DIV` without it and title matches `cổ tức bằng cổ phiếu` → `stock_dividend`; `ISS` + `thưởng` → `stock_dividend`;
    `ISS` + `CBCNV|ESOP` → `listing_change`; `ISS` + `quyền mua|phát hành thêm` → `rights` with `issue_price` parsed from the title
    (`giá 10,000|10.000 đồng`), unparsed → `NULL` + rule `corporate_action_amount_missing`; anything else → not stored + `corporate_action_unmapped`.
    Ratio: `a:b` from `exerciseRatio` r = b/a via `Fraction(r).limit_denominator(1000)` (0.1 → 10:1, 0.3 → 10:3, 0.15 → 20:3); `ratio_a, ratio_b` NULL for cash.
    Dates from the `T00:00:00` strings; `ex_date = exrightDate`; `source_event_id = id`; `source = "vci_iq"`.
  - `fetch_events(fetcher, symbol, run_date) -> (rows, anomalies, requests)`: `fromDate=20100101`, `toDate=run_date+400d` as `YYYYMMDD`, `size=50`,
    pages `0..` until `last`; bucket `vci_iq`; archived under feed `corporate_actions` as `<SYM>-p<page>.json.gz`.
- Contract: data.md §1.2 V5, §3 `corporate_actions`; VN§6 event types.
- Acceptance: the fixture parses to 4 rows: cash 1,000 VND ex 2026-05-28 pay 2026-06-10 public 2026-05-22; bonus 10:1 ex 2026-09-21 (`stock_dividend`);
  2 ESOP → `listing_change`; a hand-made `DIV` row without `valuePerShare` and title "… cổ tức bằng cổ phiếu tỉ lệ 15%" → `stock_dividend` 20:3; a `DIV`
  row with neither → `NULL` + anomaly; `toDate` always present in the archived request name; a 418 page → `SourceBlocked` after `TRIES`.
- Out of scope: DB writes, budget/order, the press step (BE-ca-step3).

#### BE-ca-repo — F-014/F-015/F-016: repository functions for corporate actions, diff log, factors, recon rows, press order
- Story: F-014 ; Side: be ; Effort: high ; Size: ~160 lines ; Lead: opus
- Files: `packages/market_data/finvest_market_data/infrastructure/repositories.py`, `packages/market_data/tests/test_repositories_db.py`
- Change:
  - `upsert_corporate_actions(conn, rows, fetched_at) -> tuple[int, int]` (upserted, changes): per row, read the existing by `(source, source_event_id)`;
    for each of `type, ex_date, record_date, pay_date, ratio_a, ratio_b, cash_per_share, issue_price` that differs write one `corporate_action_log`
    row (`field, old, new` as text, `changed_at = fetched_at`); unchanged rows write no log (idempotent); `fetched_at` always updated.
  - `ca_symbols_in_order(conn, limit=None) -> list[str]`: VN30 (`symbol_index_membership` current rows) → `SELECT DISTINCT symbol FROM scenarios`
    (plain SQL, `# shortcut: api-owned table read by name; move to a view if a third reader appears`) → remaining listed names by
    `ca_checked_at NULLS FIRST, ca_checked_at, symbol`; delisted excluded. `mark_ca_checked(conn, symbols, at)`.
  - `corporate_actions_for(conn, symbols) -> dict[symbol, list[CorporateAction]]`; `replace_adj_factors(conn, symbol, rows, rules_version)` (delete + insert,
    `factor` as `Decimal` string → `NUMERIC(20,12)`); `adj_factors_for(conn, symbol)`; `replace_recon_mismatches(conn, symbol, rows)`;
    `newest_src_bars(conn, symbol, source) -> list[(trading_date, adj_c)]` (DISTINCT ON newest `fetched_at`); `nominal_bars(conn, symbol) -> list[(trading_date, c, nominal_kind, ref)]`.
- Contract: data.md §3; backlog F-014 criteria 2–3.
- Acceptance (`db`): the backlog diff case (ex 2026-11-05 → 2026-11-07 → one log row `ex_date`, re-run → no new row); order test: VN30 member, a
  scenario symbol and 3 others with `ca_checked_at` NULL/old/new → `[vn30, scen, null, old, new]`; `replace_adj_factors` stores `0.980000000000`
  and reads back equal as `Decimal`; `replace_recon_mismatches` twice → same row count.
- Out of scope: the feed, parsing, the analytics math.

#### BE-ca-step3 — F-014: crawl step 3 (`corporate_actions` feed, budget B, diff log, job summary)
- Story: F-014 ; Side: be ; Effort: high ; Size: ~220 lines ; Lead: opus
- Files: `services/crawler/finvest_crawler/feeds/corporate_actions.py` (new), `services/crawler/finvest_crawler/settings.py` (`rate_per_s["vci_iq"] = 1`,
  `ca_budget: int = 40`), `services/crawler/finvest_crawler/cli.py` (`corporate-actions --date` subcommand), `apps/api/finvest_api/jobs/runner.py`,
  `services/crawler/tests/test_feed_corporate_actions.py` (new), `apps/api/tests/test_jobs.py`
- Change:
  - `run_corporate_actions(settings, run_date, *, budget, on_progress) -> CaResult(status, symbols_checked, events_upserted, changes, symbols_deferred,
    requests, changed_symbols: list[str])`: `insert_crawl_run(feed="corporate_actions")`; walk `ca_symbols_in_order`; stop when `requests + next ≥ budget`
    (the rest = deferred, status `partial`); per symbol `fetch_events` → `upsert_corporate_actions` (commit per symbol) → anomalies via `insert_anomaly`
    (`trading_date = ex_date`) → `mark_ca_checked`; `SourceBlocked` → status `blocked`, finish the run row with `reason = source_blocked`, re-raise as
    the feed's manifest-less result (runner raises `_Blocked`-style with `source = "vci_iq"`); `finish_crawl_run(rows = events, requests)`.
  - `runner.py`: `prog.steps = 3`; after step 2 (also when `partial`) → `step(3, "corporate_actions", today)`; `summary["corporate_actions"] = {…}` per
    platform.md §2.6 v1.14; blocked → job `failed`, `error.source = "vci_iq"`, `error.message = "nguồn vci_iq đang chặn tạm, thử lại sau ~1 giờ"`
    (existing `_blocked_msg`); `summary` keeps steps 1–2. Leaves a `changed_symbols` list on the runner for BE-ca-recompute (no behaviour yet).
- Contract: platform.md §2.6 v1.14 (step 3, summary, blocked); data.md §1.2 V5 (B = 40), §3, §4 `corporate_actions` feed.
- Acceptance: fixture-fed run with 3 symbols and `budget = 2` → 1 checked, 2 deferred, status `partial`, `crawl_runs.requests = 1`; second run with the
  ex-date changed in the fixture → `changes = 1`, log row present; third identical run → `changes = 0`; 3 × 418 → `blocked`, no further request, run row
  reason `source_blocked`; job test: summary shape exactly as the contract, `progress.steps == 3`, a blocked step 3 keeps `summary.bars_1d`.
- Out of scope: factor recompute (BE-ca-recompute), UI, the recon run.

#### BE-ca-recompute — F-015: per-press recompute of factors and reconstructed nominal rows (glue over `finvest_analytics.adjust`)
- Story: F-015 ; Side: be ; Effort: high ; Size: ~340 lines (v1.1: round 1 was 296 incl. ~130 test; round 2 adds ~45; the ~170 counted source only) ; Lead: opus
- Files: `services/crawler/finvest_crawler/feeds/recompute.py` (new), `services/crawler/finvest_crawler/feeds/corporate_actions.py` (call site only),
  `services/crawler/finvest_crawler/cli.py` (`recompute --symbols`), `apps/api/finvest_api/jobs/runner.py` (recompute set after step 3),
  `packages/market_data/finvest_market_data/infrastructure/repositories.py` (v1.1: the five queries move here, nit a),
  `services/crawler/tests/test_recompute.py` (new), `apps/api/tests/test_jobs.py` (reason test). After AI-adjust-version (R6a).
- Change:
  - `recompute(conn, symbols, *, rules_version=RULES_VERSION) -> dict[symbol, (factors, reconstructed_rows, anomalies)]`: per symbol load
    `corporate_actions_for`, `nominal_bars` (observed dates + `ref`), `newest_src_bars(source="vci")`; call `finvest_analytics.adjust.series.reconstruct`
    (R6; `InvalidCorporateAction` → `insert_anomaly(rule = adj_factor_invalid_input | adj_factor_no_pre_close, value = reason)`, symbol continues with the
    remaining events); `replace_adj_factors` (12-place strings, R4) and `upsert_bars_1d(nominal_kind="reconstructed", fetched_at = newest src fetched_at,
    source = "vci")` — observed rows untouched by the repo guard. Commit per symbol.
  - v1.1 `newest_src_bars(conn, symbol, source) -> rows (trading_date, adj_o/h/l/c, v, value, fetched_at, last)`: `last = max(trading_date) OVER
    (PARTITION BY fetched_at)` computed **before** the `DISTINCT ON (trading_date)` newest-per-date pick; the glue passes `AdjBar(..., last=row.last)`
    so each row is divided by its own version's G (data.md §1.4 (4), R6a). The OHLC of a row uses the same G as its close.
  - v1.1 Recompute set (Decisions, platform.md §2.6 v1.15): `recompute_set(conn, changed) -> (names, skipped)` = `changed` ∪ names whose max vci
    `bars_1d_src.fetched_at` > max `reconstructed` `bars_1d.fetched_at` (none → included), filtered `ca_checked_at IS NOT NULL`; `since` is dropped.
    Runner appends `"recompute: <n> symbols, <k> skipped"` to the `corporate_actions` run row `reason` (prior reason kept with "; "); 0 source requests.
  - v1.1 layering: `recompute.py` imports no table and builds no SQL; `newest_src_bars`, anomaly dedupe, CA ids, `recompute_set`, `append_reason` live in
    `repositories.py` like every other feed.
- Contract: 2-tech-plan.ai.md R1–R6, R6a, R9 (`rules_version`); data.md §1.4 (1), (4), §3 `adj_factors`; platform.md §2.6 v1.15; A18-A.
- Acceptance (`db`, fixtures): G7 — src `A(D−1) = 49,000`, cash 1,000 ex D → `adj_factors` row `0.980000000000`, `bars_1d` D−1 = 50,000 `reconstructed`;
  G9 — an observed 93,500 on an ex-date−1 stays; G12 — FPT fixture rows + the spike event → factor `10/11 = 0.909090909091`, reconstructed 2026-09-18
  close 71,701 (± 1 VND, recorded in the build note); a symbol with `ca_checked_at NULL` is skipped and counted; re-running changes no row (byte-identical
  `adj_factors`). v1.1: **G13-db** — full version F0 (12 days, nominal 50,000 every day, fetched before cash 1,000 ex E = day 8) plus a short version F1
  (days 8–12, adjusted by f = 0.98, fetched after E): every day 1–7 reconstructs to 50,000 (fails on round 1: 51,020); **set** — a symbol whose src
  `fetched_at` is older than any `since` and that has no reconstructed row is in the set, and is not after `recompute`; **reason** — `NULL` →
  `recompute: 2 symbols, 1 skipped`, `x` → `x; recompute: 2 symbols, 1 skipped` (real `_recompute`, not faked).
- Out of scope: the read path, recon, UI.

#### BE-market-view-ca — F-023/F-015: `SqlMarketView` corporate actions, adjusted series, R9 snapshot; `/health.rules_version`; reproducibility test
- Story: F-023, F-015 ; Side: be ; Effort: high ; Size: ~180 lines ; Lead: opus
- Files: `apps/api/finvest_api/market_view.py`, `apps/api/finvest_api/main.py`, `apps/api/openapi.json` (regenerated, if `test_openapi_current` demands),
  `apps/api/tests/test_health.py`, `apps/api/tests/test_market_view_db.py`, `apps/api/tests/test_whatif_reproducible_db.py` (new)
- Change:
  - Implement the port additions of AI-adjust-series: `corporate_actions(symbol, as_of)` (rows with `ex_date ≤ as_of`, from `corporate_actions` joined to
    `adj_factors`), `adjusted_close(symbol, start, end, *, as_of)` = `bars_1d` nominal × Π factors over `(d, as_of]` (R5, 2 dp, via the AI `adjusted`
    function on rows loaded here — no formula in the api).
  - `bars_1d` (simulator basis, Decisions): replace the BE-observed-bar shortcut — observed rows × Π factors over `(d, today]`, integer half-up.
  - `_served` (R9): max `fetched_at` over bar rows served **and** the CA rows whose factors were applied (`ex_date ≤ as_of`); a future ex-date does not
    move it (G11).
  - `/api/health`: `"rules_version": RULES_VERSION` (import from `finvest_rules.costs`); update `test_health` expectations.
- Contract: platform.md §2.6 v1.14 (`/health`), §2.5 `data_snapshot`; contracts/analytics.md §1.4; analytics.md §1.1; 2-tech-plan.ai.md R5, R9.
- Acceptance (`db`): G11 exactly (`2026-10-27T16:22:00+07:00`, and `16:14` when `ex_date > as_of`); `/api/health` body has the current `RULES_VERSION`
  string; reproducibility — seed bars + CA, call `POST /whatif` twice → identical `json.dumps(sort_keys=True)` bytes and `rules_version == RULES_VERSION`;
  an observed close 50,000 on D−1 with factor 0.98 ex D is served as 49,000 by `bars_1d` and as `49,000.00` by `adjusted_close` with `as_of ≥ D`,
  as 50,000 with `as_of < D`.
- Out of scope: the engine reading nominal (F-043/F-044), the F-021 page, versioned factors (F-088).

#### BE-mv-basis — F-015: the simulator basis reads `bars_1d` (observed + reconstructed), not mixed `bars_1d_src` versions (v1.1, consult nit d)
- Story: F-015 ; Side: be ; Effort: high ; Size: ~80 lines ; Lead: opus
- Files: `apps/api/finvest_api/market_view.py`, `apps/api/tests/test_market_view_db.py`
- Change:
  - `SqlMarketView.bars_1d`: read `bars_1d` rows of both `nominal_kind`s × Π factors over `(d, today]` (the existing observed branch, applied to
    every row); the `bars_1d_src` DISTINCT-ON read stays only as a **symbol-level fallback** when the symbol has no `reconstructed` row yet
    (names V5 has not reached, platform.md §2.6 budget) — never mixed per date with `bars_1d` rows.
  - `_served` unchanged (max `fetched_at` of the rows served + CA rows applied).
- Contract: data.md §1.4 (4); platform.md §2.5 `data_snapshot`; 2-tech-plan.ai.md R5, R7 `ours`.
- Acceptance (`db`): F0 full version (nominal 50,000, before cash 1,000 ex E) + F1 short version after E + reconstructed `bars_1d` rows from
  BE-ca-recompute's G13-db → `bars_1d(start..end)` returns 49,000 on every pre-E day (never 51,020 × 0.98 = 50,000 for the old rows, i.e. no
  step at the F1 window edge); a symbol with no reconstructed row returns the newest-version src rows (today's behaviour); G11 bytes unchanged.
- Out of scope: `adjusted_close` (already on `bars_1d`), `first_bar_date`, dropping the fallback (when V5 coverage is full, S06).

#### BE-recon-cli — F-016: `crawl recon` (0 source calls), VN30 + scenario symbols, R8 board check, run row, press hook
- Story: F-016 ; Side: be ; Effort: high ; Size: ~160 lines ; Lead: opus
- Files: `services/crawler/finvest_crawler/feeds/recon.py` (new), `services/crawler/finvest_crawler/cli.py` (`recon [--symbols …]`),
  `apps/api/finvest_api/jobs/runner.py` (`summary.recon` after recompute), `services/crawler/tests/test_recon_feed.py` (new), `apps/api/tests/test_jobs.py`
- Change:
  - `run_recon(settings, run_date, symbols=None) -> ReconRun`: symbols default = VN30 ∪ scenario symbols (`ca_symbols_in_order` head); per symbol
    `nominal_bars`, `adj_factors_for`, `newest_src_bars("vci")` → `finvest_analytics.adjust.recon.reconcile` → `replace_recon_mismatches`; R8: for each
    ex-date with an observed previous bar carrying `ref`, `ref_check(f, pre_close, ref, tick)` false → anomaly `adj_factor_ref_mismatch`; missing data
    (no src rows / no nominal rows) listed, never counted as pass; `crawl_runs` feed `recon` (`requests 0`, `rows` = mismatches, `reason` = the
    `summary(...)` line); prints the summary and one line per symbol (days checked, mismatches, first mismatching date).
  - Runner: after recompute, `run_recon` on the same default set; `summary["recon"] = {"symbols", "checked", "mismatches"}` (platform.md §2.6 v1.14,
    one sentence added in this plan: `summary.recon` is optional and null when step 3 did not run).
- Contract: 2-tech-plan.ai.md R7, R8; data.md §1.4 (3), §3 `recon_mismatches`; backlog F-016.
- Acceptance (`db`): G10 from seeded rows → exactly one `recon_mismatches` row (0.2045); G = 1 and equal closes → 0 rows; a 1-VND diff with no ex-date
  between → mismatch tagged `unit_or_adapter`; 29 of 30 VN30 names with data → summary "29/30" naming the missing one and exit code 1; R8 with
  `ref = round_to_tick(f × P)` → no anomaly, with `ref` off by 2 ticks → anomaly row.
- Out of scope: S2 cross-check (BE-recon-s2), the F-021 page.

#### BE-recon-s2 — F-016: S2 cross-check as a second `theirs` (30 calls) — **first to slip** (v1.3, consult round 2: aligned with the AI answer)
- Story: F-016 ; Side: be ; Effort: medium ; Size: ~90 lines ; Lead: sonnet ; After: BE-recon-cli, AI-recon-xsrc
- Files: `services/crawler/finvest_crawler/feeds/recon.py`, `services/crawler/finvest_crawler/cli.py` (`--cross-check ssi`), `services/crawler/tests/test_recon_feed.py`
  (no analytics files: `reconcile(self_check=)` is AI-recon-xsrc)
- Change: with `--cross-check ssi`, for each symbol `SsiSource.bars([sym], "1d", run_date, COUNT)` (S2; thousand VND → VND in the adapter already) →
  `upsert_bars_1d_src(source="ssi", fetched_at = archive mtime)` → a second `reconcile` against `newest_src_bars("ssi")`, rows kept apart by a
  `source` column? **No** — `recon_mismatches` PK is `(symbol, trading_date)`: the S2 result is printed and counted in the run row `reason` only
  ("vci: k, ssi: m mismatches"); storing both sources waits for F-021. 1 req/s bucket, `SourceBlocked` → the cross-check stops, local result stands.
  **No VND slack.** `_compare` passes `self_check=(source == "vci")`: the 1-VND self-consistency branch (R7) is a check against the source a
  reconstructed row was inverted from (V2 only, data.md §1.4); against S2 a reconstructed row takes the ordinary `G_v = 1` exact / 0.1 % branches.
  A nominal close sits on the tick (VN§3), so S2's 10 VND resolution represents every `G_v = 1` close exactly; a diff there is a real adapter bug.
- Contract: 2-tech-plan.ai.md R7 v1.2 + AI-recon-xsrc; data.md §1.2 S2 (resolution), §1.4 (4) last paragraph (self-check rule); §3 `bars_1d_src`.
- Acceptance: with the `ssi/history/FPT-1d.json.gz` fixture the S2 rows land in `bars_1d_src` with `source='ssi'` as **65,180** VND for 2026-09-18;
  ours 65,182.73 (71,701 × 1/1.1, ex-date 09-21) vs S2 65,180 = 0.0042 % → **0 mismatches** on that date; a hand-broken S2 close (65.28 → 65,280)
  → 1 `factor_or_event`; `_compare` is called with `self_check=False` for `ssi` and `True` for `vci` (assert on the call); a 418 run keeps the local summary.
- Out of scope: storing S2 mismatches, anything on screen, any change in `services/analytics`.

#### OPS-guards — F-033: no-broker audit test; test compose override
- Story: F-033 ; Side: be ; Effort: medium ; Size: ~90 lines ; Lead: opus
- Files: `apps/api/tests/test_no_broker_audit.py` (new), `docker-compose.test.yml` (new), `README.md` (one "testing stack" paragraph)
- Change:
  - Audit test (kernel, no `db` marker): package names from `uv.lock` (`name = "…"`) and `apps/web/package-lock.json` keys against a denylist
    (`ssi-fctrading`, `ssi_fctrading`, `vnstock`, `dnse`, `tcbs`, `vps-api`, `entrade`, `pyvnd`, `ccxt`, `ib_insync`, `alpaca`); source under
    `apps/`, `services/`, `packages/` (`.py .ts .tsx`, excluding tests) must not contain `placeOrder|/orders?\b|/order/|newOrder|cancelOrder|/trading/`
    as a URL or identifier (the test lists hits with file:line). Fails the build on any hit.
  - `docker-compose.test.yml`: ports `127.0.0.1:18080:80`, `127.0.0.1:18001:8000`, `127.0.0.1:15432:5432`, db volume `./data-test/pg`, api/crawler
    `./data-test:/app/data`; README: `docker compose -p finvest-test -f docker-compose.yml -f docker-compose.test.yml up -d` and the "never touch
    `finvest-live` / `gw-app@finance_invest`" line (tester.md §8).
- Contract: PR-130; system.md §5 (loopback only); tester.md §8.
- Acceptance: the audit passes on `sprint-05`; adding `vnstock` to a copy of `uv.lock` in a tmp dir makes it fail; `docker compose -f … -f … config`
  shows only loopback ports 18080/18001/15432 and no `8080`.
- Out of scope: runtime egress blocking, CI.

#### FE-e2e-carry — S05-RW: bring `apps/web/e2e/` onto the sprint branch (first time)
- Story: S05-RW ; Side: fe ; Effort: medium ; Size: ~20 lines (≈ 600 copied, not written) ; Lead: sonnet
- Files: `apps/web/e2e/screens.mjs`, `apps/web/e2e/real-stack.mjs`, `apps/web/e2e/crawl-button.mjs`, `apps/web/e2e/w768.mjs` (all
  `git checkout origin/test/sprint-04/fe -- apps/web/e2e`), `apps/web/package.json` (`"e2e:shots": "node e2e/screens.mjs"` script only)
- Change: copy as-is; no behaviour edits; `BASE`/`OUT`/`PW_DIR` env vars stay the interface (dev.md step 6 shot rule). Playwright stays out of
  `package.json` dependencies (S03/S04 decision; `/tmp/pw`).
- Contract: visual-design.md §9.1; sprint-04 tech plan FE-shots.
- Acceptance: `node --check apps/web/e2e/*.mjs` passes; `npm test` unchanged; files identical to the source branch (`git diff --stat` 0 against it).
- Out of scope: new screens (FE-shots), any src change.

#### FE-crawl-step3 — F-014: crawl status step 3, "+N sự kiện quyền (k thay đổi)", "· N mã chờ lượt sau", screen (f) mocks
- Story: F-014 ; Side: fe ; Effort: medium ; Size: ~120 lines ; Lead: sonnet
- Files: `apps/web/src/components/CrawlStatus.tsx`, `apps/web/src/i18n/en.json`, `apps/web/src/i18n/vi.json`, the CrawlStatus test file
  (`rg -l 'crawl.done' apps/web/src --glob '*.test.tsx'`), `apps/web/e2e/screens.mjs` (screen (f) mock payloads only)
- Change:
  - Running: `steps` from `progress.steps` (3); step 3 → `crawl.step3` "sự kiện quyền" / "rights events", unit `crawl.unit.symbols` ("mã" / "names").
  - Done line parts, in order (app-shell.md §Crawl button): ticks · sessions · `crawl.done.events` "+{{n}} sự kiện quyền ({{changes}} thay đổi)" when
    `summary.corporate_actions` is non-null · skipped · `crawl.done.deferred` "· {{n}} mã chờ lượt sau" / "· {{n}} names left for the next press" with
    `n = bars_1d.symbols_deferred + corporate_actions.symbols_deferred` when > 0 · duration.
  - Error: `error.source === "vci_iq"` renders "VCI IQ" in `crawl.error.source`; a failed step 3 keeps the steps 1–2 parts before the error line
    (the `summary` is still there).
  - `screens.mjs` (f): running mock at step 3 ("Bước 3/3 — sự kiện quyền: 18/40 mã") and the done/blocked mocks with the new summary.
- Contract: platform.md §2.6 v1.14 (summary shape); ux/app-shell.md §Crawl button (Running, Done rows).
- Acceptance: vitest — running step 3 text, done line equals the spec sample with `events 3, changes 1, deferred 12`; `deferred 0` → no "chờ lượt" part;
  `corporate_actions null` → no events part; i18n key parity; a 1280 light shot of (f) in the build note (dev.md step 6).
- Out of scope: data-quality page (F-021), the freshness chip.

#### FE-rw — S05-RW: 768–1023 one-line top bar, table header ≤ 2 lines, DCA single shift line with "Xem"
- Story: S05-RW ; Side: fe ; Effort: medium ; Size: ~170 lines ; Lead: sonnet
- Files: `apps/web/src/styles/shell.css`, `apps/web/src/components/TopBar.tsx` + `FreshnessChip.tsx` + `CrawlButton.tsx` (only if the date-only / icon-only
  switch is JS, not CSS), `apps/web/src/features/scenarios/ScenarioTable.tsx`, `apps/web/src/features/scenarios/table.css`, `apps/web/src/features/scenarios/ScenarioCard.tsx`,
  `apps/web/src/features/scenarios/scenarios.css`, `apps/web/src/i18n/en.json`, `apps/web/src/i18n/vi.json`, their existing tests
- Change:
  - visual-design.md §4 (768–1023): brand and nav links `white-space: nowrap`; the chip's date-only and the crawl button's icon-only rules move from
    `max-width: 767px` to `max-width: 1023px` (nav still inline ≥ 768); accessible names unchanged.
  - §6.4: benchmark headers "so với VN-Index" / "so với E1VFVN30" with `title="(điểm %)"`; footer note "Cột so với: chênh lệch tính bằng điểm %";
    no header may exceed 2 lines at 1280 (`th` gets `max-width` + the existing wrap).
  - §6.3: DCA card renders **one** shift line "Ngày mua dời sang ngày giao dịch kế tiếp: {{n}} lần" with a native `<details><summary>Xem</summary>`
    listing the dates (house style for a disclosure: `.btn-link` look, focus ring from app.css); lump sum keeps its single line.
- Contract: visual-design.md §4, §6.3, §6.4, §9.2 (lines "top bar/page header do not wrap at 768 and 800", "DCA card shows at most one shift line").
- Acceptance: vitest — DCA fixture with 5 shifts renders one shift line + 5 dates inside `details`; table headers match the new labels and the footer
  note exists; shell.css rule test (jsdom, base rules only) keeps the 32 px hit target; build note carries a 1280 light shot; the 768/800 proof is
  FE-shots'.
- Out of scope: new breakpoints, drawer behaviour, the scenario form.

#### FE-shots — S05-RW/F-014 UI: screenshot run incl. 768×1024 and 800×900, §9.2 checklist, copied into FI_ROOT (tester, manual)
- Story: S05-RW ; Side: fe ; Effort: medium ; Size: ~60 lines ; Lead: sonnet ; **manual: true (fi-fe-tester, /fi-test fe)**
- Files: `apps/web/e2e/screens.mjs` (viewport list), `.finvest/sprints/sprint-05/shots/*.png`, `.finvest/sprints/sprint-05/4-test.fe.md`
- Change: §9.1 set (375/1280 × light/dark, screens a–g, focus shot) + **768×1024 light and 800×900 light for (a) and (f)**; §9.2 lines incl. the two
  S05 lines; axe all rules 0 on /scenarios both schemes; run against the **test compose project** (tester.md §8, ports 18080/18001), never 8080.
  Finish = report + `shots/` in FI_ROOT's SPRINT_DIR (retro R5).
- Contract: visual-design.md §9.1, §9.2; tester.md §6, §8.
- Acceptance: all shots listed with pass/fail per checklist line; the 768/800 shots show one bar line and no label broken over 2 lines.
- Out of scope: BE tests (`4-test.be.md` is the BE tester's run through /fi-test be, same R5 rule).

## Contract and doc changes made at planning (already in the files)
- `contracts/platform.md` v1.14 §2.6: step 3, `summary.corporate_actions`, `symbols_deferred`, blocked rules, recompute, `/health.rules_version`.
  BE-recon-cli adds `summary.recon` (optional) — the lead treats it as in-contract.
- `architecture/data.md` v1.4: §1.2 V5 (fields, `toDate`, B = 40) and S2 (re-probe) spike lines; §3 `bars_1d.ref`, `symbols.ca_checked_at`; §5 item closed.
- `briefs/tester.md` §6 (retro R5) + §8 compose isolation; `briefs/dev.md` step 6 and `briefs/lead.md` step 5 (retro R3).

## Risks (technical)
1. The SSI row move (0010) runs on the live db at the first `up` after merge: the observed 26–28/10 bars must survive → acceptance test on a copy
   first (`make test-db`), and the sponsor's press on 28/10 (L2) is the live check.
2. B = 40 is a guess with 4 observed calls: the first live press logs `crawl_runs.requests`; if V5 blocks, step 3 ends `blocked` and the job is
   `failed` with steps 1–2 kept — the sponsor sees it on the status line, nothing is lost.
3. Title parsing for rights issues is untested against real data (no rights event in the fixture) → `NULL` + anomaly by design; the first real rights
   event is a tester fixture, not a code guess.
4. Three tasks touch `runner.py` serially (observed-bar → step3 → recompute → recon); any slip there delays M2. Mitigation: each is ≤ 30 runner lines.
