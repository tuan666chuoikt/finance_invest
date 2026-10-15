# ADR-S-004 — Frontend: React + Vite + TS; board realtime by HTTP polling (SSE as upgrade path)
Status: Accepted · 2026-10-15

## Decision
React 18, Vite, TypeScript, TanStack Query (caching, refetchInterval), TanStack Table + virtualisation for the
board, `lightweight-charts` (Apache 2) for candles, i18next with `en.json`/`vi.json` and a key-parity test
(F-031). Types generated from `packages/contracts/openapi.json`.

Realtime (R3): the web **polls** `GET /api/board/watchlist` every 3 s in session (60 s when closed). The crawler's
`poll` process refreshes the watchlist from VCI (1 call) every 3 s and the market from SSI (3 calls) every 45 s into
an in-memory snapshot the API serves; rows carry `as_of` and the server computes `stale`. G6 (≤ 5 s median,
badge > 15 s) is met with a 3 s poll + ≤ 3 s source refresh. Only if R3 measurement shows otherwise do we add
`GET /board/stream` (SSE, same row shape) — no schema change.

## Why not WebSocket/SSE now
It is more code (connection lifecycle, reconnect, back-pressure) for a single viewer whose refresh budget is 5 s;
polling through TanStack Query is ~5 lines and already gives stale handling.
