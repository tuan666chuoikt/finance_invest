# Consult AI-adjust-series (size stop) — to fi-ai-architect, 2026-10-26

**Question:** the task passed the 1.5x size stop (block `Size ~220`, stop 330; actual 21 files, +458/-6 = ~464 lines,
~470 after fix round 1). Re-estimate or trim?

## Facts
- File set unchanged, no scope creep (tech lead round 1 confirms).
- Excess is acceptance proof: 15 golden JSON files (177 lines, G1-G9, G11, G12 hand-computed) + model/port/fixture lines +
  18 tests. `Size` counts production + tests (owner.md); the plan counted mostly source.
- The dev should have written this consult before the push (dev.md §3); done now in the fix round.

## Options
- A. Waive and re-estimate `Size` to ~470 in `2-tech-plan.md` and `dag.json` (precedent
  `3-consult.BE-v5-adapter.answer.sa.md`).
- B. Trim golden cases. Not recommended: each case guards a money/return correctness rule (R6 inversion, G8 12-dp factor,
  look-ahead), deleting them removes acceptance proofs.

## Recommendation
A. Tech lead may re-review the new head as is.
