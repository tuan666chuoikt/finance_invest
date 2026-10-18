# 3-pr FE-scenario-cards (F-056 / F-055 / F-048)

## Round 1 — APPROVE (reviewed head 8d15395383499ee3e1951e9c6e2784bc36801abe)
Branch already contains origin/sprint-03 (58156bb); no merge needed.
Files reviewed (9): ScenariosPage.tsx, ScenarioCard.tsx, CardMenu.tsx, states.tsx, routes.tsx, both tests, en.json, vi.json. All inside the planned file set.
Size: 258 non-test lines vs ~250 planned (1.03x), under the 1.5x stop.
Contract: money strings formatted only (no money math, sign from string); dates via formatDate (no new Date); approximate flag on envelope.approximate; benchmarks available/n-a never "0 %"; shifts, missing_sessions, below_one_lot rendered; one POST /whatif per card; error.code -> i18n.
UX: all states (Empty, NoBars + Add disabled, skeleton, UNREACHABLE -> ApiErrorState retry, per-card error + Edit), N hotkey, menu arrows/Esc, delete confirm. Each acceptance criterion has a test.
Checks: q.sh web-tsc exit 0; q.sh web-test exit 0, 10 files / 52 tests passed. No e2e infra in apps/web (same as FE-scenario-form); no e2e spec for this task.
Must-fix: none.
Nits / follow-ups (not blocking):
1. DOM order puts the card menu before the (i) buttons; UX keyboard line says (i) then menu. Reorder in a later task.
2. useWhatIf inherits retry:1 so a 422 card errors ~1s late; set retry:false for ApiError status < 500 in api.ts (outside this file set).
3. VN-Index "non-investable" is a title tooltip only (no keyboard-reachable equivalent); missing-sessions uses native <details>.
4. Column layout (3/2/1) untested in jsdom; tester to check 1024/768/360 px.

Merged into sprint-03: 97056f87506584ad6ce9441ba6675d75451dcf66
