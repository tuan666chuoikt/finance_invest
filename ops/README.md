# ops

Deployment is `docker-compose.yml` at the repo root (db, api, web, crawler; crawler is in the `tools` profile so `make up` does not start it).
Backups, TLS and nginx are out of scope for now.

## File ownership

`api` and `crawler` run as your host user (`FINVEST_UID`/`FINVEST_GID`, set by the Makefile from `id`; plain
`docker compose` falls back to 1000:1000, or set them in `.env`). One-time fix for files an earlier root
container wrote:

    sudo chown -R $(id -u):$(id -g) data/raw data/exports
    sudo chown $(id -u):$(id -g) data     # if data/ itself is root-owned (created by the Docker daemon); non-recursive

`data/pg` is left alone on purpose: the postgres image manages its ownership itself (it must stay owned by the
container's postgres user). Do not chown it.

## Manual crawl (F-034)

There is no scheduler. Crawl by hand, by one of two ways: the web button (`POST /api/jobs`, run inside the api container,
which mounts `./data`) or `make crawl DATE=YYYY-MM-DD`. Never run both at once. The api container runs the image built by
`make up`: after a code change, run `make up` again.

Ports on loopback: web 8080, api 8001 (8000 is the sponsor's gateway).

Past-day crawls probe FPT, HPG, VNM first: an empty tape counts as no trades only once a probe shows the source still serves that day; otherwise the day is `missed`, and a `missed` run never overwrites a stored `partial`/`complete` session.
The `crawl_sessions` ledger keeps the richest replay: a replay with fewer rows (a `missed` run, or a `partial`/`source_no_longer_serves` the morning after) leaves the stored row alone; the manifest file on disk is always written.
Ledger repair from ticks: migration 0008; re-runnable via `python -c 'from finvest_market_data.infrastructure import repositories as r; ...'` (`r.repair_crawl_sessions_from_ticks(conn)`) inside the api container.

Daily bars (step 2 of a press): stores the last final session (today after 15:05, else the previous trading day). It costs 3 SSI requests (the whole board for the latest session, every name) + 2 VCI (the indices) + at most 40 VCI (names the board did not cover, oldest last bar first; the rest are `deferred` to the next press). While it runs the `crawl_sessions` row shows `partial/running`. When the source blocks us the run stops with "nguồn … đang chặn tạm, thử lại sau ~1 giờ": retry after about an hour. Interior holes and a cold DB need `make backfill` (no cap, resumable; V2 serves one symbol per call, about 1 780 requests, so it may need several runs if blocked).

## Test database (`make test-db`)

`make test-db` creates `finvest_test` in the compose db (idempotent) and runs `pytest -m db` with
`FINVEST_DATABASE_URL=postgresql+psycopg://finvest:<POSTGRES_PASSWORD from .env>@127.0.0.1:55432/finvest_test`.
The db is published on loopback only (`127.0.0.1:55432`). Per-branch db: `make test-db FINVEST_TEST_DB=finvest_test_<branch>`.
If auth fails because the role password drifted from `.env` (the S03 T6 root cause), repair once: `make db-shell`, then
`ALTER ROLE finvest PASSWORD '<value of POSTGRES_PASSWORD in .env>';`.

`make smoke` runs `ops/smoke.sql` (VNINDEX value/volume ratio, weekend ledger rows, latest runs and sessions); checks (1) and (2) must print 0 rows.

## Manual fixes

- 2026-10-25 (T5c): `DELETE FROM crawl_sessions WHERE feed='bars_1d' AND trading_date='2026-10-24'` via `make db-shell` (2026-10-24 is a Saturday, orphan row). Result: `DELETE 1` (row was `partial`). Follow-up: `make smoke` check (1) still lists 4 legacy VNINDEX rows (2004-07-02, 2004-07-22, 2004-09-06 with value ~1e14, 2007-08-16 with value 0); not touched here.
