# ADR-S-005 — Money and quantities: integer VND, integer shares, Decimal ratios; no floats in the domain
Status: Accepted · 2026-10-15

## Decision
Prices, cash, fees, taxes, values: Python `int` VND / SQL `BIGINT`. Shares: `int`. Ratios (bonus a:b,
fees 0.15 %, factors): `Decimal` / `NUMERIC`; rounding rules are explicit per rule (ceiling/floor **inward** to
tick, VN§3; fees half-up to 1 VND; adjusted prices half-up to 1 VND). Index levels `NUMERIC(12,2)`. JSON carries
money as integers and ratios/percentages as decimal strings (platform.md §1.2). Adapters convert thousand VND
(SSI history ×1000) at the boundary (C9). numpy in analytics uses int64 VND arrays; Decimal only at the ledger.

## Consequences
Golden cases (PR-037) can assert exact equality to 1 VND; no 0.1 + 0.2 surprises; the UI formats, never computes.
