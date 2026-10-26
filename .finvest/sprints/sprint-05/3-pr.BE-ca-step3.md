# 3-pr BE-ca-step3 (F-014) — tech lead BE

## Round 1 — 2026-10-26 — APPROVE
Reviewed head H = 3c92a550b556041003873739115f5f640a84227e (e7e6313 + `chore(merge)` sync with origin/sprint-05 695ca05, no conflicts).
Size: 6 files, +288 / -7 (plan ~220, stop 330) — within 1.5x.

### Files reviewed
- `services/crawler/finvest_crawler/feeds/corporate_actions.py` (new): budget rule `requests + 1 >= budget` -> `partial` matches the plan
  ("stop when requests + next >= budget"); per-symbol commit; `SourceBlocked` -> `blocked`, reason `source_blocked`, no further request;
  other errors -> rollback, run `failed`, re-raised. Repo calls match the real signatures (`finish_crawl_run`, `insert_anomaly(trading_date = ex_date)`,
  `corporate_actions_for` keys every symbol). `changed_symbols` = log rows or new event ids.
- `settings.py`: `vci_iq` bucket 1 req/s, `ca_budget = 40` (data.md §1.2 V5). `cli.py`: `corporate-actions --date`, exit 2 on blocked.
- `apps/api/finvest_api/jobs/runner.py`: `steps = 3`, step 3 after a `partial` step 2, skipped after a blocked step 1/2 (summary null),
  summary keys exactly platform.md §2.6 v1.14, set before the `_Blocked` raise (partial step 3 counts kept), error source `vci_iq` + `_blocked_msg`.
- Tests: `test_feed_corporate_actions.py` (5), `test_jobs.py` (+3, 3 updated; the `trading_date` assertion moved to `bars_args` because
  the final progress is now step 3 — the web does not read `progress.trading_date`).

### Hand check
Budget 2, 3 symbols, 1 page each: before AAA 0+1 < 2 -> read (1 request); before BBB 1+1 >= 2 -> stop. 1 checked, 2 deferred, `partial`,
requests 1 — matches `test_budget_defers_the_rest`.

### Must-fix
None.

### Nits / notes (non-blocking)
1. AC says "ex-date changed -> changes = 1"; the test changes the ex-date of all 3 symbols and asserts 3 (one log row per symbol). Same rule,
   different fixture; a one-symbol change would match the AC literally.
2. Any non-blocked error of one symbol (shape rejected, 3x 5xx) fails the whole step 3 / job. VN30 order is fixed, so a bad V5 payload for one
   VN30 name would fail every press until fixed. Plan is silent; `sa` may want a per-symbol `skipped` like step 2 batches (next plan).
3. Tier starvation (build note): VN30 + scenario symbols take ~30+ of the 39 usable requests every press, so tier 2 rotates ~9 names/press;
   data.md §4 still describes a "±7 d + Sunday full pass" schedule. For `sa` at the next plan, not this task.
4. The FakeRepo diff compares all dataclass fields, the real repo only `CA_FIELDS`; the real diff-log SQL is covered by BE-ca-repo db tests.

### Checks on H
- `make test-kernel`: 324 passed, 36 deselected; ruff all checks passed; mypy no issues (5 files); lint-imports 5 kept / 0 broken.
- Affected: `test_feed_corporate_actions.py` + `test_jobs.py`: 25 passed.
- `-m db -k "corporate or ca_ or jobs"`: 2 skipped (no db) — not required: the task touches no migration, repository or SQL.

### Merge
Merged H 3c92a55 into sprint-05 (base 695ca05): merge sha 5d1976afedfe59ff2b9a885812a703d38dd6d804.
