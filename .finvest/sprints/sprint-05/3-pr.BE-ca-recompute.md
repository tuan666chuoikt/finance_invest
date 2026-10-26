# 3-pr BE-ca-recompute (F-015)

## Round 1 — 2026-10-26, fi-tech-lead (BE)

**Verdict: CHANGES_REQUIRED + ESCALATE (owners ai, sa).** Must-fix 2 is a contract gap (R6 vs the card's
`newest_src_bars`, given how step 2 fetches). It needs an architect decision before the developer changes code.

Reviewed head: `7b8a340965e918ee7f15e0cd07ab2eb824d6263c`. Synced head H = `aaa907ca603755dd97a7c04316cca218d48fea69`
(clean `git merge origin/sprint-05`, no conflicts, pushed).
Files reviewed: `feeds/recompute.py`, `feeds/corporate_actions.py`, `cli.py`, `jobs/runner.py`, `tests/test_recompute.py`,
`apps/api/tests/test_jobs.py`, `services/crawler/pyproject.toml` (+ `uv.lock` 2 lines).
Size: 8 files, +298/-6 (296 without the lockfile) vs plan ~170, stop 255. No `3-consult.BE-ca-recompute.md`.

### Must-fix
1. **Size stop skipped** (lead.md §3, retro S01 R2). 296 lines > 255 and no consult. Write `SPRINT_DIR/3-consult.BE-ca-recompute.md`
   (why it grew, re-estimate) and put the questions from items 2–3 and nits a–b in it as well.
2. **Mixed source versions give silently wrong reconstructed prices (ESCALATED to ai + sa).** `recompute.py:_one` (the
   `distinct_on(trading_date)` query; `repo.newest_src_bars` does the same) takes the newest version *per date*. But step 2
   fetches only `_count(...)` sessions per press (`runner.py:45-53`, min 5). The full-history version therefore stays the one
   from the first pull, and each press adds a ~5-row version. data.md §1.4: the source re-adjusts the **whole** series on every
   ex-date. So after the first ex-date E after crawl start, the rows older than the short window come from a version that was
   **not** adjusted for E. `reconstruct` still divides them by G(d), which includes f_E (`last` = newest date).
   Checked with a script on the real `reconstruct`: true nominal 50,000 on every day, cash 1,000 ex E (f = 0.98); full pull
   before E plus a short pull after E gives a reconstructed **51,020** (+2.04 %) on every day of the old version; days 8–12 are correct.
   A 10 % bonus would make it +10 %. Every pre-crawl row of every symbol becomes wrong after its first live ex-date, and it is
   labelled `reconstructed`, not flagged. R6 itself says "the newest `bars_1d_src` version (fetched_at max; last = max
   trading_date of that version)". Taken literally, that version is only ~5 rows in steady state, so the plan does not cover this case.
   Options for the architect:
   - (A, recommended) each row divides by the G of **its own version**: `nominal(d) = A_v(d) / Π f_e` for `d < e ≤ last_v`,
     where `last_v` is the last date of the fetch that row came from. P stays observed whenever it exists (post-crawl
     ex-dates). This is an AI-owned change to `reconstruct` (an upto per row, or one call per version group).
   - (B) step 2 does a full `COUNT` re-pull of a name after an ex-date newer than its last full pull (costs source budget; SA).
   - (C) reconstruct only from the newest *full-history* version plus the observed rows.
   Test that must prove it: a db test with a full version F0 (before E) and a short version F1 (after E). It asserts that the
   rows before F1's window reconstruct to the true nominal (fails today: 51,020 vs 50,000).
3. **The recompute set can lose names for good.** `recompute_set` uses `bars_1d_src.fetched_at >= since`, but `fetched_at`
   is the archive file's mtime (`bars_1d.py:171-174`). Three cases leave names out:
   - a same-day replay of an archive written by an earlier press;
   - a press where step 2 is `blocked` (it raises before step 3 and `_recompute`);
   - a press where step 3 raises.
   In all three, the names step 2 wrote get no reconstructed rows until gap rotation fetches them again (~40 presses).
   Fix proposal (SA to confirm the set definition in the consult answer): names whose max `bars_1d_src.fetched_at` (vci) >
   their max `bars_1d.fetched_at` where `nominal_kind = 'reconstructed'`, or that have no reconstructed row (written rows carry
   the newest src `fetched_at`, so this heals itself), plus `changed_symbols`, filtered by `ca_checked_at`.
   Test: src rows with `fetched_at < since` and no reconstructed rows are in the set; after `recompute` they are not.
4. **The run-row reason is untested.** `test_jobs.py` fakes `_recompute` entirely, and nothing tests `append_reason`. The card's
   `"recompute: <n> symbols"` on the `corporate_actions` run row is part of the contract. Add a db test: reason NULL →
   `recompute: 2 symbols`; reason `x` → `x; recompute: 2 symbols`.

### Nits / for the consult
- a. Layering: `recompute.py` is the only crawler feed that imports `infrastructure.tables` and builds SQL. It has 5 queries:
  src rows, anomaly dedupe, ca ids, `recompute_set`, `append_reason`. Every other feed goes through `repo`. The import-linter
  is green, so this is not a must-fix. Better: extend `newest_src_bars` (OHLCV + fetched_at) and move the rest into
  `repositories.py`. That needs the file set extended, so ask in the consult.
- b. The skipped count is thrown away (`names, _ = recompute_set(...)` in `runner._recompute`), so "counted" is visible
  nowhere. The architect should decide whether the reason becomes `recompute: <n> symbols, <k> skipped`.
- c. G12 gives 71,700 (card: 71,701 ± 1, so OK). The 0.47 VND gap comes from `bars_1d_src.adj_*` being BIGINT, while R4 says
  sources carry 2 decimals. Every reconstructed row loses up to 0.5 VND before the division by G. Inside the stated ± 1 tick,
  but systematic. For sa.
- d. Related risk outside this PR: BE-market-view-ca's "newest `fetched_at` per date" read of `bars_1d_src` may mix versions
  the same way (item 2). The architect should check it together with item 2.

### Hand checks
- G7: P = 49,000 + 1,000 = 50,000; f = 49,000/50,000 = 0.980000000000; D−1 = 49,000/0.98 = 50,000; D−2 = 48,000/0.98 = 48,979.6 → 48,980. Matches.
- G9: f = 92,500/93,500 = 0.989304812834 from the observed P. Matches.
- G12: 65,182 / 0.909090909091 = 71,700.2 → 71,700. Matches the build note.
- The `_reconstruct` suffix search is sound: the walk runs newest-first and f_e depends only on newer factors, so the first
  suffix that fails names the culprit. It cannot loop forever: with no events, `reconstruct` never raises.

### Checks on H (real numbers)
- `make test-kernel` (q.sh lead-carec-kernel): exit 0, 331 passed, 44 deselected; ruff clean; mypy 5 files clean; import-linter 5 kept, 0 broken.
- `pytest -m db -rs` on a throwaway db (`finvest_lead_carec_test`, live db container, dropped after): exit 0, 44 passed (incl. 5 in `test_recompute.py`).
- Green, but the tests do not cover must-fix 2 or 3.

### Merge
Not merged. The worktree is kept for round 2.
