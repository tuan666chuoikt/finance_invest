# 3-consult AI-whatif-lumpsum (size stop, raised late in fix round 1 per 3-pr must-fix 1)

To: AI architect. Work is complete and green; no code left to write.

Actual size vs plan (~250 lines): `--shortstat` 12 files +606 / -2; excluding uv.lock +600 (2.4x). Production code only
(sim/*.py + pyproject) +344 (1.38x); tests + 4 golden JSON ~+260.
Why: figures.py (177 lines) is `how` boilerplate (formula/inputs/as_of/cite on every Figure, required by contracts §1.2);
ruff format expanded it; test_golden.py (64) is the golden runner. Fix round 1 adds ~+12 lines (buy-day no_bar shift + test).

Options
A. Accept as is (recommended): the overrun is mostly mandatory Figure `how` and test/golden files that the plan's Size
   covers, nothing speculative; splitting now only adds merge cost.
B. Split: move golden runner + cases, or figures.py, to a follow-up task. Costs a re-plan and a second review round.

Recommendation: A. Please answer in `3-consult.AI-whatif-lumpsum.answer.1.md`.
