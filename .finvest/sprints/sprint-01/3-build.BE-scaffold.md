# BE-scaffold build
Result: DONE. uv workspace (3 members), settings, `finvest-crawl ticks`, `GET /health`, Makefile, import-linter.
Files: pyproject.toml, uv.lock, Makefile, .env.example, README.md (run section), 3 package pyprojects + skeletons,
crawler settings.py/cli.py/conftest.py, api main.py, tests.
Contract: platform.md 1.3 envelope + section 2 /health; codebase.md 1,3,4,5.
Checks: `make test-kernel` exit 0: 5 passed; ruff all passed; mypy no issues (1 file); lint-imports 3 kept, 0 broken.
CLI: `--date 2026-10-18` prints "not a trading day (weekend)" exit 0; `--date 2026-10-16` exit 3 "not implemented".
`git status` clean of data/ after creating data/raw/x.
Deviations: env prefix FINVEST_ (matches codebase.md FINVEST_SOURCE_*). Ruff lint select E,F,I and `.finvest` excluded
(the host's default ruff set flagged .finvest/bin scripts). Weekend check only; holidays arrive with finvest_rules.
Outside-set edits: services/crawler/tests/test_cli.py (acceptance tests), root pyproject [project] (virtual root needs deps).
Notes for tester: `uv` was not installed; installed via `pip install uv` (0.13.1). No market_data placeholder test (no logic).

## Fix round 1
Health moved to /api/health (main.py, test_health.py, README); 503 test asserts full envelope. make test-kernel exit 0: 5 passed, ruff ok, mypy ok. Head de7404a. Other nits skipped.
