# 3-pr BE-recon-cli (F-016), sprint-05

## Round 1 (fi-tech-lead BE, 2026-10-26): CHANGES_REQUIRED

Reviewed head H = 9fd0da2 (d6d3006 + `chore` sync merge of origin/sprint-05 23a7f8d, clean, pushed).
Files reviewed: `services/crawler/finvest_crawler/feeds/recon.py` (new), `services/crawler/finvest_crawler/cli.py`,
`apps/api/finvest_api/jobs/runner.py`, `services/crawler/tests/test_recon_feed.py` (new), `apps/api/tests/test_jobs.py`.
File set exactly the plan's. Size: 5 files, +288/-3 vs plan ~160, stop 240. No `3-consult.BE-recon-cli.md`.

Contract: `summary.recon = {"symbols","checked","mismatches"} | null` matches platform.md 2.6 lines 195-196 exactly
(null when bars are blocked: tested). `crawl_runs` feed `recon`, `requests 0`, `rows` = mismatches, `reason` = summary line:
tested. R7 via `finvest_analytics.adjust.recon.reconcile` (no rule re-implemented). R8 reading of `ref` (board ref of the
ex-date's own bar, pre_close = previous trading day's observed close, reconstructed pre_close skipped) matches
2-tech-plan.ai.md R8 and VN§6; accepted. 0 source calls: yes (only repo reads/writes).

Hand numbers (recomputed): G10 50,000 x 0.98 = 49,000; |49,000-48,900|/48,900 x 100 = 0.20450 -> 0.2045 (row);
vs 48,980 -> 0.0408 (no row). R8 tick 50 (HOSE, 10,000 <= 49,000 < 50,000): ref 49,050 -> diff 50 <= 50 pass; ref 49,100 ->
diff 100 > 50 anomaly. All match the tests.

### Must-fix
1. **Size stop skipped** (lead.md 3, retro S01 R2). 288 > 240 and no consult; flagging it in the build note is not the
   consult. Write `SPRINT_DIR/3-consult.BE-recon-cli.md` (waive + re-estimate to ~300, excess = db tests, precedent
   BE-v5-adapter / BE-ca-recompute) and include the file-set question of item 2. Proof: the file exists.
2. **Tick rule outside the rules module** (`recon.py:44` `tick_size`). codebase.md line 40: `finvest_rules` owns
   "ceiling/floor/tick rounding"; checklist "market rules only via the rules module". Move `tick_size(exchange, type_, price)`
   to `packages/market_rules/finvest_rules/` (e.g. `prices.py`, citing VN§3) and import it in `recon.py`; move
   `test_tick_sizes_by_venue` into the `finvest_rules` kernel tests. This adds a file outside the set: ask fi-software-architect
   for the plan line in the same consult (item 1). Proof: `rg -n 'def tick_size' services` empty; kernel test green.
3. **R8 false anomalies on UPCoM** (`recon.py:51-53`, `_r8`). VN§3: UPCoM reference = VWAP of the previous day, not its
   close, so `round_to_tick(f x close)` vs the board ref is off by more than 1 tick on most UPCoM ex-dates and writes a
   wrong `adj_factor_ref_mismatch` row. We store no VWAP, so skip R8 when `exchange == "UPCOM"` (like the unknown-tick case,
   one-line comment citing VN§3) and name it in the consult for fi-ai-architect (R8 says "every ex-date"). Proof: a db test
   with an UPCOM symbol, ref 2 ticks off -> `anomalies == 0` and no `data_anomalies` row; it fails without the change.

### Nits (optional)
- `runner.py:145`: a recon exception after a blocked step 3 replaces the "nguồn vci_iq đang chặn" message with the recon
  error. Consider raising `_Blocked` first and reconciling in a `finally`, or keep it and say so.
- `runner.py:145`: `run_recon` builds a new engine per press; the runner already has `engine` (`conn=` exists).
- No test that a scenario symbol (not VN30) is in `default_symbols`; one insert into `scenarios` in the 29/30 test would cover it.
- `--symbols A,A` makes `expected` 2 but `summary` counts 1 (`set`); `list(dict.fromkeys(...))` keeps them consistent.

### Checks on H (9fd0da2)
- `make test-kernel` (q.sh): exit 0, 335 passed, 57 deselected; ruff clean; mypy no issues; lint-imports pass.
- db (q.sh, throwaway db `finvest_reconcli_test` on the compose server, dropped after): `test_recon_feed.py` +
  `test_recompute.py` 17 passed; full `-m db` 57 passed, 335 deselected.
- `apps/api/tests/test_jobs.py`: 20 passed.

## Round 2 (fi-tech-lead BE, 2026-10-26): APPROVE

Reviewed head H = b6ef0d4 (fix round 1 on 9fd0da2). Already contains origin/sprint-05 (no sync merge needed).
Files reviewed (fix diff 9fd0da2..b6ef0d4 + whole branch vs origin/sprint-05): `packages/market_rules/finvest_rules/prices.py` (new),
`packages/market_rules/tests/test_prices.py` (new), `services/crawler/finvest_crawler/feeds/recon.py`, `services/crawler/finvest_crawler/cli.py`,
`services/crawler/tests/test_recon_feed.py`; `runner.py` / `test_jobs.py` unchanged since round 1.
Size: 7 files, +305/-4 vs ~160 (stop 240); `3-consult.BE-recon-cli.md` now exists (waive to ~300, excess = db tests).

Must-fix status:
1. Size stop: consult written (size waiver, file-set lines, R8 UPCoM). Done.
2. Tick rule: `finvest_rules/prices.py::tick_size` matches VN§3 (HOSE 10/50/100, HOSE ETF 10, HNX 100, HNX ETF 1, UPCoM 100);
   `rg 'def tick_size' services` empty; `test_tick_sizes_by_venue` now in the kernel (kernel 335 -> 336). Done.
3. R8 on UPCoM: `_r8` skips `exchange == "UPCOM"`, comment cites VN§3. New db test
   `test_r8_skips_upcom_whose_reference_is_the_previous_vwap`: verified here red without the change (1 failed, 8 passed), green with it. Done.
Nits taken: `--symbols A,A` deduped; scenario symbol SCEN in the default-set test ("30/31 ... missing V07"). Not taken (accepted):
recon error after a blocked step 3 replaces the blocked message; new engine per press.

Open for the architects (non-blocking, recorded in the consult): fi-software-architect to add the two `finvest_rules` files to the
plan block and confirm the ~300 re-estimate; fi-ai-architect to amend R8 to "HOSE/HNX ex-dates" (UPCoM ref = VWAP, not stored).

### Nits (optional, next touch)
- `test_recon_feed.py` ~line 145: three blank lines before the UPCoM test (ruff passes; formatter would trim).
- `tick_size`: HOSE covered warrants are also 10 đ (VN§3); only `type_ == "ETF"` is matched. No CW in the symbol master today.

### Checks on H (b6ef0d4)
- `make test-kernel` (q.sh): exit 0, 336 passed, 57 deselected; ruff clean; mypy no issues; lint-imports 5 kept, 0 broken.
- db (q.sh, throwaway `timescale/timescaledb:2.17.2-pg16` container on 127.0.0.1:25432, removed after; live stack untouched):
  full `-m db` 57 passed, 336 deselected (`test_recon_feed.py` 9).
- `apps/api/tests/test_jobs.py`: 20 passed.

### Merge
- Merged b6ef0d4 into sprint-05 (base 23a7f8d): merge sha 3a0c633 (3a0c63367c7cbb6d381f9d06711a0dd804354f37). Worktree removed.
