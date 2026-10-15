# ADR-A-004 — "Why it moved" = beta/relative decomposition + dated evidence items with uncertainty; no causal claims, no LLM
Status: Accepted · 2026-10-15

## Decision
Decomposition on our adjusted returns with β estimated on 250 sessions ending before the window (min 120); sector =
equal-weight ICB-2 peers; both the relative and the beta variant are shown with the estimation window and 95 % intervals
(analytics.md §3). Evidence items are facts with timestamps and sources; absent data (proprietary flow, A17) appears as
`unavailable`, never silently omitted. Titles and strings avoid causal verbs (PM list, tested). No LLM in v1 (A4); a
markdown export lets the sponsor ask an external assistant; a `Summariser` port is reserved for a local model.

## Consequences
The view teaches L6 without pretending to know causes; βs on illiquid UPCoM names will be noisy, and the interval says so.
