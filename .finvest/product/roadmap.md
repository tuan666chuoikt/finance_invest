# Finvest — Roadmap

Owner: `fi-pm`. Source: `product/prd.md` §8 (Approved v2), `product/backlog.md`.
Changelog: 2026-10-16 — sponsor priority change (sponsor-answers 2026-10-16 23:17): the scenario dashboard slice
(what-if lump-sum + DCA, saved scenarios, side-by-side dashboard) is pulled forward to **S03**; R1 remainder moves to
S04–S05 and every later release shifts by one sprint. Same PRD scope.
2026-10-26 — sprint-04 became the visual-design sprint (A25, 18/18 accepted). The planned "S04 prices" row is now **S05**,
"S05 trust" is **S06**, and every later release shifts by one more sprint. F-013 2→1, F-023 3→2 (mostly delivered in S03).

## Velocity

- **20 points per sprint `[measured S01: 20/20; S03: 30/30 in 9 days ≈ 23/7 days; S04: 18/18, CSS-only, not a capacity signal]`** — kept at the sprint-01 and sprint-03 retros (one data point,
  needed a 3-task fix loop). Recalibrate each retro from points accepted (not started); re-plan this file if
  actual velocity differs by more than 25 %.
- Sprint length is one `/fi-sprint-plan` → `/fi-retro` cycle; calendar dates are not committed.

## Releases

| Release | Points | Sprints | Exit = PRD §8 release criteria |
|---|---|---|---|
| S03 slice Scenario dashboard | 25 | S03 | Sponsor follows ≥ 2 saved scenarios side by side; F-040/F-041/F-057 worked examples pass to 1 VND; approximate flag on every adjusted-price result; disclaimer; "how computed"; EN/VI |
| S04 slice Visual design (A25) | 18 | S04 | Screens match `ux/visual-design.md`; 28 screenshots pass the §9 checklist |
| R1 Data foundation | 74 | S01–S02, S05–S06 | ≥ 5 tick manifests, 0 silent gaps; daily ≥ 99.5 %; VN30 adjusted reconciled; rules page with status; timer ran a week; EN/VI |
| R2 What-if (rest) | 38 | S07–S08 | Golden cases within 1 VND; 0.05 % agreement on 10 dividend stocks; benchmark; "how computed"; disclaimer |
| R3 Price board | 45 | S09–S11 | ≤ 5 s median; stale badge proven by cutting source; all states spec'd and tested; VN§3 colours |
| R4 Scenarios | 46 | S12–S14 | Look-ahead test; shared engine; OOS on every ranking; documented "best of last 7 days" example |
| R5 Why it moved | 24 | S14–S15 | Reproducible decomposition; dated, sourced evidence; no causal wording; disclaimer |
| R6 Later | ~41 rough | after S15 | Defined after the R5 retro (news A9, fundamentals, journal, backup …) |

v1 (slice + R1–R5): 77 stories, 257 points ≈ 12.9 sprints at the measured velocity. R2's "golden cases" and
"0.05 % dividend agreement" exits still gate removal of the approximate flag (F-014, F-015, F-043, F-044).

## Sprint plan S01–S06 (draft; finalised at each `/fi-sprint-plan`)

Order rule: **start the tick store first** (C1: every lost session is lost for good).

| Sprint | Goal | Stories | Pts |
|---|---|---|---|
| S01 | Ticks are being collected every evening | F-030, F-010, F-011, F-020, F-017 | 20 |
| S02 | Crawl runs itself; reference data exists | S02-1..4, F-003, F-019, F-004, F-012 | 21 |
| **S03** | **Sponsor follows many investment scenarios side by side** | F-031, F-032, F-006, F-040, F-041, F-057, F-055, F-056, F-048, F-051 | **25** |
| S04 | **The web app looks like a real product** (A25, inserted) | F-129, F-130, F-131, F-132, S04-RW | 18 ✓ |
| **S05** | **Prices are right: daily update, corporate actions, nominal + adjusted** (manual press, A23) | F-013, F-014, F-015, F-016, F-023, F-033, S05-RW | **19** |
| S06 | Sponsor can see and trust the data | F-001, F-002, F-005, F-021, F-022, F-018 | 21 |

S03 starts as soon as F-012's daily bars (BE-bars-store, BE-bars-backfill) are merged. It is 25 points, 25 % over
the measured 20 (edge of the re-plan band): **first to slip is F-048** (benchmarks → S04), then the table toggle of
F-056. Build order: F-006 + F-031 in parallel → F-040 → F-041, F-057 → F-055 → F-056 → F-048, F-051, F-032.
S03 risk: without F-013 (S04) "today" means the latest back-filled bar, shown as "data as of …"; re-running the
back-fill refreshes it. The "timer ran a week" and "≥ 5 tick sessions" exits keep counting from F-019 (S02) in
the background, so R1 can still exit at S06. Since A23 there is no timer: R1's "timer ran a week" exit reads "a press on ≥ 5 trading days" (PO to confirm with the PRD A23 alignment).

**Moved by the S03 change (one line each; sprint numbers as of 2026-10-16 — add one since the 2026-10-26 shift):**
- F-013 S03 → S04: "today" can use the back-filled bars for now; daily update needed only once the dashboard is in use.
- F-014, F-015, F-016 S03 → S04: they remove the approximate flag; the flag makes S03 honest meanwhile.
- F-018 S03 → S05: the KBS crawl already covers the full market in an evening (10-16: 0 skips), so ordering is a fallback.
- F-033 (audit half of F-032) → S04: the banner ships in S03; the no-broker audit protects nothing new until then.
- F-001 (rest), F-002, F-005, F-021, F-022 S04 → S05: data-trust pages; the sponsor asked for scenarios first.
- F-042 (other fill rules), F-053 (single what-if screen) stay in R2, now S07–S08: the dashboard covers the need.

## Later releases (story order)

- **R2 rest (S07–S08):** F-043, F-044, F-050 first (clear the approximate flag with F-014/F-015) → F-045, F-046,
  F-042 → F-047, F-049, F-052, F-053, F-054.
- **R3 (S09–S11):** F-060, F-061, F-062, F-063 → F-068, F-064, F-066, F-065,
  F-067 → F-069, F-070, F-071, F-072. Needs A14 (default watchlist).
- **R4 (S12–S14):** F-080 first (engine + look-ahead, reuses the S03 what-if engine) → F-081, F-082, F-083 → F-084, F-085, F-086, F-087 →
  F-088, F-089, F-090 (needs A13), F-091, F-092, F-093.
- **R5 (S14–S15):** F-100 → F-101, F-102, F-103 → F-104, F-105, F-106.

## Risks to the plan

| Risk | Effect | Response |
|---|---|---|
| Velocity differs from the assumed 20 | All dates move | Re-plan after S01 retro |
| Free tick endpoint cannot do a full-market pass in an evening | F-017 partial manifests | F-018 priority order; completeness reported, not targeted (G1) |
| Source blocks or changes format | Crawl stops | F-010 fixtures, F-011 stop-and-report, second adapter as follow-up |
| Machine off on trading days | Tick holes | Accepted (A7); listed on F-021 |
| S03 at 25 pts (first web UI + engine) | Slice not done in one sprint | F-048 slips first; dashboard without benchmarks is still usable |
| Sponsor reads adjusted-price results as exact | Wrong lesson on dividend stocks | Approximate flag on every card (test-enforced) until F-014/F-015/F-043/F-044 |
