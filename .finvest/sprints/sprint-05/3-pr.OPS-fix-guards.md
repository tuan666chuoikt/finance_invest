# 3-pr OPS-fix-guards

## Round 1 — 2026-10-26 — fi-tech-lead (BE) — CHANGES_REQUIRED

Reviewed head H = `6238aea` (origin/sprint-05 4d47710 already merged in; no conflicts). Size 3 files, +9/-3 (est ~15): ok.
Files: `apps/api/tests/test_no_broker_audit.py`, `docker-compose.test.yml`, `README.md`. Design matches plan/PR-130; port 15433 and README line fine;
compose config shows 127.0.0.1:15433 only, no 15432/8080 published (needs POSTGRES_PASSWORD set).

### Must-fix
1. `apps/api/tests/test_no_broker_audit.py:31` E501 (132 > 110): `make test-kernel` exits 1 on ruff. Wrap the suffix tuple
   (e.g. a module constant `SUFFIXES = (...)` and `p.suffix not in SUFFIXES`). Proof: `make test-kernel` exit 0.

### Checks on H
- `make test-kernel`: pytest 342 passed, 62 deselected; ruff 1 error (E501) -> exit 1. mypy/lint-imports not reached.

## Round 2 — 2026-10-26 — fi-tech-lead (BE) — APPROVE

Must-fix 1 fixed (SUFFIXES constant, 820e4fa). Synced origin/sprint-05 cleanly (merge 508ffe9, no conflicts). Reviewed head H = `508ffe9`.
Checks: `make test-kernel` exit 0: 342 passed, 62 deselected; ruff, mypy clean. Size 3 files +12/-3.
Merge sha: 2df45e4
