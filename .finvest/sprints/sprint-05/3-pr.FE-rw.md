# 3-pr FE-rw round 1
APPROVE. Head H=36c111419d3f8209f2394c74d431d3eceb562c4b (synced with origin/sprint-05, clean ff-style merge commit, no conflicts).
Files reviewed: ScenarioCard.tsx, ScenarioTable.tsx, scenarios.css, table.css, shell.css, en/vi.json, 3 tests. Diff 56+/8- vs ~170 estimate.
Checks: tsc exit 0; vitest 14 files / 93 tests pass. e2e not run: scripts target the live stack (old build); 768/800 proof belongs to FE-shots. 1280 light shot present (shots/FE-rw).
Matches §4, §6.3, §6.4. Nits: DCA sell_date shift keeps its own line (dev flagged; tester to decide); no .btn-link class so summary styled locally; unused title only on vs_ columns (fine).
Merge sha: 80d47cb313010092b1bd957cd3236f927eb4544e
