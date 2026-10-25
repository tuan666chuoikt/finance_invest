# 3-pr OPS-rw-smoke-dsn

## Round 1 (fi-tech-lead, BE, 2026-10-25) — CHANGES_REQUIRED
Reviewed head H = 2788d07 (d58f713 + clean merge of origin/sprint-04 ee8cc98, pushed). Size: 6 files, +37/-1 (plan ~70): OK.
Files reviewed: Makefile, docker-compose.yml, .env.example, ops/smoke.sql, ops/README.md, README.md. All in the file set.

### Checks on H
- `make test-kernel` (q.sh kernel): **RED** — 1 failed, 258 passed, 26 deselected (log /tmp/fi-q/171622-kernel.log).
  `services/crawler/tests/test_qa_sprint01.py::test_f030_compose_publishes_only_api_on_loopback` asserts `ports["db"] == []`;
  the new `127.0.0.1:55432:5432` mapping breaks it. Real regression caused by this diff, not a flake.
- `pytest -m db` (q.sh db) with the plan DSN shape against the compose db (container IP 172.20.0.2:5432 because the live
  container predates the port mapping; `finvest_test` already existed): **green, 26 passed**, 259 deselected.
- `ops/smoke.sql` run read-only on the live db from the main checkout: (2) 0 rows; (3a)/(3b) print; (1) **4 rows**
  (VNINDEX 2004-07-02, 2004-07-22, 2004-09-06 value ~6-9e14 ratio ~1e10; 2007-08-16 value 0). Matches 3-build.

### Must-fix
1. `services/crawler/tests/test_qa_sprint01.py:157` — update the F-030 guard to the new intent instead of dropping it:
   crawler publishes nothing; db publishes exactly `[("127.0.0.1","55432")]`; api exactly `[("127.0.0.1","8001")]`; and every
   published port of every service has `host_ip == "127.0.0.1"`. F-030's acceptance is "bound to 127.0.0.1 only", which the loopback
   db still satisfies, so this is a stale test, not a contract change. The file is outside the plan's set: the lead authorizes this one
   test edit as a direct consequence of the plan's T6 line; record it under "Outside-set edits" in 3-build.
   Proof: `make test-kernel` green (0 failed) on the new head, and the test fails if the db mapping is changed to `0.0.0.0:55432`.

### Nits (optional)
- Makefile `PGPASS`: a password with URL-reserved chars (`@ / : %`) breaks the DSN; fine while `.env` uses a plain value. Comment it if you touch the line.
- `make test-db` / `make smoke` read `.env` and the compose project from the cwd, so they work from the main checkout only (a worktree has no `.env`). Worth one line in ops/README.

### For sa / pm (not a dev must-fix)
- Acceptance "make smoke prints 0 rows for check (1)" cannot hold: 4 legacy VNINDEX back-fill rows are bad data (value off by ~1e8-1e10, one value 0).
  The smoke check works as designed. Needs a decision: a small data-fix task (repair or re-fetch those 4 index_1d rows, logged in "Manual fixes"),
  or accept the criterion as "(1) lists only known legacy rows" for this sprint.
- `make test-db` on port 55432 needs `docker compose up -d db` in the main checkout after merge (recreates db container; data/pg kept). Tester step.

## Round 2 (fi-tech-lead, BE, 2026-10-25) — APPROVE
Reviewed head H = 76a1298 (cff9e11 fix + clean merge of origin/sprint-04 e5ac19f, pushed). Size: 7 files, +46/-4 (plan ~70): OK.
Files reviewed: Makefile, docker-compose.yml, .env.example, ops/smoke.sql, ops/README.md, README.md, services/crawler/tests/test_qa_sprint01.py
(outside-set edit authorized in round 1, recorded in 3-build).

### Must-fix 1 (round 1): fixed
`test_f030_compose_publishes_only_loopback` asserts crawler has no ports, db exactly 127.0.0.1:55432, api exactly 127.0.0.1:8001,
and that every published port is on 127.0.0.1. It runs (not skipped): 1 passed. Dev reports it fails with 0.0.0.0:55432.

### Checks on H
- q.sh kernel (`make test-kernel`): **green**, 259 passed, 27 deselected, ruff and mypy clean (/tmp/fi-q/172043-kernel.log).
- q.sh db (`pytest -m db`, plan DSN shape on finvest_test, reached through the container IP because the live db container predates the
  port mapping): **green**, 27 passed (26+1 incl. BE-rw-ledger-rank) (/tmp/fi-q/172058-db.log).
- `ops/smoke.sql` run read-only on the live db: (2) 0 rows (T5c holds); (1) the same 4 legacy VNINDEX rows; (3a)/(3b) print.

### Nits (not done, still optional)
- `PGPASS` breaks on URL-reserved chars in the password; `make test-db`/`make smoke` work from the main checkout only (needs `.env`).

### For pm / sa (acceptance, not a code defect)
- The acceptance line "make smoke prints 0 rows for check (1)" does not hold because of data, not code: 4 legacy VNINDEX index_1d rows
  (2004-07-02, 2004-07-22, 2004-09-06 value ~6-9e14; 2007-08-16 value 0). The check finds them as designed. PM decides at /fi-review:
  a small data-fix task (repair/re-fetch those 4 rows, logged in ops/README "Manual fixes") or accept "(1) lists only the known legacy rows".
- Tester step before `make test-db`: `docker compose up -d db` in the main checkout to apply the 55432 mapping (recreates the db
  container only; data/pg kept; brief api reconnect).
