# 6-retro — Sprint 01

Author: `fi-pm`, 2026-10-16. Inputs: 6-retro.input.md (cost + SM facts 1-9), activity.log, 5-review.tech.md,
5-review.product.md, 4-test.be.md.

## Velocity
- Committed 20 pts (F-020, F-030, F-010, F-011, F-017), accepted **20/20**. 8 BE tasks + 3 FIX tasks.
- **Decision: keep 20 points per sprint.** Measured equals assumed (0 % gap, re-plan threshold is 25 %). It is
  one data point and needed a fix loop (3 FIX tasks) to land, so 20 is the right number, not a floor to raise.
  roadmap.md velocity line updated from `[assumed]` to `[measured S01: 20/20]`.
- Cost: 45.60 USD API-equivalent for the whole session (sprint 0 + 1); main session 52 % (23.58).

## What went well
- 0 dead agents; build workflow 31 agents / 36 min, FIX run 9 agents / 7 min.
- Leads caught real defects in 4/8 tasks (scaffold /api path, schema test downgrading the app DB, stale crawler
  image, feed-ticks empty-tape + blocked-universe). Fix rounds closed every one in one round.
- Tester found the 3 field bugs a fixture suite could not (live crawl 10-15), with a strict-xfail repro;
  re-test 107/0, db 8/8.
- Live crawl 10-16 complete in 13 min (N5 ≤ 45 min now measured), 145,184 ticks, 0 blocks, 0 errors.
- Review split worked: architect owned plan-stage findings (F1/F3/F4), PM kept the `partial` label as a
  contract follow-up (S02-1) instead of a false rejection.

## What did not go well
1. **Main session ran outside FI_ROOT** for two days → fi-* agents not registered, workflow in portable mode
   (no maxTurns / omitClaudeMd / cacheTtl), main context ballooned → 52 % of cost.
2. **Size stop not enforced:** BE-schema 410 vs 200 lines; neither dev nor lead invoked the 1.5× stop.
   Root cause is also sizing: migration + db-test lines were not counted in the estimate.
3. **Merge without green checks:** FIX-only-validate approved and merged with pytest not runnable by dev or
   lead; db tests on FIX-universe-pinned unrun at merge. Only luck (SM kernel 82 pass, tester re-test) kept it safe.
4. **Time-bound live work had no clock:** the 10-15 live crawl was cut by an overnight restart; by morning
   the source no longer served 10-15 → 1,186 symbols lost forever (C1). M3 had a date, not a hour.
5. **Plan-stage defects:** 2 of 3 FAIL findings (archive-as-cache on non-session payloads, universe keyed by
   today) were assumptions about the live source that no fixture had checked. Plus the `partial` rule (§4)
   counted no-trade symbols as skips (fixed v1.3).
6. Tester ran `sm.sh push` from the main checkout and pushed `sprint-01` by accident (guard only blocks main/dev).
7. Containers write `data/` as root; sponsor needs sudo to clean (S02-2, backlog item, not an action here).

## Action items (≤ 5)

| # | Owner | File | Rule text to add / change | Sponsor |
|---|---|---|---|---|
| R1 | lead brief | `.finvest/briefs/lead.md` §6 | Add at the start of §6: "**No green, no merge.** If the side kernel (or `-m db` for tasks that touch migrations, repositories or SQL) cannot run on the synced head, the verdict is `BLOCKED: checks not runnable`, never APPROVE. Record the q.sh summary line; 'not runnable' is not a pass." | needs sponsor OK |
| R2 | lead brief + dev brief | `.finvest/briefs/lead.md` §3; `.finvest/briefs/dev.md` §3 | lead §3 add: "Run `git diff origin/sprint-NN...HEAD --shortstat`; if it exceeds 1.5× the block's `Size` and no `3-consult.<TASK>.md` exists, CHANGES_REQUIRED with must-fix 'size stop skipped'." dev §3 add: "Check the size before every push, not only at the end." | needs sponsor OK |
| R3 | sa | `.finvest/briefs/owner.md` "Task block format" (after the Keep-tasks line) | "Size counts production + test + migration lines. Every assumption about a live source's behaviour (which session a payload belongs to, what an empty response means, whether a list drifts by day) cites a recorded fixture or a data.md §1.2 line; uncited → an S-spike task before the build task." | needs sponsor OK |
| R4 | sm | `CLAUDE.md` "Running a sprint" step 1 + `.finvest/bin/sm.sh` `guard()` | CLAUDE.md: "Start every Finvest session with `cd $FI_ROOT` (`/home/stein/Desktop/Learning/finance_invest`); if `/agents` does not list fi-*, stop and restart there; `/compact` or `/fi-handoff` after each phase." sm.sh: `guard()` refuses `push` unless the branch matches `task/*` or `test/*` (`sprint-*` only via `sm.sh merge`). | needs sponsor OK |
| R5 | pm | `.claude/agents/fi-pm.md` "Sprint planning" | Add: "Any task that depends on a live source's serving window (tick crawl of a session) gets its own milestone with a clock deadline in `due` (`YYYY-MM-DD HH:MM` VN time, e.g. 'crawl 10-15 done by 2026-10-15 23:00'), owner sm, and a risk line saying what is lost if missed." | needs sponsor OK |

## Câu hỏi cho sponsor — A22
- **A22-R1:** Lead không được APPROVE khi không chạy được test (kernel/db), phải trả BLOCKED? Khuyến nghị: **đồng ý**.
- **A22-R2:** Lead tự trả CHANGES_REQUIRED khi diff vượt 1.5× Size mà dev không consult? Khuyến nghị: **đồng ý**.
- **A22-R3:** Size tính cả test + migration; mọi giả định về nguồn live phải dẫn fixture, không có thì làm spike trước? Khuyến nghị: **đồng ý**.
- **A22-R4:** Luôn mở session Finvest trong FI_ROOT (+ compact sau mỗi phase) và sm.sh chỉ cho push nhánh task/*, test/*? Khuyến nghị: **đồng ý**.
- **A22-R5:** Việc crawl live theo phiên được đặt milestone riêng có giờ hạn chót (giờ VN), owner sm? Khuyến nghị: **đồng ý**.
