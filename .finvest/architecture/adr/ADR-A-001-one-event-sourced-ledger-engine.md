# ADR-A-001 — One event-sourced ledger engine for what-if and backtests; nominal prices + corporate-action events
Status: Accepted · 2026-10-15

## Decision
A single `simulate()` loop (analytics.md §1.2) drives both the what-if (trivial buy/sell strategy) and every backtest
(PR-071). It replays **nominal** daily bars and applies corporate actions as dated events (cash in on pay date, shares in
on arrival, rights paid on ex-date); every state change is a ledger row and all figures are derived from the ledger.
Adjusted series are used only by indicators, charts, decomposition and the F-046 agreement test.

## Why
Adjusted-price replay hides lot rounding, dividend tax, settlement and the cash drag that the sponsor must learn (L2);
two engines would disagree somewhere and the golden cases could prove only one of them.

## Consequences
One set of golden cases covers both features; the CSV ledger and the screen cannot diverge; CA data quality (PR-011)
is on the critical path of every return figure, so missing `pay_date`/arrival dates are flagged, never guessed silently.
