# ops

Deployment is `docker-compose.yml` at the repo root (db, api, crawler; crawler is in the `tools` profile so `make up` does not start it).
Systemd timers, backups, TLS and nginx are out of scope for sprint 01 (F-019).

## File ownership

`api` and `crawler` run as your host user (`FINVEST_UID`/`FINVEST_GID`, set by the Makefile from `id`; plain
`docker compose` falls back to 1000:1000, or set them in `.env`). One-time fix for files an earlier root
container wrote:

    sudo chown -R $(id -u):$(id -g) data/raw data/exports

`data/pg` is left alone on purpose: the postgres image manages its ownership itself (it must stay owned by the
container's postgres user). Do not chown it.
