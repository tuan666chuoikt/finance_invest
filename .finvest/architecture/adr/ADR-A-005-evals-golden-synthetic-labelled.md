# ADR-A-005 — Correctness is proven by golden cases, synthetic series and labelled windows, offline
Status: Accepted · 2026-10-15

## Decision
Three eval families live in `tests/fixtures/analytics/` and run in the kernel (< 30 s): (1) ≥ 20 hand-computed golden
cases (YAML with the hand calculation, F-050) matched to 1 VND; (2) synthetic series with analytically known signals,
trades and returns; (3) attribution recovery on synthetic β and 5 hand-labelled real windows. Honesty rules
(analytics.md §4) are property tests with Hypothesis. Testers keep an independent calculator (CLAUDE.md Done rule).

## Consequences
Any formula change must update a golden case explicitly (reviewers see the diff); no eval depends on the network or
on `[verify]` rules being settled — unverified rules are parameters of the fixture.
