# Tester brief (FE / BE). Also follow common.md and your agent definition.

1. **Inputs:** `1-sprint-plan.md` (stories in scope), the backlog acceptance criteria of those stories
   (`rg -n 'F-0xx' backlog.md` then `sed -n`), the cited contracts/UX sections, the `3-build.*.md`
   "for the tester" notes. Test on the synced `sprint-NN` head in your own worktree `test-<side>-NN`.
2. **Never edit code under test.** Your files are tests, fixtures and your report only. A product bug
   goes in the report with steps, expected vs actual, and the owner stage (build/plan/...).
3. **Coverage map:** every acceptance criterion → at least one test that would fail without the
   feature. Write the map as a table in your report.
4. **What to attack:**
   - BE: API contract exactness; crawler idempotency (re-run same day → no duplicates); gaps and
     out-of-order ticks; market-closed days and holidays; corporate actions (split, bonus shares,
     cash dividend) in adjusted series; what-if/backtest numbers vs an independent spreadsheet-style
     calculation (fees, 0.1% sell tax, lot 100, T+2); look-ahead bias; rate-limit and source-down
     behaviour; injection on symbol/date params.
   - FE: price board realtime updates (colour rules ceiling/floor/reference), stale-data banner, empty
     and error states, number/date formatting (vi-VN), keyboard and screen-reader access, mobile width.
5. **Run once, rerun reds only**, through `q.sh`; e2e under `flock /tmp/fi-e2e.lock`.
6. **Report** `SPRINT_DIR/4-test.<side>.md`: verdict PASS/FAIL, coverage map, bugs, real numbers.
   Commit your tests on `test/sprint-NN/<side>` and push with `sm.sh push`; the lead merges them.
7. **Log** `<fe|be>-test <story-or-batch> green|red "<pass/fail counts>" 4-test.<side>.md`; hand back ≤ 5 lines.
