# 3-consult BE-jobs-crawl — architect answer (2026-10-24)

## Q1 size: **A — accept as is**, no split.
Every file in the diff is in the card's Files line; the acceptance list (7 cases + 3 must-fix tests) forces the test
volume, and thread + lock + route + migration are one unit. The overage is my estimate's error (BE tasks with a
background thread and failure-path tests run ~1.6x the prod lines, same lesson as FE-scenario-form).
- `2-tech-plan.md` BE-jobs-crawl: Size ~240 → ~350 (actual ≈ 500 ≤ 1.5 × 350 = 525). Old copy `2-tech-plan.prev-3.md`.
- `dag.json`: BE-jobs-crawl `size` 240 → 350, `dagRev` 6 → 7. Old copy `dag.prev-3.json`.

## Q2 contract gaps — platform.md is now **v1.9** (old copy `platform.prev-9.md`); code needs no change.
1. `sessions_added` = `COUNT(DISTINCT trading_date)` of `bars_1d_src` after step 2 minus before. Written into §2.6.
   `symbols_skipped` = a count, also written.
2. `count`: **accept the dev's reading** — older of the two table maxima, an empty table ignored, `COUNT` only when both
   are empty. Written into §2.6 with the consequence (empty `index_1d` → the job does not back-fill indices; `make backfill`
   does). Reason: the alternative (empty table → `COUNT`) would make every manual run a full back-fill while live VNINDEX
   stays empty (LIVE-03), burning the source rate budget; per-symbol MIN(MAX) is wrong for delisted symbols. Index
   back-fill through the job becomes a follow-up once the index source works (note for the pm, no new task now).
3. §1.3 fixed to `JOB_RUNNING` (code and §2.6 already agree). `apps/web/src/i18n/{en,vi}.json` line 41 still key
   `error.JOB_ALREADY_RUNNING` — renamed in FE-crawl-button (its file set), not in this PR.

Nothing here needs the sponsor. Lead: re-run the size check against Size ~350; the PR may proceed on the fix-round-1 code.
