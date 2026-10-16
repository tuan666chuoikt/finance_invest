# Finvest — Roadmap

Owner: `fi-pm`. Source: `product/prd.md` §8 (Approved v2), `product/backlog.md`.

## Velocity

- **20 points per sprint `[measured S01: 20/20 accepted]`** — kept at the sprint-01 retro (one data point,
  needed a 3-task fix loop). Recalibrate each retro from points accepted (not started); re-plan this file if
  actual velocity differs by more than 25 %.
- Sprint length is one `/fi-sprint-plan` → `/fi-retro` cycle; calendar dates are not committed.

## Releases

| Release | Points | Sprints | Exit = PRD §8 release criteria |
|---|---|---|---|
| R1 Data foundation | 81 | S01–S04 | ≥ 5 tick manifests, 0 silent gaps; daily ≥ 99.5 %; VN30 adjusted reconciled; rules page with status; timer ran a week; EN/VI |
| R2 What-if | 53 | S05–S07 (S07 shared with R3) | Golden cases within 1 VND; 0.05 % agreement on 10 dividend stocks; benchmark; "how computed"; disclaimer |
| R3 Price board | 45 | S07–S09 | ≤ 5 s median; stale badge proven by cutting source; all states spec'd and tested; VN§3 colours |
| R4 Scenarios | 48 | S10–S12 | Look-ahead test; shared engine; OOS on every ranking; documented "best of last 7 days" example |
| R5 Why it moved | 24 | S12–S13 | Reproducible decomposition; dated, sourced evidence; no causal wording; disclaimer |
| R6 Later | ~41 rough | after S13 | Defined after the R5 retro (news A9, fundamentals, journal, backup …) |

v1 (R1–R5): 71 stories, 251 points ≈ 12.6 sprints at the assumed velocity.

## R1 sprint plan (draft; finalised at each `/fi-sprint-plan`)

Order rule: **start the tick store first** (C1: every lost session is lost for good).

| Sprint | Goal | Stories | Pts |
|---|---|---|---|
| S01 | Ticks are being collected every evening | F-030, F-010, F-011, F-020, F-017 | 20 |
| S02 | Crawl runs itself; reference data exists | F-019, F-003, F-004, F-012, F-031 | 19 |
| S03 | Prices are right: daily, corporate actions, adjusted | F-013, F-014, F-015, F-016, F-018, F-032 | 20 |
| S04 | Sponsor can see and trust the data | F-001, F-002, F-005, F-021, F-022, F-023 | 22 |

S04 is 2 points over the assumed velocity; F-022 is the first to slip into S05. The "timer ran a week" and
"≥ 5 tick sessions" criteria start counting once F-019 lands in S02, so they are met by the end of S04 if the
machine is on for 5 trading days.

## Later releases (story order)

- **R2 (S05–S07):** F-040, F-041, F-042, F-050 (kit grows with each event) → F-043, F-044, F-045, F-046 →
  F-047, F-048, F-049, F-051, F-052, F-053, F-054.
- **R3 (S07–S09):** F-060, F-061, F-062, F-063 → F-068, F-064, F-066, F-065,
  F-067 → F-069, F-070, F-071, F-072. Needs A14 (default watchlist).
- **R4 (S10–S12):** F-080 first (engine + look-ahead) → F-081, F-082, F-083 → F-084, F-085, F-086, F-087 →
  F-088, F-089, F-090 (needs A13), F-091, F-092, F-093.
- **R5 (S12–S13):** F-100 → F-101, F-102, F-103 → F-104, F-105, F-106.

## Risks to the plan

| Risk | Effect | Response |
|---|---|---|
| Velocity differs from the assumed 20 | All dates move | Re-plan after S01 retro |
| Free tick endpoint cannot do a full-market pass in an evening | F-017 partial manifests | F-018 priority order; completeness reported, not targeted (G1) |
| Source blocks or changes format | Crawl stops | F-010 fixtures, F-011 stop-and-report, second adapter as follow-up |
| Machine off on trading days | Tick holes | Accepted (A7); listed on F-021 |
