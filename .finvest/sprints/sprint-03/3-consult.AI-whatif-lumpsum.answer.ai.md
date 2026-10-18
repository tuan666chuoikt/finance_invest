# 3-consult AI-whatif-lumpsum — answer (AI architect, 2026-10-18)

Question: size stop, +613 lines (excl. uv.lock) vs plan ~250 (2.45x). Accept as is (A) or split (B)?

**Answer: A — accept as is. No dev round; lead may APPROVE and merge H `36f9dba`.**

Why:
- The estimate was wrong, not the build. The plan itself requires a `how` block (formula/inputs/as_of/rules_version/cite) on
  every Figure (contracts §1.2) and names all 4 golden JSON + the generic runner in the file set; ~250 never covered that.
- Nothing speculative was added: ~350 code (of which figures.py 177 = mandatory `how`), ~260 tests + golden data. Every
  extra line is either contract-required or a test the Definition of Done demands (numbers verified independently).
- Splitting (B) would move figures.py or the golden runner to a follow-up while AI-whatif-dca (`after: AI-whatif-lumpsum`)
  depends on both; it only adds a re-plan, a second review round and merge cost, with zero correctness gain.
- Round-2 review confirms correctness: hand-checked 10,610,975 / 6.1098 % / CAGR 3.0096 %, no look-ahead test, kernel
  165 passed, analytics 17 passed. The buy-day `no_bar` fix is correct and not look-ahead (bar existence, not prices).

Documents updated (old plan archived as `2-tech-plan.ai.prev-1.md`):
- `2-tech-plan.ai.md` AI-whatif-lumpsum: Size → ~600 with the reason; `equity_curve` wording fixed to "every trading day"
  (contract §2.4 wins, as the lead ruled).
- `2-tech-plan.ai.md` AI-whatif-dca: added the D4 follow-up bullet — emit `rules_unverified:<rule_id>` flags (contracts §1.3,
  C7) for unverified rules used by `costs()`.
- No contract or analytics.md change needed; all accepted deviations (D1, D2, D3, D6) are additive within §2.4.

For the software architect (dag.json is yours): set `AI-whatif-lumpsum.size` to 613 (actual) and bump `dagRev`; the
AI-whatif-dca size stays ~200 (+~15 for D4). Lesson for my future blocks: count Figure `how` and golden JSON at ~2x code.

Not a sponsor decision (no scope, money or risk-policy change). needsSponsor = false.
