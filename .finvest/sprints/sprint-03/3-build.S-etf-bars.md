# 3-build S-etf-bars (spike N3)
Result: DONE. Verdict: **covered, no follow-up task.**

Run: Sun 2026-10-18 20:18 VN (market closed, so data is final), anonymous, 2 requests ~1 s apart.

## Findings
- V2 gap-chart `E1VFVN30`, `ONE_DAY`, `countBack` 60: HTTP 200, 1 envelope entry, **60 bars**, first bar **2026-07-22**, last 2026-10-16.
  Fields as FPT (`o h l c v t accumulatedVolume accumulatedValue minBatchTruncTime`). Response body is gzip.
- Closes are already whole numbers (33200, 33250, 33000 ... 33450); after the x1000 half-up rule all 60 are integer VND. Min volume 104,200.
- V3 getAll (HTTP 200, 3,685 rows): `E1VFVN30` listed, `type` = `ETF`, `board` = `HSX`, organName "Quy ETF DCVFMVN30", icbCode2 8700. Table has 21 HSX/ETF rows.
  The symbols feed stores it, `make backfill` (universe = symbols table) covers it with no code change.
- Local DB count: not checked (no psql / DB on this machine).

## data.md §1.2-style row
| V2 (ETF) | `gap-chart` `symbols:["E1VFVN30"]` | ETF daily OHLCV | same envelope as stocks; 60 bars from countBack 60, closes integer VND, `v` units | Benchmark source for `benchmarks` (analytics §2.4) |
| V3 (ETF) | `symbols/getAll` | symbol master | `E1VFVN30`: type `ETF`, board `HSX` (21 HSX ETF rows) | covered by sprint-02 symbols feed |

## Files
- `services/crawler/tests/fixtures/vci/gap_chart/E1VFVN30-1d.json.gz` (1,361 bytes, exact response bytes, 60 bars, gzip -t ok).

## Deviations / notes
- Not checked: 15:00-23:00 window (run was a Sunday evening, 20:18, so no live session); full history depth (only 60 bars asked).
- No production code, no outside-set edits; kernel set untouched.
