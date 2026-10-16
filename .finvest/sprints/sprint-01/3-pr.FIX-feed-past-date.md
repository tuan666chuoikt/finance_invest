# 3-pr FIX-feed-past-date (sprint-01)

## Round 1 (fi-tech-lead, BE) — APPROVE

Reviewed head H = 97e163a7af632391bd347930352fe5bfd49ac278 (99e0a62 + `chore(merge)` sync with origin/sprint-01
@ 2532ecf, FIX-only-validate; clean merge, no conflicts).

### Files reviewed (diff origin/sprint-01...H, 6 files, +71/-13; block estimate ~90)
- `services/crawler/finvest_crawler/fetch.py` — `archive: bool = True` kw; replay-read unchanged and first; write
  skipped only when `archive=False`; counters unchanged. Other callers (ssi, vci x2) keep the default.
- `services/crawler/finvest_crawler/adapters/kbs/source.py` — get(archive=False) → parse_ticks → write only if
  accepted and path absent. Replay path never rewrites. parse_ticks untouched.
- `services/crawler/finvest_crawler/feeds/ticks.py` — date rule `served_date is not None or trading_date < today`,
  `today` = `datetime.now(Asia/Ho_Chi_Minh).date()` or injected. Conclusive → break; `missed` if 0 fetched, else
  `partial` with `names[i:]` listed as `source_no_longer_serves`. Docstring no longer says "probe".
- tests: test_fetch.py, test_adapter_kbs.py, test_feed_ticks.py.

### Contract check (platform.md §4 v1.2, ADR-S-008, data.md §1.2 K1)
- Archive written only after the adapter accepted the tape: yes (empty and other-session tapes never stored).
- `partial` reason null unless loop stopped early; early stop lists untouched symbols with
  `source_no_longer_serves`: yes (complete→partial path keeps reason null).
- K1 rule: past date empty/other-session = conclusive; today empty = `no_ticks`: yes. VN time zone used for "today".
- CLI exit code: partial/missed → 0, blocked → 2 (unchanged).

### Tests vs acceptance
- Fetcher archive=False: `test_archive_false_returns_body_without_writing` (fails on base).
- KBS empty tape and 10-15 tape for 10-14 not archived: `test_rejected_tape_is_never_archived[2]` (fail on base).
- Good tape written once, replayed, mtime unchanged: `test_accepted_tape_written_once_then_replayed`
  (regression guard; base already behaved so).
- Feed partial (today=10-16, FPT archived, VNM empty): status/reason/fetched=1/requests=2/replays=1/skipped/no VNM
  file — `test_past_date_empty_tape_after_good_one_is_partial`.
- Feed missed (first tape empty): 0 fetched, 2 requests, no file — `test_past_date_empty_first_tape_is_missed`.
- Today empty first tape → no_ticks: `test_empty_first_tape_is_inconclusive_not_missed` (today=D) green.
- Past-date other-session (2 requests): renamed `test_past_date_other_session_is_missed`, green.
- Ran the three test files with base source + new tests: 10 failed (fetch/kbs on behaviour, feed tests on the new
  `today` kw and on the rule). By reasoning, the base code yields partial/reason=null + a written VNM file, so the
  partial/missed asserts fail on behaviour too.

### Checks on H (py3.12 venv from test-be-01, PYTHONPATH → this worktree)
- pytest -m "not db": 81 passed, 7 deselected
- ruff: all checks passed; mypy: no issues (5 files); lint-imports: 3 contracts KEPT
- `-m db` not run (no Timescale on host); `test_two_runs_against_db` uses good tapes only, so the new rule does not apply.

### Must-fix
None.

### Nits (no action required)
1. `VN = ZoneInfo("Asia/Ho_Chi_Minh")` now defined in both cli.py and feeds/ticks.py; fold into one place when
   finvest_rules lands.
2. Real-clock default of `today` has no test (trivial one-liner).

### Notes for sponsor/tester
Stale empty tapes already on disk are still replayed and now yield missed/partial for past dates; delete them by hand
(out of scope, code never deletes).

### Merge
Merged H into sprint-01: merge sha 539fb1584363c625a4f908bb30c45f05d9464121 (base 2532ecf).
