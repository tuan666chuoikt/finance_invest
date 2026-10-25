# 3-pr FE-fix-table
## Round 1: APPROVE (head 1aa757f8e444f77feb297656ce9b9f71fb88bb45)
Synced: merged origin/sprint-04 (FE-fix-panel, no conflicts) into the task branch.
Files reviewed: ScenarioTable.tsx, ScenarioTable.test.tsx, table.css (+26/-7, within ~60 estimate; no consult needed).
- BUG-2: pl_vnd uses a local signedVnd (explicit "+" only when Number(v) > 0; safer than the card's string check on "0.00"); arrow/cls take cell.num; sorting unchanged on num. Benchmark cells stay plain text via cell() as before (plan: behaviour unchanged).
- Worked example by hand: 51,290,559 - 50,000,000 = 1,290,559 VND; 1,290,559 / 50,000,000 = 2.581 % -> "+2,58 %". Matches the test.
- Contract visual-design §3.2: ▲/+ up, ▼/− down, = zero (--ref) identical to cards. OK.
- BUG-4: thead th white-space normal (.th-btn inherits via all: inherit), td.num keeps table nowrap, padding 0 8px. No column hidden. No short benchmark label exists in i18n; dev kept long label and lets the header wrap (accepted deviation, plan said "if one exists").
Must-fix: none.
Nits: none.
Checks (synced head): tsc exit 0; vitest 14 files / 87 tests pass. New test "gain and zero rows" verified by lead: 1 of 7 fails with the origin/sprint-04 ScenarioTable.tsx, all pass with the change. No Playwright e2e in repo; 1280 fit (scrollWidth <= clientWidth) left to tester FE-shots-rw per plan.
Merge: 5dd0944ca93024d5976032edf86749cb68d5c1d1 (into sprint-04 base 860af49; sprint-04 had moved past 931ce32 since sync, sm.sh merged cleanly)
