# ADR-S-002 — Data sources: own thin adapters to KBS / VCI / SSI public endpoints, not the vnstock package
Status: Accepted (pending A16) · 2026-10-15

## Context (verified 2026-10-15, data.md §1)
vnstock Gen 5 is pre-compiled, installed from a private index, PyPI-quarantined since 2026-09-24, custom licence,
account registration required, and its Community caps are far below the endpoints it wraps (1m 180 d vs ~3 y on VCI;
trades 5,000 vs whole session on KBS; order book / foreign flow Sponsor-only). The underlying endpoints answer
anonymous requests: KBS (full-session tick tape in one call), VCI (daily since 2006, 1m since 2023-09, symbols incl.
delisted, corporate events, watchlist board), SSI iBoard (full-market snapshot in 3 calls, daily since 2010).
TCBS is behind a Cloudflare challenge; VNDirect timed out.

## Decision
Implement `MarketDataSource` adapters ourselves with httpx: `kbs` (ticks), `vci` (bars 1m/1d, symbols, events,
watchlist board), `ssi` (close snapshot, market board, daily cross-check). Per-source token bucket (≤ 2 req/s),
personal user-agent, every response archived, stop after 3 consecutive 429/403/HTML responses (PR-135). The vnstock
4.x source on GitHub is reference documentation only; it is not a dependency.

## Consequences
No account, no binary blob, deeper data. We carry the parsing risk (C6): Pydantic payload models + recorded
fixtures per endpoint; a shape change fails the feed loudly and keeps the raw payload for a new fixture.
The ToS exposure is identical to vnstock's (it calls the same URLs) and is put to the sponsor as A16.
