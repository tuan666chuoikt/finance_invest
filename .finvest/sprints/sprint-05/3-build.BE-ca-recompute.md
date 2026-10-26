# 3-build BE-ca-recompute (F-015) — branch task/sprint-05/BE-ca-recompute, head 7b8a340965e918ee7f15e0cd07ab2eb824d6263c

Result: DONE. `recompute(conn, symbols, *, rules_version)` rebuilds `adj_factors` and the `reconstructed` `bars_1d` rows per symbol
(0 source requests, commit per symbol); the runner calls it after step 3; `finvest-crawl recompute --symbols A,B` for by-hand use.

## Files
- `services/crawler/finvest_crawler/feeds/recompute.py` (new): `recompute`, `recompute_set(conn, changed, since) -> (names, skipped)`, `append_reason`.
- `.../feeds/corporate_actions.py`: `CaResult.run_id` only (call-site edit, so the runner can note the recompute on the run row).
- `.../cli.py`: `recompute --symbols`. `apps/api/finvest_api/jobs/runner.py`: `_recompute(engine, ca, since)` after step 3 (also after a
  `blocked` step 3: events read so far are stored), appends `"recompute: <n> symbols"` to the `corporate_actions` run row `reason`.
- `services/crawler/tests/test_recompute.py` (new, 5 db tests); `apps/api/tests/test_jobs.py` (fake `_recompute`, call order asserted).
- Outside-set edits: `services/crawler/pyproject.toml` + `uv.lock` (crawler now declares `finvest-analytics`, workspace source; import-linter allows it).

## What changed / decisions
- Recompute set = `changed_symbols` + names with a `bars_1d_src` (source vci) row whose `fetched_at >= job start`, filtered `ca_checked_at IS NOT NULL`;
  filtered-out names are counted (second return value of `recompute_set`).
- Input read with one local query on `bars_1d_src` (newest version per date) instead of `repo.newest_src_bars`: `bars_1d` needs NOT NULL
  o/h/l/v, and `newest_src_bars` returns only `adj_c`. o/h/l are reconstructed with the same G(d) as the close, `v`/`value` copied from the source.
  `fetched_at` of the written rows = max source `fetched_at`.
- `InvalidCorporateAction` has no ex-date, so on a raise the ex-date is found by retrying suffixes newest-first; that ex-date is dropped,
  anomaly `adj_factor_invalid_input` (value = reason) written, the symbol continues. Events with `ex_date <=` first source bar: anomaly
  `adj_factor_no_pre_close` (value `no_bar_before_ex_date`), never guessed (R1). Anomalies are not duplicated while an identical one is open.
- Events after the newest source bar get no factor row (R6: the source could not know them; they are computed on the press after the bar exists).
- `adj_factors.ca_id` = lowest `corporate_actions.id` of the ex-date (R3); `rules_version` = `RULES_VERSION`.

## Checks
- db (throwaway timescale container, db `finvest_be_ca_recompute_test`): `test_recompute.py` + `test_repositories_db.py` 35 passed.
- `pytest -m "not db"`: 324 passed, 41 deselected; ruff clean; mypy no issues (5 files); lint-imports kept.
- G7: factor 0.980000000000, D-1 = 50,000 reconstructed; D-2 = 48,000/0.98 = 48,980. Re-run: `adj_factors` and `bars_1d` rows equal.
- G9: observed 93,500 stays `observed`; factor from the observed P = 92,500/93,500 = 0.989304812834 (src inversion would have given 93,499).
- G12 (FPT fixture + 10 % bonus ex 2026-09-21): factor 0.909090909091; reconstructed 2026-09-18 close = **71,700** (db stores source close 65,182,
  not 65,182.47; 65,182 x 1.1 = 71,700.2). Within the card's 71,701 +-1 VND; the 0.47 VND is the integer storage of `adj_c`.
- Skipped-and-counted: `recompute_set` with BBB (`ca_checked_at NULL`) -> `(["AAA","CCC"], 1)`.

## Deviations
- Size: 296 lines (prod 119+31, tests 149) vs plan ~170 (1.5x = 255). I found it at the end, with everything built and green; nothing is left to
  split, so I did not stop. The overrun is the OHLC reconstruction, the ex-date finder for invalid events, anomaly dedupe and 5 db tests.

## For the tester
- G12: compare the 09-18 value (71,700) with a public nominal history page. `finvest-crawl recompute --symbols FPT` re-runs it by hand.
- FPT has ESOP/cash events before the V2 window: expect 2 open `adj_factor_no_pre_close` anomalies (ex 2026-05-28, 2026-06-24), by design.

## Fix round 1 (2026-10-26, fi-be-dev) — implements `answer.ai.md` + `answer.sa.md`
Merged `origin/sprint-05` (has AI-adjust-version R6a: `AdjBar.last`).
- **Must-fix 1:** `3-consult.BE-ca-recompute.md` written (size ~356 vs card ~340).
- **Must-fix 2 (option A):** `repositories.newest_src_bars` now returns rows `(trading_date, adj_o/h/l/c, v, value, fetched_at, last)`, `last = max(trading_date)
  OVER (PARTITION BY fetched_at)` before the DISTINCT ON; `recompute._one` passes `AdjBar(..., last)` and divides OHLC by `cumulative(..., r.last)`.
  Db tests G13 (V0 days 1-10, V1 days 8-12, cash ex day 11) and G13b (V1 days 12-16): days 1-10 = 50,000, factor 0.980000000000.
  With `last` removed, G13 gives 51,020 and factor 0.980392156863 (checked, both tests fail).
- **Must-fix 3:** `repositories.recompute_set(conn, changed)` = changed + names whose newest vci `bars_1d_src.fetched_at` > newest reconstructed `bars_1d.fetched_at`
  (none: in), filtered `ca_checked_at IS NOT NULL`; `since` removed from the runner. Test: an old-`fetched_at` name with no reconstructed row is in the set, not after `recompute`;
  a later archive puts it back.
- **Must-fix 4 / nit b:** `recompute.recompute_press(engine, changed, run_id)` (runner calls it; test_jobs fakes `runner.recompute_press`) appends
  `recompute: <n> symbols, <k> skipped` via `repo.append_run_reason`. Db test with the real function: NULL -> `recompute: 2 symbols, 1 skipped`, `x` -> `x; recompute: 2 symbols, 1 skipped`.
  Deviation: the db test calls `recompute_press` (crawler package), not an api-private `_recompute`, so it needs no api import.
- **Nit a:** `recompute.py` imports no table; new repo functions `recompute_set`, `corporate_action_ids`, `insert_anomaly_once`, `append_run_reason`; `newest_src_bars` extended
  (its only other user was `test_repositories_db`, updated). Nit c/d: no change (SA/AI decisions).
- Outside-set edit: `packages/market_data/tests/test_repositories_db.py` (newest_src_bars row shape).
- Checks: `make test-kernel` exit 0, 335 passed, 47 deselected, ruff clean, mypy 5 files clean, import-linter kept; `pytest -m db` full on a throwaway db
  (dropped): 47 passed.
