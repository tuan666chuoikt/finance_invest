# 3-build.S-v2-batch: DONE, verdict cap = 1 symbol per call (fresh run, rung 2 empty)

Result: no production code, no fixture (cap = 1, per acceptance). `make test-kernel` unaffected (no file changed besides this report).
Earlier attempt (5 x HTTP 418, 15:18) and the 9 x `200 []` calls are superseded; this run follows rev 2 of the plan and the sa answer (take B).

## Live calls (2 of the 6 allowed; by hand, curl, one at a time, >= 2 s apart, UA `finvest-personal/0.1 (+learning tool, single user)`, 2026-10-24 ~16:15 VN)
`to` = 1792861199 (Sat 2026-10-24 23:59:59 VN). Body shape as `_gap_chart`.
| # | body (symbols, countBack, to) | status | bytes | wall | symbols back / asked | bars per symbol |
|---|---|---|---|---|---|---|
| 1 | `["FPT"]`, 8, 1792861199 | 200 | 634 | 0.44 s | 1 / 1 | 8 |
| 2 | `["FPT","VNM"]`, 8, 1792861199 | 200 | 2 (`[]`) | 0.74 s | 0 / 2 | 0 |

Rung 1 control succeeded (client not blocked), rung 2 (two live HOSE names, same exchange) returned `[]`. Per the ladder the run stops at the first `[]` after rung 1, so rungs 3-6 were not made.

## Verdict
**cap = 50 / 1 / 1** : V2 `gap-chart` serves one symbol per call as of 2026-10-24. Even a live-only, same-exchange 2-name list gives `[]`, so hypothesis 3 (mixed exchanges) is ruled out, and the "several symbols per call" in data.md §1.2 V2 is not working. A different multi-symbol body shape (hypothesis 2) was not tested: it would need a captured browser request (option C, out of scope).
- Not measured (stopped by rule): delisted names omitted vs empty (rung 4); 50-name call latency vs 1-name control; back-fill shape. 1-name call ran 0.44 s, so the 6.7 s/name job average is not the source's latency (see the 418 side finding in the sa answer).
- Citation for BE-bars-batch: call 1 and 2 lines above. Set `BATCH_MAX = 1`; request figures ~1 780 at 2 req/s ~ 15 min.

## Outside-set edits
none. Spike scratch script: `scratchpad/call.sh` (not committed).
