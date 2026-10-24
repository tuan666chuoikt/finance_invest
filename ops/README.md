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
