# ADR-A-003 — Every ranking ships with its out-of-sample window; multiple-testing warning; survivorship-controlled universe
Status: Accepted · 2026-10-15

## Decision
`rank()` returns in-sample and OOS blocks together and the response schema marks `oos`/`pairs` required (PR-073, G5);
k rolling pairs with Spearman ρ show rank instability. Payloads state `n_scenarios` and the fixed VI/EN sentence that the
best of n is expected to look good by chance. Backtest universes are `symbols_as_of(start)` incl. later-delisted names,
with forced exit on delisting (PR-075). Sensitivity grids flag fragile optima (PR-074).

## Consequences
The API cannot serve the hindsight screen the sponsor could build by hand (L5); extra compute (2× windows) is inside N3.
Formal reality-check tests (White, Hansen) are out of scope v1; the plain-language warning carries the lesson.
