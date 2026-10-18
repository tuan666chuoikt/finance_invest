# Sprint 03 — Plan

Owner: `fi-pm`, 2026-10-16. Sprint starts when sprint-02's daily bars merge (BE-bars-store merged 66d6b99;
BE-bars-backfill pending) — **assumed Sat 2026-10-17 → Fri 2026-10-23 18:00** `[assumed]`; if the start slips,
every M date below moves by the same number of days (C rows do not move: they follow the market).
Inputs: `product/backlog.md` (Sprint-03 slice), `product/roadmap.md` (S03 row), `product/ux/app-shell.md`,
`product/ux/scenario-dashboard.md`, `sprint-01/6-retro.md` (R5), sponsor priority change 2026-10-16 23:17.

## Goal

**The sponsor saves many investment scenarios and follows them side by side in the web UI.** By Friday
`apps/web` runs on 127.0.0.1 in EN/VI, the sponsor creates ≥ 2 lump-sum/DCA scenarios, and the dashboard shows
each one's value, P/L, equity curve, benchmarks and "how computed", with the approximate flag on every
adjusted-price result. F-040/F-041/F-057 worked examples pass to 1 VND.

## Capacity

- Velocity **20 points `[measured S01: 20/20]`** (S02 not yet measured). Committed: **25 points** (+25 %, edge
  of the re-plan band; accepted at the backlog change 2026-10-16).
- First to slip: **F-048** (benchmarks → S04), then the F-056 table toggle. The dashboard without benchmarks is still usable.

## Committed stories

| Story | Pts | Title | Order / depends on |
|---|---|---|---|
| F-006 | 1 | Trading-cost rules v1 (`rules_version`) | first, parallel with F-031 |
| F-031 | 3 | Web app shell EN/VI (first `apps/web`) | first, parallel with F-006 |
| F-040 | 3 | Lump-sum buy: lots, fee, residual cash, non-trading shift | after F-006, F-012 bars |
| F-041 | 2 | Value at end date: liquidation value, P/L, CAGR | after F-040 |
| F-057 | 3 | DCA: monthly amount, whole lots, carried cash | after F-040 (uses F-003) |
| F-055 | 3 | Saved scenarios: create / edit / delete | after F-040, F-057 |
| F-056 | 5 | Scenario dashboard (cards, table, curve, flag, states) | after F-041, F-055, F-031 |
| F-032 | 1 | Disclaimer banner on analysis routes | after F-031 + F-056 routes |
| F-048 | 2 | Benchmarks VN-Index + E1VFVN30 | after F-041, F-057 — first to slip |
| F-051 | 2 | "How computed" panel | after F-041 |
| **Total** | **25** | | |

Acceptance criteria: as written in `product/backlog.md` (all Ready, worked examples included). Decision times:
F-040 close of N, F-041 close of M (or latest stored bar, "as of"), F-057 close of each contribution date,
F-048 same dates/cash-flow dates as the scenario.

## Milestones

| Id | Name | Due (VN time) | Stories |
|---|---|---|---|
| M1 | Rules v1 + app shell | 2026-10-18 18:00 (day 2) | F-006, F-031 |
| M2 | What-if engine: lump-sum, value, DCA — worked examples to 1 VND | 2026-10-20 18:00 (day 4) | F-040, F-041, F-057 |
| M3 | Saved scenarios + dashboard + banner | 2026-10-22 18:00 (day 6) | F-055, F-056, F-032 |
| M4 | Benchmarks + how computed | 2026-10-23 18:00 (day 7) | F-048, F-051 |
| C1…C5 | Nightly crawl verification (R5), owner sm | each trading day 23:00 | see below |

**Clock milestones (retro R5).** The F-019 timer is installed (BE-scheduler 7a74581: 15:30 run, 20:00 retry).
KBS serves only the current session and stops by next morning, so each trading evening the SM checks that the
timer wrote that session's manifest; if it is missing at 21:00 the SM runs `make crawl` by hand (or prompts the
sponsor) and confirms the manifest before 23:00. Weekend 10-17/10-18 has no session.

