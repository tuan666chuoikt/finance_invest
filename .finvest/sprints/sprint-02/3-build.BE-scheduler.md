# 3-build BE-scheduler (F-019)

Result: built, pushed. `catchup` command, systemd user timer/service, `make install-timers`/`uninstall-timers`, ops README.

Files: feeds/catchup.py (new), cli.py (`catchup` sub-command), repositories.py (`last_session_date`),
ops/systemd/finvest-crawl.{service,timer}, Makefile, ops/README.md, tests/test_catchup.py, tests/test_cli.py.

Behaviour: start = last session + 1 (or today if no rows); end = today if >= 15:05 VN else yesterday; `trading_days`
only; `complete`/`missed` skipped; a raising day is logged, the rest run, then `CatchupFailed` -> exit 2; any `blocked` -> exit 2.
`run(settings, d, None)` opens its own connection; `conn` is used only to read status.

Checks: `make test-kernel` 111 passed, ruff + mypy + lint-imports green. Timer calendar verified with
`systemd-analyze calendar` (next 15:30 +07).

Not verified: `make install-timers` on the sponsor machine (not run here: would enable a real timer), live M2 run
Thu 2026-10-22, `last_session_date` against real Postgres (no db-marked test added).
`systemd-analyze verify` on the service only complains about the `__FI_ROOT__` placeholder (substituted at install).

Deviations: none. Outside-set edits: none.
Tester notes: run `make up && make install-timers`, check `systemctl --user list-timers finvest-crawl.timer`.

## Fix round 2
- Must-fix: removed the stray tracked copy of this report from the task branch (`git rm`); fix-round-1 notes now live here only.
- Proof: `git diff origin/sprint-02...HEAD --stat -- .finvest` is empty.
