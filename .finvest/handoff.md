# Finvest hand-off: read this first in a fresh session

Owner: the Scrum Master. Updated **2026-10-16 ~16:30**. Keep under ~6 KB: current state only. History lives in
git, `product/sponsor-answers.md` and the activity logs.

## 0. Start here
1. You must be running in FI_ROOT (`/agents` lists fi-*). If not, stop and tell the sponsor to restart there.
2. `CLAUDE.md` holds the rules (retro S01 rules R1–R5 applied 2026-10-16).
3. Run `.finvest/bin/progress.py`; read the last ~3 entries of `product/sponsor-answers.md`.

## 1. Status
- Sprint 0 done: PRD v2, backlog (71 stories), architecture (15 ADRs), A1–A22 answered.
- **Sprint 01 DONE** (20/20 pts; tech re-review PASS; PM 5/5 DONE; retro `sprints/sprint-01/6-retro.md`).
  Branch `sprint-01` pushed. **Waiting for the sponsor to merge `sprint-01` into `main`** (37+ commits).
- Velocity measured: 20 points/sprint.
- `current-sprint` still says sprint-01. Next: `/fi-sprint-plan` for sprint-02.

## 2. Sprint-02 inputs (from 5-review.product.md and 5-review.tech.md)
- S02-1 (high, before F-021): implement platform.md v1.3 §4 — no-trade symbols count as `complete`.
- S02-2: run containers as the host user and chown `data/` once (today data/ files are root-owned).
- S02-3: live re-run of 2026-10-16 gives the same checksum; `DATE=2026-10-14` must give `missed`.
- S02-4: remove the 1,186 stale empty tapes in `data/raw/ticks/2026-10-15/` (root-owned; needs S02-2 or sudo).
- S02-5: scheduler F-019 (nightly crawl). Until it lands, the SM/sponsor runs `make crawl` after 15:00 each
  trading day; plan it as a clock milestone (R5).

## 3. Running now
- Nothing. The compose stack (db + api) is UP on the sponsor's machine (127.0.0.1:8000).
- `.env` in FI_ROOT was copied from the tester's worktree so it matches the existing `data/pg`.
- Worktree `finance_invest-worktrees/test-be-01` (branch test/sprint-01/be, pushed 7ef36c8) still exists;
  its tests are not merged into sprint-01 yet — have a lead review/merge them early in sprint-02.

## 4. Data so far
- 225,520 ticks: 2026-10-15 partial (354/1540 symbols; rest lost), 2026-10-16 911 fetched + 629 no-trade.

## 5. Open decisions for the sponsor
- Merge sprint-01 → main. Next free label: **A23**.

## 6. Environment notes
- Linux; `flock`, `md5sum`; no `gh` (merges via `sm.sh merge`). `sm.sh push` only pushes task/* and test/*.
- Workflow: `.finvest/bin/finvest-sprint.workflow.js`; use `portable: true` only if fi-* agents are not loaded.

## 7. Cost
- Session 980c2e15 (sprint 0 + sprint 01): $45.60 API-equivalent; main session 52% (ran outside FI_ROOT,
  very long context). Measure with `FI_ROOT=<dir the session ran in> .finvest/bin/cost.py <session> --by-part`.
