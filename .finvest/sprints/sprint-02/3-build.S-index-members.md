# 3-build S-index-members (spike, no production code)

Result: both sources answer anonymously. Probed 2026-10-16 ~22:50 ICT, curl, ≤2 req/s, UA set. Note: bodies are gzip-encoded even without Accept-Encoding; use `--compressed`.

## Probes
| URL | HTTP | Rows | Symbol field | Notes |
|---|---|---|---|---|
| VCI getByGroup?group=VN30 | 200 | 30 | `symbol` | body is `[{"symbol":"ACB"},...]`, symbols only, 511 B. Matches SSI VN30 set exactly. |
| VCI ...group=HNX30 | 200 | 30 | `symbol` | differs from VN30 (not an echo) |
| VCI ...group=UPCOMLARGE | 200 | 0 | - | `[]`: no such group; not an error |
| VCI ...group=NOPE (unknown) | 200 | 0 | - | `[]`, no error: empty list is indistinguishable from "unknown group" |
| VCI ...group=HNX / UPCOM / VN100 | 200 | 299 / 814 / 100 | `symbol` | bonus: HNX 299 equals S1 hnx count, so group=HNX/UPCOM/HOSE-style exchange listings work as a cheap listing cross-check |
| SSI /stock/group/VN30 | 200 | 30 | `stockSymbol` | full S1-style rows (55 KB), `exchange`=hose |
| SSI /stock/group/HNX30 | 200 | 30 | `stockSymbol` | `exchange`=hnx |
| SSI /stock/group/NOPE | 200 | 0 | - | `{"code":"SUCCESS",...,"data":[]}` |
| SSI /stock/exchange/hose (S1) | 200 | 409 | `stockSymbol` | 727 KB; envelope `{code,message,data}` |

All lists are the CURRENT constituents only (no history, no effective date). Membership history would need our own daily snapshot.

## S1 firstTradingDate
Present on every row (409/409) as a string `yyyymmdd` (8 chars, e.g. `"20250513"`). Unknown/legacy is `"0"` (384 of 409 rows are `"0"`, only 25 carry a date). So treat `"0"` as null; do not use it as a listing date for the full universe.

## data.md §1.2 rows (paste)
| S1b | **SSI iBoard** `GET https://iboard-query.ssi.com.vn/stock/group/{VN30|HNX30}` | current index constituents | 30 rows each, full S1 row shape, `stockSymbol`; no history; unknown group = empty data, HTTP 200 | index membership flag (current only) |
| V6 | **VCI** `GET https://trading.vietcap.com.vn/api/price/symbols/getByGroup?group={VN30|HNX30|VN100|HNX|UPCOM}` | current group members, symbols only | 30 / 30 / 100 / 299 / 814 rows, field `symbol`; `UPCOMLARGE` and unknown groups return `[]` HTTP 200 | cheapest membership + per-exchange listing cross-check (tiny, 0.5 KB for VN30) |
Verdict: VCI V6 is preferred (small payload); SSI group is the fallback. There is no free UPCOM-large group; membership covers VN30, HNX30, VN100 only. BE-symbols-enrich can keep membership.

## Fixtures (gzip, committed)
- services/crawler/tests/fixtures/vci/index_members/{VN30,HNX30,UPCOMLARGE}.json.gz (exact bytes; UPCOMLARGE is `[]`)
- services/crawler/tests/fixtures/ssi/index_members/VN30.json.gz (first 8 of 30 rows, envelope kept, re-serialised compact JSON, 2.8 KB)
- services/crawler/tests/fixtures/ssi/exchange/hose.json.gz (46 rows: first 41 plus 5 with a real firstTradingDate, envelope kept, 10 KB)

Checks: no code or tests touched; make test-kernel not run (unaffected). Outside-set edits: none. Deviation: SSI fixtures are trimmed and re-serialised, not exact bytes (full responses exceed 20 KB); hose has 46 rows not 50 (≤50).
