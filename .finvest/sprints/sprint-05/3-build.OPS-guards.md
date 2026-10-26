# 3-build OPS-guards (F-033)
Result: done. Branch task/sprint-05/OPS-guards.
Files: apps/api/tests/test_no_broker_audit.py (3 tests, kernel), docker-compose.test.yml, README.md (testing stack bullet).
Checks: audit tests 3 passed (q.sh, 0.5s). Audit passes on sprint-05 (no deny-list dep, no order identifiers in non-test source).
Negative check: test_audit_catches_banned_dependency appends `vnstock` to a tmp copy of uv.lock, audit reports it.
Compose: `config` with both files shows only published 18001, 15432, 18080; no 8080/8001/55432. Uses `!override` (Compose >= 2.24; here v5.1.1) because list merge would otherwise append base ports.
Outside-set edits: .gitignore + `data-test/`.
Notes for tester: the source scan skips tests/, e2e/, test_*, *.test.*, *.spec.*, node_modules, .venv.

## Fix round 1
Fixed all 3 must-fix: E501 (kernel green), PEP 503 normalisation of both sides (ib-insync now caught; tests for it and for order_hits added), test override uses image finvest-test-app:local on api+crawler and README/header use `up -d --build`. Merged origin/sprint-05.
