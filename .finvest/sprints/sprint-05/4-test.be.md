# Sprint 05 — BE test report (fi-be-tester, 2026-10-26)

Head tested: `origin/sprint-05` aedaf0c (worktree `test-be-05`, branch `test/sprint-05/be` b781ed8, pushed).
**Verdict: FAIL** on data accuracy (B-05-1, high). **Migration 0010 rehearsal: PASS** (no blocker for the live deploy).

## 1. Migration rehearsal (live db at 0009 -> 0010)
Live was only read: `pg_dump -Fc` from `finvest-live-db-1` (6.8 s, 47.6 MB); live still at 0009 afterwards. Restored into my own
stack (project `finvest-test-be`, `timescaledb_pre/post_restore`, 12.8 s) then `alembic upgrade head`.

| | before (live dump) | after 0010 |
|---|---|---|
| `bars_1d_src` source=ssi | 947 rows (947 symbols, all 2026-10-23) | 0 |
| `bars_1d_src` source=vci | 4,534,014 | 4,534,014 |
| `bars_1d` | (table absent) | 947, all `observed`/`ssi` |
| `index_1d` / `symbols` / `ticks` | 9,347 / 1,775 / 225,520 | identical |
| new tables | - | adj_factors, bars_1d, corporate_action_log, corporate_actions, recon_mismatches, `symbols.ca_checked_at` |

- **Time: upgrade 1.8-2.0 s wall** (incl. container start; log "947 ssi rows moved"). Downgrade 1.5 s.
- No data loss: the 947 moved rows (o/h/l/c/v/value/fetched_at) are byte-identical (`cmp`) to the live ssi rows.
- **Downgrade to 0009 works**: ssi rows restored (947, identical to live again), new tables and column gone, `alembic_version` 0009;
  up again 1.8 s, 947 in `bars_1d`. Caveat (B-05-6): only `observed` ssi rows come back, older duplicate versions are gone (documented by build).
- api (test stack :18001) `/api/health` = `{"status":"ok","db":"ok","rules_version":"2026.10.28"}` (note: the route is `/api/health`, `/health` is 404 as on live).
- What-if FPT/HPG (lump 50M, buy 2025-03-03, sell 2026-10-16) on the migrated db: results identical to live's (sprint-04 code) except `rules_version`;
  FPT hand check: close 107,512 -> 400 sh, fee round(400*107,512*0.0015)=64,507, cash 6,930,693 = api. Repeat calls md5-identical.
- Injection probes (symbol `FPT; DROP TABLE`, date `' OR 1=1--`, 2099 date, unknown symbol): 400/422 VALIDATION, tables intact.

## 2. Suites (all through q.sh, own db `finvest_test` on :15433, never `make test-db` = live port)
| Suite | Result |
|---|---|
| kernel `pytest -m "not db"` (incl. analytics + market_rules + crawler fixtures) | **337 passed**, 60 deselected |
| `ruff` | **1 error** E501 `services/analytics/tests/test_recon.py:118` -> `make test-kernel` exits 2 (B-05-4) |
| mypy / lint-imports | ok / ok |
| db `pytest -m db` | **60 passed** |
| `make smoke` (via my compose project) | ok, 0 rows on checks 1-2; last runs listed |
| my oracle `tests_be05/` | 13 passed, 1 xfailed (B-05-3) |

## 3. Coverage map (acceptance -> tests that fail without the feature)
| Story / criterion | Test (existing = E, mine = T) | Result |
|---|---|---|
| F-014 row fields from V5; type mapping | E `test_adapter_vci_events`, T real press: 509 events in 26 symbols (270 cash, 65 stock, 41 rights, 133 listing) | **FAIL**: stock dividends under ISS unmapped (B-05-1) |
| F-014 ex-date change -> one log row, re-run none | E `test_upsert_corporate_actions_logs_each_changed_field_once`, `test_ex_date_change_is_logged_once` | pass (live replay not done: see §5) |
| F-014 VN30 + scenario first, deferred count, budget | E `test_ca_symbols_in_order...`, `test_budget_defers_the_rest`; T real press | order ok (26 VN30 names read first); budget = B-05-2 |
| F-014 unmapped amount -> NULL + anomaly | T real press: 43 `corporate_action_amount_missing`, 0 cash rows with NULL amount | pass |
| F-015 G1-G5, G3b factors; G6 chain; G7/G7b/G8; G9; G12; G13/G13b | T `test_oracle_ca.py` (Fractions, written from the plan table, not the code) + E golden JSON runner | pass |
| F-015 random vs oracle | T 3,000 random mixes (cash/bonus/rights/split) factor == oracle to 12 dp; 3,000 round-trips factor -> inversion within 1 VND | pass |
| F-015 invalid input | T cash >= P, P=0, ratio 0, rights w/o price -> `InvalidCorporateAction` | pass |
| F-015 real data: stored `adj_factors` vs oracle (392 factors, 26 names) | T `realdata_check.py`: 384 equal to 12 dp; 8 differ by < 1.1e-4 relative = 1 VND of P (inversion rounding, old 2011-2020 rows) | pass (expected rounding) |
| F-015 reconstructed x G vs source, 85,854 rows | T same script: **0 rows > 1 VND** | pass (but see B-05-1: tautological where an event is missing) |
| F-015/F-016 re-run idempotent | T `recompute --symbols FPT,HPG` x2: counts and md5 of `bars_1d` identical | pass |
| F-016 G10 rows (0.204 % yes / 0.041 % no) | E `test_g10...` (analytics + crawler db) | pass |
| F-016 VN30 30/30 | real: `crawl recon` after the press = **26/30**, missing VNM VPB VPL VRE | **not met** (B-05-2) |
| F-016 S2 cross-check | real `recon --cross-check ssi`: 38 s, 26 names, 0 S2 blocks; 9,640 ssi mismatches reported (7,333 rows > 0.1 % by my count, all <= 2020-11; mostly HPG SHB ACB MBB) | ran; exit 0 although mismatches (B-05-6); results are V2-vs-S2 convention differences until B-05-1 fixed |
| F-023 snapshot = max fetched-at, reproducible, /health rules_version | E `test_snapshot_is_max_fetched_at_of_served_rows`, `test_whatif_reproducible_db`, `test_health`; T live-stack repeat calls | pass |
| F-013 board bar per press, idempotent, missed press | E `test_board_bar_lands_observed...`, `test_press_asks_the_board_then_only_the_gaps`; real press | **not exercised live** (B-05-5); fixture tests pass |
| F-033 no broker | E `test_no_broker_audit` (5 tests); T probes | pass; blind spot B-05-3 |
| G12 real FPT value | stored V2 A(2026-09-18) = 65,182 (integer) -> reconstructed **71,700** (golden JSON with 65,182.47 gives 71,701; both within 1 VND; the 71,700 in build note is the real-data figure). Public nominal page not consultable from this sandbox: FPT really traded ~71.7k on 18/09 per V2 x 1.1 only. | recorded |

