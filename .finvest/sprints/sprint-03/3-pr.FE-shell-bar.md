# 3-pr FE-shell-bar - round 1
Verdict: CHANGES_REQUIRED. Reviewed head H=a5a2dcf (task branch synced with origin/sprint-03, clean auto-merge).
Files reviewed: all 10 in the plan set (TopBar, LangSwitch, FreshnessChip, ApiErrorState, useBarsStatus, useHotkey, 2 tests, en/vi.json). Size 249+/24- vs plan ~210 (<=1.5x, ok). Code matches plan/contract; stale weekday shortcut is commented; Alt+L ignores inputs.
Checks on synced head: vitest 5 failed | 16 passed (1 file failed); tsc/vite build exit 0.
Must-fix:
1. src/app/disclaimer.test.tsx (from FE-disclaimer, now in sprint-03) renders routeObjects -> Layout -> TopBar -> FreshnessChip -> useBarsStatus with no QueryClientProvider: "No QueryClient set" (5 tests red: /scenarios, /data-quality, /rules, vi, en). Fix: wrap `at()` in that test with a QueryClientProvider (fetch stubbed) - preferred, App.tsx stays untouched per plan - and keep the test green. Proof: `npx vitest run` fully green on the synced head. (Touching disclaimer.test.tsx is an allowed outside-set edit; record it in 3-build.)
Nits: none.

# 3-pr FE-shell-bar - round 2
Verdict: APPROVE. Reviewed head H=8bfaa313d9481ad09dfb6e08f7b1e53f6256c335 (already up to date with origin/sprint-03).
Files reviewed: round-1 set + disclaimer.test.tsx fix (QueryClientProvider + stubbed fetch; outside-set, recorded in 3-build). Size 260+/26- vs plan ~210 (<=1.5x).
Must-fix 1 resolved. Nits: none.
Checks: vitest 5 files, 21/21 passed; tsc exit 0; no e2e suite exists in apps/web yet.
Merged into sprint-03: deda013a403663bc9c294fd06ca292da57368a37
