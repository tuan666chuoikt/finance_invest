# Sprint 02 — Plan

Owner: `fi-pm`, 2026-10-16. Sprint runs **Mon 2026-10-19 → Fri 2026-10-23** (5 trading days, no VN holiday).
Inputs: `product/backlog.md`, `product/roadmap.md` (S02 row), `handoff.md` §2 (S02-1..S02-5),
`sprint-01/5-review.product.md`, `sprint-01/6-retro.md` (R1–R5 approved, A22).

## Goal

**The crawl runs itself and its status is honest; reference data exists.** By Friday a systemd user timer starts
the tick crawl on every trading day with no manual action (F-019, using the F-003 calendar), a fully captured
session is labelled `complete` (S02-1), containers no longer leave root-owned files in `data/` (S02-2), and the
symbol master (F-004) plus the daily OHLCV back-fill (F-012) are stored.

## Capacity

- Velocity **20 points `[measured S01: 20/20]`**. Committed: **21 points** (+1, 5 % over; inside the 25 % re-plan band).
- First to slip if the sprint runs late: F-012 criterion 3 (coverage %), then S02-4. Nothing else is stretch.

## Committed stories

| Story | Pts | Title | Order / depends on |
|---|---|---|---|
| S02-1 | 2 | Tick status rule: no-trade symbols count as `complete` (platform.md v1.3 §4) | first; must land before F-021 (S04) |
| S02-2 | 1 | Containers run as the host user; `data/` chowned once | first (no deps) |
| S02-3 | 1 | Live acceptance re-run: 10-16 same checksum, 10-14 `missed` | after S02-1 (manifest status) — tester |
| S02-4 | 1 | Clean 1,186 stale empty tapes in `data/raw/ticks/2026-10-15/`, re-manifest 10-15 | after S02-2 and S02-1 |
| F-003 | 3 | Trading calendar | parallel; before F-019 "non-trading days" criterion |
| F-019 | 3 | Best-effort scheduler (15:30 run, 20:00 retry, boot catch-up) | after F-003, S02-2 (timer runs as host user) |
| F-004 | 5 | Symbol master (all exchanges, delisted kept) | parallel |
| F-012 | 5 | Daily OHLCV back-fill | after F-004 (universe) |
| **Total** | **21** | | |

Follow-up acceptance criteria (stories S02-1..S02-4 are not in the backlog; criteria fixed here):
- **S02-1** Given a session where every symbol is fetched or returned an empty tape after close, Then status =
  `complete`, empty tapes are counted in a separate field (e.g. `symbols_no_trades`), and `symbols_skipped` holds
  only real skips (http_429, timeout, blocked …). Given one real skip, Then `partial`. Example: 10-16 (911 fetched
  + 629 no-trade, 0 skips) → `complete`. Contract (platform.md §4) amended by the architect first.
- **S02-2** Given `make up` / `make crawl` on a fresh run, Then every new file under `data/` is owned by the host
  UID/GID; existing root-owned files are chowned by one documented command.
- **S02-3** Given the S02-1 build, When `make crawl DATE=2026-10-16` is re-run, Then row count 145,184 and checksum
  unchanged; When `make crawl DATE=2026-10-14`, Then manifest `missed`, reason `source_no_longer_serves`.
- **S02-4** Given S02-2 is merged, Then the 1,186 stale empty tapes are removed without sudo and the 10-15 manifest
  is re-written under the S02-1 rule (still `partial`: 1,186 symbols lost, listed with reason).

Next by roadmap order and **moved to S03**: F-031 App shell EN/VI (3). S03 becomes F-031 + F-013…F-032 = 23 pts;
the S02 retro re-plans S03/S04 in `roadmap.md` (R1 grew by the 5 follow-up points).

## Milestones

| Id | Name | Due (VN time) | Stories |
|---|---|---|---|
| M1 | Honest status + host-owned data | 2026-10-20 18:00 | S02-1, S02-2 |
| M2 | Calendar + scheduler live (timer fired once on its own) | 2026-10-22 15:45 | F-003, F-019 |
| M3 | Reference data: symbol master + back-fill done | 2026-10-23 18:00 | F-004, F-012 |
| M4 | Live checks + 10-15 cleanup | 2026-10-23 18:00 | S02-3, S02-4 |
| C1…C5 | Manual crawl of each session (R5), owner sm | each trading day 23:00 | see below |

