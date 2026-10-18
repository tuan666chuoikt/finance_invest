# Finvest hand-off: read this first in a fresh session

Owner: the Scrum Master. Updated **2026-10-16 ~23:30** (machine shut down by the sponsor's request). Keep under
~6 KB: current state only. History lives in git, `product/sponsor-answers.md` and the activity logs.

## 0. Start here
1. You must be running in FI_ROOT (`/agents` lists fi-*). If not, tell the sponsor to restart there.
2. `CLAUDE.md` holds the rules (retro S01 R1–R5 applied). **Autopilot:** the sponsor said (2026-10-16) "nếu không
   có gì quan trọng bạn cứ chạy đừng hỏi tôi" — run plan/build/test/review/retro/merge-to-main yourself; ask only
   for scope, money, data loss, irreversible or no-safe-default product questions.
3. `make up` (db + api) — the stack is down after the shutdown. Then `.finvest/bin/progress.py`.

## 1. Status
- Sprint 01 DONE and **merged into main** (0615915).
- **Sprint 02 building** (`current-sprint` = sprint-02, branch `sprint-02`): 9/10 workflow tasks merged
  (QA-S01-tests, BE-status-no-trades, OPS-host-user, BE-calendar, S-index-members, BE-scheduler,
  BE-symbols-feed, BE-bars-store, BE-symbols-enrich). **Left: BE-bars-backfill** (was in the workflow when the
  machine went down) + manual QA-S02-live and OPS-cleanup-1015.
  → Restart: Workflow `.finvest/bin/finvest-sprint.workflow.js` args
  `{sprint:"sprint-02", seats:{fe:0,be:2,ai:0}, leads:{fe:0,be:1}}` (add `portable:true` only if fi-* agents are
  not loaded). Merged tasks are detected and skipped; check `git ls-remote origin 'task/sprint-02/BE-bars-backfill'`
  and its worktree first (a half-built branch resumes as stage build/review).
- After sprint 02: /fi-test be, /fi-review, retro, merge sprint-02 → main, then sprint 03.
- **Timer installed** (`make install-timers`, systemd user timer): first unattended run Mon 2026-10-19 15:30.
  Runs only while the sponsor is logged in. Clock milestones C1–C5: each trading evening check the timer's
  manifest by 21:00; if missing, `make crawl` by hand before 23:00 (ticks are lost if missed).

## 2. Sprint 03 (next) — sponsor priority: investment scenarios + multi-scenario dashboard
- Sponsor (2026-10-16 23:1x): "bây giờ bạn bắt đầu tạo kịch bản… giao diện để theo dõi nhiều kịch bản… từ ngày nào
  đến ngày nào, bao nhiêu tiền". PM re-cut backlog/roadmap; UX `product/ux/scenario-dashboard.md`.
- `sprints/sprint-03/1-sprint-plan.md` done: 10 stories, 25 pts (F-031, F-032, F-006, F-040, F-041, F-057, F-055,
  F-056, F-048, F-051); results on adjusted prices carry an "approximate" flag (test-enforced).
- **AI architect was writing `sprints/sprint-03/2-tech-plan.ai.md` when the machine went down** — check whether the
  file exists/complete; if not, re-dispatch fi-ai-architect for it. Then fi-software-architect writes
  `2-tech-plan.md` (FE + API tasks) and `dag.json` merging both. Then set current-sprint=sprint-03 and build.
- Risk: F-048 needs VN-Index/E1VFVN30 daily bars — check BE-bars-backfill covers them.

## 3. Sprint-02 manual items
- QA-S02-live: re-run 2026-10-16 → same checksum; `DATE=2026-10-14` → `missed`; complete status on no-trade days.
- OPS-cleanup-1015: 1,186 stale empty tapes in `data/raw/ticks/2026-10-15/` are root-owned → give the sponsor one
  `sudo` command (only those files, verified empty) or leave them.

## 4. Data
- 225,520 ticks: 2026-10-15 partial (354/1540), 2026-10-16 911 fetched + 629 no-trade. Daily bars: pending backfill.

## 5. Environment
- Linux; `flock`, `md5sum`; no `gh` (merges via `sm.sh merge`; `sm.sh push` only task/* and test/*).
- `.env` in FI_ROOT matches the existing `data/pg` (copied from the tester's worktree).
- Next free sponsor label: **A23**.

## 6. Cost
- Session 980c2e15 (sprint 0 → sprint 02 build): ≈ $46 by 10-16 16:30 + sprint 02/03 planning since; main session
  ran outside FI_ROOT (52%). Start new sessions in FI_ROOT.
