# 3-pr OPS-guards (F-033, PR-130)

## Round 1 — 2026-10-26 — fi-tech-lead (BE, opus) — CHANGES_REQUIRED

Reviewed head H = `db1eab0` (task head 032d67a + clean sync merge of origin/sprint-05 33e63c1, pushed).
Size: 4 files, +67/-0 (estimate ~90) — within plan. Outside-set edit `.gitignore` (`data-test/`) reported and accepted.
Files reviewed: `apps/api/tests/test_no_broker_audit.py`, `docker-compose.test.yml`, `README.md`, `.gitignore`.

### Must-fix
1. **Kernel red (ruff E501)** — `apps/api/tests/test_no_broker_audit.py:1`, `:7`, `:25` exceed 110 columns. `make test-kernel`
   stops at ruff ("Found 3 errors"). Proof: `make test-kernel` exits 0.
2. **Deny-list misses `ib_insync`** — `test_no_broker_audit.py:14`. `uv.lock` stores PEP 503-normalised names
   (`ib-insync`, never `_`; repo uv.lock has zero `_` names). The check compares `n.lower()` and `n.lower().replace("_","-")`
   against a DENY set that holds only `ib_insync`, so `name = "ib-insync"` returns `[]` (probed on H). Normalise both sides
   once (e.g. `re.sub(r"[-_.]+", "-", n.lower())` against a normalised DENY) and drop the now-redundant `ssi_fctrading`
   duplicate. Proof: a test like `test_audit_catches_banned_dependency` with a tmp uv.lock holding `name = "ib-insync"`
   expects `["ib-insync"]`.
3. **Test stack shares the live image tag** — `docker-compose.test.yml` (api, crawler). Base sets `image: finvest-app:local`;
   the override keeps it (compose `config` on H shows `image: finvest-app:local` for api). With the README command
   (`up -d`, no `--build`) the test project reuses the image already built by `finvest-live`, so testers test live's code,
   not the sprint head; with `--build` it re-tags the image the live stack runs from. Both break tester.md §8 isolation.
   Fix: `image: finvest-test-app:local` on api and crawler in the override, and `--build` in the README command (and the
   override's header comment). Proof: `docker compose -p finvest-test -f docker-compose.yml -f docker-compose.test.yml config`
   shows no `finvest-app:local`.

### Nits (optional)
- No negative test for `order_hits` (plan acceptance does not require one); a 3-line tmp-dir test with a `placeOrder`
  line would guard the regex.

### Checks on H
- `pytest apps/api/tests/test_no_broker_audit.py`: 3 passed (0.09s).
- `make test-kernel`: pytest 283 passed, 28 deselected; **ruff: 3 errors (E501) → exit 2**; mypy: no issues (5 files);
  lint-imports: exit 0.
- `compose config` (both files, Compose v5.1.1): published only 127.0.0.1:18001, 15432, 18080; no 8080/8001/55432;
  volumes `./data-test`, `./data-test/pg`. Plan acceptance on ports met.
- Contract: PR-130 deny-list and regex match the plan verbatim; system.md §5 loopback met; no secrets, no network.

## Round 2 — 2026-10-26 — fi-tech-lead (BE, opus) — APPROVE

Reviewed head H = `6109003` (fix 80a5606 + clean sync merge of origin/sprint-05 7c8087b, pushed).
Size: 4 files, +93/-0 (estimate ~90) — within 1.5×. Files reviewed: `apps/api/tests/test_no_broker_audit.py`,
`docker-compose.test.yml`, `README.md`, `.gitignore`.

### Round 1 must-fix
1. E501 — fixed; `make test-kernel` exit 0 (ruff "All checks passed!").
2. Normalisation — fixed: `norm()` (PEP 503 `[-_.]+` → `-`) on lock names, DENY held normalised (`ib-insync`, no `_` dup);
   `test_audit_catches_normalised_name` proves `ib-insync` is caught.
3. Image tag — fixed: api + crawler `image: finvest-test-app:local`; README and header use `up -d --build`.
   `config` (also `--profile tools`) shows no `finvest-app:local`; web has no image tag, so compose names it per project.

### Nits
- None blocking. Round-1 nit (order_hits negative test) done: `test_audit_catches_order_call`.

### Checks on H
- `pytest apps/api/tests/test_no_broker_audit.py`: 5 passed (0.11s).
- `make test-kernel`: pytest 293 passed, 30 deselected; ruff clean; mypy no issues (5 files); lint-imports all KEPT.
  Audit also green against the newly merged BE-v5-adapter / vci events code.
- `compose -p finvest-test -f docker-compose.yml -f docker-compose.test.yml config`: published only 127.0.0.1:18001/15432/18080;
  no 8080/8001/55432; volumes `./data-test`, `./data-test/pg`.

Merged: `a87190a` into sprint-05 (base 7c8087b).
