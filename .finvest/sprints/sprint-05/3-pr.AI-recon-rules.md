# 3-pr AI-recon-rules (F-016, sprint-05)

## Round 1 — 2026-10-26, fi-tech-lead (BE) — CHANGES_REQUIRED

Reviewed head H = 333b7d4 (cb94171 + `chore` sync merge of origin/sprint-05 5d1976a, no conflicts, pushed).
Files reviewed: `services/analytics/finvest_analytics/adjust/recon.py`, `services/analytics/tests/test_recon.py`.
Size: 177 insertions vs ~130 planned (1.36x, under the 1.5x stop). File set exactly the plan's.

### Must-fix
1. `recon.py:59` — `diff_pct` can overflow `NUMERIC(8,4)` (max 9,999.9999), which the plan's signature line says it
   must fit (data.md §3 `recon_mismatches.diff_pct NUMERIC(8,4)`). The case that overflows is the exact one the G = 1 rule
   exists to catch: a source adapter left in thousand VND (theirs 93.5 vs ours 93,500) gives `diff_pct = 99900.0000`
   (probed on H), so the SA's recon CLI would die on numeric overflow at the insert instead of recording the
   `unit_or_adapter` row. Cap the value at `Decimal("9999.9999")` (one line, comment why). Test that must prove it:
   in `test_recon.py`, `reconcile([nom("2026-10-06", 93500)], [], [src("2026-10-06", "93.5")])` → one mismatch with
   `note == UNIT_OR_ADAPTER` and `diff_pct == Decimal("9999.9999")` (fails on H today: 99900.0000).

### Nits (no change required)
- `Mismatch.trading_date` instead of the plan's `date`: accepted (matches the `recon_mismatches` column, avoids shadowing
  `datetime.date`). Extra defaulted `note` field: accepted, documented in the build note.
- `summary` prints "1 mismatches"; fine for a log line, the plan's own example uses "k mismatches".
- `ref_check` / `round_to_tick` do not guard `tick <= 0`; the CLI passes a VN§3 tick, so leave it.

### Correctness review (accepted)
- No look-ahead: `G = cumulative(factors, d, last)` with `last = max(src trading_date)`; later ex-dates not applied (tested).
- Branch order right: `reconstructed` first, so a G = 1 pre-crawl row with a 2-dp A (≤ 0.5 VND off) is not flagged by the
  exact-equality rule; observed G = 1 → exact; observed G ≠ 1 → `> 0.1000 %`.
- Missing symbols and `checked == 0` never count as a pass in `summary`.
- Hand recompute (Decimal): 50,000 × 0.98 = 49,000.00; 100 / 48,900 × 100 = 0.2045; 20 / 48,980 × 100 = 0.0408 (G10);
  51,000 × 0.753846153846 = 38,446.15 → 0.15 VND (G8). All match the tests.
- Money in Decimal/int, pure module, no I/O, no secrets, no new dependency.

### Checks on H (q.sh)
- `make test-kernel`: exit 0 in 13s — 330 passed, 36 deselected; ruff clean; mypy 5 source files clean; lint-imports pass.
- No migration/SQL touched, so `-m db` not required.
