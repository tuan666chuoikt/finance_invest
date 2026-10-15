# Sprint 01 — Plan

Owner: `fi-pm`. Inputs: `product/backlog.md` (Approved), `product/roadmap.md` (S01 row), `architecture/system.md`,
`architecture/data.md` §1–§4 (approved 2026-10-15, A16–A21 = A).

## Goal

**Ticks are being collected every evening.** By sprint end the sponsor runs one command on Ubuntu, the app starts on
127.0.0.1, and one command crawls the current session's tick tape for every listed symbol (KBS K1), writing raw
archive + normalised rows under `finance_invest/data/` and a per-session manifest that shows every skipped symbol
and every missed session — never a silent gap (G1, C1).

Why first: KBS serves only the current session (data.md §1.2), so every day without a crawler is lost for good.

## Capacity

- Velocity **20 points `[assumed]`** (no sprint has run). Committed: **20 points**, no stretch.
- Recalibrate at the S01 retro from points **accepted**, not started (roadmap rule).
- Live acceptance needs **≥ 1 trading-day evening** inside the sprint (KBS has no past sessions); fixtures cover the rest.

## Committed stories

| Story | Pts | Title | Order / depends on |
|---|---|---|---|
| F-020 | 1 | Data folder under the repo, git-ignored | first (no deps) |
| F-030 | 3 | Local docker compose, one-command start and crawl | after F-020; "crawl a date" criterion closes with F-017 |
| F-010 | 5 | MarketDataSource adapter with fixtures and unit conversion | parallel with F-030 |
| F-011 | 3 | Rate limits, caching, backoff, stop on block | after F-010 interface |
| F-017 | 8 | Tick crawl after close with manifest | after F-010, F-011, F-020 |
| **Total** | **20** | | |

Not in S01 (roadmap S02+): F-019 scheduler (so S01 crawls are started by hand), F-004 symbol master, F-003 calendar,
F-018 priority order, F-021 data-quality page.

## Milestones

| Id | Name | Target | Stories |
|---|---|---|---|
| M1 | Platform up: data folder + compose on 127.0.0.1 | 2026-10-19 `[assumed]` | F-020, F-030 |
| M2 | Adapters offline-tested, rate-limited | 2026-10-21 `[assumed]` | F-010, F-011 |
| M3 | First real session crawled with manifest | 2026-10-23 (Fri, trading day) `[assumed]` | F-017 (+ F-030 crawl criterion) |

Dates are targets for the progress report, not commitments (roadmap: calendar dates not committed).

## Definition of Ready check

DoR = traced to PR, Given/When/Then, points ≤ 8, money/decision-time rule where relevant, dependencies known,
architecture decision exists, testable without sponsor input.

| Story | PR | G/W/T | Pts | Arch basis | Deps | Testable | Ready? |
|---|---|---|---|---|---|---|---|
| F-020 | PR-132 | yes | 1 | data.md §2 raw archive `data/raw/…`; A12 | none | `git status` clean after a crawl | **Yes** |
| F-030 | PR-131 | yes | 3 | system.md §5, ADR-S-001 (PG16+Timescale in Docker), ADR-S-003 | F-020; crawl criterion needs F-017 | bind check from a second host / `ss -ltn` | **Yes** |
| F-010 | PR-016, C9 | yes | 5 | ADR-S-002 own adapters; data.md §1.2 K1/V1/V2/V3; ADR-S-005 integer VND | none | fixtures, network disabled | **Yes** — note 1 |
| F-011 | PR-135 | yes | 3 | data.md §1.2 rate policy (KBS/VCI 2 req/s, SSI 1 req/s, 1→2→4→8 s, stop after 3) | F-010 | fake server returning 429/403/HTML challenge | **Yes** |
| F-017 | PR-013, C1 | yes | 8 | ADR-S-008 tick idempotence + manifests; data.md §3 `ticks`, `crawl_runs`, `crawl_sessions` | F-010, F-011, F-020 | fixtures for idempotence/checksum; one live evening | **Yes** — notes 2–4 |

Notes (technical, decided here or left to the architects; no sponsor input needed):
1. **F-010 unit criterion.** K1 already quotes VND and shares; the "thousand VND / ×10 volume" path is exercised
   by the S2 (SSI, thousand VND) fixture. The adapter documents each source's unit rule.
2. **F-017 symbol universe without F-004.** The symbol master is S02. In S01 the tick feed takes its list from
   V3 `symbols/getAll` at run time (listed stocks + ETFs, CW and delisted excluded) and writes that list into the
   manifest. F-004 later replaces the source of the list, not the feed. Architects size this inside F-017's tasks.
3. **F-017 "machine off / source no longer serves".** Without F-003/F-019, the S01 test is: `crawl --date <past
   date>` → manifest status `missed`, reason "source no longer serves" (K1 ignores `?date=`). Boot catch-up and
   holiday skipping are F-019/F-003 (S02).
4. **F-017 side field.** `ticks.side` nullable; K1 `LC` observed empty (data.md §5). Storing NULL meets "side where
   given". The 10:00 in-session sample spike is optional, not a sprint gate.

## Risks

| Risk | Effect | Response |
|---|---|---|
| Velocity ≠ 20 (first sprint, F-017 is an 8) | F-017 slips → goal missed | Build order puts F-017 tasks on the critical path from day 1; F-030 crawl criterion slips with it, nothing else does |
| No trading-day evening with a working build before review | F-017 accepted on fixtures only | M3 targeted on Fri 2026-10-23; otherwise review notes "live run pending" and the story stays NOT DONE |
| KBS blocks or changes format | Crawl stops | F-011 stop-and-record "source blocked"; V1 fallback is config (system.md §8); fixtures catch format drift |
| Full pass > evening window (N5 ≤ 45 min `[assumed]`) | Partial manifests | Manifest lists skipped symbols (G1); F-018 priority order is S03 |
| Sessions lost before S01 ships (C1) | Permanent tick holes from crawl start | Accepted; crawl start date recorded in the first manifest; the store is "from date X" by design |
| Machine off on trading days (A7) | Holes | Accepted; scheduler F-019 is S02 |

## Sponsor questions

None (A22 not needed).
