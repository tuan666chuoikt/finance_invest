# 3-pr BE-compose — round 1 (lead, opus)
Verdict: **CHANGES_REQUIRED** (1 must-fix). Reviewed head H=a710fff74c3237328effa14ebe51aea91a7de08f (already in sync with origin/sprint-01, no merge needed).
Files reviewed: docker-compose.yml, Dockerfile, .dockerignore, .env.example, Makefile, README.md, ops/README.md (87+/6-, est ~150).
Contract: system.md §5 OK (api 127.0.0.1:8000 only, db unpublished, alembic at start-up); platform.md §2 health body matches; ADR-S-001 tag deviation 2.17-pg16 -> 2.17.2-pg16 accepted (the planned tag does not exist; reported in 3-build).

## Must-fix
1. docker-compose.yml:20-41 + Makefile:`crawl` — the crawler runs a stale image. api and crawler each `build: .` with no shared `image:`, so compose builds two images (be-compose-api, be-compose-crawler). `make up` (`up -d --build`) rebuilds only api (crawler is in profile `tools`), and `docker compose run` never rebuilds an existing image. Reproduced: added a file under services/, ran `make up` -> api image 47afc87a -> edfd1762, crawler stayed 178cab6e. Consequence: after BE-feed-ticks merges, `git pull && make up && make crawl DATE=…` still runs the old "not implemented" code (or, later, old crawler logic writing data). The plan says one image for api and crawler. Fix: give both services the same `image:` name (e.g. `finvest-app:local`) so `make up` refreshes what the crawler runs, and/or make `crawl` use `docker compose run --rm --build crawler …`. Proof (add to the PR transcript): change any source file, `make up`, then `docker compose images`/`docker inspect` shows api and crawler on the same image id and `make crawl` runs the new code.

## Nits (not blocking)
- docker-compose.yml:15 healthcheck `pg_isready` without `-h 127.0.0.1` uses the unix socket, which answers during the image's init temp server (listen_addresses=''); first-run alembic can race it. Passed in my fresh run (health in 10 s), so nit; `-h 127.0.0.1` closes it.
- Containers run as root: `data/` and `data/pg` end up root/uid-70 owned on the host, so cleanup needs sudo and host-side `uv run finvest-crawl` cannot write `data/raw`. Consider `user:` for crawler later (F-019).
- .env.example: "change it if you like" — changing POSTGRES_PASSWORD after `data/pg` exists breaks api auth; say "set before the first `make up`".
- 3-build claims the weekday path "returns 3 through make": make itself exits 2 (container exit 3 is printed as make Error 3). Fine for the card; testers/timers should call compose directly if they need the 3.
- Dockerfile copies the whole workspace before `uv sync`, so every source edit re-installs deps; copy lock + pyproject, sync deps (`--no-install-workspace`), then copy sources, when build time matters.

## Checks on H (re-run by lead)
- `docker compose config -q` OK.
- Fresh data dir: `make up` exit 0; `/api/health` -> {"status":"ok","db":"ok","version":"0.1.0","rules_version":null} after 10 s; `ss -ltn`: only 127.0.0.1:8000, nothing on 5432; alembic_version 0001, 5 public tables.
- `make crawl DATE=2026-10-18` -> "not a trading day (weekend)", exit 0; DATE=2026-10-16 -> make exit 2 (container 3, allowed).
- `make down && make up` -> health ok, 0 error/traceback lines in api log; `git status --porcelain` empty.
- make test-kernel: exit 0, 63 passed, ruff + mypy + import-linter clean.
- Cleaned up: compose down, data/ and .env removed; worktree kept for the fix.

# 3-pr BE-compose — round 2 (lead, opus)
Verdict: **APPROVE**. Reviewed head H=4548ca9c72f20a775448a0072d0ffd6f2c529da7 (in sync with origin/sprint-01 21754d4, no merge needed).
Files reviewed (fix diff a710fff..H): docker-compose.yml, Makefile, .env.example (+5/-3).

## Round-1 must-fix
1. FIXED. api and crawler share `image: finvest-app:local`; `make crawl` uses `run --rm --build`. Proof re-run by lead: edited cli.py weekend message, `make up`, `make crawl DATE=2026-10-18` printed the edited text; reverted, crawl rebuilt and printed the original.
Nits taken: healthcheck `-h 127.0.0.1`; .env.example "set before the first `make up`". Remaining nits (root-owned data/, Dockerfile layer caching) stay open for F-019 / later; not blocking.

## Checks on H (re-run by lead)
- `docker compose config -q` exit 0.
- Fresh data dir + .env from .env.example: `make up` exit 0 (8 s); /api/health -> {"status":"ok","db":"ok","version":"0.1.0","rules_version":null} after 4 s; `ss -ltn`: only 127.0.0.1:8000, nothing on 5432.
- `make crawl DATE=2026-10-18` -> weekend message, make exit 0; direct `docker compose run` exit 0. DATE=2026-10-16 -> make exit 2 (container 3, allowed until BE-feed-ticks).
- `make down && make up` -> health ok, 0 error/traceback lines in api log, alembic_version 0001; `git status --porcelain` empty.
- make test-kernel: exit 0, 63 passed, ruff + mypy clean, import-linter 3 kept / 0 broken.
- Cleaned up: compose down, data/ and .env removed.
- Merged: f796d6d74ec6f1d3585241b761dc4a414babb1f1 into sprint-01.
