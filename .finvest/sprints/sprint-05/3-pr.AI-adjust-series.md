# 3-pr AI-adjust-series — tech lead (BE/AI side)

## Round 1 — 2026-10-26 — CHANGES_REQUIRED

Reviewed head H = 65a1f6b (dev 38b6998 + sync merge of origin/sprint-05 a87190a, no conflicts, pushed).

### Files reviewed
adjust/__init__.py, adjust/series.py, domain/models.py, domain/ports.py, fixtures.py, tests/test_adjust_series.py,
tests/golden/adjust/*.json (15 files; read 008, 009, 011, 012 in full, runner checks the rest). File set = plan set, no
outside-set edits.

### Must-fix
1. **Size stop skipped** (lead.md §3, retro S01 R2). `--shortstat`: 21 files, +458/-6 = 464 lines vs block `Size ~220`
   (stop 330); no `3-consult.AI-adjust-series.md` exists. The build note's "report instead of consult" is not the process.
   Fix: write `SPRINT_DIR/3-consult.AI-adjust-series.md` to fi-ai-architect (re-estimate or trim; precedent
   `3-consult.BE-v5-adapter.answer.sa.md`, option A waive + re-estimate). I see no scope creep: file set unchanged,
   the excess is golden data (177 JSON lines, 15 files) + model/port/fixture lines.
2. **Port contract drift: `snapshot(self, as_of=None)`** — `domain/ports.py:18`, `fixtures.py:41`. analytics.md §1.1
   says `def snapshot(self) -> datetime  # max fetched_at of what it will serve`; the plan card says "Fixture
   `MarketView.snapshot()` = max fetched_at over bars served **and** CA rows applied". The change is not needed and is
   wrong by default: `snapshot()` with `None` counts **every** CA row, including ex_date > as_of, so any sim caller of a
   FixtureView with actions gets a snapshot moved by an unapplied future event (violates R9). It also diverges from
   `SqlMarketView`, which tracks served rows (`apps/api/finvest_api/market_view.py:20,49,63`) and keeps `snapshot(self)`.
   Fix: restore `snapshot(self) -> datetime` in the port; in `FixtureView`, record the max `fetched_at` of the CA rows
   that `adjusted_close` applied (and that `corporate_actions` served), same served-tracking pattern as `SqlMarketView._served`;
   `snapshot()` = max(snapshot_at, that). Tests that must prove it: golden runner calls `view.snapshot()` (no arg) after
   `adjusted_close` — 011 (= 2026-10-27T16:22+07) and 011b (= 2026-10-26T16:14+07) stay green; plus one test: a
   FixtureView holding only a future-ex-date CA row, after `adjusted_close(..., as_of=before ex_date)`, returns
   `snapshot() == snapshot_at` (fails on the current code's `None` path).

### Decisions from the build note
- D1 `reconstruct(..., observed: dict[date, int])`: accepted — R6 needs the observed P, a date set cannot carry it.
- D2 cumulative G quantized to 12 dp half-up: accepted (matches G8 `G = 0.753846153846`). **Note for SA /
  BE-market-view-ca**: the SQL cumulative must quantize the product the same way, or `adjusted_close` will differ in the
  last cent on long chains.
- D3 `corporate_actions(symbol, start, end, *, as_of)`: correct per analytics.md §1.1.
- D4 `snapshot(as_of=None)`: rejected, see must-fix 2.
- D5, D6 (`RECONSTRUCTED_HOW` constant only; Figure attachment is F-043/44), D7: accepted.

### Nits (optional)
- `NominalBar.nominal_kind: str` → `Literal["observed", "reconstructed"]` (`Literal` is already imported in models.py).
- G12 golden uses hand-made rows for 09-17/09-21/09-22; only the 09-18 value 65,182.47 is from V2. Fine since G12 is a
  tester check, not acceptance; say "synthetic neighbours" in its `hand` line.
- `reconstruct` takes P from `observed` only when the latest *source* bar before D is observed; if the source lacks a
  date that is observed, it falls back to inversion. Acceptable (source covers every trading day), worth a one-line comment.

### Correctness checked
- Look-ahead: `adjusted` filters bars `<= as_of` and `cumulative(..., upto=as_of)`; fixture feeds only bars/CA `<= as_of`;
  `test_no_look_ahead_shifted_future_changes_nothing` changes a future bar + future ex-date and asserts equality. OK.
- R6 inversion: `prev.c / cumulative(factors, d, last)` = A(D−1)/G(D) with only factors e > D present when walking
  backwards; events `> last` and `<= first` skipped; observed dates never emitted (G9). OK.
- Hand recompute (Decimal): G12 65,182.47 × 1.1 = 71,700.717 → 71,701; G8 38,446 / 0.753846153846 = 50,999.796 → 51,000;
  G4 (50,000 − 1,000 + 2,000)/1.2 = 42,500; 0.98 × 0.769230769231 = 0.75384615384638 → 0.753846153846. All match the JSON.

### Checks on H (65a1f6b)
- `make test-kernel` (flock, q.sh): exit 0 — 311 passed, 30 deselected; ruff clean; mypy 5 files clean; lint-imports 5 kept, 0 broken.
- `tests/test_adjust_series.py`: 18 passed.
- `-m db` not required (no migration/repository/SQL in this task).

## Round 2 — 2026-10-26 — APPROVE

Reviewed head H = 16bf674 (fix 6354a4f + sync merge of origin/sprint-05 ec4275a, no conflicts, pushed).

### Files reviewed
Whole diff again (21 files, +469/-5): adjust/series.py, adjust/__init__.py, domain/models.py, domain/ports.py, fixtures.py,
tests/test_adjust_series.py, golden 001, 006, 012 (changed). File set = plan set; sync merge touched no task file.

### Round 1 must-fix
1. Size stop: `3-consult.AI-adjust-series.md` now exists (option A, waive + re-estimate to ~470; excess is golden
   acceptance data, no scope creep, confirmed again). Size rule satisfied. **Open for fi-ai-architect:** answer the
   consult and re-estimate `Size` in `2-tech-plan.ai.md` / `dag.json` (dag still says the old value); not a merge blocker.
2. Fixed. `MarketView.snapshot(self) -> datetime` is back in the port (`ports.py:18`) as analytics.md §1.1 states.
   `FixtureView` records `fetched_at` of the CA rows `corporate_actions` serves (`fixtures.py:31-34`, bounded by
   `ex_date <= min(end, as_of)`), `adjusted_close` goes through it, `snapshot()` = max(snapshot_at, served) — same
   served-tracking pattern as `SqlMarketView`. New `test_snapshot_ignores_unapplied_future_ca_row` fails on the round-1
   code (the `None` path counted the future row's 2026-10-27 fetched_at). Golden 011/011b call `snapshot()` with no arg, green.

### Nits from round 1
All taken (`Literal` nominal_kind, G12 "synthetic neighbours", comment on the observed-P fallback in `reconstruct`).

### Note for BE-market-view-ca (SA)
`SqlMarketView` does not yet implement `adjusted_close` / `corporate_actions`; the port now requires them. Its task must
add both, track served CA `fetched_at` into `_served`, and quantize the cumulative factor to 12 dp half-up (D2).

### Correctness re-checked
Hand recompute (G6): f1 = 49,000/50,000 = 0.98; f2 = 10/13 = 0.769230769231; G = 0.753846153846;
51,000 × G = 38,446.153… → 38,446.15 = JSON. Look-ahead guards unchanged and green.

### Checks on H (16bf674)
- `make test-kernel` (flock, q.sh): exit 0 — 316 passed, 36 deselected; ruff clean; mypy 5 files clean; lint-imports 5 kept, 0 broken.
- `services/analytics/tests`: 61 passed; `test_adjust_series.py`: 19 passed.
- `-m db` not required (no migration/repository/SQL).

Merged: 695ca05 into sprint-05 (sm.sh merge, base ec4275a, head 16bf674).