## 4. The one real press (test stack, job 8, 15:03-15:19 VN)
duration 955 s. ticks partial 891 symbols / 165,918 rows (1 skipped); step 2 `bars_1d` target **2026-10-23** (not 26/10): 90 fetched, 1,451 deferred, 43 requests,
9,542 rows; step 3 **blocked** after 33 V5 requests (30 ok pages incl. FPT/MBB/VIC page 2, then 3 blocked) -> 26 names checked, 509 events upserted, 0 log rows (first read),
1,514 deferred; recompute 26 symbols; recon 26/30, 0 mismatches. Plus one `recon --cross-check ssi` (S2, 30 calls, not a press).

## 5. Bugs
| Id | Sev | Owner stage | Finding |
|---|---|---|---|
| B-05-1 | **high** | build (BE-v5-adapter, `adapters/vci/events.py::_map`) | V5 files "Trả Cổ tức bằng Cổ phiếu tỉ lệ N%" under `eventCode=ISS`, but `_map` only maps that title under `DIV`; ISS handles only "thưởng". Result: **147 stock-dividend events unmapped** in the 26 names (`corporate_action_unmapped` 364 total). Steps: press, then `select ... from data_anomalies where rule='corporate_action_unmapped'`. Example HPG: ISS 10 % ex 2026-05-25 (also 20 % 2025-06-26, 30 % 2022, 35 % 2021) not stored; `adj_factors` has no factor for them; reconstructed nominal is continuous across the ex-date (23,955 on 22/05 -> 24,100 on 25/05, should drop ~10 %) so all HPG/SHB/ACB/MBB nominal history before the event is understated. Expected: `stock_dividend` a:b from `exerciseRatio`. Local recon cannot see it (ours x G == source by construction). A "Cổ phiếu thưởng" case with no ex-date (8) is fine. |
| B-05-2 | medium | plan/build (budget B) | V5 blocked after **30 ok calls** at 1 req/s (hold ~1 h, platform said "raise B after >= 60"); B = 40 therefore ends in a block, 26 of VN30 covered, recon **26/30** (VNM VPB VPL VRE). F-016 "30/30" needs a second press >= 1 h later. Record the ~30-call budget in data.md §1.2 V5 and lower B (~28) or accept two presses; page-2 names (FPT/MBB/VIC) cost 2 calls. |
| B-05-3 | low | build (F-033) | audit scans only `.py/.ts/.tsx`; `placeOrder`/`/order/` in `.mjs/.js/.jsx` is not caught (`tests_be05/test_f033_probe.py`, xfail strict). |
| B-05-4 | low | build (AI-recon) | ruff E501 `test_recon.py:118` (118 > 110): `make test-kernel` fails at lint, mypy/imports never run by the target. |
| B-05-5 | low | build (runner) | `_target(now)` uses `now` taken before step 1; ticks takes ~15 min, so a press started 15:00-15:05 targets the previous day and never stores today's board bar (F-013). Re-evaluate `now` at step 2 or document "press after 15:05". |
| B-05-6 | low | build/plan | (a) `recon --cross-check ssi` exits 0 with 9,640 mismatches and stores S2 history as `bars_1d_src` source `ssi` (88,181 rows) — the same name 0010 treats as board rows: a downgrade+upgrade after a cross-check would promote S2 history to `observed`. (b) 0010 downgrade keeps one version per ssi row. |
| B-05-7 | info | ops (tester.md) | `docker-compose.test.yml` maps db to 127.0.0.1:15432, which `harbor-local-postgres-1` already holds; I used 15433 via an override (`tests_be05/docker-compose.port.yml`). Update the file or tester.md. |

Not verified (cap of one press): live idempotent replay of step 3 (0-request archive replay), the board bar of the run date, any ex-date change in V5 (needs two days). Idempotency of the local part is proven (recompute x2).

## 6. Test stack left running for the FE tester
Compose project **`finvest-test-be`** (worktree `finance_invest-worktrees/test-be-05`, `-f docker-compose.yml -f docker-compose.port.yml`):
web http://127.0.0.1:18080, api http://127.0.0.1:18001 (`/api/health`), db 127.0.0.1:15433 (db `finvest` = live copy + migration 0010 + today's press; throwaway db `finvest_test` for db tests).
Data volume `./data-test` in that worktree. Down with `docker compose -p finvest-test-be -f docker-compose.yml -f docker-compose.port.yml down -v`.
