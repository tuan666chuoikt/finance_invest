
## Round 1 (fi-tech-lead FE) - CHANGES_REQUIRED
Head H=4917753d18f35f1ad2b6a6d59a90036eb5da5e9d (already up to date with origin/sprint-05, no merge needed).
Files reviewed: ScenarioCard.tsx, ScenarioCard.test.tsx, i18n/vi.json, en.json (+18/-3, within Size ~30; i18n key is an outside-set edit but allowed by the plan's "one-word key").
Code: correct. isBuy predicate shared by buyShifts and per-line filter; after_end/to:null renders "bỏ qua"; lump-sum lines unchanged; new test uses the real shape (5 contribution shifts) and asserts one dca-shifts line, "5 lần", zero "Ngày bán dời".
Checks (after npm ci in worktree): tsc exit 0; vitest 14 files / 94 tests pass.
Must-fix:
1. Build note has no 1280 light screenshot (lead.md step 5, retro S04 R3). Attach one (apps/web ScenarioCard with a DCA scenario, 1280 wide, light theme) to 3-build.FE-fix-dca-shifts.md; if no served build exists, run the dev server/vite from this branch to take it. No code change needed.
Nits: Shift.to typed string yet null handled via cast in test; acceptable, note for contract owner.

## Round 2 (fi-tech-lead FE) - APPROVE
Head H=3c07f77c458ce2402d6a969d17c60979e4087de7 (synced with origin/sprint-05). Must-fix 1 resolved: shots/FE-fix-dca-shifts/dca-card-1280-light.png attached in build note. No code change since round 1.
Checks: tsc exit 0; vitest 14 files / 94 tests pass. Fe05-widths DCA lines left to FE tester (FE-shots).
Merged into sprint-05: 70a16d5d1c5a0fb4f20e33e6837d51513c21282f (first sm.sh attempt refused because APPROVE was not yet written; redone).