**Clock milestones (retro R5).** KBS serves only the current session and stops serving it by the next morning
(10-15 lost 1,186 symbols this way). Until F-019 has fired on its own once (M2), the SM — or the sponsor, prompted
by the SM — runs `make crawl` after 15:00 and confirms the manifest before 23:00:

| Id | Session | Start after | Done by | Lost if missed |
|---|---|---|---|---|
| C1 | 2026-10-19 Mon | 15:00 | 2026-10-19 23:00 | the whole 10-19 tick tape, for good (C1) |
| C2 | 2026-10-20 Tue | 15:00 | 2026-10-20 23:00 | the whole 10-20 tick tape |
| C3 | 2026-10-21 Wed | 15:00 | 2026-10-21 23:00 | the whole 10-21 tick tape |
| C4 | 2026-10-22 Thu | 15:00 | 2026-10-22 23:00 | the whole 10-22 tick tape |
| C5 | 2026-10-23 Fri | 15:00 | 2026-10-23 23:00 | the whole 10-23 tick tape |

Once M2 is met, the remaining C rows become checks ("timer manifest present by 23:00"); the SM still runs
`make crawl` by hand if the timer's manifest is missing at 21:00. Each missed C row is also a lost day for the R1
"≥ 5 tick manifests" and "timer ran a week" exit counts.

## Definition of Ready check

| Story | Trace | G/W/T | Pts | Arch basis | Deps | Testable | Ready? |
|---|---|---|---|---|---|---|---|
| S02-1 | PR-013, G1 | yes (above) | 2 | platform.md v1.3 §4 (to amend) | none | fixtures + live 10-16 manifest | **Yes** — architect amends §4 first |
| S02-2 | PR-132 | yes (above) | 1 | system.md §5 compose | none | `stat` on new files | **Yes** |
| S02-3 | PR-013 | yes (above) | 1 | ADR-S-008 | S02-1 | live, any evening | **Yes** |
| S02-4 | PR-013 | yes (above) | 1 | — (ops) | S02-2, S02-1 | `find … -user root` empty | **Yes** |
| F-003 | PR-002 | yes | 3 | VN§2; calendar as data | none | 2026-09-02 holiday fixture | **Yes** |
| F-019 | PR-020 | yes | 3 | system.md (systemd user timer) | F-003, S02-2 | timer list + one unattended run | **Yes** — note 1 |
| F-004 | PR-003 | yes | 5 | data.md §1.2 V3 listings | none | fixtures; idempotent re-run | **Yes** — note 2 |
| F-012 | PR-010 | yes | 5 | data.md §1.2/§1.4 (earlier dates reconstructed) | F-004 | interrupt + resume test | **Yes** — note 3 |

Notes (technical, left to the architects; no sponsor input):
1. **F-019 boot catch-up.** K1 has no past sessions, so catch-up after 23:00/next morning will record `missed`
   (`source_no_longer_serves`) — that meets the criterion ("fetches if served, or records the gap").
2. **F-004 vs the S01 universe.** The tick feed keeps its pinned-per-session universe; F-004 replaces only the
   source of the list (S01 plan note 2). Index-membership history starts from crawl start where the source has no past.
3. **F-012 back-fill is not live-bound** (daily history stays served), so it needs no clock milestone; a long
   back-fill must not run at the same time as the 15:30 tick crawl (shared rate budget, F-011).

## Risks

| Risk | Effect | Response |
|---|---|---|
| A C-row crawl is missed (nobody at the machine, overnight restart) | That session's ticks lost for good | C1–C5 clock milestones, owner sm, 23:00 deadline; F-019 first on the BE critical path after S02-2 |
| 21 pts vs velocity 20 | F-012 coverage or S02-4 slips | Named first-to-slip above; no other stretch |
| F-019 merged but timer never fires unattended before review | Criterion 1 only on unit tests | M2 needs one real unattended run (Thu 10-22 15:30); otherwise NOT DONE |
| Back-fill hits KBS/VCI rate limits or blocks | Crawl stops, tick crawl starved | F-011 stop-and-record; back-fill scheduled outside 15:00–23:00 |
| S02-1 contract change touches F-017 tests | Regression in the tick feed | Architect amends §4 before build; lead runs full kernel + `-m db` (R1 "no green, no merge") |
| Test worktree `test-be-01` not merged | S01 tests missing in sprint-02 | Lead reviews/merges it on day 1 (handoff §3) |

## Sponsor questions

None (A23 not needed). Pending from handoff: merge `sprint-01` → `main` before the sprint-02 branch is cut.
