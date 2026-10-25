# 3-pr FE-fix-panel
## Round 1: APPROVE (head 2329af3b12e20b43bfd4da7799500327d82a8814)
Files reviewed: panel.css, HowComputed.test.tsx (+15/-1, within ~50 estimate). Already in sync with origin/sprint-04.
Must-fix: none. Nit: lint script absent in apps/web (builder's "lint exit 0" not reproducible; no impact).
Checks: vitest 14 files / 86 tests pass; tsc exit 0. Test asserts weight 400, text-align not right, formula display block (spec §6.6 satisfied). Visual 375/1280 left to tester.
Merge: 931ce3243badd70a539db94beeeefc5d15057d33
