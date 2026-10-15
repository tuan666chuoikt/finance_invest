---
description: Testing — BE tester, then FE tester, on the synced sprint head
argument-hint: [be | fe]
---
Testing. Side: $ARGUMENTS (default both, BE first).

1. Dispatch `fi-be-tester` and/or `fi-fe-tester` (sonnet) with: sprint, worktree `test-<side>-NN` from
   `origin/sprint-NN`, "Follow briefs/common.md and briefs/tester.md".
2. Their test branches are reviewed and merged by `fi-tech-lead` like any task (dispatch it with the branch).
3. Relay verdict and pass/fail counts from the activity log; bugs become rework by owner stage.
