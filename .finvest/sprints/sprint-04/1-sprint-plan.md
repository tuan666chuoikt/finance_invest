# Sprint 04 — Plan

Owner: `fi-pm`, 2026-10-25. **Sun 2026-10-25 → Tue 2026-10-27 18:00** (short sprint, sponsor request A25).
Inputs: `product/sponsor-answers.md` A25, `product/backlog.md` (Sprint-04 slice), `product/ux/visual-design.md` (new),
`product/ux/app-shell.md`, `product/ux/scenario-dashboard.md`, `sprints/sprint-03/6-retro.md` (R3, R4, R5).

## Goal
**The web app looks like a real product.** By Tue 18:00 /scenarios and the shell use the design tokens and layout of
`ux/visual-design.md` — system sans font, tabular figures, VN board colours with ▲/▼/= cues, cards grid 1/2/3 columns,
table, side-panel form, how-computed drawer, all states — in light and dark, and the tester's 28 screenshots
(375 + 1280 px × light + dark) pass the §9 checklist. No behaviour change; every existing test stays green.

## Capacity
- Velocity **20 `[measured S01 20/20; S03 30/30 delivered over an extended 9 days]`**. Committed **18 pts** (2 pts buffer)
  because the sprint is only ~2.5 days and L1 needs the sponsor on Monday.
- First to slip: **S04-RW** items E2E pin, smoke, AI-3 (no user impact), then F-132's axe guard in dark (manual check
  instead). Never slipped: F-129, F-131 (the sponsor's request).

## Committed stories

| Story | Pts | Title | Order / depends on |
|---|---|---|---|
| F-129 | 5 | Design tokens + base stylesheet (light/dark, type, spacing, focus, buttons, inputs) | first; blocks F-130, F-131 |
| F-132 | 2 | Visual acceptance check: screenshot script + guards | parallel with F-129 (script needs only the running app) |
| F-130 | 3 | Shell look: top bar, disclaimer band, crawl status line, mobile | after F-129 |
| F-131 | 5 | Scenarios screen look: grid, card, table, form panel, how-computed, states | after F-129; parallel with F-130 |
| S04-RW | 3 | Carry-overs: T5b, T5c, T6, pin `sell_date` in real-stack.mjs, VNINDEX `value / v` smoke, AI notes 1–3 (F-048 wording) | parallel lane (BE/AI), any time |
| **Total** | **18** | | |

Acceptance criteria: `product/backlog.md` Sprint-04 slice. Decision time: n/a for F-129…F-132 (presentation only);
S04-RW AI-2 keeps F-048's decision time (same dates as the scenario).

## Definition of Done — addition for UI stories (from S04, A25 root cause)
On top of the CLAUDE.md DoD: **the FE tester attaches the screenshots of `ux/visual-design.md` §9.1 (375 and 1280 px,
light and dark) to `4-test.fe.md` and marks every §9.2 checklist line pass/fail against `visual-design.md`.** The PM
review opens them; a UI story without screenshots, or with a mismatch, is NOT DONE (stage `build`; spec gap → `backlog`).
Tech plans for any UI task name the CSS files they touch and include the look in their scope.

## Milestones

| Id | Name | Due (VN time) | Stories |
|---|---|---|---|
| M1 | Tokens + base stylesheet + guards in place | 2026-10-26 12:00 | F-129, F-132 (guards part) |
| L1 | Live crawl of the 10-26 session (retro R5, F-034 live acceptance), owner sm | 2026-10-26 23:00 | — (ops check) |
| M2 | Shell + scenarios screen styled; carry-overs merged | 2026-10-27 12:00 | F-130, F-131, S04-RW |
| M3 | Screenshots 28/28 checked, review, merge | 2026-10-27 18:00 | F-132 (screens), all |

**L1 (clock):** Mon 2026-10-26 the sponsor presses "Cào dữ liệu" after 15:00; sm confirms the 10-26 tick manifest and
the `crawl_runs` row by 23:00. The first full catch-up may need 2 presses ~1 h apart (VCI block). **Lost if missed: the
10-26 tick tape, for good.** sm reminds the sponsor at 15:00 (no timer since A23).

## Risks
1. **Short sprint (2.5 days)** — M1 slips → F-131 slips; mitigation: F-129 is CSS only and starts now; F-132 script in parallel.
2. **Tester browser:** screenshots need headless Chromium (Playwright) on the host; no system Chrome is installed. If it cannot
   be installed for free, the tester uses the Playwright-bundled browser (free, npm) — sm confirms before M1.
3. **Dark-mode contrast** of yellow (`--ref`) and cyan (`--floor`) on white is borderline; the spec darkens them, axe confirms.
4. **Behaviour regressions** from removing inline styles / adding classes: all 81 vitest + real-stack + crawl-button e2e must stay green.
5. **L1 needs the sponsor** on Monday afternoon; missed = 10-26 tape lost (does not block the sprint goal).
6. Open sponsor item **A24-D1** (size stop counts tests?) — until answered, the current rule (production + tests) applies;
   CSS lines count as production.
