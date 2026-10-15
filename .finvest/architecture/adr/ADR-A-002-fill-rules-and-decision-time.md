# ADR-A-002 — Declared fill rules; decision at close t, default fill next open for rule strategies
Status: Accepted · 2026-10-15

## Decision
Fills are `close_t | next_open | vwap_t | limit(p)` and always shown on the result (PR-031). What-if defaults to
`close_t` (the user names a date in hindsight on purpose). Backtests default to `next_open`: a rule evaluated on the
close of t cannot be executed at that same close; `close` is allowed but tagged `optimistic_close_fill`. Strategies
receive only `view.*(…, as_of=t)`. No fill outside `[low, high]`; zero-volume days do not fill. T+2 (VN§5): shares bought
at a fill on day d are sellable at a `close` fill on d+2 and at a `next_open` fill on d+3.

## Consequences
Look-ahead is a construction property, verified by the perturbation test (analytics.md §4). Backtest returns are lower
than "close-to-close" tutorials show; the UI explains the gap (L4). ATO/ATC order mechanics are not modelled (no
intraday order book in daily mode); 1m/tick replay is a later extension of the same fill interface.
