# ops

Deployment is `docker-compose.yml` at the repo root (db, api, crawler; crawler is in the `tools` profile so `make up` does not start it).
Backups, TLS and nginx are out of scope for sprint 01 (F-019).

## File ownership

`api` and `crawler` run as your host user (`FINVEST_UID`/`FINVEST_GID`, set by the Makefile from `id`; plain
`docker compose` falls back to 1000:1000, or set them in `.env`). One-time fix for files an earlier root
container wrote:

    sudo chown -R $(id -u):$(id -g) data/raw data/exports
    sudo chown $(id -u):$(id -g) data     # if data/ itself is root-owned (created by the Docker daemon); non-recursive

`data/pg` is left alone on purpose: the postgres image manages its ownership itself (it must stay owned by the
container's postgres user). Do not chown it.

## Scheduled crawl (F-019)

`finvest-crawl catchup` runs `ticks` for every trading day since the last recorded session (today only, if there is none),
skipping `complete` and `missed` days; it exits 2 if a day ended `blocked` or raised. A systemd user timer runs it
Mon-Fri at 15:30 and 20:00 Asia/Ho_Chi_Minh (`Persistent=true` replays a run missed while the machine was off).

    make up                 # db must be running
    make install-timers     # copies units to ~/.config/systemd/user, enables the timer and linger
    systemctl --user list-timers finvest-crawl.timer
    journalctl --user -u finvest-crawl.service
    make uninstall-timers

A manual re-run of one day stays `make crawl DATE=YYYY-MM-DD`.
