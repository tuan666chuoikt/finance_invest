# 4-test FE — sprint-03, retest round 3 (fi-fe-tester)

**Verdict: PASS** — C1, C2, S1 verified fixed. Branch `test/sprint-03/fe` = origin/sprint-03 merged (8331959) + test edits. Previous: `4-test.fe.prev-2.md`.

| Bug | Result |
|---|---|
| C1 (POST /jobs 500 / unreachable) | FIXED: both cases show an error naming the cause (crawl-button.mjs "POST 500 INTERNAL", "POST network down") |
| C2 (double-click) | FIXED: exactly 1 POST, button disabled + aria-busy |
| S1 (top-bar targets) | FIXED: crawl button >= 24x24 at 375 px (and desktop check passes) |

Numbers: vitest 13 files / 81 tests green (no `it.fails` left; the earlier ones were already flipped). real-stack.mjs 40/40. crawl-button.mjs 44 pass / 3 fail — all 3 are "real idle" cases (button label, aria-busy, tab order) that cannot hold while the BE tester's real crawl job (id 5, running) is on the stack; they passed in round 2 and in an earlier run of this round when no job ran. Not an FE bug; all mocked-state cases pass.

Test maintenance: real-stack.mjs hard-coded FPT lump-sum numbers that drift with the live latest close (the crawl added new bars): updated 30.152.493 -> 29.673.693 and P/L −39,70 -> −40,65 % (API -40.6526, checked against /whatif). Suggest pinning sell_date in a later round.
Not checked: dark mode, real finished crawl, the three "real idle" cases while idle (re-run once the BE job ends).
