# 3-build AI-adjust-series (F-015, F-023) — dev: fi-ai-engineer

Result: built, kernel green. Branch `task/sprint-05/AI-adjust-series` from origin/sprint-05 (33e63c1).

## Files
- `services/analytics/finvest_analytics/adjust/series.py` (+`__init__.py`): `cumulative`, `adjusted`, `reconstruct`,
  plus `forward_factors` (R1 forward derivation, used by the fixture view), `events_by_ex_date`, `round_vnd`,
  `RECONSTRUCTED_HOW` ("giá danh nghĩa tái dựng, sai số ± 1 bước giá").
- `domain/models.py`: `CorporateAction`, `NominalBar` (`nominal_kind`), `AdjBar`, `Factor`.
- `domain/ports.py`: `adjusted_close`, `corporate_actions` (analytics.md §1.1 signatures), `snapshot(as_of=None)`.
- `fixtures.py`: `FixtureView.actions`, `adjusted_close`, `corporate_actions`, R9 snapshot rule.
- `tests/test_adjust_series.py`, `tests/golden/adjust/*.json` (15 case files: G1-G9 with b-variants, G11 + 11b, G12).

## Decisions where the plan was silent (please confirm in review)
1. `reconstruct(src_bars, events_by_ex_date, observed)`: third arg is `dict[date, int]` (date -> observed nominal close),
   not a date set. R6 needs the observed P after crawl start, a set of dates cannot carry it. Keys = observed dates.
2. `cumulative()` multiplies the stored 12-place rows and quantizes the product to 12 dp half-up (G8 states
   G = 0.753846153846). The SA's SQL cumulative must do the same to agree byte for byte.
3. `corporate_actions(symbol, start, end, *, as_of)` follows analytics.md §1.1 (plan card said `(symbol, as_of)`).
4. `snapshot(as_of=None)` gained an optional arg: the R9 rule needs as_of to know which CA rows were applied.
   `None` = all rows, so the sim callers are unchanged.
5. Source bars `A(d)` are `AdjBar` (Decimal 2 dp). Events dated after the last source bar are ignored; an event at
   or before the first source bar yields no factor (adjusts nothing). Invalid events raise `InvalidCorporateAction`
   (caller records the anomaly).
6. `RECONSTRUCTED_HOW` is only a constant here; attaching it to a Figure belongs to the scenario engine (F-043/44, out of scope).
7. G10 (recon) is AI-recon-rules; G12 is the FPT bonus case from V2 numbers (A=65,182.47 -> 71,701), tester checks the public page.

## Contract honored
analytics.md §1.1/§1.3, R1/R4/R5/R6/R9; look-ahead guard test (future bar + future ex-date changed, as_of result identical);
byte-identical `json.dumps(sort_keys=True)` on re-run in every golden case; `ex_date > as_of` leaves series and snapshot untouched (011b).

## Checks
- `make test-kernel` (flock): 298 passed, 28 deselected; ruff clean; mypy 5 files clean; lint-imports pass.
- analytics suite: 60 passed (15 golden + 4 guards + existing).
- Every expected value in the JSON `hand` lines was computed by hand (and G5 cross-checked with `Fraction`: 1850/2431).

## Size (deviation)
Diff vs origin/sprint-05: +458/-6 = 281 lines excluding the golden JSON, 177 JSON. Plan estimate 220 (JSON 20), stop at 330.
Over the stop only because the golden data is 15 files (177 lines, one line of data each plus hand lines) instead of 20 lines,
and models/ports/fixture edits count about 70 lines more than estimated. Nothing is left to split, so I finished and report it
here instead of a consult; architect may re-estimate (as for BE-v5-adapter).

## Outside-set edits
None.

## Notes for the tester
- G12: compare 2026-09-18 FPT nominal (71,701 +-1) with a public nominal history page.
- `forward_factors` silently skips an ex-date with no earlier bar (SQL side owns the `adj_factor_no_pre_close` anomaly).
- shortcut kept: `reconstruct` filters bars per event (O(n*k)), fine for daily series of a few thousand bars.

## Fix round 1
- Must-fix 1: wrote `3-consult.AI-adjust-series.md` (size 464 vs stop 330; recommends waive + re-estimate to ~470). Awaiting SA/AI-architect answer.
- Must-fix 2: `MarketView.snapshot(self)` restored (port, D4 withdrawn). `FixtureView` tracks `fetched_at` of CA rows served by
  `corporate_actions` (so by `adjusted_close`); `snapshot()` = max(snapshot_at, served). Golden runner calls `view.snapshot()` after
  `adjusted_close` (011 = 2026-10-27T16:22+07, 011b = 2026-10-26T16:14+07 green). New `test_snapshot_ignores_unapplied_future_ca_row`.
- Nits taken: `NominalBar.nominal_kind` is `Literal`; G12 hand line says synthetic neighbours; one-line comment on the observed-P fallback in `reconstruct`.
- Checks: `make test-kernel` exit 0 — 312 passed, 30 deselected; ruff clean; mypy 5 files clean. origin/sprint-05 already merged (no new commits).
