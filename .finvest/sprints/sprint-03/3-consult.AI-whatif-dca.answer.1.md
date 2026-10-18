# 3-consult AI-whatif-dca — answer (AI architect, 2026-10-18)

Question: size stop, +410/-73 vs plan ~215 (1.5x = 322), head `378d9f2`, lead must-fix 1–2 already fixed. Accept (A) or split (B)?

**Answer: A — accept as is. No dev round; lead may re-review head `378d9f2` and APPROVE.**

Why:
- Same estimate error as lumpsum, not a scope creep: the plan itself names `schedule` (day clamp, month wrap, after_end), per-row
  `contributions[]` with `how`, the `invested` step curve and goldens 005 (two end-date variants = 005 + 005b), 006, 007.
  ~200 counted only the code; ~175 production lines is at the estimate. The +235 is tests + 5 golden JSON the DoD requires.
- Splitting (B) would move 3 goldens + runner cases to a follow-up: zero correctness gain, one re-plan, one more review round,
  and AI-whatif-benchmarks (`after: AI-whatif-dca`) builds 009 on case 007, so that golden must land now anyway.
- The fix-round +28 (per-contribution fee rate + its test) is a correctness fix the lead required, not extra scope.

Documents updated (old plan archived as `2-tech-plan.ai.prev-2.md`; dag.json `dagRev` 2 → 3):
- `2-tech-plan.ai.md` AI-whatif-dca: Size ~200 → ~410 (actual, with reason); dag.json `AI-whatif-dca.size` 200 → 410.
- `2-tech-plan.ai.md` AI-whatif-benchmarks: Size ~180 → ~340 (same under-count: 3 goldens + `how` + tests ≈ 2x code;
  1.5x stop becomes 510); dag.json `AI-whatif-benchmarks.size` 180 → 340. Other AI blocks are already merged.

Not a sponsor decision (no scope, money or risk-policy change). needsSponsor = false.
