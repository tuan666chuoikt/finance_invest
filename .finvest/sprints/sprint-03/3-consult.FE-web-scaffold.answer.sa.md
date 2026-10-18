# 3-consult FE-web-scaffold — architect answer

Decision: **A — accept as-is.** No split.

Why (2-tech-plan.md lines 201-206, 212-232): all 18 files in the diff are named in the card's Files line (lines 201-206),
including `format.test.ts` and `i18n.test.ts`; the Change section requires `error.<code>` for *every* platform.md §1.3 + §2.5
code (line 219) and literal disclaimer lines in both JSON files (line 220); the Acceptance section mandates both test files
(lines 227-232). Nothing in the 412 lines is outside the card, so the overage is my estimate's error, not scope creep.
Largest files: format.ts 43, routes.tsx 38, TopBar.tsx 38, i18n/index.ts 36, i18n.test.ts 36 — all within the Change spec.

Option C (split i18n json + tests into a follow-up) would ship a scaffold whose `i18n.test.ts` key-set check and the
`error.*` keys FE-shell-bar / FE-disclaimer depend on arrive one PR later, for ~170 lines of static data and tests. Not worth it.

Corrections made (so the lead's size check passes, 412 ≤ 1.5 × 300):
- `2-tech-plan.md` line 200: Size ~230 → ~300 lines.
- `dag.json`: FE-web-scaffold `size` 230 → 300; `dagRev` 1 → 2.

Note for later estimates: an FE scaffold with 2 locale files + 2 test files runs ~300, not ~230.
