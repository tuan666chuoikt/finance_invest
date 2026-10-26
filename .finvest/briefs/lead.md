# Tech lead brief (review and merge). Also follow common.md and your agent definition.

1. **Inputs:** `3-build.<TASK>.md`, the task card (`$FI_DIR/bin/task.sh <TASK>`), the cited contract /
   codebase / UX sections, any `3-consult.<TASK>*.md`, the previous `3-pr.<TASK>.md` round if any.
2. **Sync** the task branch with the latest `origin/sprint-NN` in its worktree (`git merge`). Resolve
   mechanical conflicts only, in a separate `chore(merge)` commit. A conflict that changes behaviour →
   BLOCKED.
3. **Review the whole diff, file by file** (`git diff origin/sprint-NN...HEAD -- <file>`), excluding
   lockfiles and generated files. Check: plan and file set, contract exactness, layering rules, tests
   that would fail without the change, error/empty/stale-data states, no secrets, no paid source.
   Size stop (retro S01 R2): run `git diff origin/sprint-NN...HEAD --shortstat`; if it exceeds 1.5× the block's
   `Size` and no `3-consult.<TASK>.md` exists, CHANGES_REQUIRED with must-fix 'size stop skipped'.
   Money/return code: recompute at least one acceptance example by hand (or a 5-line python snippet)
   and compare. Look-ahead bias in analytics (using data after the decision time) is always must-fix.
4. **Checks on the synced head:** the affected tests + the side kernel (codebase.md) via `q.sh`; the full
   side suite only for full-run paths; FE: the key e2e journeys + the PR's spec under
   `flock /tmp/fi-e2e.lock`. Classify reds honestly (flake only if it passes alone 3×).
5. **No green, no merge** (retro S01 R1). If the side kernel (or `-m db` for tasks that touch migrations,
   repositories or SQL) cannot run on the synced head, the verdict is `BLOCKED: checks not runnable`, never
   APPROVE. Record the q.sh summary line; 'not runnable' is not a pass. A UI task's PR without its 1280 light
   shot in the build note (dev.md step 6, retro S04 R3) → CHANGES_REQUIRED.
   **Verdict first.** Write/append a round to `SPRINT_DIR/3-pr.<TASK>.md`: `APPROVE` or
   `CHANGES_REQUIRED`, files reviewed, must-fix items (numbered, each with file:line and the test that
   must prove it), nits, check results with real numbers, the reviewed head sha H.
6. **Merge only on APPROVE:** `cd <worktree> && $FI_DIR/bin/sm.sh merge <TASK> <H>` (a `--no-ff` merge
   of H into `sprint-NN`, pushed under the merge lock; it refuses if the head moved). Record the merge
   sha in `3-pr.<TASK>.md`, then `git -C $FI_ROOT worktree remove <worktree>` if clean.
7. **Escalate** (return ESCALATE with owners sa|ai|pm) when the plan, contract or UX spec must decide.
8. **Log** `lead <TASK> merged|changes "<sha or must-fix count; checks>" 3-pr.<TASK>.md`; hand back ≤ 5 lines.
