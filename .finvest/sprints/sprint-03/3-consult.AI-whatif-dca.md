# 3-consult AI-whatif-dca (size stop, written in fix round 1 per 3-pr must-fix 1)

To: AI architect. Work is complete and green; no code left to write.

Actual size vs plan (~200 + ~15 D4 = ~215; 1.5x = 322): `git diff origin/sprint-03...HEAD --shortstat`
10 files, +410 / -73 (95b7fc6 was +382 / -71; fix round 1 adds ~+28 for the per-contribution fee-rate fix and its test).
Production code ~175 (sim/dca.py 35, sim/whatif.py, sim/figures.py); tests + 5 golden JSON ~+238.
Why: DCA needs the schedule (day clamp, month wrap, leap, after_end), per-row `contributions[]` with `how`, the invested
step curve and four hand-computed goldens (005, 005b, 006, 007; plan listed fewer); the plan undercounted tests/golden again
(same as lumpsum).

Options
A. Accept as is (recommended): overrun is mandatory Figure `how`, golden/test data, nothing speculative; splitting now
   only adds a re-plan and a second review round.
B. Split: move the 3 extra goldens + their runner cases to a follow-up task. Costs a re-plan and merge work.

Recommendation: A. Please answer in `3-consult.AI-whatif-dca.answer.1.md`; the lead re-reviews once it exists.
