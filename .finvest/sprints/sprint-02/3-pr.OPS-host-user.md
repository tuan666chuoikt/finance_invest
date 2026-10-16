# 3-pr OPS-host-user — round 1 (lead, opus)

**Verdict: CHANGES_REQUIRED** — reviewed head H = ff2d29f (fb82a5a + sync merge of origin/sprint-02 fe3068d, no conflicts; pushed).

Files reviewed: docker-compose.yml, Makefile, .env.example, ops/README.md. Size +19 lines vs ~30 estimate (OK). File set exact; no contract change; db service untouched (correct); no secrets.

## Must-fix
1. **Crawler cannot write on a checkout where `data/` does not exist yet** (Makefile:16-22, ops/README.md:11).
   The Docker daemon creates missing bind-mount sources as root, so `make up` (db's `./data/pg`) or the first
   `compose run` leaves `data/` = root:root. The crawler, now uid 1000, then fails. Real output in this worktree
   (fresh, `data/` root-owned): `docker compose run --rm crawler ticks --date 2026-10-16 --only FPT` → exit 1,
   `PermissionError: [Errno 13] Permission denied: '/app/data/raw'`. The README fix `chown -R data/raw data/exports`
   does not help (those dirs do not exist; `data/` itself is root).
   Fix: Makefile `up` and `crawl` first run `mkdir -p data/raw data/exports` as the host user (before compose can
   create `data/`), and README's one-time fix also covers a root-owned `data/` (non-recursive
   `sudo chown $(id -u):$(id -g) data`, so `data/pg` stays untouched).
   Proof to record in 3-build: on a checkout with no `data/` dir, `make crawl DATE=<day>` (an `--only FPT` variant is
   fine) exits 0 and `find data/raw -newer docker-compose.yml ! -user $(id -u) | wc -l` prints 0.

## Nits
- .env.example says compose also reads `.env`, but under `make` the exported Makefile values win over `.env`
  (shell env beats `.env` in compose). Either say "plain `docker compose` reads them from `.env`" or use
  `FINVEST_UID ?=` only when not in `.env`. Wording fix is enough.
- Plan acceptance says `GET /health`; the route is `/api/health` (plan typo, no code change).

## Checks (on H)
- `make test-kernel`: exit 0 — 99 passed, 8 deselected; ruff clean; mypy no issues; lint-imports green.
- After chowning only `data/` to 1000 (simulating the fix): crawl `--only FPT` exit 0; `find data/raw -newer docker-compose.yml ! -user 1000 | wc -l` = 0 (5 entries).
- `docker compose run --rm --entrypoint id crawler` → uid=1000 gid=1000; `crawler --help` exit 0.
- api as mapped user (run on 127.0.0.1:8001, main stack holds 8000): `GET /api/health` 200 after 4s; `id -u` in container = 1000.

# 3-pr OPS-host-user — round 2 (lead, opus)

**Verdict: APPROVE** — reviewed head H = c807442 (fix 8c3c2c1 + sync merge of origin/sprint-02, no conflicts; pushed).

Files reviewed: docker-compose.yml, Makefile, .env.example, ops/README.md. Size +23/-1 vs ~30 estimate (OK). File set exact; db untouched; no secrets; no contract change.

## Round-1 must-fix
1. Fixed: Makefile `up`/`crawl` run `mkdir -p data/raw data/exports` as the host user before compose; README adds the non-recursive `chown data` and keeps `data/pg` untouched.
   Proof (lead, isolated temp worktree with no `data/`, project fi-ophu-review, throwaway db password): `make crawl` created data/, data/raw, data/exports as stein; after `alembic upgrade head` (run as uid 1000 in the api image), `make crawl DATE="2026-10-16 --only FPT"` exit 0, 2383 rows, summary complete; `find data/raw -newer docker-compose.yml ! -user $(id -u) | wc -l` = 0 (of 5). Stack and temp worktree removed.
- Nits from round 1: .env.example wording fixed; `/api/health` plan typo needs no code.

## Nits (no action)
- A fresh db needs migrations before `make crawl` (only `api` runs alembic); pre-existing, not this task.

## Checks (on H)
- `make test-kernel`: exit 0 — 103 passed, 8 deselected; ruff clean; mypy no issues; import contracts 4 kept, 0 broken.
- Merged: 24697db into sprint-02 (sm.sh merge, H=c807442).
