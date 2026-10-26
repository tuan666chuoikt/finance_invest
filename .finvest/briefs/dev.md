# Developer brief (FE / BE / AI). Also follow common.md and your agent definition.

0. **Read lean.** Your task card: `$FI_DIR/bin/task.sh <TASK>` prints your plan block and the sections it
   cites. Read it once; never search the whole tech plan. Read only the cited sections of contracts,
   codebase.md, data.md, analytics.md and UX specs (`rg -n` the heading, `sed -n` the range).
1. **Worktree:** `git -C $FI_ROOT fetch -q origin && git -C $FI_ROOT worktree add $WT/<TASK> -b
   task/sprint-NN/<TASK> origin/<base or sprint-NN>` (reuse it if it exists). Work only there.
2. **Build only your file set.** A one-line mechanical edit outside it is allowed; list it under
   `## Outside-set edits`. Anything larger or ambiguous: stop, write `SPRINT_DIR/3-consult.<TASK>.md`
   (question, options, your recommendation) and return CONSULTING.
3. **Size stop:** when `git diff origin/sprint-NN...HEAD --shortstat` (excluding lockfiles and generated
   files) passes **1.5×** the block's `Size`, stop: commit and push what works, write
   `3-consult.<TASK>.md` asking the architect to split the rest. Check the size before every push, not only at the end.
4. **Commit** small conventional commits (`feat(sim): ...`) on your task branch.
5. **Checks (once, then only the reds):**
   - typecheck + lint of the touched package;
   - the tests related to your change, plus the side's **kernel set** (codebase.md);
   - the full side suite only if you touched a full-run path (codebase.md lists them);
   - FE e2e: only your feature's own spec, once, under `flock /tmp/fi-e2e.lock`; on red, fix and rerun
     only the failures. Key journeys are run by the lead, not you;
   - money/return code: a test with a hand-computed expected value (fees, tax, lot rounding, dividends).
6. **Write** `SPRINT_DIR/3-build.<TASK>.md`: result, files, what changed, contract honored, checks with
   real numbers (q.sh summary lines), deviations, outside-set edits, notes for the tester.
   **UI task (retro S04 R3):** attach one 1280×800 light screenshot of the touched screen (`PW_DIR=/tmp/pw BASE=http://127.0.0.1:<your port>
   OUT=SPRINT_DIR/shots/<TASK> node apps/web/e2e/screens.mjs`, then keep only the touched screen; mocked API is fine; the
   script is on the sprint branch from S05 — if it is not, say so in the build note instead) — no shot, no PR.
7. **Push and PR:** `cd <worktree> && $FI_DIR/bin/sm.sh push` then `$FI_DIR/bin/sm.sh pr <TASK>`
   (opens a GitHub PR when `gh` exists; otherwise prints "branch-only", which is fine).
8. **Log** `dev <TASK> pr-open "<checks summary>" 3-build.<TASK>.md`, then hand back in ≤ 5 lines.
9. **Fix round** (you are a fresh agent): read only the must-fix list in `3-pr.<TASK>.md`, any
   `3-consult.<TASK>.answer.*.md` written since, `git diff origin/sprint-NN...HEAD --stat` and the files
   the items name. Merge `origin/sprint-NN` in, rerun only the affected checks plus each item's test,
   push, append a "Fix round n" section to `3-build.<TASK>.md`, log, hand back.
