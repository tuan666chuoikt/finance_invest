# 3-build FE-how-computed

Result: done. Branch task/sprint-03/FE-how-computed. 7 files, +285 lines (fixture JSON included).

Files: features/scenarios/{result.ts, figureText.ts, HowComputed.tsx (HowComputed + InfoButton), HowComputed.test.tsx, fixtures/envelope-001.json}; i18n en/vi (`how.*`, `approximate.source_adjusted`, `figure.*`; inserted mid-file to avoid merge conflicts with FE-shell-bar's tail edits).

Contract: analytics.md §1.1/§1.4/§2.4 mirrored; money shown as sent, no math.

Checks: typecheck exit 0; vitest 4 files / 18 tests passed (4 new: breakdown + approximate on/off, every-figure walk, Esc + focus return).

Deviations:
- InfoButton has a required `name` prop (leaf key -> `figure.<name>` label); HowComputed has optional `label`.
- Fixture cagr_pct is the real Figure (135906.7439 for 3 days), not null.
- Fixture JSON cannot use `satisfies WhatIfEnvelope` (JSON imports widen literals); test uses `as WhatIfEnvelope`.
- how.inputs shown with raw key names (no per-input labels); the heuristic prints 4-dp strings as % and integers plain.
- Benchmark index inputs ("1256.40") are made-up fixture numbers (not in AI plan).

Outside-set edits: none. Tester note: jsdom lacks dialog.showModal; test polyfills it. Run `npm ci` in the worktree (no shared node_modules).
