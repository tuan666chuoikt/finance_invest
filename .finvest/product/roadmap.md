# Finvest — Roadmap

Owner: `fi-pm`. Source: `product/prd.md` §8 (Approved v2), `product/backlog.md`.
Changelog: 2026-10-16 — sponsor priority change (sponsor-answers 2026-10-16 23:17): the scenario dashboard slice
(what-if lump-sum + DCA, saved scenarios, side-by-side dashboard) is pulled forward to **S03**; R1 remainder moves to
S04–S05 and every later release shifts by one sprint. Same PRD scope.

## Velocity

- **20 points per sprint `[measured S01: 20/20 accepted]`** — kept at the sprint-01 retro (one data point,
  needed a 3-task fix loop). Recalibrate each retro from points accepted (not started); re-plan this file if
  actual velocity differs by more than 25 %.
- Sprint length is one `/fi-sprint-plan` → `/fi-retro` cycle; calendar dates are not committed.

## Releases

| Release | Points | Sprints | Exit = PRD §8 release criteria |
|---|---|---|---|
| S03 slice Scenario dashboard | 25 | S03 | Sponsor follows ≥ 2 saved scenarios side by side; F-040/F-041/F-057 worked examples pass to 1 VND; approximate flag on every adjusted-price result; disclaimer; "how computed"; EN/VI |
| R1 Data foundation | 76 | S01–S02, S04–S05 | ≥ 5 tick manifests, 0 silent gaps; daily ≥ 99.5 %; VN30 adjusted reconciled; rules page with status; timer ran a week; EN/VI |
| R2 What-if (rest) | 38 | S06–S07 | Golden cases within 1 VND; 0.05 % agreement on 10 dividend stocks; benchmark; "how computed"; disclaimer |
| R3 Price board | 45 | S08–S10 | ≤ 5 s median; stale badge proven by cutting source; all states spec'd and tested; VN§3 colours |
| R4 Scenarios | 46 | S11–S13 | Look-ahead test; shared engine; OOS on every ranking; documented "best of last 7 days" example |
| R5 Why it moved | 24 | S13–S14 | Reproducible decomposition; dated, sourced evidence; no causal wording; disclaimer |
| R6 Later | ~41 rough | after S14 | Defined after the R5 retro (news A9, fundamentals, journal, backup …) |

v1 (slice + R1–R5): 76 stories, 254 points ≈ 12.7 sprints at the measured velocity. R2's "golden cases" and
"0.05 % dividend agreement" exits still gate removal of the approximate flag (F-014, F-015, F-043, F-044).

## Sprint plan S01–S05 (draft; finalised at each `/fi-sprint-plan`)

Order rule: **start the tick store first** (C1: every lost session is lost for good).

| Sprint | Goal | Stories | Pts |
|---|---|---|---|
| S01 | Ticks are being collected every evening | F-030, F-010, F-011, F-020, F-017 | 20 |
| S02 | Crawl runs itself; reference data exists | S02-1..4, F-003, F-019, F-004, F-012 | 21 |
| **S03** | **Sponsor follows many investment scenarios side by side** | F-031, F-032, F-006, F-040, F-041, F-057, F-055, F-056, F-048, F-051 | **25** |
| S04 | Prices are right: daily update, corporate actions, nominal + adjusted | F-013, F-014, F-015, F-016, F-023, F-033 | 19 |
| S05 | Sponsor can see and trust the data | F-001, F-002, F-005, F-021, F-022, F-018 | 21 |

S03 starts as soon as F-012's daily bars (BE-bars-store, BE-bars-backfill) are merged. It is 25 points, 25 % over
the measured 20 (edge of the re-plan band): **first to slip is F-048** (benchmarks → S04), then the table toggle of
F-056. Build order: F-006 + F-031 in parallel → F-040 → F-041, F-057 → F-055 → F-056 → F-048, F-051, F-032.
S03 risk: without F-013 (S04) "today" means the latest back-filled bar, shown as "data as of …"; re-running the
back-fill refreshes it. The "timer ran a week" and "≥ 5 tick sessions" exits keep counting from F-019 (S02) in
the background, so R1 can still exit at S05.

**Moved by the S03 change (one line each):**
- F-013 S03 → S04: "today" can use the back-filled bars for now; daily update needed only once the dashboard is in use.
- F-014, F-015, F-016 S03 → S04: they remove the approximate flag; the flag makes S03 honest meanwhile.
- F-018 S03 → S05: the KBS crawl already covers the full market in an evening (10-16: 0 skips), so ordering is a fallback.
- F-033 (audit half of F-032) → S04: the banner ships in S03; the no-broker audit protects nothing new until then.
- F-001 (rest), F-002, F-005, F-021, F-022 S04 → S05: data-trust pages; the sponsor asked for scenarios first.
- F-042 (other fill rules), F-053 (single what-if screen) stay in R2, now S06–S07: the dashboard covers the need.

## Later releases (story order)

- **R2 rest (S06–S07):** F-043, F-044, F-050 first (clear the approximate flag with F-014/F-015) → F-045, F-046,
  F-042 → F-047, F-049, F-052, F-053, F-054.
- **R3 (S08–S10):** F-060, F-061, F-062, F-063 → F-068, F-064, F-066, F-065,
  F-067 → F-069, F-070, F-071, F-072. Needs A14 (default watchlist).
- **R4 (S11–S13):** F-080 first (engine + look-ahead, reuses the S03 what-if engine) → F-081, F-082, F-083 → F-084, F-085, F-086, F-087 →
  F-088, F-089, F-090 (needs A13), F-091, F-092, F-093.
- **R5 (S13–S14):** F-100 → F-101, F-102, F-103 → F-104, F-105, F-106.

## Risks to the plan

| Risk | Effect | Response |
|---|---|---|
| Velocity differs from the assumed 20 | All dates move | Re-plan after S01 retro |
| Free tick endpoint cannot do a full-market pass in an evening | F-017 partial manifests | F-018 priority order; completeness reported, not targeted (G1) |
| Source blocks or changes format | Crawl stops | F-010 fixtures, F-011 stop-and-report, second adapter as follow-up |
| Machine off on trading days | Tick holes | Accepted (A7); listed on F-021 |
| S03 at 25 pts (first web UI + engine) | Slice not done in one sprint | F-048 slips first; dashboard without benchmarks is still usable |
| Sponsor reads adjusted-price results as exact | Wrong lesson on dividend stocks | Approximate flag on every card (test-enforced) until F-014/F-015/F-043/F-044 |
