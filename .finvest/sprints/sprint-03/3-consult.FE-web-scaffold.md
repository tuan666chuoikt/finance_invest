# 3-consult FE-web-scaffold (size overage)

Question: the non-lockfile diff is 412 insertions vs block Size ~230 (1.5x = 345). Accept the overage?

Breakdown: en.json + vi.json 56 lines; i18n.test.ts + format.test.ts 62 lines (tests for the hand-checked
pct/VND/U+2212 rules); `error.*` keys are required by platform.md 1.3/2.5; remaining ~294 is the card's file set.

Options:
A. Accept as is (all files are in the card's file set; no scope creep).
B. Trim tests/keys and re-add them in the next FE task (risks missing error.* keys in the scaffold).
C. Split: move i18n json + tests to a follow-up task.

Recommendation: A. Splitting costs another task + PR for ~170 lines of low-risk static data and tests.