| Id | Session | Check | Done by | Lost if missed |
|---|---|---|---|---|
| C1 | 2026-10-19 Mon | manifest present 21:00, else manual crawl | 2026-10-19 23:00 | the whole 10-19 tick tape, for good |
| C2 | 2026-10-20 Tue | same | 2026-10-20 23:00 | the whole 10-20 tick tape |
| C3 | 2026-10-21 Wed | same | 2026-10-21 23:00 | the whole 10-21 tick tape |
| C4 | 2026-10-22 Thu | same | 2026-10-22 23:00 | the whole 10-22 tick tape |
| C5 | 2026-10-23 Fri | same | 2026-10-23 23:00 | the whole 10-23 tick tape |

Each missed C row is also a lost day for the R1 "≥ 5 tick manifests" and "timer ran a week" exit counts.

## Definition of Ready check

| Story | Trace | G/W/T | Pts | Arch basis | Deps | Testable | Ready? |
|---|---|---|---|---|---|---|---|
| F-006 | PR-001 | yes | 1 | VN§4–§5 | none | effective_from test | **Yes** |
| F-031 | PR-137 | yes | 3 | ux/app-shell.md; system.md (127.0.0.1) | none | missing-key test | **Yes** — note 1 |
| F-040 | PR-030 | yes + example | 3 | F-012 `bars_1d_src`, F-003 | F-006, bars | 635,975 example; perturb-after-N test | **Yes** |
| F-041 | PR-030 | yes + example | 2 | — | F-040 | 10,610,975 example | **Yes** |
| F-057 | PR-070 | yes + example | 3 | F-003 calendar | F-040 | month-5 example | **Yes** |
| F-055 | PR-072 | yes | 3 | local DB (data.md) | F-040, F-057, F-004 | validation + restart | **Yes** — note 2 |
| F-056 | PR-072 | yes | 5 | ux/scenario-dashboard.md | F-041, F-055 | flag test; states | **Yes** |
| F-032 | PR-130 | yes | 1 | — | F-031 | route enumeration test | **Yes** |
| F-048 | PR-034 | yes + example | 2 | index + ETF daily bars | F-041, F-057 | +1.11 pp example; n/a cell | **Yes** — note 3 |
| F-051 | PR-110 | yes | 2 | — | F-041 | every-figure test | **Yes** |

Notes (technical, left to the architects; no sponsor input):
1. **First web app.** The architect picks the `apps/web` stack and the analytics/API contract (contracts/platform.md,
   contracts/analytics.md) before build; the engine lives in a pure package so the R4 backtester (F-080) reuses it.
2. **F-055 < 2 s for 20 × 10-year scenarios** is measured on the sponsor's machine at review, not in CI.
3. **F-048 needs VN-Index and E1VFVN30 daily bars.** If F-012's back-fill does not cover the index or the ETF,
   the architect adds them to the back-fill in this sprint (no new source); until then the cell reads "n/a — data
   from …", never zero (criterion already covers it).

## Risks

| Risk | Effect | Response |
|---|---|---|
| 25 pts vs velocity 20; first web UI + engine | Slice not done by Friday | F-048 slips first, then the table toggle; nothing else is stretch |
| BE-bars-backfill merges late | F-040 onward has no bars; start slips | M dates move with the start; F-006 + F-031 need no bars |
| A C-row check is missed (timer fails, machine off, nobody checks) | That session's ticks lost for good | C1–C5, owner sm, 21:00 check / 23:00 deadline |
| Back-fill re-run during 15:30–23:00 | Shares the rate budget with the tick crawl | Back-fill only outside 15:00–23:00 (S02 note 3) |
| Sponsor reads adjusted-price results as exact | Wrong lesson on dividend stocks | Approximate flag on every card, test-enforced (F-056) |
| Index/ETF bars missing | F-048 shows n/a | DoR note 3; F-048 is first to slip anyway |
| Money math off by rounding | Wrong P/L shown | Worked examples to 1 VND are acceptance gates; testers recompute independently |

## Sponsor questions

None (A23 not needed).
