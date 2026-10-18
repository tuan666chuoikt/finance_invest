# 3-build FIX-index-value

Result: DONE. Branch task/sprint-03/FIX-index-value, head 0c0783c0e9c0bf28caedafa7f9806faef400d130. Diff +80/-11 (excl. fixture), plan size ~110.

## What changed
- `vci/source.py`: new `_value_vnd(av, ref, sym, day, raw)`; `_rows` yields raw `av`; `parse_bars` passes `ref = v*c`, `parse_index_bars` passes `None`.
  - Stocks: of `av` / `av*1e6` pick the one with ratio to `ref` closest to 1 (log distance). Index, or `v == 0`/`av <= 0`: `av >= 1e9` is VND else million.
  - Result `< 0` or `> 2**63-1` -> `None` + `log.warning("vci value dropped ... (raw: path)")`, bar kept.
- `vci/payloads.py`: docstring and field comment say mixed unit, cite VN30 2012-02-06 (raw) and 2026-10-16 (million).
- `feeds/bars_1d.py` unchanged.
- Fixture `tests/fixtures/vci/gap_chart/VN30-1d.json.gz`: one live V2 request (VN30, countBack 20000, 3,667 bars), trimmed to 59 bars (2012-02-06 .. 2026-10-16, envelope kept; the two 2018-01-23/24 zero-value days dropped; contains both unit eras and both era flips 2018-01-25, 2025-08-12).

## Contract honored
platform.md §4 v1.6 (`value` NULL on overflow), data.md §1.2 V2 v1.2 (mixed unit). Live finding: raw-VND era is 2012-02-06 .. 2025-08-11 (51 of 59 fixture bars), million era from 2025-08-12; real max over full history 3.76e13 VND.

## Checks
- ruff: All checks passed. mypy: no issues (5 files). lint-imports: kept (run before the final edit; no import change after).
- kernel `pytest -m "not db"`: 197 passed, 20 deselected.
- New tests: index unit x3 (222242000000 -> 222_242_000_000; 6386472.73 -> 6_386_472_730_000; 20000.5 -> 20_000_500_000), stock x2 (474963.63 and 474963630000 -> 474_963_630_000), BIGINT/negative -> None + 1 warning + bar kept, VN30 fixture (all values in (0, 2**63), max/min < 1e4, 2026-10-16 value 6_386_472_732_020 from raw 6386472.73202), feed test with VN30 fixture + FPT + VNINDEX: complete, 159 rows, index_1d holds VN30 and VNINDEX, summary line has `coverage`.

## Deviations
- Plan example "av = 1e13, v = 1, c = 1 -> None" cannot hold under the specified closest-to-1 rule: the raw reading 1e13 is closer to ref = 1 and fits BIGINT, so it returns 1e13. The test uses `v = 1e9, c = 1e8` (ref 1e17; million reading 1e19 > 2**63-1) and a negative `av`. Intent (overflow -> None, one warning, bar kept) is covered. SA may want to fix the example in the plan.
- Fixture is 59 bars (<= 60).

## Outside-set edits
None.

## Notes for the tester
Live check per plan (`make backfill`, `SELECT count(*) FROM bars_1d_src WHERE value IS NOT NULL AND value > 1000 * v * adj_c` = 0) not run here (host-owned data/). VN30 archive file name will be `VN30-1d-<count>`; existing stale archive files from before the fix store raw payloads, so replay re-parses with the new code, no re-fetch needed.
