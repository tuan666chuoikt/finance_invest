# PR review: BE-scaffold (task/sprint-01/BE-scaffold -> sprint-01)

## Round 1 (2026-10-15, lead BE, opus)

**Verdict: CHANGES_REQUIRED** (1 must-fix)

Reviewed head H = `941227c4268acab2b44281fad2e1d7751769825d` (already contains origin/sprint-01 `e2764ba`, so no sync merge was needed).

Files reviewed (21, uv.lock excluded): `.env.example`, `Makefile`, `README.md`, `pyproject.toml`,
`apps/api/{pyproject.toml, finvest_api/__init__.py, finvest_api/main.py, tests/test_health.py}`,
`packages/market_data/{pyproject.toml, finvest_market_data/{,domain/,application/,infrastructure/}__init__.py}`,
`services/crawler/{pyproject.toml, finvest_crawler/{__init__,settings,cli}.py, finvest_crawler/{adapters,feeds}/__init__.py, tests/conftest.py, tests/test_cli.py}`.

Plan and file set: matches. The only file outside the set is `services/crawler/tests/test_cli.py`, which holds the acceptance tests. Size is 270 changed lines without the lock, against an estimate of ~180 (1.5x, at the limit). Root `[project]` is justified in the build report. No new dependency beyond the plan (`tzdata` is a runtime need for `zoneinfo`, which is fine).

### Must-fix

1. **`/health` is served at the wrong path.** In `apps/api/finvest_api/main.py:19` the route is `@app.get("/health")`, so it answers at `http://127.0.0.1:8000/health`. platform.md §1.1 sets the base URL to `http://127.0.0.1:8000/api`, and every §2 path is relative to that base. BE-compose's acceptance (2-tech-plan.md:283, :291) runs `curl 127.0.0.1:8000/api/health`. Checked on H: `TestClient(app).get('/api/health')` returns **404**.
   Fix: serve it under `/api`. Either `APIRouter(prefix="/api")` included in `app`, which later routes reuse, or `@app.get("/api/health")`. Update `apps/api/tests/test_health.py` so both tests call `/api/health`, and add an assert that `/health` is not the contract path (optional). Also fix the README run-section comment (`GET /api/health`).
   Proof: `test_health_ok` and `test_health_db_down` pass against `/api/health`. Both fail on H with 404.

### Nits (optional, no new round needed for them)

- `test_health.py:46`: the 503 test checks only `code`. Assert the whole envelope shape (`set(body["error"]) == {"code","message","details"}`) as the acceptance says "asserts 503 envelope".
- `cli.py:22`: `except ImportError` will also swallow a real import failure inside `feeds/ticks.py` once it exists (for example a missing dependency) and report "not implemented" with exit 3. Prefer `except ModuleNotFoundError as e: if e.name != "finvest_crawler.feeds.ticks": raise`. BE-feed-ticks can do this when it replaces the stub. Stray `)` in the comment on the same line.
- `main.py:15`: the API reads `FINVEST_DATABASE_URL` from `os.environ` only, so a local `.env` is not picked up by `uvicorn`. The default matches `.env.example`, and compose will pass the env, so this is harmless for now.
- `conftest.py:6`: `__import__("os")` is better written as `import os`.

### Checks on H (real numbers)

- `uv sync`: exit 0.
- `make test-kernel`: exit 0. pytest 5 passed (1 warning: Starlette httpx deprecation). ruff all passed. mypy no issues (1 file). lint-imports **3 kept, 0 broken**.
- `finvest-crawl ticks --date 2026-10-18`: prints "not a trading day (weekend)", exit 0.
- `finvest-crawl ticks --date 2026-10-16`: prints "not implemented" to stderr, exit 3.
- `data/raw/x` created by hand: `git status` clean.
- `GET /api/health` on TestClient: **404** (must-fix 1).

Security: no secrets. `database_url` has `repr=False` and a test proves it. No paid source, no network in tests (`--disable-socket`). No SQL string building (`text("SELECT 1")` constant).

Side note for the Scrum Master: the "Cited" block that `task.sh BE-scaffold` prints is mis-parsed (fragments such as `codebase.md §3: \`finvest_market_dat`). This is not part of this PR.

## Round 2 (2026-10-15, lead BE, opus)

**Verdict: APPROVE**

Reviewed head H = `de7404a` (contains origin/sprint-01 `e2764ba`; no sync merge needed).
Files reviewed (fix diff 941227c..de7404a): `apps/api/finvest_api/main.py`, `apps/api/tests/test_health.py`, `README.md`.

- Must-fix 1 (health path): resolved. Route is `@app.get("/api/health")` (main.py:19). Both health tests call
  `/api/health`. They fail on 941227c's route (404) and pass now. `/health` now returns 404, as it should.
- Nit (503 envelope): taken. The test asserts `set(error) == {code, message, details}`.
- Nits on cli.py `except ImportError`, `.env` loading in the API, and conftest `__import__` stay open. They do not block. BE-feed-ticks should
  narrow the ImportError when it replaces the stub.

### Checks on H (real numbers)
- `make test-kernel`: exit 0. pytest 5 passed (1 Starlette httpx deprecation warning). ruff all passed. mypy no issues (1 file). lint-imports 3 kept, 0 broken.
- `finvest-crawl ticks --date 2026-10-18`: "not a trading day (weekend)", exit 0. `--date 2026-10-16`: "not implemented", exit 3.
- `git status` clean.
- Merged: `446bc788fad2479be839cb94ed0b4db93db4e703` into sprint-01 (head de7404a).
