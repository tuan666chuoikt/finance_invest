# ADR-A-006 — Metric conventions: 250 sessions/year, CAGR on calendar days, Sharpe on arithmetic daily excess
Status: Accepted · 2026-10-15

## Decision
Annualisation factor 250 (VN trades ~248–250 days/year); CAGR = `(E/A)^(365/calendar_days) − 1` (F-041);
volatility = `std(daily simple returns, ddof=1) × √250`; Sharpe = `mean(daily − rf_daily) × 250 / volatility` with
`rf_daily = (1 + rf)^(1/250) − 1`, rf default 5 %/y (A13); Sortino uses downside deviation vs `rf_daily`; max drawdown on
the daily equity curve (int VND) with duration and time under water; win rate per closed round trip; exposure = days
with a position / days; turnover = traded value / mean equity / years. Statistics in float64, money in int, outputs
as decimal strings; every metric is a `Figure` with its formula.

## Consequences
Numbers match the F-090 example (12 % − 5 %) / 20 % = 0.35; different conventions in other tools are explained in the
glossary rather than silently matched.
