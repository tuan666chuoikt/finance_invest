# 3-pr FE-how-computed — round 1
**APPROVE** (head 346ded642b5acfd8e6f346dd188c3ac46afffb64, synced with origin/sprint-03 by clean auto-merge, no conflicts)
Files reviewed: result.ts, figureText.ts, HowComputed.tsx, HowComputed.test.tsx, fixtures/envelope-001.json, i18n en/vi. Only the planned set. Size 285 lines incl. 39-line fixture vs ~200 (1.43x, under 1.5x).
Contract: types mirror analytics §1.1/§1.4/§2.4; decimals stay strings; cagr_pct nullable; approximate text via i18n key. Fixture liquidation 635975+10000000-15000-10000=10610975 ok.
Checks (synced head): typecheck exit 0; vitest 6 files / 25 tests passed. No route/e2e journey in this PR.
Nits (no block): inputText prints 4-dp ratios like fee_rate 0.0015 as a percent (0,0015 %) – wrong unit semantics, revisit with per-input labels; price_basis shown as raw enum.
Merge sha: ccf6c1f6a2abe5ebeb187401895d43a210189dbf
