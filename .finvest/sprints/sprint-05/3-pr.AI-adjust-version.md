# 3-pr AI-adjust-version

## Round 1 (fi-tech-lead BE, 2026-10-26) — CHANGES_REQUIRED

Reviewed head **H = 33365abe62e21b65a0c55fa2a5c9dc10c0eaaf08**. Sync: the branch already contains origin/sprint-05 (130e2a7), so no merge was needed.
Files reviewed, all of them: `domain/models.py`, `adjust/series.py`, `adjust/recon.py`, `tests/test_adjust_series.py`,
`tests/test_recon.py`, `tests/golden/adjust/013-g13-versions.json`, `013b-g13b-version-gap.json`. File set = plan set.

### Must-fix
1. **Size stop skipped** (lead.md §3, retro S01 R2). `git diff origin/sprint-05...HEAD --shortstat`: 7 files, +227/-13 =
   240 lines. The block says `Size ~90` (25 prod + 50 tests + 15 golden), so the stop is at 135. No `3-consult.AI-adjust-version.md` exists.
   The excess is not scope creep: prod is 19/9 (the estimate was 25), tests are 67/4 (estimate 50) and golden JSON is 141 lines (estimate 15; two
   pretty-printed cases with 12 + 15 `src`/`src_last` rows each). The fix is the same as the AI-adjust-series precedent: write
   `3-consult.AI-adjust-version.md` to fi-ai-architect (option: waive and re-estimate to ~240). Also correct the build note. Its
   "Size: 86 insertions/13 deletions incl. tests+golden" leaves out the 141 golden lines; the real number is +227/-13.
   Proof: the consult file exists and the build note quotes the real shortstat. No code change is required.

### Correctness (verified, nothing to fix)
- R6a in `reconstruct`: observed P first. When `last_v < D`, P is the nominal of the prev row (no inversion). Otherwise it inverts with
  `G_v = cumulative(factors, D, last_v)`. Each row's nominal uses `b.last or last`. Events after the global newest bar
  still get no factor (the loop is still bounded by `e <= last`). There is no look-ahead: every G is bounded by the row's own version date.
- R7 in `reconcile`: `g = cumulative(factors, d, row.last or last)` per theirs row. `last=None` falls back to the list max, so
  callers that do not set `last` behave exactly as before. The only non-test `AdjBar(` call site is `series.py:58` (positional, 3 args),
  so the new field with its default breaks nothing.
- Hand check (Decimal, half-up): G13 P = 49,000 + 1,000 = 50,000, f = 1 − 1,000/50,000 = 0.980000000000, days 8–10 =
  49,000/0.98 = 50,000, days 1–7 = 50,000/1 = 50,000. The v1 rule gives round(50,000/0.98) = 51,020. G13b P = 50,000 without
  inversion, f = 0.98, days 12–16 = 49,000. All of these match the JSON.
- Fail-without check: I copied the package and restored `adjust/{series,recon}.py` from origin/sprint-05. On that copy 4 tests fail:
  golden 013 (days 1–7 = 51020), golden 013b, the Hypothesis property and `test_g13_recon_uses_each_rows_own_version_last`.
  The other 26 tests pass.
- G1–G12 are byte-identical: no golden file changed. The runner's new `recon_exact` output key is asserted only where a case expects it.
- The Hypothesis property is not vacuous. It runs on G7, G7b, G8 and G12 (G9 is skipped because it has an observed row). With `overlap=0`
  it uses the new `last_v < D` branch, and with `overlap≥1` it uses the inversion branch.
- Layering: lint-imports 5 kept, 0 broken. No new dependency (hypothesis was already in use). No SQL, no secrets, no network.

### Nits (optional)
- `series.py` `last_v < d` branch: `cumulative(factors, prev.trading_date, last_v)` is always 1 there, because `last_v ==
  prev.trading_date` and every factor so far has an ex-date after D. `round_vnd(prev.c)` says the same thing more plainly.
- The property always cuts before the *first* ex-date. Cutting between D1 and D2 of G8 would also test a V0 whose `G_v ≠ 1`.
- `test_snapshot_ignores_unapplied_future_ca_row` was reformatted (+5 lines), which is unrelated churn.
- G13b `hand`: "f = 49,000/50,000" should read `1 − 1,000/50,000`. The numbers are equal only by coincidence.

### Checks on H
- `make test-kernel` via q.sh, under the test lock: exit 0 in 13 s. **335 passed, 39 deselected**. ruff passed, mypy found no issues in 5 files,
  lint-imports 5 kept / 0 broken (`/tmp/fi-q/130311-kernel.log`).
- `-m db` was not run: the change has no migration, repository or SQL.

## Round 2 (fi-tech-lead BE, 2026-10-26) — APPROVE

Reviewed head **H = 33365abe62e21b65a0c55fa2a5c9dc10c0eaaf08** (unchanged since round 1: the fix round edited only `.finvest/` docs).
Sync: after a fresh fetch the branch still contains origin/sprint-05 (130e2a7), so there was nothing to merge. I re-read the prod diff of
`domain/models.py`, `adjust/series.py` and `adjust/recon.py`. It is identical to round 1, and round 1's correctness, hand-check and
fail-without findings still hold.

### Round 1 must-fix
1. Size stop: fixed. `3-consult.AI-adjust-version.md` now exists. It asks fi-ai-architect for option A (waive and re-estimate to ~240; precedent
   AI-adjust-series round 2). The build note now quotes the real shortstat (+227/-13, 7 files). The consult is still unanswered, and
   `Size` in `2-tech-plan.ai.md:125` and `dag.json` still says ~90. The architect should answer it and re-estimate. This does not block the merge
   (same handling as AI-adjust-series).

### Nits
Round 1's nits are still open and optional: drop the `cumulative(...)` that is always 1 in the `last_v < d` branch, cut the property between D1 and D2,
remove the unrelated reformat, and fix the G13b `hand` wording.

### Checks on H
- `make test-kernel` via q.sh, under the test lock: exit 0 in 12 s. **335 passed, 39 deselected**. ruff passed, mypy found no issues in 5 files,
  lint-imports 5 kept / 0 broken (`/tmp/fi-q/130542-kernel.log`).
- `-m db` was not run because the change has no migration, repository or SQL.

Merged: **97dcde1c5119a5a3ca8e2c050118043e21d47656** into sprint-05 (base 130e2a7, head 33365ab).
