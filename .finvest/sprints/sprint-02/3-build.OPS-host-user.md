# 3-build OPS-host-user (S02-2)
Result: DONE (acceptance partly verified, see below).
Files: docker-compose.yml (user + HOME=/tmp on api/crawler, not db), Makefile (export FINVEST_UID/GID from id), .env.example, ops/README.md (chown + why data/pg stays). Diff: 19 insertions.
Checks (real output): `docker compose config` shows `user: 1000:1000` on api/crawler; `docker compose run --rm --build crawler --help` exit 0; `--entrypoint id crawler -u` prints 1000 (= host uid).
Not run: `make crawl` against live sources and `find data/raw ... | wc -l`, and `make up` /health 200 (no network crawl or long-running stack run by me). Tester/lead should run them.
Notes: host uid here is 1000 so the 1000 fallback was not distinguished from the Makefile value; test with a different uid if wanted.
Deviations: none. Outside-set edits: none.

## Fix round 1
Must-fix 1: Makefile `up` and `crawl` now `mkdir -p data/raw data/exports` as the host user before compose runs; ops/README adds non-recursive `sudo chown $(id -u):$(id -g) data` for a root-owned `data/`. Nit: .env.example wording fixed (Makefile wins over .env; plain compose reads .env).
Proof (data/ removed, fresh db): `make crawl` created data/ as stein; `crawl ticks --date 2026-10-16 --only FPT` exit 0, 2383 rows; `find data/raw -newer docker-compose.yml ! -user $(id -u) | wc -l` = 0 (156 entries). Full-day `make crawl` not completed (too long, killed); `/api/health` plan typo ignored.
