# 4-test.be — Sprint 01 backend test report

Tester: fi-be-tester. Head under test: origin/sprint-01 36788eb. Branch `test/sprint-01/be`. Verdict: **FAIL (red)** — live crawl incomplete, 3 product bugs (1 reproduced by an xfail test).

## Numbers
- `make test-kernel`: 85 passed, 1 xfailed (QA-BUG-1), 7 db deselected; ruff, mypy, lint-imports ok.
- Same suite with sockets blocked by a QA plugin (offline proof, F-010): 85 passed, 1 xfailed.
- `pytest -m db` on timescaledb 2.17.2 (`finvest_test`): 7 passed.
- My new file `services/crawler/tests/test_qa_sprint01.py`: 14 tests, 13 pass + 1 strict xfail.

## Coverage map (criterion -> test that fails without the feature)
| Story / criterion | Test(s) | Result |
|---|---|---|
| F-020 data under `data/`, git-ignored | qa `test_f020_data_dir_default_and_gitignored_and_retention_keep_all` (fresh repo + project .gitignore); live: nothing from data/ in `git status` (via exclude of my symlink only) | pass |
| F-020 retention default keep-all | same test (`retention_days is None`) | pass |
| F-030 starts on 127.0.0.1 only | qa `test_f030_compose_publishes_only_api_on_loopback` (db/crawler no ports, api 127.0.0.1:8000) | pass |
| F-030 one command + date crawls | qa `test_f030_make_crawl_takes_date`; live `make up` (12 s) + `make crawl DATE=2026-10-15` ran | pass |
| F-010 unit conversion | dev `test_units`, `test_adapter_ssi::test_fixture_thousand_vnd_to_vnd`, kbs row normalisation | pass |
| F-010 offline suite | whole suite re-run with sockets blocked | pass |
| F-010 second adapter swap, no core change | dev `test_registry::test_bars_swap_changes_no_calling_code` | pass |
| F-011 budget, cached | qa `test_f011_budget_never_exceeded_20_calls_at_2_per_s`; dev `test_archive_is_cache_and_exact`, `test_rate_limit_per_source` | pass |
| F-011 429/403 x3 -> backoff 1,2 -> stop "source blocked" | dev `test_three_429_blocked`, `test_cloudflare_challenge_is_blocked`; qa `test_f011_blocked_mid_run_skips_rest_and_reports`, failures-not-cached | pass |
| F-011 user agent personal tool | qa `test_f011_ua_identifies_personal_tool...` ; host allow-list `test_f011_host_allowlist...` | pass |
| F-017 per-symbol rows, raw archived | dev `test_complete_run_and_manifest_file`; live archive 1542 files | pass |
| F-017 manifest fetched/rows/checksum/skipped+reason | qa `test_f017_checksum_matches_oracle_from_raw_archive` (own sha256 from raw JSON), `..._each_skip_has_reason_and_is_listed_in_file` | pass |
| F-017 idempotent re-run | qa `..._rerun_manifest_file_checksum_and_disk_unchanged`, `..._shuffled_and_duplicated_payload_same_checksum` (out-of-order + duplicate ticks); live re-run replayed 354 symbols, 0 duplicates | pass |
| F-017 missed session never silent | qa `..._past_date_manifest_is_written_not_silent`, `..._crashed_run_is_failed_not_absent` | pass (but see BUG-2) |
| Injection on symbol param | qa `test_f017_symbol_param_cannot_escape_archive` | **xfail = BUG-1** |

## Live end-to-end (real KBS/VCI, 2026-10-15 session)
Run via project path `make up` / `make crawl DATE=2026-10-15`, data in `finance_invest/data` (git-ignored).
- The first run (started 22:25 on 10-15) was killed by a session restart after ~631 symbols; no manifest was written and its `crawl_runs` row (id 1) stayed unfinished (status NULL).
- Resumed 2026-10-16 08:04 (archive-first, 478 s, exit 0). K1 serves only the *current* session and had moved on: every symbol not already archived returned an empty tape.
- **Result: status `partial`. Universe 1540 (VCI getAll). Attempted 1540, succeeded 354, skipped 1186 (all `no_ticks`).**
- Ticks: manifest rows 80,272; DB `ticks` 80,336 across 355 symbols (see BUG-3). Requests in resume: 910 (354 replays free).
- Checksum line: `sha256:4cb05d2c13bc3a118d9b5fa179b0c4dc096841331044cce26b77b7e1f57c586c`.
- Disk: raw archive 7.3 MB (1542 files), Postgres 21 MB. DB counts equal archived tape lengths for every symbol.
- The ~1186 symbols' 10-15 ticks are permanently lost (C1 risk materialised). Full-pass duration is therefore NOT measured (N5 <= 45 min unverified); throughput observed ~2 symbols/s (631 symbols in the first ~5 min).
- A fresh full crawl of 2026-10-16 may only be run after 15:00 local; not done by me.

## Bugs (owner = build unless noted)
- **QA-BUG-1 (low, security/robustness)**: `--only "../../../../x"` becomes the archive filename and the URL path; reproduced: a file `escaped.json.gz` was written outside the `raw/ticks/<date>` dir (and the request URL was rewritten to `/escaped`). Validate symbols against `^[A-Z0-9]{1,10}$`. Test is strict-xfail; remove the mark when fixed.
- **QA-BUG-2 (high, G1 "no silent gap")**: a late/resumed run of a past date writes empty tapes from the *next* session into the old date's archive (1186 empty `*.json.gz` under `2026-10-15`) and replays them forever, and the result is `partial` + `no_ticks` rather than `missed/source_no_longer_serves`, because the probe symbol was replayed from archive and so `fetched > 0`. Expected: once a non-probe symbol returns an empty/other-session tape for a past date the run should say what happened; an empty tape must not be archived as that date's data. (plan/build)
- **QA-BUG-3 (medium)**: universe drifted between run 1 and run 2 (symbol DSH, 64 ticks, present in DB but not in the manifest); the manifest rows/checksum (80,272) disagree with the DB (80,336). Universe should be archived/replayed with the date. A killed run also leaves its `crawl_runs` row unfinished instead of `failed`.

## Not tested / limits
No separate VCI/SSI live smoke; holiday handling is S02 (F-003); mypy does not cover the crawler adapters (dev note).
