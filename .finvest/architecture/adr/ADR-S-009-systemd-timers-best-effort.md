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

## Amendment 2026-10-16 (S02 planning, F-019)
One unit pair instead of two: `finvest-crawl.timer` carries both `OnCalendar` lines (15:30 and 20:00 Mon–Fri, Asia/Ho_Chi_Minh) with `Persistent=true`, and `finvest-crawl.service` runs `crawler catchup`, which walks every trading day (F-003 calendar) from the last `crawl_sessions` row to today and runs `ticks` for each day whose status is absent, `partial`, `blocked` or `failed` (`complete` and `missed` are final). `Persistent=true` fires the missed timer at boot, so no separate catch-up unit; the service waits up to 3 min for the docker daemon (`ExecStartPre`). Today is included only after 15:05 VN (put-through closes 15:00, VN§2) so a boot catch-up never archives a half session.
