# Consult S-v2-batch (owner: sa; cc ai, pm)

## Finding
V2 `gap-chart` returned HTTP 200 with body `[]` (2 bytes) for EVERY multi-symbol request I sent. No fixture can be
recorded, so the acceptance (>= 48 symbols x 8 days) cannot be met. Single-symbol calls from the app work (the
2026-10-24 16:08 `FPT-1d-6000` call returned 4,949 rows), so the endpoint is up.

Calls made (all anonymous, urllib or curl, body `{"timeFrame":"ONE_DAY","symbols":[...],"countBack":N,"to":epoch}`,
UA `finvest-personal/0.1`), 0.1-0.5 s each, all `200 []`:
- `to` = Sat 2026-10-24 23:59:59 VN: 50 (48 live HOSE/HNX + VTS,VTL delisted), 100, 200 symbols (countBack 8); 8 live symbols x 6000; 3 symbols (FPT,VNM,VTS) via curl.
- `to` = Fri 2026-10-23 23:59:59 VN: the same four shapes again.
Total 9 live calls: **over the plan's cap of 6**. My fault: a script loop re-ran all four shapes after I only meant to change `to`.
I stopped; no more calls were made. All responses were 2 bytes, so no load was put on the source.

## Not measured
Cap per call, latency of a 50-symbol call vs ~6.7 s for 1 symbol, bars per symbol, delisted behaviour, and back-fill shape
(8 x 6000 returned `[]` too). Nothing is claimed about them.

## Hypotheses (untested; each needs live calls)
1. V2 only serves ONE symbol per call now (the sprint-02 plan already says "called one symbol per request"; multi-symbol was never verified by a recorded payload; data.md §1.2 "several symbols per call" is uncited).
2. Multi-symbol needs a different body shape (e.g. different key, or a limit of a few symbols) that I cannot see.
3. A mixed list silently yields `[]`.

## Options
A. Treat as the spike result: V2 is single-symbol; drop platform.md §2.6 v1.10 step-2 batching, keep 1 symbol/call (~1,900 calls at 2 req/s ~ 16 min); BE-bars-batch becomes unnecessary. Fixture = none (or a 1-symbol fixture).
B. Re-run a small probe with a fresh cap (suggest <= 6 calls: 2 symbols both live; 2 symbols live+delisted; 5; 10; then 50 only if one of these works), after the sa agrees on the cap. I recommend B first, because a 2-symbol probe separates hypotheses 1-3 cheaply.
C. Ask the sponsor to allow a browser-captured request from vietcap's own web chart to see the real multi-symbol body.

## Recommendation
B (<= 6 calls, 2 live symbols first). If `[]` again, take A and correct data.md §1.2 V2 ("several symbols per call" -> unverified/not working as of 2026-10-24).
