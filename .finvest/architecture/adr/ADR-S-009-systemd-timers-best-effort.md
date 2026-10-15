# ADR-S-009 — Scheduling: systemd user timers on the host, boot catch-up, no in-process scheduler
Status: Accepted · 2026-10-15

## Decision
`~/.config/systemd/user/finvest-crawl@.timer` instances for 15:30 and 20:00 Mon–Fri (`OnCalendar`), each running
`docker compose run --rm crawler all --date today`; `finvest-catchup.service` on boot (3-min delay, `Persistent=true`)
runs the same for every trading day since the last manifest. `loginctl enable-linger` so timers run without a
desktop login. The crawler itself decides per `trading_calendar` whether the day is a session and exits early
otherwise. In-session board polling (R3) is a long-running compose service under profile `board`, started by the
sponsor when wanted (C11: not a monitoring tool).

## Alternatives
APScheduler inside a long-running container (proposal): needs the container to be always up, adds a second
clock/calendar to debug, and PR-020 explicitly asks for a timer. cron: no boot catch-up semantics.

## Consequences
A missed run shows as a failed unit and as a `missed` manifest; manual re-run is `make crawl DATE=`.
